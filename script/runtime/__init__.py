import inspect
from typing import Union
import aiohttp

from .. import astutil

endpoint = 'http://127.0.0.1:8188/'
prompt = {}
count = -1

def assign_id() -> str:
    global count
    count += 1
    return str(count)

def positional_args_to_keyword(node: dict, args: tuple) -> dict:
    args = list(args)
    kwargs = {}
    for group in 'required', 'optional':
        group: dict = node['input'].get(group)
        if group is None:
            continue
        for name in group:
            kwargs[name] = args.pop(0)
            if len(args) == 0:
                return kwargs
    if len(args) != 0:
        print(f'Ib Custom Nodes: {node["name"]} has more positional arguments than expected: {args}')
    return kwargs

def get_type_stub(node: dict, class_id: str, type_callback) -> str:
    def to_type_hint(type: Union[str, list], optional: bool = False) -> str:
        if isinstance(type, list):
            # c = 'list[str]'
            c = f'Literal[\n    {f",{chr(10)}    ".join(astutil.to_str(s) for s in type)}\n    ]'
        elif type == 'INT':
            c = 'int'
        elif type == 'FLOAT':
            c = 'float'
        elif type == 'STRING':
            c = 'str'
        elif type == 'BOOLEAN':
            c = 'bool'
        else:
            type_id = astutil.str_to_class_id(type)
            type_callback(type_id)
            c = type_id
        if optional:
            # c = f'Optional[{c}]'
            c = f'{c} | None'
        return c

    inputs = []
    for (group, optional) in ('required', False), ('optional', True):
        group: dict = node['input'].get(group)
        if group is None:
            continue
        for name, config in group.items():
            inputs.append(f'{name}: {to_type_hint(config[0], optional)}')
    c = f'def {class_id}({", ".join(inputs)})'

    outputs = len(node['output'])
    if outputs >= 2:
        c += f' -> tuple[{", ".join(to_type_hint(type) for type in node["output"])}]'
    elif outputs == 1:
        c += f' -> {to_type_hint(node["output"][0])}'
    
    return c + ': ...'

async def load(api_endpoint: str = endpoint, vars: dict = None):
    global prompt, endpoint

    endpoint = api_endpoint

    if vars is None:
        vars = inspect.currentframe().f_back.f_locals

    async with aiohttp.ClientSession() as session:
        # http://127.0.0.1:8188/object_info
        async with session.get(f'{endpoint}object_info') as response:
            assert response.status == 200
            nodes = await response.json()

    print(f'Nodes: {len(nodes)}')

    type_stubs = {}
    def add_type_stub(type_id: str):
        nonlocal type_stubs
        if type_id not in type_stubs:
            type_stubs[type_id] = f'class {type_id}: ...'
    node_stubs = ''

    for node in nodes.values():
        class_id = astutil.str_to_class_id(node['name'])

        def f(*args, _comfyscript_node=node,  **kwargs):
            global prompt

            node = _comfyscript_node
            # print(node['name'], args, kwargs)

            id = assign_id()

            prompt[id] = {
                'inputs': positional_args_to_keyword(node, args) | kwargs,
                'class_type': node['name'],
            }

            outputs = len(node['output'])
            if outputs == 0:
                return
            elif outputs == 1:
                return [id, 0]
            else:
                return [[id, i] for i in range(outputs)]
        
        vars[class_id] = f

        node_stubs += get_type_stub(node, class_id, add_type_stub) + '\n'
    
    # __init__.pyi
    with open(__file__ + 'i', 'w') as f:
        f.write(
'''from typing import Literal

class ComfyScript:
    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc_value, traceback): ...

''')
        f.write('\n'.join(type_stubs.values()) + '\n\n')
        f.write(node_stubs)

def clear_prompt():
    global prompt, count
    prompt = {}
    count = -1

async def queue_prompt():
    global prompt, endpoint
    # print(prompt)
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{endpoint}prompt', json={'prompt': prompt}) as response:
            assert response.status == 200
            return await response.json()

# TODO: Make prompt local to ComfyScript
class ComfyScript:
    async def __aenter__(self):
        clear_prompt()

    async def __aexit__(self, exc_type, exc_value, traceback):
        print(await queue_prompt())

__all__ = ['load', 'clear_prompt', 'queue_prompt', 'ComfyScript']