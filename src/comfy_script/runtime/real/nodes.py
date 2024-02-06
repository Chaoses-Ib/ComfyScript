from __future__ import annotations
from pathlib import Path
import traceback
from typing import Iterable

from . import RealModeConfig
from .. import factory
from ..nodes import _positional_args_to_keyword

def load(nodes_info: dict, vars: dict | None, config: RealModeConfig) -> None:
    fact = RealRuntimeFactory(config)
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

class RealRuntimeFactory(factory.RuntimeFactory):
    def __init__(self, config: RealModeConfig):
        super().__init__()
        self._config = config

    def new_node(self, info: dict, defaults: dict, output_types: list[type]):
        import nodes

        c = nodes.NODE_CLASS_MAPPINGS[info['name']]

        config = self._config
        if config.callable:
            orginal_new = c.__new__
            if not config.wrapper:
                kwdefaults = getattr(orginal_new, '__kwdefaults__', None)
                if kwdefaults is not None:
                    _comfy_script_v = kwdefaults.get('_comfy_script_v')
                    if _comfy_script_v is not None:
                        # c or its base class has been modified (#18)
                        if _comfy_script_v[1]['name'] == info['name']:
                            return c
                        else:
                            orginal_new = _comfy_script_v[0]

            def create(_comfy_script_c=c, _comfy_script_orginal_new=orginal_new):
                obj = _comfy_script_orginal_new(_comfy_script_c)
                obj.__init__()
                return obj

            def new(cls, *args, _comfy_script_v=(orginal_new, info, defaults, config), **kwds):
                orginal_new, info, defaults, config = _comfy_script_v
                config: RealModeConfig

                obj = orginal_new(cls)
                obj.__init__()

                if config.args_to_kwds:
                    # kwds should take precedence over args
                    kwds = _positional_args_to_keyword(info, args) | kwds
                    args = ()

                if config.use_config_defaults:
                    if config.args_to_kwds:
                        kwds = defaults | kwds
                    else:
                        pos_kwds = _positional_args_to_keyword(info, args)
                        kwds = { k: v for k, v in defaults.items() if k not in pos_kwds } | kwds

                # Call the node
                outputs = getattr(obj, obj.FUNCTION)(*args, **kwds)
                
                # See ComfyUI's `get_output_data()`
                if config.unpack_single_output and isinstance(outputs, Iterable) and not isinstance(outputs, dict) and len(outputs) == 1:
                    return outputs[0]
                
                return outputs
            
            if not config.wrapper:
                c.__new__ = new
                if not hasattr(c, 'create'):
                    setattr(c, 'create', create)
            else:
                # TODO: functools.update_wrapper?
                c = type(c.__name__, (c,), {
                    '__new__': new,
                    'create': create,
                })
        
        return c

__all__ = []