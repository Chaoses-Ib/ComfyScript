from typing import Union

from .. import astutil
from . import node

def _remove_extension(path: str) -> str:
    for ext in (
        # `supported_pt_extensions`
        '.ckpt', '.pt', '.bin', '.pth', '.safetensors',
        '.vae.pt', '.vae.safetensors',
        '.yaml'
    ):
        path = path.removesuffix(ext)
    return path

def is_bool_enum(enum: list[str]) -> (bool, bool):
    if len(enum) != 2:
        return False
    lower = [s.lower() for s in enum]
    if lower == ['enable', 'disable'] or lower == ['on', 'off']:
        return True
    elif lower == ['disable', 'enable'] or lower == ['off', 'on']:
        return True
    return False

def bool_enum_default(enum: list[str]) -> bool:
    lower = enum[0].lower()
    if lower in ('enable', 'on'):
        return True
    elif lower in ('disable', 'off'):
        return False
    raise ValueError(f'Invalid bool enum: {enum}')

def to_bool_enum(enum: list[str], b: bool) -> str:
    if bool_enum_default(enum) == b:
        return enum[0]
    else:
        return enum[1]

class RuntimeFactory:
    def __init__(self, vars: dict, prompt: dict):
        self._vars = vars
        self._prompt = prompt
        self._data_type_stubs = {}
        self._node_type_stubs = []

    def add_node(self, info: dict) -> dict:
        class_id = astutil.str_to_class_id(info['name'])
        enums = {}
        enum_type_stubs = ''
        input_defaults = {}

        def to_type_hint(type_info: Union[str, list], name: str = None, optional: bool = False, default = None) -> str:
            nonlocal enum_type_stubs

            if isinstance(type_info, list):
                if is_bool_enum(type_info):
                    c = 'bool'
                    if default is None:
                        default = bool_enum_default(type_info)
                else:
                    # c = 'list[str]'

                    # c = f'Literal[\n        {f",{chr(10)}        ".join(astutil.to_str(s) for s in type)}\n        ]'

                    # TODO: Group by directory?
                    enum_c, enum = astutil.to_str_enum(name, { _remove_extension(s): s for s in type_info }, '    ')
                    enum_type_stubs += '\n' + enum_c
                    c = f'{class_id}.{name}'

                    enums[name] = enum

                    if default is None and len(type_info) > 0:
                        default = type_info[0]
            elif type_info == 'INT':
                c = 'int'
            elif type_info == 'FLOAT':
                c = 'float'
            elif type_info == 'STRING':
                c = 'str'
            elif type_info == 'BOOLEAN':
                c = 'bool'
            else:
                type_id = astutil.str_to_class_id(type_info)
                if type_id not in self._data_type_stubs:
                    self._data_type_stubs[type_id] = f'class {type_id}: ...'

                    self._vars[class_id] = type(class_id, (), {})
                c = type_id
            
            if optional:
                # c = f'Optional[{c}]'
                c = f'{c} | None'
                if default is None:
                    input_defaults[name] = None

                    c += ' = None'
            
            if default is not None:
                input_defaults[name] = default

                if isinstance(default, str):
                    default = astutil.to_str(default)
                c += f' = {default}'
            
            return c

        inputs = []
        for (group, optional) in ('required', False), ('optional', True):
            group: dict = info['input'].get(group)
            if group is None:
                continue
            for name, type_config in group.items():
                type_info = type_config[0]
                config = {}
                if len(type_config) > 1:
                    config = type_config[1]
                inputs.append(f'{name}: {to_type_hint(type_info, name, optional, config.get("default"))}')
        
        # Classes are used instead of functions for:
        # - Different syntax highlight color for nodes and utility functions/methods
        # - In-class enums
        c = f'class {class_id}:\n'

        outputs = len(info['output'])
        if outputs >= 2:
            output_type_hint = f' -> tuple[{", ".join(to_type_hint(type) for type in info["output"])}]'
        elif outputs == 1:
            output_type_hint = f' -> {to_type_hint(info["output"][0])}'
        else:
            output_type_hint = ''

        # Docstring
        # TODO: Min, max
        c += (
f"""    '''```
    def {class_id}(
        {f",{chr(10)}        ".join(inputs)}
    ){output_type_hint}
    ```""")
        
        for i, input in reversed(list(enumerate(inputs))):
            if '=' not in input:
                removed = False
                for j, input in enumerate(inputs[:i]):
                    if '=' in input:
                        inputs[j] = input[:input.index('=')].rstrip() + ' | None'
                        removed = True
                if removed:
                    c += '\n    Use `None` to use default values of arguments that appear before any non-default argument.\n    '
                break
        
        c += "'''\n"

        # __new__
        c += f'    def __new__(cls, {", ".join(inputs)}){output_type_hint}: ...\n'
        
        c += enum_type_stubs
        
        self._node_type_stubs.append(c)
        
        n = node.Node(self._prompt, info, input_defaults)
        for enum_id, enum in enums.items():
            setattr(n, enum_id, enum)
        self._vars[class_id] = n

    def type_stubs(self) -> str:
        c = (
'''from __future__ import annotations
from enum import Enum

class ComfyScript:
    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc_value, traceback): ...

''')
        c += '\n'.join(self._data_type_stubs.values()) + '\n\n'
        c += '\n'.join(self._node_type_stubs)
        return c

__all__ = [
    'RuntimeFactory',
]