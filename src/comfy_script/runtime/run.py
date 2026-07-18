'''
ComfyUI instance management.

- Load ComfyUI modules.
- Optionally start the server, initialize `comfyui_base_url` & `comfy_script.client.client`.
- Can be used in Jupyter Notebook.
- Can be used independently, without ComfyScript workflows.
- Can be used in custom nodes to use the current ComfyUI instance.
- Wait for all tasks to be done.

Methods in this module are in the order they will get executed.

Historically, the ComfyUI package from hiddenswitch is called 'comfyui',
which also has changed its name several times.
It's planned to rename it to 'hiddenswitch' to avoid confusion.
'''
from __future__ import annotations
import asyncio
from dataclasses import dataclass
import inspect
from pathlib import Path
import sys
import threading
import warnings

comfyui_started = False
comfyui_base_url = None

_passive = False
'''Using loaded ComfyUI'''

_redirect___main___file_warn = False

@dataclass
class ComfyUIArgs:
    '''CLI arguments to be passed to ComfyUI.'''

    argv: list[str]
    '''```sh
    usage: [-h] [--listen [IP]] [--port PORT] [--tls-keyfile TLS_KEYFILE] [--tls-certfile TLS_CERTFILE] [--enable-cors-header [ORIGIN]] [--max-upload-size MAX_UPLOAD_SIZE]
                [--extra-model-paths-config PATH [PATH ...]] [--output-directory OUTPUT_DIRECTORY] [--temp-directory TEMP_DIRECTORY] [--input-directory INPUT_DIRECTORY] [--auto-launch]
                [--disable-auto-launch] [--cuda-device DEVICE_ID] [--cuda-malloc | --disable-cuda-malloc] [--force-fp32 | --force-fp16]
                [--bf16-unet | --fp16-unet | --fp8_e4m3fn-unet | --fp8_e5m2-unet] [--fp16-vae | --fp32-vae | --bf16-vae] [--cpu-vae]
                [--fp8_e4m3fn-text-enc | --fp8_e5m2-text-enc | --fp16-text-enc | --fp32-text-enc] [--force-channels-last] [--directml [DIRECTML_DEVICE]] [--disable-ipex-optimize]
                [--preview-method [none,auto,latent2rgb,taesd]] [--use-split-cross-attention | --use-quad-cross-attention | --use-pytorch-cross-attention] [--disable-xformers]
                [--force-upcast-attention | --dont-upcast-attention] [--gpu-only | --highvram | --normalvram | --lowvram | --novram | --cpu] [--default-hashing-function {md5,sha1,sha256,sha512}]  
                [--disable-smart-memory] [--deterministic] [--dont-print-server] [--quick-test-for-ci] [--windows-standalone-build] [--disable-metadata] [--disable-all-custom-nodes]
                [--multi-user] [--verbose] [--front-end-version FRONT_END_VERSION] [--front-end-root FRONT_END_ROOT]

    options:
    -h, --help            show this help message and exit
    --listen [IP]         Specify the IP address to listen on (default: 127.0.0.1). If --listen is provided without an argument, it defaults to 0.0.0.0. (listens on all)
    --port PORT           Set the listen port.
    --tls-keyfile TLS_KEYFILE
                            Path to TLS (SSL) key file. Enables TLS, makes app accessible at https://... requires --tls-certfile to function
    --tls-certfile TLS_CERTFILE
                            Path to TLS (SSL) certificate file. Enables TLS, makes app accessible at https://... requires --tls-keyfile to function
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
    --force-channels-last
                            Force channels last format when inferencing the models.
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
    --force-upcast-attention
                            Force enable attention upcasting, please report if it fixes black images.
    --dont-upcast-attention
                            Disable all upcasting of attention. Should be unnecessary except for debugging.
    --gpu-only            Store and run everything (text encoders/CLIP models, etc... on the GPU).
    --highvram            By default models will be unloaded to CPU memory after being used. This option keeps them in GPU memory.
    --normalvram          Used to force normal vram use if lowvram gets automatically enabled.
    --lowvram             Split the unet in parts to use less vram.
    --novram              When lowvram isn't enough.
    --cpu                 To use the CPU for everything (slow).
    --default-hashing-function {md5,sha1,sha256,sha512}
                            Allows you to choose the hash function to use for duplicate filename / contents comparison. Default is sha256.
    --disable-smart-memory
                            Force ComfyUI to agressively offload to regular ram instead of keeping models in vram when it can.
    --lowvram             Split the unet in parts to use less vram.
    --novram              When lowvram isn't enough.
    --cpu                 To use the CPU for everything (slow).
    --default-hashing-function {md5,sha1,sha256,sha512}
                            Allows you to choose the hash function to use for duplicate filename / contents comparison. Default is sha256.
    --disable-smart-memory
                            Force ComfyUI to agressively offload to regular ram instead of keeping models in vram when it can.
    --deterministic       Make pytorch use slower deterministic algorithms when it can. Note that this might not make images deterministic in all cases.
    --default-hashing-function {md5,sha1,sha256,sha512}
                            Allows you to choose the hash function to use for duplicate filename / contents comparison. Default is sha256.
    --disable-smart-memory
                            Force ComfyUI to agressively offload to regular ram instead of keeping models in vram when it can.
    --deterministic       Make pytorch use slower deterministic algorithms when it can. Note that this might not make images deterministic in all cases.
    --disable-smart-memory
                            Force ComfyUI to agressively offload to regular ram instead of keeping models in vram when it can.
    --deterministic       Make pytorch use slower deterministic algorithms when it can. Note that this might not make images deterministic in all cases.
    --deterministic       Make pytorch use slower deterministic algorithms when it can. Note that this might not make images deterministic in all cases.
    --dont-print-server   Don't print server output.
    --quick-test-for-ci   Quick test for CI.
    --windows-standalone-build
                            Windows standalone build: Enable convenient things that most people using the standalone windows build will probably enjoy (like auto opening the page on startup).        
    --disable-metadata    Disable saving prompt metadata in files.
    --disable-all-custom-nodes
                            Disable loading all custom nodes.
    --multi-user          Enables per-user storage.
    --verbose             Enables more debug prints.
    --front-end-version FRONT_END_VERSION
                            Specifies the version of the frontend to be used. This command needs internet connectivity to query and download available frontend implementations from GitHub releases.  
                            The version string should be in the format of: [repoOwner]/[repoName]@[version] where version is one of: "latest" or a valid version number (e.g. "1.0.0")
    --front-end-root FRONT_END_ROOT
                            The local filesystem path to the directory where the frontend is located. Overrides --front-end-version.
    ```'''

    context_local: bool
    '''
    Load ComfyUI only for the current context (thread). Calling the loaded nodes from other contexts (threads) in real mode will cause exceptions. Only works for comfyui package (hiddenswitch/ComfyUI) at the moment.

    Default: `False`

    ### Details
    The comfyui package (hiddenswitch/ComfyUI) will bind the execution context to the current thread, so when the calling thread is not the thread loaded it, it can't get the current context. This shouldn't be a problem most times, but some GUI libraries require to handle events in different threads (e.g. pywebview), and thus will cause exceptions like this:
    ```
    ...
    File "/hiddenswitch/comfyui/comfy/execution_context.py", line 28, in current_execution_context
    return _current_context.get()
           ^^^^^^^^^^^^^^^^^^^^^^
    LookupError: <ContextVar name='comfyui_execution_context' at 0x0000012345678900>
    ```
    So this is turned off by default (and also to keep consistent with the official ComfyUI).
    '''

    def __init__(self, *argv: str, context_local: bool = False):
        for arg in argv:
            if not isinstance(arg, str):
                raise TypeError(f'ComfyScript: Invalid argv type: {arg}')
        self.argv = list(argv)
        self.context_local = context_local

    def to_argv(self) -> list[str]:
        return self.argv

def _is_comfyui_started():
    import sys

    nodes = sys.modules.get('nodes')
    return nodes is not None and 'NODE_CLASS_MAPPINGS' in vars(nodes) and 'NODE_DISPLAY_NAME_MAPPINGS' in vars(nodes)

def _redirect___main___file(main_file: str):
    '''
    Redirect `__main__.__file__` to `ComfyUI/main.py` to keep compatibility with some nodes.

    e.g. ComfyUI-Text_Image-Composite (#89), ComfyUI-3D-Pack, ComfyUI_Custom_Nodes_AlekPet,  ComfyUI_MagicQuill, ComfyUI_FizzNodes, zhangp365/ComfyUI-utils-nodes, hinablue/ComfyUI_3dPoseEditor, whmc76/ComfyUI-Openpose-Editor-Plus, ...
    '''
    # GitHub: "import __main__" comfyui language:Python NOT "add_comfyui_directory_to_sys_path"
    import wrapt

    class MainWrapper(wrapt.ObjectProxy):
        _main_file = main_file
        # _enabled = True

        @property
        def __file__(self):
            pass

        @__file__.getter
        def __file__(self):
            # if not MainWrapper._enabled:
            #     return self.__wrapped__.__file__

            global _redirect___main___file_warn
            if _redirect___main___file_warn:
                # e.g. ComfyUI-Inspire-Pack.ConcatConditioningsWithMultiplier.INPUT_TYPES()
                print("ComfyScript: __main__.__file__ is redirected to ComfyUI/main.py to keep compatibility with some nodes")
                _redirect___main___file_warn = False

            # MainWrapper._enabled = False
            # import traceback
            # traceback.print_stack()
            # MainWrapper._enabled = True

            return MainWrapper._main_file

    import __main__
    import sys
    sys.modules['__main__'] = MainWrapper(sys.modules['__main__'])

    # del __main__
    # import __main__
    # print(__main__.__file__)

def _spoof_logger_if_needed():
    '''Spoof `LogInterceptor` if `start_comfyui()` in Jupyter Notebook.

    A hack for another hack. Ideally this should be fixed in ComfyUI, but Jupyter Notebook is not clearly supported,
    and I don't want to waste time arguing with others, so just hack it here.

    See also https://github.com/ipython/ipykernel/issues/786
    '''
    if not hasattr(sys.stdout, 'buffer'):
        from comfy.cli_args import args

        new_stdout = sys.stdout
        new_stderr = sys.stderr

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            try:
                import app.logger as logger
            except ModuleNotFoundError:
                # hiddenswitch
                import comfy.app.logger as logger
                from comfy.cmd.main_pre import args
            logger.setup_logger(log_level=args.verbose)

            # `if logs` in setup_logger() doesn't check correctly
            logger.setup_logger = lambda *args, **kwargs: None
        except ImportError:
            pass
        finally:
            sys.stdout = new_stdout
            sys.stderr = new_stderr

def _hiddenswitch_share_context_vars():
    '''Share hiddenswitch/comfyui context vars
    
    See ComfyUIArgs.context_local.
    '''
    try:
        import comfy.execution_context

        current_context = comfy.execution_context.current_execution_context()
        comfy.execution_context.current_execution_context = lambda: current_context
    except Exception:
        warnings.warn('Failed to share context-local execution context')

def _exit_hook(code = None, *, comfyui, no_server, main_globals: dict, start_locals: dict):
    if code != 0:
        exit(code)

    if comfyui == 'comfyui':
        _hiddenswitch_setup_polyfills(start_locals)

    args = main_globals['args']
    async def run(server, address='', port=8188, verbose=True, call_on_start=None):
        # await asyncio.gather(server.start(address, port, verbose, call_on_start), server.publish_loop())

        if no_server:
            return

        try:
            await server.start(address, port, verbose, call_on_start)
        except OSError:
            def dynamic_port_hook(address: str, port: int) -> int:
                locals = inspect.currentframe().f_back.f_locals
                site = locals['site']

                _, port = site._server.sockets[0].getsockname()

                args.port = port
                # comfyui
                if hasattr(server, 'port'):
                    server.port = port

                if verbose:
                    print("Starting server\n")
                    print("To see the GUI go to: http://{}:{}".format(address, port))
                if call_on_start is not None:
                    call_on_start(address, port)

            await server.start(address, 0, False, dynamic_port_hook)
    main_globals['run'] = run

def _hiddenswitch_setup_polyfills(start_locals: dict | None = None):
    '''
    Should be called after `comfy.cmd.main.main()`.

    - `start_locals`: Currently not used.
    '''
    import importlib.metadata
    import traceback
    import types

    for name in 'cuda_malloc', 'execution', 'folder_paths', 'latent_preview', 'main', 'server':
        module = sys.modules.get(f'comfy.cmd.{name}')
        if module:
            sys.modules[name] = module
            # globals()[name] = module

    try:
        import comfy.cmd.server
        import main
        server = getattr(comfy.cmd.server.PromptServer, 'instance', None)
        if server is None:
            main.server = main.server_module
            # TODO: Hook something to get other variables?
        else:
            main.server = server
            main.loop = server.loop
            main.q = server.prompt_queue
    except Exception as e:
        # Give up
        # https://github.com/Chaoses-Ib/ComfyScript/issues/127#issuecomment-5011175162
        warnings.warn('hiddenswitch server broken')

    # if start_locals is not None:
    #     for name in 'loop', 'server', 'q', 'extra_model_paths_config_path':
    #         setattr(main, name, start_locals[name])

    try:
        import comfy.nodes.base_nodes
        import comfy.nodes.common
        nodes = types.ModuleType('nodes')
        nodes.__dict__.update(comfy.nodes.base_nodes.__dict__)
        exported_nodes = getattr(server, 'nodes', None)
        if exported_nodes is None:
            exported_nodes = comfy.cmd.server.nodes
        setattr(nodes, 'NODE_CLASS_MAPPINGS', exported_nodes.NODE_CLASS_MAPPINGS)
        setattr(nodes, 'NODE_DISPLAY_NAME_MAPPINGS', exported_nodes.NODE_DISPLAY_NAME_MAPPINGS)
        setattr(nodes, 'EXTENSION_WEB_DIRS', exported_nodes.EXTENSION_WEB_DIRS)
        setattr(nodes, 'MAX_RESOLUTION', comfy.nodes.common.MAX_RESOLUTION)
        # TODO: load_custom_node, load_custom_nodes
        sys.modules['nodes'] = nodes
        # globals()['nodes'] = nodes

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
    except Exception as e:
        warnings.warn('hiddenswitch nodes broken')

def _start_comfyui_autonomy(
    comfyui: Path | str | None = None,
):
    '''
    Currently, the server will not be started even if `no_server=False`.
    '''
    if comfyui != 'comfyui':
        print(f'ComfyScript: Importing ComfyUI from {comfyui}')
        sys.path.insert(0, str(comfyui))
        import main
    else:
        print(f'ComfyScript: Importing ComfyUI from hiddenswitch/comfyui package')

        import comfy.cmd.main as main

        _hiddenswitch_setup_polyfills()

    # Included in `import main`
    # execute_prestartup_script()

    # This server is not used by real mode, but some nodes require it to load
    main.server = main.server.PromptServer(None)
    main.server.add_routes()

    # TODO: temp_directory, output_directory, input_directory

    # extra_model_paths
    import os
    import itertools
    extra_model_paths_config_path = os.path.join(os.path.dirname(os.path.realpath(main.__file__)), 'extra_model_paths.yaml')
    if os.path.isfile(extra_model_paths_config_path):
        main.load_extra_path_config(extra_model_paths_config_path)

    if main.args.extra_model_paths_config:
        for config_path in itertools.chain(*main.args.extra_model_paths_config):
            main.load_extra_path_config(config_path)

    main.init_custom_nodes()

    main.cuda_malloc_warning()

    # TODO: hijack_progress

def _start_comfyui_managed(comfyui, args, no_server):
    sys.argv.append('--quick-test-for-ci')
    def exit_hook(code = None, *, comfyui=comfyui, no_server=no_server):
        outer = inspect.currentframe().f_back
        return _exit_hook(code, comfyui=comfyui, no_server=no_server, main_globals=outer.f_globals, start_locals=outer.f_locals)

    # The original event loop should be restored after start comfyui (#23)
    original_loop = None
    try:
        original_loop = asyncio.get_event_loop_policy().get_event_loop()
    except Exception as e:
        pass

    if comfyui != 'comfyui':
        print(f'ComfyScript: Importing ComfyUI from {comfyui}')
        sys.path.insert(0, str(comfyui))

        # main: dict = runpy.run_module('main', {'exit': exit_hook}, '__main__')
        import comfy.options
        enable_args_parsing = comfy.options.enable_args_parsing
        def enable_args_parsing_hook():
            globals = inspect.currentframe().f_back.f_globals
            globals['__name__'] = '__main__'
            globals['exit'] = exit_hook
            _redirect___main___file(globals['__file__'])

            enable_args_parsing()

            _spoof_logger_if_needed()

        comfy.options.enable_args_parsing = enable_args_parsing_hook

        import main

        del main.exit
        main.__name__ = 'main'
        comfy.options.enable_args_parsing = enable_args_parsing
    else:
        print(f'ComfyScript: Importing ComfyUI from hiddenswitch/comfyui package')

        try:
            # main_pre must be the earliest import since it suppresses some spurious warnings
            import comfy.cmd.main_pre
        except Exception:
            pass

        if args and not args.context_local:
            _hiddenswitch_share_context_vars()

        _spoof_logger_if_needed()

        import comfy.cmd.main as main

        main.exit = exit_hook
        # or hasattr(main, 'entrypoint')
        if inspect.iscoroutinefunction(main.main):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main.main())
        else:
            main.main()
        del main.exit

        try:
            main.init_custom_nodes()
        except Exception:
            warnings.warn('init nodes failed: {e}')

    asyncio.get_event_loop_policy().set_event_loop(original_loop)

    if not no_server:
        try:
            import server
            server_instance = server.PromptServer.instance
        except (ImportError, AttributeError):
            # main.server is no longer the server instance since ComfyUI v0.3.10 (https://github.com/comfyanonymous/ComfyUI/pull/6114)
            server_instance = main.server

        threading.Thread(target=server_instance.loop.run_until_complete, args=(server_instance.publish_loop(),), daemon=True).start()

        comfyui_base_url = f'http://127.0.0.1:{main.args.port}/'
        client.client = client.Client(comfyui_base_url)

def start_comfyui(
    comfyui: Path | str | None = None,
    args: ComfyUIArgs | None = None,
    *,
    no_server: bool = False,
    join_at_exit: bool = True,
    autonomy: bool = False,
):
    '''
    Start ComfyUI. Immediately return if ComfyUI is already started.

    - `comfyui`: Path to ComfyUI directory.

      The default path is `ComfyScript/../..`, which only works if ComfyScript is installed at `ComfyUI/custom_nodes/ComfyScript`.

      If the default path does not exist, or the value of this argument is `'comfyui'`, then the runtime will try to load ComfyUI from the [`comfyui` package](https://github.com/comfyanonymous/ComfyUI/pull/298).

    - `args`: CLI arguments to be passed to ComfyUI. See `ComfyUIArgs` for details.

    - `no_server`: Do not start the server.

    - `join_at_exit`: Join ComfyUI (wait for all tasks to be done) at process exit.

    - `autonomy`: If enabled, currently, the server will not be started even if `no_server=False`.

    ## Returns
    `comfyui_started`, `comfyui_base_url`, `comfy_script.client.client` will be initialized.
    '''
    global comfyui_started, comfyui_base_url, _passive

    if not comfyui_started and _is_comfyui_started():
        comfyui_started = True
        _passive = True
        print(f'ComfyScript: Using loaded ComfyUI')

        import main
        comfyui_base_url = f'http://127.0.0.1:{main.args.port}/'
        client.client = client.Client(comfyui_base_url)

        if not no_server and join_at_exit:
            import atexit
            atexit.register(join_comfyui)

        return

    if comfyui_started and (comfyui_base_url is not None or no_server):
        return
    comfyui_started = False
    comfyui_base_url = None

    if comfyui is None:
        default_comfyui = Path(__file__).resolve().parents[5]
        if (default_comfyui / 'comfy_extras').exists() and (default_comfyui / 'main.py').exists():
            comfyui = default_comfyui
        else:
            try:
                import comfy
            except ImportError:
                raise ImportError(f'ComfyUI is not found at {default_comfyui} and hiddenswitch/comfyui package')

    argv = args.to_argv() if args is not None else []
    if sys.modules.get('torch') is not None and '--disable-cuda-malloc' not in argv:
        print('ComfyScript: PyTorch is imported before start ComfyUI, PyTorch config will be skipped. If it is possible, you should only `import torch` after start_comfyui()/load() is called.')
        argv.append('--disable-cuda-malloc')

    orginal_argv = sys.argv[1:]
    sys.argv[1:] = argv

    if not autonomy:
        _start_comfyui_managed(comfyui=comfyui, args=args, no_server=no_server)
    else:
        _start_comfyui_autonomy(comfyui)

    sys.argv[1:] = orginal_argv

    _redirect___main___file_warn = True
    comfyui_started = True

    if not no_server and join_at_exit:
        import atexit
        atexit.register(join_comfyui)

def _fix_progress_bar_global_hook():
    if _passive:
        return
    
    # hijack_progress()
    # import server
    # server.PromptServer.instance.last_prompt_id = 'https://github.com/Chaoses-Ib/ComfyScript'
    import comfy.utils
    if hasattr(comfy.utils, 'set_progress_bar_global_hook'):
        comfy.utils.set_progress_bar_global_hook(None)
    else:
        # set_progress_bar_global_hook is removed in new versions of comfyui package
        import comfy.execution_context
        try:
            comfy.execution_context.current_execution_context().server.receive_all_progress_notifications = False
        except Exception:
            # receive_all_progress_notifications is readonly in new versions, give up
            pass

def join_comfyui():
    '''Wait for all tasks to be done.'''

    import server
    server = getattr(server.PromptServer, 'instance', None)
    if server is None:
        return

    prompt_queue = getattr(server, 'prompt_queue', None)
    if prompt_queue is None:
        return

    import time
    while prompt_queue.get_tasks_remaining() != 0:
        time.sleep(0.1)

from .. import client
