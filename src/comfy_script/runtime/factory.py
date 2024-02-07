from __future__ import annotations
from enum import Enum
from typing import Any

from .. import astutil
from .. import client
from . import data

def _remove_extension(path: str) -> str:
    for ext in (
        # `supported_pt_extensions`
        '.vae.pt', '.vae.safetensors',
        
        '.ckpt', '.pt', '.bin', '.pth', '.safetensors',
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

    def __init__(self, import_fullname_types: bool = False):
        '''
        - `import_fullname_types`: WIP.
        '''
        self._vars = { id: None for k, dic in self.GLOBAL_ENUMS.items() for id in dic.values() }
        self._data_type_stubs = {}
        self._enum_values = {}
        self._enum_type_stubs = {}
        self._node_type_stubs = []

        self._import_modules = set() if import_fullname_types else None
        '''WIP.'''
    
    async def init(self) -> None:
        try:
            id = 'Embeddings'
            embeddings = await client._get_embeddings()
            
            enum_c, t = astutil.to_str_enum(id, { s: f'embedding:{s}' for s in embeddings }, '')

            enum_c += f'\n    def name(self) -> str: ...\n'
            def name(self):
                s: str = self.value
                return s.removeprefix('embedding:')
            setattr(t, 'name', name)

            self._enum_type_stubs[id] = enum_c

            self._vars[id] = t
            self._enum_values[id] = embeddings
        except Exception as e:
            print(f'ComfyScript: Failed to get embeddings: {e}')

    def _get_type_or_assign_id(self, raw_id: str) -> type | str:
        id = astutil.str_to_class_id(raw_id)
        while id in self._vars:
            t = self._vars[id]
            if getattr(t, '_raw_id', None) == raw_id:
                return t
            id += '_'
        
        self._vars[id] = type(id, (), { '_raw_id': raw_id })
        return id

    def _set_type(self, raw_id: str, id: str, t: type) -> None:
        if id in self._vars:
            assert self._vars[id]._raw_id == raw_id
        setattr(t, '_raw_id', raw_id)
        self._vars[id] = t

    # Sync with docs/Runtime.md
    GLOBAL_ENUMS = {
        # checkpoints
        'CheckpointLoaderSimple': {'ckpt_name': 'Checkpoints'},
        # clip
        'CLIPLoader': {'clip_name': 'CLIPs'},
        # clip_vision
        'CLIPVisionLoader': {'clip_name': 'CLIPVisions'},
        # configs
        # 'CheckpointLoader': {'config_name': 'Configs'},
        # controlnet
        'ControlNetLoader': {'control_net_name': 'ControlNets'},
        # diffusers
        'DiffusersLoader': {'model_path': 'Diffusers'},
        # embeddings
        # gligen
        'GLIGENLoader': {'gligen_name': 'GLIGENs'},
        # hypernetworks
        'HypernetworkLoader': {'hypernetwork_name': 'Hypernetworks'},
        # loras
        'LoraLoader': {'lora_name': 'Loras'},
        # mmdets
        # onnx
        # photomaker
        'PhotoMakerLoader': {'photomaker_model_name': 'PhotoMakers'},
        # sams
        # style_models
        'StyleModelLoader': {'style_model_name': 'StyleModels'},
        # ultralytics
        # unet
        'UNETLoader': {'unet_name': 'UNETs'},
        # upscale_models
        'UpscaleModelLoader': {'model_name': 'UpscaleModels'},
        # vae + vae_approx
        'VAELoader': {'vae_name': 'VAEs'},
        
        'KSampler': {
            # comfy.samplers.KSampler.SAMPLERS
            'sampler_name': 'Samplers',
            # comfy.samplers.KSampler.SCHEDULERS
            'scheduler': 'Schedulers'
        },
        # 'LatentUpscaleBy': {'upscale_method': 'UpscaleMethods'},
    }

    def get_global_enum(self, info: dict, name: str, values: list[str | bool]) -> (str, Enum) | None:
        global_enum = self.GLOBAL_ENUMS.get(info['name'])
        if global_enum is not None:
            id = global_enum.get(name)
            if id is not None:
                enum_c, t = astutil.to_str_enum(id, { _remove_extension(s): s for s in values }, '')
                self._enum_type_stubs[id] = enum_c

                self._vars[id] = t
                self._enum_values[id] = values

                return id, t

        if len(values) > 0:
            for id, id_values in self._enum_values.items():
                if id_values == values:
                    return id, self._vars[id]
        else:
            # If the list is empty, being able to get global enum or not doesn't matter
            pass

        return None

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

            id = astutil.str_to_raw_id(name)

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
                    global_enum = self.get_global_enum(info, name, type_info)
                    if global_enum is not None:
                        c, t = global_enum

                        # For backward compatibility
                        enum_type_stubs += '\n' + f'    {id} = {c}\n'
                        # c += f' | {class_id}.{id}'
                        enums[id] = t
                    else:
                        if len(type_info) > 0:
                            if isinstance(type_info[0], str):
                                # c = 'list[str]'

                                # c = f'Literal[\n        {f",{chr(10)}        ".join(astutil.to_str(s) for s in type)}\n        ]'

                                # TODO: Group by directory?
                                enum_c, t = astutil.to_str_enum(id, { _remove_extension(s): s for s in type_info }, '    ')
                            elif isinstance(type_info[0], int):
                                enum_c, t = astutil.to_int_enum(id, type_info, '    ')
                            elif isinstance(type_info[0], float):
                                enum_c, t = astutil.to_float_enum(id, type_info, '    ')
                            else:
                                print(f'ComfyScript: Invalid enum type: {type_info}')
                                enum_c, t = astutil.to_str_enum(id, {}, '    ')
                        else:
                            # Empty enum
                            enum_c, t = astutil.to_str_enum(id, {}, '    ')

                        enum_type_stubs += '\n' + enum_c
                        c = f'{class_id}.{id}'

                        enums[id] = t

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
                if self._import_modules is not None and '.' in name:
                    # TODO: list[]
                    spec = astutil.find_spec_from_fullname(name)
                    if spec is not None:
                        try:
                            package = __import__(spec.name)
                            self._vars[package.__name__] = package
                        except Exception as e:
                            print(f'ComfyScript: Failed to import {spec.name}: {e}')

                        if spec.name not in self._import_modules:
                            self._import_modules.add(spec.name)
                        
                        c = name
                    else:
                        c = '.'.join([astutil.str_to_raw_id(part) for part in name.split('.')])
                    t = None
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
                    input_defaults[id] = None

                    c += ' = None'
            
            if not output and default is not None:
                input_defaults[id] = default

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
                input_id = astutil.str_to_raw_id(name)

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
                inputs.append(f'{input_id}: {type_and_hint(type_info, name, optional, config.get("default"))[1]}')

        output_name = info['output_name']
        for i, name in enumerate(output_name):
            if name is None:
                '''
                "MultiAreaConditioning": {
                    "output": [
                        "CONDITIONING",
                        "INT",
                        "INT"
                    ],
                    "output_name": [
                        null,
                        "resolutionX",
                        "resolutionY"
                    ],
                    "name": "MultiAreaConditioning",
                    "category": "Davemane42",
                }
                '''
                output_name[i] = info['output'][i]
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
from enum import Enum as StrEnum, IntEnum, Enum as FloatEnum

''')
        if self._import_modules is not None:
            c += '\n'.join(f'import {module}' for module in self._import_modules) + '\n\n'
        c += '\n'.join(self._data_type_stubs.values()) + '\n\n'
        c += '\n'.join(self._enum_type_stubs.values()) + '\n\n'
        c += '\n'.join(self._node_type_stubs)
        return c

__all__ = [
    'RuntimeFactory',
]