from enum import Enum
from typing import Callable, Union
from .. import astutil

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

class TypeStubGenerator:
    def __init__(self, def_class: Callable[[str], None]):
        self._def_class = def_class
        self._input_types = {}
        self._node_types = []

    def add_node(self, node: dict, class_id: str, def_enum: Callable[[str, Enum], None]) -> dict:
        '''
        Returns default value dict.
        '''
        defaults = {}

        input_enums = ''

        def to_type_hint(type: Union[str, list], name: str = None, optional: bool = False, default = None) -> str:
            nonlocal input_enums

            if isinstance(type, list):
                if is_bool_enum(type):
                    c = 'bool'
                    if default is None:
                        default = bool_enum_default(type)
                else:
                    # c = 'list[str]'

                    # c = f'Literal[\n        {f",{chr(10)}        ".join(astutil.to_str(s) for s in type)}\n        ]'

                    # TODO: Group by directory?
                    enum_c, enum = astutil.to_str_enum(name, { _remove_extension(s): s for s in type }, '    ')
                    input_enums += '\n' + enum_c
                    c = f'{class_id}.{name}'

                    def_enum(name, enum)

                    if default is None and len(type) > 0:
                        default = type[0]
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
                if type_id not in self._input_types:
                    self._input_types[type_id] = f'class {type_id}: ...'
                    self._def_class(type_id)
                c = type_id
            
            if optional:
                # c = f'Optional[{c}]'
                c = f'{c} | None'
                if default is None:
                    defaults[name] = None

                    c += ' = None'
            
            if default is not None:
                defaults[name] = default

                if isinstance(default, str):
                    default = astutil.to_str(default)
                c += f' = {default}'
            
            return c

        inputs = []
        for (group, optional) in ('required', False), ('optional', True):
            group: dict = node['input'].get(group)
            if group is None:
                continue
            for name, type_config in group.items():
                type = type_config[0]
                config = {}
                if len(type_config) > 1:
                    config = type_config[1]
                inputs.append(f'{name}: {to_type_hint(type, name, optional, config.get("default"))}')
        
        # Classes are used instead of functions for:
        # - Different syntax highlight color for nodes and utility functions/methods
        # - In-class enums
        c = f'class {class_id}:\n'

        outputs = len(node['output'])
        if outputs >= 2:
            output_type_hint = f' -> tuple[{", ".join(to_type_hint(type) for type in node["output"])}]'
        elif outputs == 1:
            output_type_hint = f' -> {to_type_hint(node["output"][0])}'
        else:
            output_type_hint = ''

        c += (
f"""    '''```
    def {class_id}(
        {f",{chr(10)}        ".join(inputs)}
    ){output_type_hint}
    ```""")
        
        # TODO: Min, max
        
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

        c += f'    def __new__(cls, {", ".join(inputs)}){output_type_hint}: ...\n'
        
        c += input_enums
        
        self._node_types.append(c)
        
        return defaults

    def generate(self) -> str:
        c = (
'''from __future__ import annotations
from enum import Enum

class ComfyScript:
    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc_value, traceback): ...

''')
        c += '\n'.join(self._input_types.values()) + '\n\n'
        c += '\n'.join(self._node_types)
        return c

__all__ = [
    'TypeStubGenerator',
]