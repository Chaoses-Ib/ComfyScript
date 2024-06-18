from __future__ import annotations
from dataclasses import dataclass
import inspect
import json
from pathlib import Path
import sys
import threading
import traceback
from typing import Callable, Iterable
import uuid
from warnings import warn

import asyncio
import nest_asyncio
import aiohttp
from PIL import Image

nest_asyncio.apply()

_client_id = str(uuid.uuid4())
_save_script_source = True

def load(comfyui: str | Client | Path = None, args: ComfyUIArgs | None = None, vars: dict | None = None, watch: bool = True, save_script_source: bool = True):
    '''
    - `comfyui`: The base URL of the ComfyUI server API, or a `Client` object, or a path to the ComfyUI directory, or `'comfyui'` to use the [`comfyui` package](https://github.com/comfyanonymous/ComfyUI/pull/298).

      If not specified, the following ones will be tried in order:
      1. Local server API: http://127.0.0.1:8188/
      2. Parent ComfyUI directory: The default path is `ComfyScript/../..`, which only works if ComfyScript is installed at `ComfyUI/custom_nodes/ComfyScript`.
      3. `comfyui` package
    
    - `args`: CLI arguments to be passed to ComfyUI, if the value of `comfyui` is not an API. See `ComfyUIArgs` for details.
    '''
    asyncio.run(_load(comfyui, args, vars, watch, save_script_source))

async def _load(comfyui: str | Client | Path = None, args: ComfyUIArgs | None = None, vars: dict | None = None, watch: bool = True, save_script_source: bool = True):
    global _save_script_source, queue

    _save_script_source = save_script_source

    nodes_info = None
    if comfyui is None:
        try:
            nodes_info = await client._get_nodes_info()
            if comfyui_base_url != client.client.base_url:
                print(f'ComfyScript: Using ComfyUI from {client.client.base_url}')
        except Exception as e:
            # To avoid "During handling of the above exception, another exception occurred"
            pass
        if nodes_info is None:
            start_comfyui(comfyui, args)
    elif isinstance(comfyui, str) and (comfyui.startswith('http://') or comfyui.startswith('https://')):
        client.client = client.Client(comfyui)
    elif isinstance(comfyui, client.Client):
        client.client = comfyui
    else:
        start_comfyui(comfyui, args)
    
    if nodes_info is None:
        nodes_info = await client._get_nodes_info()
    print(f'Nodes: {len(nodes_info)}')

    await nodes.load(nodes_info, vars)
    
    # TODO: Stop watch if watch turns to False
    if watch:
        queue.start_watch()

@dataclass
class ComfyUIArgs:
    '''CLI arguments to be passed to ComfyUI.'''

    argv: list[str]
    '''```sh
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
    ```'''

    def __init__(self, *argv: str):
        for arg in argv:
            if not isinstance(arg, str):
                raise TypeError(f'ComfyScript: Invalid argv type: {arg}')
        self.argv = list(argv)

    def to_argv(self) -> list[str]:
        return self.argv

comfyui_started = False
comfyui_base_url = None

def start_comfyui(comfyui: Path | str = None, args: ComfyUIArgs | None = None, *, no_server: bool = False, join_at_exit: bool = True, autonomy: bool = False):
    '''
    Start ComfyUI. Immediately return if ComfyUI is already started.

    - `comfyui`: Path to ComfyUI directory.
    
      The default path is `ComfyScript/../..`, which only works if ComfyScript is installed at `ComfyUI/custom_nodes/ComfyScript`.

      If the default path does not exist, or the value of this argument is `'comfyui'`, then the runtime will try to load ComfyUI from the [`comfyui` package](https://github.com/comfyanonymous/ComfyUI/pull/298).
    
    - `args`: CLI arguments to be passed to ComfyUI. See `ComfyUIArgs` for details.

    - `no_server`: Do not start the server.

    - `join_at_exit`: Join ComfyUI (wait for all tasks to be done) at process exit.

    - `autonomy`: If enabled, currently, the server will not be started even if `no_server=False`.
    '''
    global comfyui_started, comfyui_base_url
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
                raise ImportError(f'ComfyUI is not found at {default_comfyui} and comfyui package')

    argv = args.to_argv() if args is not None else []
    if sys.modules.get('torch') is not None and '--disable-cuda-malloc' not in argv:
        print('ComfyScript: PyTorch is imported before start ComfyUI, PyTorch config will be skipped. If it is possible, you should only `import torch` after start_comfyui()/load() is called.')
        argv.append('--disable-cuda-malloc')

    orginal_argv = sys.argv[1:]
    sys.argv[1:] = argv

    def setup_comfyui_polyfills(main_locals: dict = None):
        '''
        Should be called after `comfy.cmd.main.main()`.

        - `main_locals`: Currently not used.
        '''
        import importlib.metadata
        import traceback
        import types

        for name in 'cuda_malloc', 'execution', 'folder_paths', 'latent_preview', 'main', 'server':
            module = sys.modules[f'comfy.cmd.{name}']
            sys.modules[name] = module
            # globals()[name] = module
        
        import comfy.cmd.server
        server = getattr(comfy.cmd.server.PromptServer, 'instance', None)
        if server is None:
            main.server = main.server_module
            # TODO: Hook something to get other variables?
        else:
            main.server = server
            main.loop = server.loop
            main.q = server.prompt_queue
        
        # if main_locals is not None:
        #     for name in 'loop', 'server', 'q', 'extra_model_paths_config_path':
        #         setattr(main, name, main_locals[name])
        
        import comfy.nodes.common
        nodes = types.ModuleType('nodes')
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

    if not autonomy:
        sys.argv.append('--quick-test-for-ci')
        def exit_hook(code = None):
            if code != 0:
                exit(code)
            
            outer = inspect.currentframe().f_back

            if comfyui == 'comfyui':
                setup_comfyui_polyfills(outer.f_locals)

            args = outer.f_globals['args']
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
            outer.f_globals['run'] = run

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

                enable_args_parsing()
            comfy.options.enable_args_parsing = enable_args_parsing_hook

            import main

            del main.exit
            main.__name__ = 'main'
            comfy.options.enable_args_parsing = enable_args_parsing
        else:
            print(f'ComfyScript: Importing ComfyUI from comfyui package')

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
        
        asyncio.get_event_loop_policy().set_event_loop(original_loop)
        
        if not no_server:
            threading.Thread(target=main.server.loop.run_until_complete, args=(main.server.publish_loop(),), daemon=True).start()

            comfyui_base_url = f'http://127.0.0.1:{main.args.port}/'
            client.client = client.Client(comfyui_base_url)
    else:
        if comfyui != 'comfyui':
            print(f'ComfyScript: Importing ComfyUI from {comfyui}')
            sys.path.insert(0, str(comfyui))
            import main
        else:
            print(f'ComfyScript: Importing ComfyUI from comfyui package')

            import comfy.cmd.main as main

            setup_comfyui_polyfills()
    
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

    sys.argv[1:] = orginal_argv

    comfyui_started = True

    if not no_server and join_at_exit:
        import atexit
        atexit.register(join_comfyui)

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

class TaskQueue:
    def __init__(self):
        self._tasks = {}
        self._watch_thread = None
        self._queue_empty_callback = None
        self._queue_remaining_callbacks = [self._when_empty_callback]
        self._watch_display_node = None
        self._watch_display_node_preview = None
        self._watch_display_task = None
        self.queue_remaining = 0

    async def _get_history(self, prompt_id: str) -> dict | None:
        async with client.client.session() as session:
            async with session.get(f'{client.client.base_url}history/{prompt_id}') as response:
                if response.status == 200:
                    json = await response.json()
                    # print(json)
                    return json.get(prompt_id)
                else:
                    print(f'ComfyScript: Failed to get history: {await client.response_to_str(response)}')

    async def _watch(self):
        from tqdm.auto import tqdm
        pbar = None

        while True:
            try:
                async with client.client.session() as session:
                    async with session.ws_connect(f'{client.client.base_url}ws', params={'clientId': _client_id}) as ws:
                        self.queue_remaining = 0
                        executing = False
                        progress_data = None
                        async for msg in ws:
                            # print(msg.type)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                msg = msg.json()
                                # print(msg)
                                if msg['type'] == 'status':
                                    data = msg['data']
                                    queue_remaining = data['status']['exec_info']['queue_remaining']
                                    if self.queue_remaining != queue_remaining:
                                        self.queue_remaining = queue_remaining
                                        if not executing:
                                            for callback in self._queue_remaining_callbacks:
                                                callback(self.queue_remaining)
                                        print(f'Queue remaining: {self.queue_remaining}')
                                elif msg['type'] == 'execution_start':
                                    executing = True
                                elif msg['type'] == 'executing':
                                    data = msg['data']
                                    if data['node'] is None:
                                        prompt_id = data['prompt_id']
                                        task: Task = self._tasks.get(prompt_id)
                                        if task is not None:
                                            del self._tasks[prompt_id]

                                        if self.queue_remaining == 0:
                                            for task in self._tasks.values():
                                                print(f'ComfyScript: The queue is empty but {task} has not been executed')
                                                await task._set_result_threadsafe(None, {})
                                            self._tasks.clear()
                                        
                                        for callback in self._queue_remaining_callbacks:
                                            callback(self.queue_remaining)
                                        executing = False

                                        history = await self._get_history(prompt_id)
                                        outputs = {}
                                        if history is not None:
                                            outputs = history['outputs']
                                        await task._set_result_threadsafe(None, outputs, self._watch_display_task)
                                        if self._watch_display_task:
                                            print(f'Queue remaining: {self.queue_remaining}')
                                elif msg['type'] == 'executed':
                                    data = msg['data']
                                    prompt_id = data['prompt_id']
                                    task: Task = self._tasks.get(prompt_id)
                                    if task is not None:
                                        await task._set_result_threadsafe(data['node'], data['output'], self._watch_display_node)
                                        if self._watch_display_node:
                                            print(f'Queue remaining: {self.queue_remaining}')
                                elif msg['type'] == 'progress':
                                    # See ComfyUI::main.hijack_progress
                                    # 'prompt_id', 'node': https://github.com/comfyanonymous/ComfyUI/issues/2425
                                    progress_data = msg['data']
                                    # TODO: Node
                                    value = progress_data['value']
                                    max = progress_data['max']
                                    if value == 1:
                                        if pbar is not None:
                                            pbar.close()
                                        pbar = tqdm(initial=value, total=max)
                                    else:
                                        pbar.update(value - pbar.n)
                                        if value == max:
                                            pbar.close()
                                            pbar = None
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                event = client.BinaryEvent.from_bytes(msg.data)
                                if event.type == client.BinaryEventTypes.PREVIEW_IMAGE:
                                    prompt_id = progress_data.get('prompt_id')
                                    if prompt_id is not None:
                                        task: Task = self._tasks.get(prompt_id)
                                        task._set_node_preview(progress_data['node'], event.to_object(), self._watch_display_node_preview)
                                    else:
                                        warn(f'Cannot get preview node, please update the ComfyUI server to at least 66831eb6e96cd974fb2d0fc4f299b23c6af16685 (2024-01-02)')
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
            except Exception as e:
                print(f'ComfyScript: Failed to watch, will retry in 5 seconds: {e}')
                traceback.print_exc()
            await asyncio.sleep(5)
        '''
        {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 0}}, 'sid': 'adc24049-b013-4a58-956b-edbc591dc6e2'}}
        {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 1}}}}
        {'type': 'execution_start', 'data': {'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
        {'type': 'execution_cached', 'data': {'nodes': ['9', '15', '5', '8', '12', '13', '16', '6', '1', '14', '0', '2', '20', '11', '17', '7', '10', '19', '3', '4', '18'], 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
        {'type': 'executing', 'data': {'node': '21', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
        {'type': 'progress', 'data': {'value': 1, 'max': 15}}
        ...
        {'type': 'progress', 'data': {'value': 15, 'max': 15}}
        {'type': 'executing', 'data': {'node': '22', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
        {'type': 'executing', 'data': {'node': '23', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
        {'type': 'executed', 'data': {'node': '23', 'output': {'images': [{'filename': 'C_00001_.png', 'subfolder': '', 'type': 'output'}]}, 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
        {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 0}}}}
        {'type': 'executing', 'data': {'node': None, 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
        '''

    def start_watch(self, display_node: bool = True, display_task: bool = True, display_node_preview: bool = True):
        '''
        - `display_node`: When an output node is finished, display its result.
        - `display_task`: When a task is finished (all output nodes are finished), display all the results.

        `load()` will `start_watch()` by default.

        ## Previewing
        Previewing is disabled by default. Pass `--preview-method auto` to ComfyUI to enable previewing.
    
        The default installation includes a fast latent preview method that's low-resolution. To enable higher-quality previews with [TAESD](https://github.com/madebyollin/taesd), download the [taesd_decoder.pth](https://github.com/madebyollin/taesd/raw/main/taesd_decoder.pth) (for SD1.x and SD2.x) and [taesdxl_decoder.pth](https://github.com/madebyollin/taesd/raw/main/taesdxl_decoder.pth) (for SDXL) models and place them in the `models/vae_approx` folder. Once they're installed, restart ComfyUI to enable high-quality previews.
        
        The default maximum preview resolution is 512x512. The only way to change it is to modify ComfyUI::MAX_PREVIEW_RESOLUTION.
        '''

        if display_node or display_task or display_node_preview:
            try:
                import IPython
                self._watch_display_node = display_node
                self._watch_display_task = display_task
                self._watch_display_node_preview = display_node_preview
            except ImportError:
                print('ComfyScript: IPython is not available, cannot display task results')

        if self._watch_thread is None:
            self._watch_thread = threading.Thread(target=asyncio.run, args=(queue._watch(),), daemon=True)
            self._watch_thread.start()

    def add_queue_remaining_callback(self, callback: Callable[[int], None]):
        self.remove_queue_remaining_callback(callback)
        self._queue_remaining_callbacks.append(callback)

    def remove_queue_remaining_callback(self, callback: Callable[[int], None]):
        if callback in self._queue_remaining_callbacks:
            self._queue_remaining_callbacks.remove(callback)

    def watch_display(self, display_node: bool = True, display_task: bool = True, display_node_preview: bool = True):
        '''
        - `display_node`: When an output node is finished, display its result.
        - `display_task`: When a task is finished (all output nodes are finished), display all the results.
        '''
        self._watch_display_node = display_node
        self._watch_display_task = display_task
        self._watch_display_node_preview = display_node_preview

    async def _put(self, workflow: data.NodeOutput | Iterable[data.NodeOutput] | Workflow, source = None) -> Task | None:
        global _client_id
        
        if isinstance(workflow, data.NodeOutput) or isinstance(workflow, Iterable):
            prompt, id = Workflow(outputs=workflow)._get_prompt_and_id()
        elif isinstance(workflow, Workflow):
            prompt, id = workflow._get_prompt_and_id()
        else:
            raise TypeError(f'ComfyScript: Invalid workflow type: {workflow}')
        # print(prompt)

        async with client.client.session() as session:
            extra_data = {}
            if _save_script_source:
                extra_data = {
                    'extra_pnginfo': {
                        'ComfyScriptSource': source
                    }
                }
            async with session.post(f'{client.client.base_url}prompt', json={
                'prompt': prompt,
                'extra_data': extra_data,
                'client_id': _client_id,
            }) as response:
                if response.status == 200:
                    response = await response.json()
                    # print(response)
                    task = Task(response['prompt_id'], response['number'], id)
                    self._tasks[task.prompt_id] = task
                    return task
                else:
                    print(f'ComfyScript: Failed to queue prompt: {response}{await client.response_to_str(response)}')
    
    def put(self, workflow: data.NodeOutput | Iterable[data.NodeOutput] | Workflow, source = None) -> Task | None:
        if source is None:
            outer = inspect.currentframe().f_back
            source = ''.join(inspect.findsource(outer)[0])
        return asyncio.run(self._put(workflow, source))
    
    def __iadd__(self, workflow: data.NodeOutput | Iterable[data.NodeOutput] | Workflow):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        return self.put(workflow, source)
    
    def _when_empty_callback(self, queue_remaining: int):
        if queue_remaining == 0 and self._queue_empty_callback is not None:
            try:
                if self._queue_empty_callback() is False:
                    self._queue_empty_callback = None
            except Exception as e:
                msg = 'when_empty callback raised an exception:'
                warn(msg)
                traceback.print_exc()

    def when_empty(
        self,
        callback: Callable[[], None | bool] | Callable[[Workflow], None | bool] | None,
        source = None
    ):
        '''Call the callback when the queue is empty.

        - `callback`
          - `None` to remove the callback.
          - If the callback takes 0 argument, it will be called directly.
          - If the callback takes 1 argument, it will be passed an *entered* `Workflow`, so that you don't need to write it yourself and indent the code one more level. 
          - If the callback returns `False`, it will be removed and the workflow will not be queued.
          - If the callback raises an exception, the workflow will not be queued.

        Only one callback can be registered at a time. Use `add_queue_remaining_callback()` if you want to register multiple callbacks.
        '''
        if callback is None:
            self._queue_empty_callback = None
            return
        if source is None:
            outer = inspect.currentframe().f_back
            source = ''.join(inspect.findsource(outer)[0])
        argc = len(inspect.signature(callback).parameters)
        if argc == 1:
            def callback(callback=callback, source=source):
                wf = Workflow()
                wf.__enter__()
                try:
                    result = callback(wf)
                    if result is not False:
                        asyncio.run(wf._exit(source))
                    else:
                        # Clear the output hook
                        asyncio.run(wf._exit(source, False))
                    return result
                except Exception as e:
                    # Clear the output hook
                    asyncio.run(wf._exit(source, e))

                    msg = 'when_empty callback raised an exception:'
                    warn(msg)
                    traceback.print_exc()
                
        self._queue_empty_callback = callback
        if self.queue_remaining == 0:
            self._when_empty_callback(0)

    def cancel_current(self):
        '''Interrupt the current task'''
        return asyncio.run(self._cancel_current())
    async def _cancel_current(self):
        async with client.client.session() as session:
            async with session.post(f'{client.client.base_url}interrupt', json={
                'client_id': _client_id,
            }) as response:
                if response.status != 200:
                    print(f'ComfyScript: Failed to interrupt current task: {await client.response_to_str(response)}')

    def cancel_remaining(self):
        '''Clear the queue'''
        return asyncio.run(self._cancel_remaining())
    async def _cancel_remaining(self):
        async with client.client.session() as session:
            async with session.post(f'{client.client.base_url}queue', json={
                'clear': True,
                'client_id': _client_id,
            }) as response:
                if response.status != 200:
                    print(f'ComfyScript: Failed to clear queue: {await client.response_to_str(response)}')

    def cancel_all(self):
        '''Interrupt the current task and clear the queue'''
        return asyncio.run(self._cancel_all())
    async def _cancel_all(self):
        await self._cancel_remaining()
        await self._cancel_current()

class Task:
    def __init__(self, prompt_id: str, number: int, id: data.IdManager):
        self.prompt_id = prompt_id
        self.number = number
        self._id = id
        self._new_outputs = {}
        self._fut = asyncio.Future()
        self._node_preview_callbacks: list[Callable[[Task, str, Image.Image]]] = []

    def __str__(self):
        return f'Task {self.number} ({self.prompt_id})'
    
    def __repr__(self):
        return f'Task(n={self.number}, id={self.prompt_id})'
    
    def _set_node_preview(self, node_id: str, preview: Image.Image, display: bool):
        for callback in self._node_preview_callbacks:
            callback(self, node_id, preview)
        
        if display:
            from IPython.display import display

            display(preview, clear=True)
    
    async def _set_result_threadsafe(self, node_id: str | None, output: dict, display_result: bool = False) -> None:
        if node_id is not None:
            self._new_outputs[node_id] = output
            if display_result:
                from IPython.display import display

                display(clear=True)
                result = data.Result.from_output(output)
                if isinstance(result, data.ImageBatchResult):
                    await Images(result)._display()
                else:
                    display(result)
        else:
            self.get_loop().call_soon_threadsafe(self._fut.set_result, output)
            if display_result:
                from IPython.display import display

                image_batches = []
                others = []
                # TODO: Sort by the parsed id
                for _id, output in sorted(output.items(), key=lambda item: item[0]):
                    result = data.Result.from_output(output)
                    if isinstance(result, data.ImageBatchResult):
                        image_batches.append(result)
                    else:
                        others.append(result)
                if image_batches or others:
                    display(clear=True)
                if image_batches:
                    await Images(*image_batches)._display()
                if others:
                    display(*others)
    
    async def _wait(self) -> list[data.Result]:
        '''`Task` can be directly awaited like `await task`. This method is for internal use only.'''

        outputs: dict = await self._fut
        return [data.Result.from_output(output) for output in outputs.values()]
    
    def __await__(self) -> list[data.Result]:
        return self._wait().__await__()

    def wait(self) -> list[data.Result]:
        return asyncio.run(self)
    
    async def result(self, output: data.NodeOutput) -> data.Result | None:
        id = self._id.get_id(output.node_prompt)
        if id is None:
            return None
        
        output = self._new_outputs.get(id)
        if output is not None:
            return data.Result.from_output(output)

        outputs: dict = await self._fut
        output = outputs.get(id)
        if output is not None:
            return data.Result.from_output(output)
        return None
    
    def wait_result(self, output: data.NodeOutput) -> data.Result | None:
        return asyncio.run(self.result(output))

    # def wait(self):
    #     return asyncio.run(self._wait())
    # async def _wait(self):
    #     async with client.client.session() as session:
    #         async with session.ws_connect(f'{client.client.base_url}ws?clientId={_client_id}') as ws:
    #             async for msg in ws:
    #                 if msg.type == aiohttp.WSMsgType.TEXT:
    #                     msg = msg.json()
    #                     # print(msg)
    #                     if msg['type'] == 'status':
    #                         data = msg['data']
    #                         if data['status']['exec_info']['queue_remaining'] == 0:
    #                             break
    #                     elif msg['type'] == 'executing':
    #                         data = msg['data']
    #                         if data['node'] is None and data['prompt_id'] == self.prompt_id:
    #                             break
    #                     elif msg['type'] == 'progress':
    #                         data = msg['data']
    #                         _print_progress(data['value'], data['max'])
    #                 elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
    #                     break

    # def __await__(self):
    #     return self._wait().__await__()

    def add_preview_callback(self, callback: Callable[[Task, str, Image.Image], None]):
        self._node_preview_callbacks.append(callback)
    
    def remove_preview_callback(self, callback: Callable[[Task, str, Image.Image], None]):
        self._node_preview_callbacks.remove(callback)

    def done(self) -> bool:
        """Return True if the task is done.

        Done means either that a result / exception are available, or that the
        task was cancelled.
        """
        return self._fut.done()
    
    def add_done_callback(self, callback, *, context = None) -> None:
        """Add a callback to be run when the task becomes done.

        The callback is called with a single argument - the future object. If
        the future is already done when this is called, the callback is
        scheduled with call_soon.

        `functools.partial()` can be used to pass parameters to the callback, e.g.:
        ```
        # Call 'print("Future:", fut)' when "fut" is done.
        task.add_done_callback(
            functools.partial(print, "Future:"))
        ```
        """
        return self._fut.add_done_callback(callback, context=context)
    
    def remove_done_callback(self, callback) -> int:
        """Remove all instances of a callback from the "call when done" list.

        Returns the number of callbacks removed.
        """
        return self._fut.remove_done_callback(callback)

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Return the event loop the task is bound to."""
        return self._fut.get_loop()

class Workflow:
    '''
    - `task: Task | None`: The last task associated with the workflow.
    '''
    def __init__(self, queue: bool = True, cancel_all: bool = False, cancel_remaining: bool = False, wait: bool = False, outputs: data.NodeOutput | Iterable[data.NodeOutput] | None = None):
        '''
        - `queue`: Put the workflow into the queue when exiting the context.
        - `cancel_all`: Call `queue.cancel_all()` before queueing the workflow, so that it can start immediately.
        - `cancel_remaining`: Call `queue.cancel_remaining()` before queueing the workflow, so that it can start after the current task finishes.
        - `wait`: Wait for the task to finish before exiting the context. No effect if `queue` is `False`.
        '''
        self._outputs = []
        if outputs is not None:
            self += outputs
        self._queue_when_exit = queue
        self._wait_when_exit = wait
        self._cancel_all_when_queue = cancel_all
        self._cancel_remaining_when_queue = cancel_remaining
        self.task = None
    
    def __iadd__(self, outputs: data.NodeOutput | Iterable[data.NodeOutput]):
        if isinstance(outputs, Iterable):
            self._outputs.extend(outputs)
        else:
            self._outputs.append(outputs)
        return self
    
    def _get_prompt_and_id(self) -> (dict, data.IdManager):
        return data._get_outputs_prompt_and_id(self._outputs)

    def api_format(self) -> dict:
        return self._get_prompt_and_id()[0]
    
    def api_format_json(self) -> str:
        return json.dumps(self.api_format(), indent=2, cls=client.WorkflowJSONEncoder)
    
    async def _queue(self, source = None) -> Task | None:
        global queue

        if self._cancel_all_when_queue:
            await queue._cancel_all()
        elif self._cancel_remaining_when_queue:
            await queue._cancel_remaining()

        self.task = await queue._put(self, source)
        for output in self._outputs:
            output.task = self.task
        return self.task
    
    def queue(self, source = None) -> Task | None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        return asyncio.run(self._queue(source))

    async def __aenter__(self) -> Workflow:
        return self.__enter__()

    def __enter__(self) -> Workflow:
        self._outputs = []
        nodes.Node.set_output_hook(self.__iadd__)
        return self
    
    async def _exit(self, source, exc_type = None, exc_value = None, traceback = None):
        nodes.Node.clear_output_hook()
        # Do not queue the workflow if an exception is raised
        if exc_type is None and self._queue_when_exit:
            if await self._queue(source):
                # TODO: Fix multi-thread print
                # print(task)
                if self._wait_when_exit:
                    await self.task

    async def __aexit__(self, exc_type, exc_value, traceback):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        await self._exit(source, exc_type, exc_value, traceback)
    
    def __exit__(self, exc_type, exc_value, traceback):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        asyncio.run(self._exit(source, exc_type, exc_value, traceback))

queue = TaskQueue()

from .. import client
from ..client import Client
from . import nodes
from . import data
from .data import *

__all__ = [
    'load',
    'Client',
    'ComfyUIArgs',
    'start_comfyui',
    'TaskQueue',
    'queue',
    'Task',
    'Workflow',
]
__all__.extend(data.__all__)