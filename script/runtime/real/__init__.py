from __future__ import annotations
import itertools
import os
from pathlib import Path
import sys

from ... import api
from . import nodes

def load(vars: dict | None = None, naked: bool = False, callable: bool = True, callable_args_to_kwds: bool = True, callable_use_config_defaults: bool = True, callable_unpack_single_output: bool = True):
    '''
    - `naked`: Enable naked mode. Equivalent to disbling `callable` and all `callable_*`. See runtime README for details.

    - `callable`: Make the nodes callable. Such that
      
      ```
      obj = MyNode()
      getattr(obj, MyNode.FUNCTION)(args)
      ```
      can be written as `MyNode(args)`.
    
      You can still create the node object by `MyNode.create()`.
    
    - `callable_args_to_kwds`: Map positional arguments to keyword arguments.

      Virtual mode and the generated type stubs for nodes determine the position of arguments by `INPUT_TYPES`, but it may differ from what the position `FUNCTION` actually has. To make the code in virtual mode compatible with  real mode, and reuse the type stubs, `callable_args_to_kwds` is used to map all positional arguments to keyword arguments. If `callable_args_to_kwds` is not used, keyword arguments should always be used.
    
    - `callable_use_config_defaults`: Use default values from `INPUT_TYPES` configs.

      `FUNCTION` may have different default values from `INPUT_TYPES` configs, either missing or different values.
    
    - `callable_unpack_single_output`: Unpack the returned tuple if it has only one item.
      
      In ComfyUI, the return value of a node is a tuple even there is only one output. For example, `EmptyLatentImage()` will return `(Latent,)` instead of `Latent`. So that
      ```python
      latent = EmptyLatentImage()
      ```
      have to be replaced with
      ```python
      latent, = EmptyLatentImage()
      ```
      without `callable_unpack_single_output`.
    '''

    comfy_ui = Path(__file__).resolve().parents[5]
    print(f'ComfyScript: Importing ComfyUI from {comfy_ui}')
    sys.path.insert(0, str(comfy_ui))

    orginal_argv = sys.argv[1:]
    sys.argv[1:] = []

    import main
    # execute_prestartup_script()

    # This server is not used by real mode, but some nodes require it to load
    main.server = main.server.PromptServer(None)
    main.server.add_routes()

    # TODO: temp_directory, output_directory, input_directory

    # extra_model_paths
    extra_model_paths_config_path = os.path.join(os.path.dirname(os.path.realpath(main.__file__)), 'extra_model_paths.yaml')
    if os.path.isfile(extra_model_paths_config_path):
        main.load_extra_path_config(extra_model_paths_config_path)

    if main.args.extra_model_paths_config:
        for config_path in itertools.chain(*main.args.extra_model_paths_config):
            main.load_extra_path_config(config_path)

    main.init_custom_nodes()

    main.cuda_malloc_warning()

    # TODO: hijack_progress

    sys.argv[1:] = orginal_argv

    # Import nodes
    nodes_info = api.get_nodes_info()
    print(f'Nodes: {len(nodes_info)}')

    nodes.load(nodes_info, vars, naked, callable, callable_args_to_kwds, callable_use_config_defaults, callable_unpack_single_output)

class Workflow:
    def __init__(self):
        import torch

        self.inference_mode = torch.inference_mode()

    def __enter__(self) -> Workflow:
        import comfy.model_management

        self.inference_mode.__enter__()

        comfy.model_management.cleanup_models()

        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        # TODO: DISABLE_SMART_MEMORY

        self.inference_mode.__exit__(exc_type, exc_value, traceback)