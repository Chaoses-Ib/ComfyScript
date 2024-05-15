from __future__ import annotations
from pathlib import Path
import traceback
from typing import Any, Iterable
from warnings import warn
import wrapt

from . import RealModeConfig, Workflow
from .. import factory
from ..nodes import _positional_args_to_keyword, Node as VirtualNode

async def load(nodes_info: dict, vars: dict | None, config: RealModeConfig) -> None:
    fact = RealRuntimeFactory(config)
    await fact.init()

    for node_info in nodes_info.values():
        try:
            fact.add_node(node_info)
        except Exception as e:
            print(f'ComfyScript: Failed to load node {node_info["name"]}')
            traceback.print_exc()
    
    globals().update(fact.vars())
    __all__.extend(fact.vars().keys())

    # if vars is None:
    #     # TODO: Or __builtins__?
    #     vars = inspect.currentframe().f_back.f_globals
    if vars is not None:
        vars.update(fact.vars())

    # nodes.pyi
    with open(Path(__file__).resolve().with_suffix('.pyi'), 'w', encoding='utf8') as f:
        f.write(fact.type_stubs())

class RealNodeOutputWrapper(wrapt.ObjectProxy):
    def __repr__(self):
        return repr(self.__wrapped__)
    
    def type(self):
        return type(self.__wrapped__)

class RealRuntimeFactory(factory.RuntimeFactory):
    def __init__(self, config: RealModeConfig):
        super().__init__(hidden_inputs=True)
        self._config = config

        if config.track_workflow:
            config.args_to_kwds = True

    def new_node(self, info: dict, defaults: dict, output_types: list[type]):
        cls = info['_cls']

        config = self._config
        if config.callable:
            orginal_new = cls.__new__
            if not config.wrapper:
                kwdefaults = getattr(orginal_new, '__kwdefaults__', None)
                if kwdefaults is not None:
                    _comfy_script_v = kwdefaults.get('_comfy_script_v')
                    if _comfy_script_v is not None:
                        # cls or its base class has been modified (#18)
                        if _comfy_script_v[1]['name'] == info['name']:
                            return cls
                        else:
                            orginal_new = _comfy_script_v[0]

            def create(_comfy_script_cls=cls, _comfy_script_orginal_new=orginal_new):
                obj = _comfy_script_orginal_new(_comfy_script_cls)
                obj.__init__()
                return obj

            virtual_node = None
            if config.track_workflow:
                virtual_node = VirtualNode(info, defaults, output_types, pack_single_output=True)

            def new(cls, *args, _comfy_script_v=(orginal_new, info, defaults, config, virtual_node), **kwds):
                orginal_new, info, defaults, config, virtual_node = _comfy_script_v
                config: RealModeConfig

                obj = orginal_new(cls)
                obj.__init__()

                # TODO: LazyCell
                if config.args_to_kwds:
                    # kwds should take precedence over args
                    kwds = _positional_args_to_keyword(info, args) | kwds
                    args = ()
                
                kwds_without_defaults = kwds
                if config.use_config_defaults:
                    if config.args_to_kwds:
                        kwds = defaults | kwds
                    else:
                        pos_kwds = _positional_args_to_keyword(info, args)
                        kwds = { k: v for k, v in defaults.items() if k not in pos_kwds } | kwds
                
                # TODO: Bool enum, path
                
                if config.track_workflow:
                    virtual_kwds = {}
                    for k, v in kwds.items():
                        if isinstance(v, RealNodeOutputWrapper):
                            virtual_kwds[k] = v._self_virtual_output
                            kwds[k] = v.__wrapped__
                        else:
                            virtual_kwds[k] = v
                    
                    virtual_outputs = None
                    try:
                        virtual_outputs = virtual_node(**virtual_kwds)
                    except Exception as e:
                        print(f'ComfyScript: track_workflow: Failed to call {info["name"]}: {e}')

                    if virtual_outputs is not None and config.trace_workflow_inject_inputs:
                        hidden = info['input'].get('hidden')
                        if hidden is not None:
                            # TODO: LazyCell
                            prompt, id = None, None
                            for k, v in hidden.items():
                                if k in kwds_without_defaults:
                                    continue
                                if v == 'PROMPT':
                                    if prompt is None:
                                        prompt, id = virtual_outputs[0]._get_prompt_and_id()
                                        unique_id = id.get_id(virtual_outputs[0].node_prompt)
                                    kwds[k] = prompt
                                elif v == 'UNIQUE_ID':
                                    if prompt is None:
                                        prompt, id = virtual_outputs[0]._get_prompt_and_id()
                                        unique_id = id.get_id(virtual_outputs[0].node_prompt)
                                    kwds[k] = unique_id
                                # TODO: EXTRA_PNGINFO: ComfyScriptSource
                
                # Lookup cache
                cache = None
                wf = Workflow._instance
                if wf is not None:
                    cache = wf._get_cache(info['name'])
                    if cache is not None:
                        if not config.track_workflow:
                            warn('Workflow cache requires `track_workflow` to work')
                            cache = None
                        else:
                            # TODO: Or FrozenDict?
                            prompt = virtual_outputs[0].api_format_json()
                            outputs = cache.get(prompt, None)
                            if outputs is not None:
                                return outputs

                # Call the node
                outputs = getattr(obj, obj.FUNCTION)(*args, **kwds)

                if config.track_workflow and virtual_outputs is not None:
                    if isinstance(outputs, Iterable) and not isinstance(outputs, dict):
                        if len(outputs) != len(virtual_outputs):
                            print(f'ComfyScript: track_workflow: {info["name"]} has different number of real and virtual outputs: {len(outputs)} != {len(virtual_outputs)}')
                        wrapped_outputs = []
                        for output, virtual_output in zip(outputs, virtual_outputs):
                            wrapped_output = RealNodeOutputWrapper(output)
                            wrapped_output._self_virtual_output = virtual_output
                            wrapped_outputs.append(wrapped_output)
                        outputs = wrapped_outputs

                # See ComfyUI's `get_output_data()`
                if config.unpack_single_output and isinstance(outputs, Iterable) and not isinstance(outputs, dict) and len(outputs) == 1:
                    outputs = outputs[0]
                
                # Cache outputs
                if cache is not None:
                    cache[prompt] = outputs
                
                return outputs
            
            if not config.wrapper:
                cls.__new__ = new
                if not hasattr(cls, 'create'):
                    setattr(cls, 'create', create)
            else:
                # TODO: functools.update_wrapper?
                cls = type(cls.__name__, (cls,), {
                    '__new__': new,
                    'create': create,
                })
        
        return cls

__all__ = []