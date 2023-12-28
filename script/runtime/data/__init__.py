from __future__ import annotations
import builtins
from enum import Enum
from typing import Iterable

from .. import factory

class IdManager:
    def __init__(self):
        self._id = -1
        self._id_map = {}

    def assign(self, key) -> str:
        self._id += 1
        self._id_map[key] = self._id
        # Must be str
        return str(self._id)

    def get(self, key) -> str | None:
        # Must be str
        id = self._id_map.get(key)
        return str(id) if id is not None else None

    def last(self) -> str:
        return str(self._id)

class NodeOutput:
    def __init__(self, node_info: dict, node_prompt: dict, output_slot: int | None):
        self.node_info = node_info
        self.node_prompt = node_prompt
        self.output_slot = output_slot
    
    def get_prompt(self) -> dict:
        prompt = {}
        self._update_prompt(prompt, IdManager())
        return prompt
    
    def _update_prompt(self, prompt: dict, id: IdManager) -> str:
        prompt_id = id.get(builtins.id(self.node_prompt))
        if prompt_id is not None:
            return prompt_id

        inputs = self.node_prompt['inputs']
        prompt_inputs = {}
        for k, v in inputs.items():
            if isinstance(v, Enum):
                prompt_inputs[k] = v.value
            elif v is True or v is False:
                input_type = None
                for group in 'required', 'optional':
                    group: dict = self.node_info['input'].get(group)
                    if group is not None and k in group:
                        input_type = group[k][0]
                        break
                if factory.is_bool_enum(input_type):
                    prompt_inputs[k] = factory.to_bool_enum(input_type, v)
                else:
                    prompt_inputs[k] = v
            elif isinstance(v, NodeOutput):
                prompt_inputs[k] = [v._update_prompt(prompt, id), v.output_slot]
            else:
                prompt_inputs[k] = v
        
        new_id = id.assign(builtins.id(self.node_prompt))
        prompt[new_id] = {
            'inputs': prompt_inputs,
            'class_type': self.node_prompt['class_type'],
        }
        return new_id

def get_outputs_prompt(outputs: Iterable[NodeOutput]) -> dict:
    if len(outputs) == 1:
        return outputs[0].get_prompt()
    
    output = NodeOutput({}, {
        'inputs': { i: output for i, output in enumerate(outputs) },
        'class_type': 'ComfyScript',
    }, None)

    prompt = {}
    id = IdManager()
    output._update_prompt(prompt, id)
    del prompt[id.last()]

    return prompt

__all__ = [
    'NodeOutput',
    'get_outputs_prompt',
]