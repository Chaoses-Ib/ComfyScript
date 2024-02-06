from __future__ import annotations
import asyncio
from dataclasses import dataclass
import itertools
import os
from pathlib import Path
import sys

def load(comfyui: Path | str = None, argv: list[str] = [], vars: dict | None = None, naked: bool = False, config: RealModeConfig | None = None):
    '''
    - `comfyui`: Path to ComfyUI directory.
    
      The default path is `ComfyScript/../..`, which only works if ComfyScript is installed at `ComfyUI/custom_nodes/ComfyScript`.

      If the default path does not exist, or the value of this argument is `'comfyui'`, then the runtime will try to load ComfyUI from the [`comfyui` package](https://github.com/comfyanonymous/ComfyUI/pull/298).
    
    - `argv`: CLI arguments to be passed to ComfyUI.

      ```sh
      usage: [-h] [--listen [IP]] [--port PORT] [--enable-cors-header [ORIGIN]] [--max-upload-size MAX_UPLOAD_SIZE] [--extra-model-paths-config PATH [PATH ...]] [--output-directory OUTPUT_DIRECTORY]
                  [--temp-directory TEMP_DIRECTORY] [--input-directory INPUT_DIRECTORY] [--auto-launch] [--disable-auto-launch] [--cuda-device DEVICE_ID] [--cuda-malloc | --disable-cuda-malloc]
                  [--dont-upcast-attention] [--force-fp32 | --force-fp16] [--bf16-unet | --fp16-unet | --fp8_e4m3fn-unet | --fp8_e5m2-unet] [--fp16-vae | --fp32-vae | --bf16-vae] [--cpu-vae]
                  [--fp8_e4m3fn-text-enc | --fp8_e5m2-text-enc | --fp16-text-enc | --fp32-text-enc] [--directml [DIRECTML_DEVICE]] [--disable-ipex-optimize] [--preview-method [none,auto,latent2rgb,taesd]]    
                  [--use-split-cross-attention | --use-quad-cross-attention | --use-pytorch-cross-attention] [--disable-xformers] [--gpu-only | --highvram | --normalvram | --lowvram | --novram | --cpu]       
                  [--disable-smart-memory] [--deterministic] [--dont-print-server] [--quick-test-for-ci] [--windows-standalone-build] [--disable-metadata] [--multi-user]

      options:
      -h, --help            show this help message and exit
      --listen [IP]         Specify the IP address to listen on (default: 127.0.0.1). If --listen is provided without an argument, it defaults to 0.0.0.0. (listens on all)
      --port PORT           Set the listen port.
      --enable-cors-header [ORIGIN]
                              Enable CORS (Cross-Origin Resource Sharing) with optional origin or allow all with default '*'.
      --max-upload-size MAX_UPLOAD_SIZE
                              Set the maximum upload size in MB.
      --extra-model-paths-config PATH [PATH ...]
                              Load one or more extra_model_paths.yaml files.
      --output-directory OUTPUT_DIRECTORY
                              Set the ComfyUI output directory.
      --temp-directory TEMP_DIRECTORY
                              Set the ComfyUI temp directory (default is in the ComfyUI directory).
      --input-directory INPUT_DIRECTORY
                              Set the ComfyUI input directory.
      --auto-launch         Automatically launch ComfyUI in the default browser.
      --disable-auto-launch
                              Disable auto launching the browser.
      --cuda-device DEVICE_ID
                              Set the id of the cuda device this instance will use.
      --cuda-malloc         Enable cudaMallocAsync (enabled by default for torch 2.0 and up).
      --disable-cuda-malloc
                              Disable cudaMallocAsync.
      --dont-upcast-attention
                              Disable upcasting of attention. Can boost speed but increase the chances of black images.
      --force-fp32          Force fp32 (If this makes your GPU work better please report it).
      --force-fp16          Force fp16.
      --bf16-unet           Run the UNET in bf16. This should only be used for testing stuff.
      --fp16-unet           Store unet weights in fp16.
      --fp8_e4m3fn-unet     Store unet weights in fp8_e4m3fn.
      --fp8_e5m2-unet       Store unet weights in fp8_e5m2.
      --fp16-vae            Run the VAE in fp16, might cause black images.
      --fp32-vae            Run the VAE in full precision fp32.
      --bf16-vae            Run the VAE in bf16.
      --cpu-vae             Run the VAE on the CPU.
      --fp8_e4m3fn-text-enc
                              Store text encoder weights in fp8 (e4m3fn variant).
      --fp8_e5m2-text-enc   Store text encoder weights in fp8 (e5m2 variant).
      --fp16-text-enc       Store text encoder weights in fp16.
      --fp32-text-enc       Store text encoder weights in fp32.
      --directml [DIRECTML_DEVICE]
                              Use torch-directml.
      --disable-ipex-optimize
                              Disables ipex.optimize when loading models with Intel GPUs.
      --preview-method [none,auto,latent2rgb,taesd]
                              Default preview method for sampler nodes.
      --use-split-cross-attention
                              Use the split cross attention optimization. Ignored when xformers is used.
      --use-quad-cross-attention
                              Use the sub-quadratic cross attention optimization . Ignored when xformers is used.
      --use-pytorch-cross-attention
                              Use the new pytorch 2.0 cross attention function.
      --disable-xformers    Disable xformers.
      --gpu-only            Store and run everything (text encoders/CLIP models, etc... on the GPU).
      --highvram            By default models will be unloaded to CPU memory after being used. This option keeps them in GPU memory.
      --normalvram          Used to force normal vram use if lowvram gets automatically enabled.
      --lowvram             Split the unet in parts to use less vram.
      --novram              When lowvram isn't enough.
      --cpu                 To use the CPU for everything (slow).
      --disable-smart-memory
                              Force ComfyUI to agressively offload to regular ram instead of keeping models in vram when it can.
      --deterministic       Make pytorch use slower deterministic algorithms when it can. Note that this might not make images deterministic in all cases.
      --dont-print-server   Don't print server output.
      --quick-test-for-ci   Quick test for CI.
      --windows-standalone-build
                              Windows standalone build: Enable convenient things that most people using the standalone windows build will probably enjoy (like auto opening the page on startup).
      --disable-metadata    Disable saving prompt metadata in files.
      --multi-user          Enables per-user storage.
      ```

    - `naked`: Enable naked mode. Equivalent to `config=RealModeConfig.naked()`. See docs/Runtime.md for details.

    - `config`: Real mode configuration. See `RealModeConfig` for details.
    '''

    if comfyui is None:
        default_comfyui = Path(__file__).resolve().parents[6]
        if (default_comfyui / 'main.py').exists():
            comfyui = default_comfyui
        else:
            try:
                import comfy
            except ImportError:
                raise ImportError(f'ComfyUI is not found at {default_comfyui} and comfyui package')

    orginal_argv = sys.argv[1:]
    sys.argv[1:] = argv
    if comfyui != 'comfyui':
        print(f'ComfyScript: Importing ComfyUI from {comfyui}')
        sys.path.insert(0, str(comfyui))
        import main
    else:
        print(f'ComfyScript: Importing ComfyUI from comfyui package')

        import importlib.metadata
        import traceback
        import types

        import comfy.cmd.main as main

        # Polyfills
        for name in 'cuda_malloc', 'execution', 'folder_paths', 'latent_preview', 'main', 'server':
            module = sys.modules[f'comfy.cmd.{name}']
            sys.modules[name] = module
            globals()[name] = module
        
        main.server = main.server_module

        import comfy.cmd.server
        import comfy.nodes.common
        nodes = types.ModuleType('nodes')
        exported_nodes = comfy.cmd.server.nodes
        setattr(nodes, 'NODE_CLASS_MAPPINGS', exported_nodes.NODE_CLASS_MAPPINGS)
        setattr(nodes, 'NODE_DISPLAY_NAME_MAPPINGS', exported_nodes.NODE_DISPLAY_NAME_MAPPINGS)
        setattr(nodes, 'EXTENSION_WEB_DIRS', exported_nodes.EXTENSION_WEB_DIRS)
        setattr(nodes, 'MAX_RESOLUTION', comfy.nodes.common.MAX_RESOLUTION)
        # TODO: load_custom_node, load_custom_nodes
        sys.modules['nodes'] = nodes
        globals()['nodes'] = nodes

        def init_custom_nodes():
            # Load comfyui-legacy custom nodes
            import comfy.nodes.package
            for entry_point in importlib.metadata.entry_points(group='comfyui_legacy.custom_nodes'):
                try:
                    module = entry_point.load()
                    if isinstance(module, types.ModuleType):
                        exported_nodes.update(
                        comfy.nodes.package._import_and_enumerate_nodes_in_module(module, print_import_times=True))
                except Exception as e:
                    print(f'ComfyScript: Failed to load legacy custom nodes from {entry_point}: {e}')
                    traceback.print_exc()

            nodes.NODE_CLASS_MAPPINGS.update(exported_nodes.NODE_CLASS_MAPPINGS)
            nodes.NODE_DISPLAY_NAME_MAPPINGS.update(exported_nodes.NODE_DISPLAY_NAME_MAPPINGS)
            nodes.EXTENSION_WEB_DIRS.update(exported_nodes.EXTENSION_WEB_DIRS)
        main.init_custom_nodes = init_custom_nodes
    
    # Included in `import main`
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
    nodes_info = client.get_nodes_info()
    print(f'Nodes: {len(nodes_info)}')

    if naked:
        config = RealModeConfig.naked()
    elif config is None:
        config = RealModeConfig()
    asyncio.run(runtime_nodes.load(nodes_info, vars, config))

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

    Directly modify class or subclass? Subclass will add another layer of abstraction, which is the opposite to the goal of real mode. However, directly modifying the class may cause problems if the class is called in other places (#20).

    `wrapper` avoids modifying the original class, and allows the original class to be used in other places.
    '''

    args_to_kwds: bool = True
    '''Map positional arguments to keyword arguments.

    Virtual mode and the generated type stubs for nodes determine the position of arguments by `INPUT_TYPES`, but it may differ from what the position `FUNCTION` actually has. To make the code in virtual mode compatible with  real mode, and reuse the type stubs, `args_to_kwds` is used to map all positional arguments to keyword arguments. If `args_to_kwds` is not used, keyword arguments should always be used.
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

    @staticmethod
    def naked() -> RealModeConfig:
        '''Equivalent to disbling all options.'''
        return RealModeConfig(False, False, False, False, False)

from ... import client
from . import nodes as runtime_nodes