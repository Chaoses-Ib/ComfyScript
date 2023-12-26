from enum import Enum

from . import stub

def _positional_args_to_keyword(node: dict, args: tuple) -> dict:
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
        print(f'ComfyScript: {node["name"]} has more positional arguments than expected: {args}')
    return kwargs

class Node:
    def __init__(self, prompt: dict, info: dict, defaults: dict):
        self.prompt = prompt
        self.info = info
        self.defaults = defaults

    def _assign_id(self) -> str:
        # Must be str
        return str(int(max(self.prompt.keys(), key=int, default='-1')) + 1)
    
    def __call__(self, *args, **kwds):
        # print(self.node['name'], args, kwds)

        id = self._assign_id()

        inputs = _positional_args_to_keyword(self.info, args) | kwds
        for k in list(inputs.keys()):
            if inputs[k] is None:
                del inputs[k]
        inputs = self.defaults | inputs
        for k, v in inputs.items():
            if isinstance(v, Enum):
                inputs[k] = v.value
            elif v is True or v is False:
                input_type = None
                for group in 'required', 'optional':
                    group: dict = self.info['input'].get(group)
                    if group is not None and k in group:
                        input_type = group[k][0]
                        break
                if stub.is_bool_enum(input_type):
                    inputs[k] = stub.to_bool_enum(input_type, v)

        self.prompt[id] = {
            'inputs': inputs,
            'class_type': self.info['name'],
        }

        outputs = len(self.info['output'])
        if outputs == 0:
            return
        elif outputs == 1:
            return [id, 0]
        else:
            return [[id, i] for i in range(outputs)]

__all__ = ['Node']