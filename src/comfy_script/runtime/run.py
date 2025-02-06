from dataclasses import dataclass

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
