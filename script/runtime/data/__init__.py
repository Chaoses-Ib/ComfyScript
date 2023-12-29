from __future__ import annotations
import asyncio
import builtins
from enum import Enum
import inspect
import json
from typing import Iterable

from .. import factory

class IdManager:
    def __init__(self):
        self._id = -1
        self._objid_id_map = {}
        self._id_obj_map = {}

    def assign_id(self, obj) -> str:
        # TODO: Assign id by node types?
        self._id += 1
        self._objid_id_map[builtins.id(obj)] = self._id
        self._id_obj_map[self._id] = obj
        # Must be str
        return str(self._id)

    def get_id(self, obj) -> str | None:
        # Must be str
        id = self._objid_id_map.get(builtins.id(obj))
        return str(id) if id is not None else None
    
    def get_obj(self, id: str) -> object | None:
        return self._id_obj_map.get(int(id))

    def last(self) -> str:
        return str(self._id)

class NodeOutput:
    '''
    - `task: Task | None`: The last task associated with the node output.
    '''
    def __init__(self, node_info: dict, node_prompt: dict, output_slot: int | None):
        self.node_info = node_info
        self.node_prompt = node_prompt
        self.output_slot = output_slot
        self.task = None
    
    def _get_prompt_and_id(self) -> (dict, IdManager):
        prompt = {}
        id = IdManager()
        self._update_prompt(prompt, id)
        return prompt, id

    def api_format(self) -> dict:
        return self._get_prompt_and_id()[0]
    
    def api_format_json(self) -> str:
        return json.dumps(self.api_format())
    
    def _update_prompt(self, prompt: dict, id: IdManager) -> str:
        prompt_id = id.get_id(self.node_prompt)
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
        
        new_id = id.assign_id(self.node_prompt)
        prompt[new_id] = {
            'inputs': prompt_inputs,
            'class_type': self.node_prompt['class_type'],
        }
        return new_id

    async def _wait(self, source = None) -> dict | None:
        if self.task is None:
            from ...runtime import queue
            self.task = await queue._put(self, source)
        return await self.task.result(self)
    
    def __await__(self) -> dict | None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        return self._wait(source).__await__()
    
    def wait(self) -> dict | None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        return asyncio.run(self._wait(source))

def _get_outputs_prompt_and_id(outputs: Iterable[NodeOutput]) -> (dict, IdManager):
    if len(outputs) == 1:
        return outputs[0]._get_prompt_and_id()
    
    output = NodeOutput({}, {
        'inputs': { i: output for i, output in enumerate(outputs) },
        'class_type': 'ComfyScript',
    }, None)

    prompt = {}
    id = IdManager()
    output._update_prompt(prompt, id)
    del prompt[id.last()]

    return prompt, id

__all__ = [
    'IdManager',
    'NodeOutput',
    '_get_outputs_prompt_and_id',
]