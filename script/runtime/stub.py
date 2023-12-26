from enum import Enum
from typing import Callable, Union
from .. import astutil

def _remove_extension(path: str) -> str:
    # `supported_pt_extensions`
    for ext in '.ckpt', '.pt', '.bin', '.pth', '.safetensors':
        path = path.removesuffix(ext)
    return path

class TypeStubGenerator:
    def __init__(self, def_class: Callable[[str], None]):
        self._def_class = def_class
        self._input_types = {}
        self._node_types = []

    def add_node(self, node: dict, class_id: str, def_enum: Callable[[str, Enum], None]) -> None:
        input_enums = ''

        def to_type_hint(type: Union[str, list], name: str = None, optional: bool = False) -> str:
            nonlocal input_enums

            if isinstance(type, list):
                # c = 'list[str]'

                # c = f'Literal[\n        {f",{chr(10)}        ".join(astutil.to_str(s) for s in type)}\n        ]'

                # TODO: Group by directory?
                enum_c, enum = astutil.to_str_enum(name, { _remove_extension(s): s for s in type }, '    ')
                input_enums += '\n' + enum_c
                c = f'{class_id}.{name}'

                def_enum(name, enum)
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
            return c

        inputs = []
        for (group, optional) in ('required', False), ('optional', True):
            group: dict = node['input'].get(group)
            if group is None:
                continue
            for name, config in group.items():
                inputs.append(f'{name}: {to_type_hint(config[0], name, optional)}')
        
        # Classes are used instead of functions for:
        # - Different syntax highlight color for nodes and utility functions/methods
        # - In-class enums
        c = f'class {class_id}:\n'

        c += f'    def __new__(cls, {", ".join(inputs)})'
        outputs = len(node['output'])
        if outputs >= 2:
            c += f' -> tuple[{", ".join(to_type_hint(type) for type in node["output"])}]'
        elif outputs == 1:
            c += f' -> {to_type_hint(node["output"][0])}'
        c += ': ...\n'

        c += input_enums
        
        self._node_types.append(c)

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