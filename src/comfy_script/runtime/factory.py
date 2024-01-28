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

def is_bool_enum(enum: list[str | bool]) -> bool:
    if len(enum) != 2:
        return False
    if isinstance(enum[0], bool):
        '''
        "Absolute value": {
            "input": {
                "required": {
                    "Value": [
                        "FLOAT",
                        {
                            "default": 1,
                            "min": -1.7976931348623157e+308,
                            "max": 1.7976931348623157e+308,
                            "step": 0.01
                        }
                    ],
                    "negative_out": [
                        [
                            false,
                            true
                        ]
                    ]
                }
            },
        }
        '''
        assert isinstance(enum[1], bool) and enum[0] != enum[1]
        return True
    elif isinstance(enum[0], str):
        lower = [s.lower() for s in enum]
        if lower == ['enable', 'disable'] or lower == ['on', 'off']:
            return True
        elif lower == ['disable', 'enable'] or lower == ['off', 'on']:
            return True
    else:
        print(f'ComfyScript: Invalid enum type: {enum}')
    return False

def bool_enum_default(enum: list[str | bool]) -> bool:
    if isinstance(enum[0], bool):
        return enum[0]
    else:
        lower = enum[0].lower()
        if lower in ('enable', 'on'):
            return True
        elif lower in ('disable', 'off'):
            return False
        raise ValueError(f'Invalid bool enum: {enum}')

def to_bool_enum(enum: list[str | bool], b: bool) -> str:
    if bool_enum_default(enum) == b:
        return enum[0]
    else:
        return enum[1]

class RuntimeFactory:
    '''RuntimeFactory is ignorant of runtime modes.'''

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

    def new_node(self, info: dict, defaults: dict, output_types: list[type]):
        raise NotImplementedError

    def add_node(self, info: dict) -> None:
        class_id = self._get_type_or_assign_id(info['name'])
        if not isinstance(class_id, str):
            print(f'ComfyScript: Node already exists: {info}')
            return
        enums = {}
        enum_type_stubs = ''
        input_defaults = {}

        def type_and_hint(type_info: str | list[str | bool], name: str = None, optional: bool = False, default = None, output: bool = False) -> (type, str):
            nonlocal enum_type_stubs

            c = None
            if isinstance(type_info, list):
                # Output types can also be lists (#9):
                '''
                {
                  "output": [
                    [
                      "cyberrealistic_v41BackToBasics.safetensors",
                      "dreamshaper_8.safetensors",
                      "realisticVisionV60B1_v20Novae.safetensors"
                    ],
                    ...
                  ],
                  "output_is_list": [
                    false,
                    ...,
                  ],
                  "output_name": [
                    "MODEL_NAME",
                    ...
                  ],
                  "name": "SDParameterGenerator",
                  "output_node": false
                }
                '''
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
                if not output:
                    t = Any
                    c = 'Any'
                else:
                    t = data.NodeOutput
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
                assert not output
                # c = f'Optional[{c}]'
                c = f'{c} | None'
                if default is None:
                    input_defaults[name] = None

                    c += ' = None'
            
            if not output and default is not None:
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
                '''
                Select to add LoRA
                Select to add Wildcard
                '''
                name = astutil.str_to_raw_id(name)

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

        output_name = info['output_name']
        if len(output_name) < len(info['output']):
            # See node_info()
            output_name.extend(info['output'][len(output_name):])
        output_with_name = list(zip(info['output'], output_name))

        output_types = [type_and_hint(type, name, output=True)[0] for type, name in output_with_name]

        outputs = len(output_with_name)
        if outputs >= 2:
            output_type_hint = f' -> tuple[{", ".join(type_and_hint(type, name, output=True)[1] for type, name in output_with_name)}]'
        elif outputs == 1:
            output_type_hint = f' -> {type_and_hint(output_with_name[0][0], output_with_name[0][1], output=True)[1]}'
        else:
            output_type_hint = ''

        # Classes are used instead of functions for:
        # - Different syntax highlight color for nodes and utility functions/methods
        # - In-class enums
        c = f'class {class_id}:\n'

        # Docstring
        # TODO: Return names
        # TODO: Display name
        # TODO: Category
        # TODO: Min, max
        # TODO: Round?
        # TODO: Indent
        doc = (
f'''    def {class_id}(
        {f",{chr(10)}        ".join(inputs)}
    ){output_type_hint}''')
        
        quote = "'''" if "'''" not in doc else '"""'
        c += (
f"""    {quote}```
{doc}
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
        
        c += f'{quote}\n'

        # __new__
        c += f'    def __new__(cls, {", ".join(inputs)}){output_type_hint}: ...\n'
        
        c += enum_type_stubs
        
        self._node_type_stubs.append(c)
        
        node = self.new_node(info, input_defaults, output_types)
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