from __future__ import annotations
from typing import Any

from .. import astutil
from . import nodes
from . import data

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
    def __init__(self):
        self._vars = {}
        self._data_type_stubs = {}
        self._node_type_stubs = []
    
    def _get_type_or_assign_id(self, raw_id: str) -> type | str:
        id = astutil.str_to_class_id(raw_id)
        while id in self._vars:
            t = self._vars[id]
            if t._raw_id == raw_id:
                return t
            id += '_'
        
        self._vars[id] = type(id, (), { '_raw_id': raw_id })
        return id

    def _set_type(self, raw_id: str, id: str, t: type) -> None:
        if id in self._vars:
            assert self._vars[id]._raw_id == raw_id
        setattr(t, '_raw_id', raw_id)
        self._vars[id] = t

    def add_node(self, info: dict) -> None:
        class_id = self._get_type_or_assign_id(info['name'])
        if not isinstance(class_id, str):
            print(f'ComfyScript: Node already exists: {info}')
            return
        enums = {}
        enum_type_stubs = ''
        input_defaults = {}

        def type_and_hint(type_info: str | list, name: str = None, optional: bool = False, default = None, output: bool = False) -> (type, str):
            nonlocal enum_type_stubs

            c = None
            if isinstance(type_info, list):
                assert not output
                if is_bool_enum(type_info):
                    t = bool
                    if default is None:
                        default = bool_enum_default(type_info)
                else:
                    # c = 'list[str]'

                    # c = f'Literal[\n        {f",{chr(10)}        ".join(astutil.to_str(s) for s in type)}\n        ]'

                    # TODO: Group by directory?
                    enum_c, t = astutil.to_str_enum(name, { _remove_extension(s): s for s in type_info }, '    ')
                    enum_type_stubs += '\n' + enum_c
                    c = f'{class_id}.{name}'

                    enums[name] = t

                    if default is None and len(type_info) > 0:
                        default = type_info[0]
            elif type_info == '*':
                t = Any
                c = 'Any'
            elif not output and type_info == 'INT':
                t = int
            elif not output and type_info == 'FLOAT':
                t = float
            elif not output and type_info == 'STRING':
                t = str
            elif not output and type_info == 'BOOLEAN':
                t = bool
            else:
                type_id = self._get_type_or_assign_id(type_info)
                if isinstance(type_id, str):
                    self._data_type_stubs[type_id] = f'class {type_id}: ...'

                    t = type(type_id, (data.NodeOutput,), {})
                    self._set_type(type_info, type_id, t)
                else:
                    t = type_id
            if c is None:
                c = t.__name__

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
            
            return t, c

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
                    '''
                    "ImpactLogger": {
                        "input": {
                            "required": {
                                "data": [
                                    "*",
                                    ""
                                ]
                            },
                            "hidden": {
                                "prompt": "PROMPT",
                                "extra_pnginfo": "EXTRA_PNGINFO"
                            }
                        },
                    }
                    '''
                    if not isinstance(config, dict):
                        if config:
                            print(f'ComfyScript: Invalid config: {config} {info}')
                        config = {}
                inputs.append(f'{name}: {type_and_hint(type_info, name, optional, config.get("default"))[1]}')

        output_types = [type_and_hint(type, output=True)[0] for type in info['output']]

        outputs = len(info['output'])
        if outputs >= 2:
            output_type_hint = f' -> tuple[{", ".join(type_and_hint(type, output=True)[1] for type in info["output"])}]'
        elif outputs == 1:
            output_type_hint = f' -> {type_and_hint(info["output"][0], output=True)[1]}'
        else:
            output_type_hint = ''

        # Classes are used instead of functions for:
        # - Different syntax highlight color for nodes and utility functions/methods
        # - In-class enums
        c = f'class {class_id}:\n'

        # Docstring
        # TODO: Return names
        # TODO: Display name
        # TODO: Min, max
        # TODO: Round?
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
        
        node = nodes.Node(info, input_defaults, output_types)
        for enum_id, enum in enums.items():
            setattr(node, enum_id, enum)
        self._set_type(info['name'], class_id, node)
    
    def vars(self) -> dict:
        return self._vars

    def type_stubs(self) -> str:
        c = (
'''from __future__ import annotations
from typing import Any
from enum import Enum

''')
        c += '\n'.join(self._data_type_stubs.values()) + '\n\n'
        c += '\n'.join(self._node_type_stubs)
        return c

__all__ = [
    'RuntimeFactory',
]