from __future__ import annotations
from pathlib import Path
from typing import Iterable

from .. import factory
from ..nodes import _positional_args_to_keyword

def load(nodes_info: dict, vars: dict | None, naked: bool = False, callable: bool = True, callable_args_to_kwds: bool = True, callable_use_config_defaults: bool = True, callable_unpack_single_output: bool = True) -> None:
    if not naked:
        fact = RealRuntimeFactory(callable, callable_args_to_kwds, callable_use_config_defaults, callable_unpack_single_output)
    else:
        fact = RealRuntimeFactory(False, False, False, False)
    
    for node_info in nodes_info.values():
        try:
            fact.add_node(node_info)
        except Exception as e:
            print(f'ComfyScript: Failed to load node {node_info["name"]}: {e}')
            # raise
    
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
    def __init__(self, callable: bool, callable_args_to_kwds: bool, callable_use_config_defaults: bool, callable_unpack_single_output: bool):
        super().__init__()
        self._callable = callable
        self._callable_args_to_kwds = callable_args_to_kwds
        self._callable_use_config_defaults = callable_use_config_defaults
        self._callable_unpack_single_output = callable_unpack_single_output

    def new_node(self, info: dict, defaults: dict, output_types: list[type]):
        import nodes

        c = nodes.NODE_CLASS_MAPPINGS[info['name']]

        # Directly modify class or subclass?
        # Subclass will add another layer of abstraction, which is the opposite to the goal of real mode.
        if self._callable:
            if not hasattr(c, 'create'):
                def create(comfy_script_c=c, comfy_script_orginal_new=c.__new__):
                    obj = comfy_script_orginal_new(comfy_script_c)
                    obj.__init__()
                    return obj
                setattr(c, 'create', create)

            orginal_new = c.__new__
            args_to_kwds = self._callable_args_to_kwds
            use_config_defaults = self._callable_use_config_defaults
            unpack_single_output = self._callable_unpack_single_output
            def new(cls, *args, comfy_script_v=(orginal_new, info, defaults, args_to_kwds, use_config_defaults, unpack_single_output), **kwds):
                orginal_new, info, defaults, args_to_kwds, use_config_defaults, unpack_single_output = comfy_script_v

                obj = orginal_new(cls)
                obj.__init__()

                if args_to_kwds:
                    # kwds should take precedence over args
                    kwds = _positional_args_to_keyword(info, args) | kwds
                    args = ()

                if use_config_defaults:
                    if args_to_kwds:
                        kwds = defaults | kwds
                    else:
                        pos_kwds = _positional_args_to_keyword(info, args)
                        kwds = { k: v for k, v in defaults.items() if k not in pos_kwds } | kwds

                # Call the node
                outputs = getattr(obj, obj.FUNCTION)(*args, **kwds)
                
                # See ComfyUI's `get_output_data()`
                if unpack_single_output and isinstance(outputs, Iterable) and not isinstance(outputs, dict) and len(outputs) == 1:
                    return outputs[0]
                
                return outputs
            c.__new__ = new
        
        return c

__all__ = []