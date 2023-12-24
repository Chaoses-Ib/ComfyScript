import asyncio
import inspect
import threading
from typing import Union
import uuid
import aiohttp

from .. import astutil

endpoint = 'http://127.0.0.1:8188/'
client_id = str(uuid.uuid4())
prompt = {}
count = -1
daemon_thread = None

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

async def load(api_endpoint: str = endpoint, vars: dict = None, daemon: bool = True):
    global prompt, endpoint, daemon_thread

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
    
    if daemon and daemon_thread is None:
        daemon_thread = threading.Thread(target=asyncio.run, args=(watch(),), daemon=True)
        daemon_thread.start()
        # TODO: Kill daemon thread if daemon turns to False

async def watch():
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f'{endpoint}ws?clientId={client_id}') as ws:
                queue_remaining = 0
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        msg = msg.json()
                        # print(msg)
                        if msg['type'] == 'status':
                            data = msg['data']
                            new_queue_remaining = data['status']['exec_info']['queue_remaining']
                            if queue_remaining != new_queue_remaining:
                                queue_remaining = new_queue_remaining
                                print(f'Queue remaining: {queue_remaining}')
                        elif msg['type'] == 'progress':
                            data = msg['data']
                            print_progress(data['value'], data['max'])
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
        await asyncio.sleep(1)
    '''
    {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 0}}, 'sid': 'adc24049-b013-4a58-956b-edbc591dc6e2'}}
    {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 1}}}}
    {'type': 'execution_start', 'data': {'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'execution_cached', 'data': {'nodes': ['9', '15', '5', '8', '12', '13', '16', '6', '1', '14', '0', '2', '20', '11', '17', '7', '10', '19', '3', '4', '18'], 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'executing', 'data': {'node': '21', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'progress', 'data': {'value': 1, 'max': 15}}
    ...
    {'type': 'progress', 'data': {'value': 15, 'max': 15}}
    {'type': 'executing', 'data': {'node': '22', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'executing', 'data': {'node': '23', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'executed', 'data': {'node': '23', 'output': {'images': [{'filename': 'C_00001_.png', 'subfolder': '', 'type': 'output'}]}, 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 0}}}}
    {'type': 'executing', 'data': {'node': None, 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    '''

def clear_prompt():
    global prompt, count
    prompt = {}
    count = -1

async def queue_prompt(source = None):
    global prompt, endpoint, client_id

    if source is None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])

    # print(prompt)
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{endpoint}prompt', json={
            'prompt': prompt,
            'extra_data': {
                'extra_pnginfo': {
                    'ComfyScriptSource': source
                }
            },
            'client_id': client_id,
        }) as response:
            assert response.status == 200
            return await response.json()

def print_progress(iteration, total, prefix = '', suffix = '', decimals = 0, length = 50, fill = '█', printEnd = '\r'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    
    From https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    """
    percent = ("{0:3." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix}{percent}%|{bar}| {iteration}/{total}{suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

async def wait_prompt(prompt_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f'{endpoint}ws?clientId={client_id}') as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    msg = msg.json()
                    # print(msg)
                    if msg['type'] == 'status':
                        data = msg['data']
                        if data['status']['exec_info']['queue_remaining'] == 0:
                            break
                    elif msg['type'] == 'executing':
                        data = msg['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break
                    elif msg['type'] == 'progress':
                        data = msg['data']
                        print_progress(data['value'], data['max'])
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break

async def exec_prompt(source = None):
    '''
    Queue a prompt and wait for it to finish.
    '''
    if source is None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
    
    response = await queue_prompt(source)
    print(response)
    await wait_prompt(response['prompt_id'])

# TODO: Make prompt local to ComfyScript
class ComfyScript:
    def __init__(self, wait: bool = False):
        '''
        - `wait`: Wait for the prompt to finish before exiting the context manager.
        '''
        self.wait_prompt = wait

    async def __aenter__(self):
        clear_prompt()

    async def __aexit__(self, exc_type, exc_value, traceback):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        response = await queue_prompt(source)
        # TODO: Fix multi-thread print
        # print(response)
        if self.wait_prompt:
            await wait_prompt(response['prompt_id'])

__all__ = [
    'load',
    'clear_prompt',
    'queue_prompt',
    'wait_prompt',
    'exec_prompt',
    'ComfyScript'
]