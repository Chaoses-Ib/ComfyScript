from __future__ import annotations
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, MutableMapping

def load(comfyui: Path | str = None, args: ComfyUIArgs | None = None, vars: dict | None = None, naked: bool = False, config: RealModeConfig | None = None, no_server: bool = True):
    '''
    - `comfyui`: Path to ComfyUI directory.
    
      The default path is `ComfyScript/../..`, which only works if ComfyScript is installed at `ComfyUI/custom_nodes/ComfyScript`.

      If the default path does not exist, or the value of this argument is `'comfyui'`, then the runtime will try to load ComfyUI from the [`comfyui` package](https://github.com/comfyanonymous/ComfyUI/pull/298).
    
    - `args`: CLI arguments to be passed to ComfyUI. See `ComfyUIArgs` for details.

    - `naked`: Enable naked mode. Equivalent to `config=RealModeConfig.naked()`. See docs/Runtime.md for details.

    - `config`: Real mode configuration. See `RealModeConfig` for details.
    '''
    from .. import run

    start_comfyui(comfyui, args, no_server=no_server)

    run._fix_progress_bar_global_hook()

    # Import nodes
    nodes_info = client.get_nodes_info()
    print(f'Nodes: {len(nodes_info)}')

    if naked:
        config = RealModeConfig.naked()
    elif config is None:
        config = RealModeConfig()
    node.nodes.clear()
    asyncio.run(nodes.load(nodes_info, vars, config, nodes=node.nodes))

class Workflow:
    # TODO: Thread-safe
    _instance: Workflow = None

    def __init__(
        self,
        *,
        cache: MutableMapping | Callable[[str], MutableMapping] | None = None
    ):
        '''
        - `cache`: Use `dict` (`{}`) for simple unbounded cache. For advanced cache, [cachetools](https://github.com/tkem/cachetools) or other libraries can be used.

          To use different cache for different types of nodes, pass a callable that accepts the node name and returns a cache. For example:
          ```
          cache=lambda node: {}
          ```
          or:
          ```
          node_cache = {}
          cache=lambda node: node_cache.setdefault(node, {})
          ```

          Note that for node output, any changes made by user code instead of nodes will be ignored.
        '''
        import torch

        self.inference_mode = torch.inference_mode()
        self._cache = cache
        self._node_cache = {}

    def __enter__(self) -> Workflow:
        Workflow._instance = self

        import comfy.model_management

        self.inference_mode.__enter__()

        comfy.model_management.cleanup_models()

        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        # TODO: DISABLE_SMART_MEMORY

        self.inference_mode.__exit__(exc_type, exc_value, traceback)

        Workflow._instance = None
    
    def _get_cache(self, node: str) -> MutableMapping | None:
        if self._cache is None:
            return None
        elif isinstance(self._cache, MutableMapping):
            return self._cache
        else:
            cache = self._node_cache.get(node, None)
            if cache is None:
                cache = self._cache(node)
                self._node_cache[node] = cache
            return cache

@dataclass
class RealModeConfig:
    callable: bool = True
    '''Make the nodes callable. Such that
      
    ```
    obj = MyNode()
    getattr(obj, MyNode.FUNCTION)(args)
    ```
    can be written as `MyNode(args)`.

    You can still create the node object by `MyNode.create()`.
    '''

    wrapper: bool = True
    '''Make the nodes callable with a wrapper class.

    Directly modify class or subclass? Subclass will add another layer of abstraction, which is the opposite to the goal of real mode. However, directly modifying the class may cause problems if the class is called in other places (#20)
    or there are name conflicts (#112).

    `wrapper` avoids modifying the original class, and allows the original class to be used in other places.
    '''

    args_to_kwds: bool = True
    '''Map positional arguments to keyword arguments.

    Virtual mode and the generated type stubs for nodes determine the position of arguments by `INPUT_TYPES`, but it may differ from what the position `FUNCTION` actually has. To make the code in virtual mode compatible with real mode, and reuse the type stubs, `args_to_kwds` is used to map all positional arguments to keyword arguments. If `args_to_kwds` is not used, keyword arguments should always be used.
    '''

    map_inputs: bool = True
    '''
    Do some conversions for inputs before calling the nodes, e.g. converting `bool` to corresponding `str`.

    See details at `comfy_script.runtime.factory.RuntimeFactory._map_input`.

    Require `args_to_kwds` at the moment.
    '''

    use_config_defaults: bool = True
    '''Use default values from `INPUT_TYPES` configs.

    `FUNCTION` may have different default values from `INPUT_TYPES` configs, either missing or different values.
    '''
    
    unpack_single_output: bool = True
    '''Unpack the returned tuple if it has only one item.
      
    In ComfyUI, the return value of a node is a tuple even there is only one output. For example, `EmptyLatentImage()` will return `(Latent,)` instead of `Latent`. So that
    ```python
    latent = EmptyLatentImage()
    ```
    have to be replaced with
    ```python
    latent, = EmptyLatentImage()
    ```
    without `unpack_single_output`.
    '''

    track_workflow: bool = True
    '''Track the workflow with virtual mode nodes.
    
    In real mode, nodes are executed directly and have no idea about the workflow, so nodes similar to `SaveImage` will not get any metadata to save. It is possible to save the script source automatically, but if the inputs are dynamic then it may not be a reproducible copy.

    `track_workflows` partially solves this by running real nodes and virtual nodes at the same time, and pass the workflows generated by virtual nodes to real nodes similar to `SaveImage`.

    Note that changes to inputs made by user code instead of nodes will not be tracked.
    '''

    trace_workflow_inject_inputs: bool = True

    @staticmethod
    def naked() -> RealModeConfig:
        '''Equivalent to disbling all options.'''
        return RealModeConfig(False, False, False, False, False, False, False, False)

from ... import client
from .. import ComfyUIArgs, start_comfyui
from . import node
from . import nodes
from . import util

__all__ = [
    'load',
    'ComfyUIArgs',
    'RealModeConfig',
    'Workflow',
    'node',
    'util'
]