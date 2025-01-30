# Models
## Checkpoints
Any checkpoint format supported by ComfyUI will work, including `.ckpt`, `.pt`, `.bin`, `.pth` and `.safetensors`.

List all checkpoints:
```python
from comfy_script.runtime import load
load()
from comfy_script.runtime.nodes import Checkpoints

print(list(Checkpoints))
# [<Checkpoints.Anything_V3_0: 'Anything-V3.0.ckpt'>, <Checkpoints.Realistic_Vision_V5_1_fp16_no_ema: 'Realistic_Vision_V5.1_fp16-no-ema.safetensors'>, ..., <Checkpoints.wd_illusion_fp16: 'wd-illusion-fp16.safetensors'>]
```

Note if you are using the ComfyUI package (hiddenswitch/ComfyUI), it will only load models under the working directory by default (e.g. `%pwd/models/checkpoints`), different from the official one. You can change this behavior with the following arguments (e.g. `load(args=ComfyUIArgs('...', '...'))` ):
```sh
-w CWD, --cwd CWD     Specify the working directory. If not set, this is the current working directory. models/, input/, output/ and other directories will be
                      located here by default. [env var: COMFYUI_CWD]
--base-paths BASE_PATHS [BASE_PATHS ...]
                      Additional base paths for custom nodes, models and inputs. [env var: COMFYUI_BASE_PATHS]
--extra-model-paths-config PATH [PATH ...]
                      Load one or more extra_model_paths.yaml files. [env var: COMFYUI_EXTRA_MODEL_PATHS_CONFIG]
--output-directory OUTPUT_DIRECTORY
                      Set the ComfyUI output directory. [env var: COMFYUI_OUTPUT_DIRECTORY]
--temp-directory TEMP_DIRECTORY
                      Set the ComfyUI temp directory (default is in the ComfyUI directory). [env var: COMFYUI_TEMP_DIRECTORY]
--input-directory INPUT_DIRECTORY
                      Set the ComfyUI input directory. [env var: COMFYUI_INPUT_DIRECTORY]
--create-directories  Creates the default models/, input/, output/ and temp/ directories, then exits. [env var: COMFYUI_CREATE_DIRECTORIES]
--user-directory USER_DIRECTORY
                      Set the ComfyUI user directory with an absolute path. [env var: COMFYUI_USER_DIRECTORY]
```
`os.chdir()`/`%cd` can also be used to change the working directory.

### [CivitAI](https://github.com/Chaoses-Ib/civitai_comfy_nodes)
```python
def CivitAICheckpointLoader(
    ckpt_air: str = '{model_id}@{model_version}',
    ckpt_name: CivitAICheckpointLoader.ckpt_name = 'none',
    download_chunks: int | None = 4,
    download_path: CivitAICheckpointLoader.download_path | None = r'models\checkpoints'
) -> tuple[Model, Clip, Vae]
```

Examples:
```python
model, clip, vae = CivitAICheckpointLoader('101055@128078')
model, clip, vae = CivitAICheckpointLoader('https://civitai.com/models/101055?modelVersionId=128078')
model, clip, vae = CivitAICheckpointLoader('https://civitai.com/models/101055/sd-xl?modelVersionId=128078')
```

### Saving checkpoints
The `CheckpointSave` node can be used to save a checkpoint.

For example:
```python
with Workflow():
    model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
    CheckpointSave(model, clip, vae, 'checkpoints/new-model')
```
The checkpoint will be saved to the output directory, e.g. `D:\ComfyUI\output\checkpoints\new-model_00001_.safetensors`.

## LoRA
### [CivitAI](https://github.com/Chaoses-Ib/civitai_comfy_nodes)
```python
def CivitAILoraLoader(
    model: Model,
    clip: Clip,
    lora_air: str = '{model_id}@{model_version}',
    lora_name: CivitAILoraLoader.lora_name = 'none',
    strength_model: float = 1.0,
    strength_clip: float = 1.0,
    download_chunks: int | None = 4,
    download_path: CivitAILoraLoader.download_path | None = r'models\loras'
) -> tuple[Model, Clip]
```

Examples:
```python
model, clip = CivitAILoraLoader(model, clip, '350450@391994', strength_clip=1, strength_model=1)
model, clip = CivitAILoraLoader(model, clip, 'https://civitai.com/models/350450?modelVersionId=391994', strength_clip=1, strength_model=1)
model, clip = CivitAILoraLoader(model, clip, 'https://civitai.com/models/350450/sdxl-lightning-lora-2step?modelVersionId=391994', strength_clip=1, strength_model=1)
```

## Flux
See [Flux Examples](../../examples/flux.ipynb).