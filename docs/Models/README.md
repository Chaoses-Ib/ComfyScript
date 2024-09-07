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