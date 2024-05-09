# Additional Nodes
These nodes are installed to help with ComfyScript. But if you want, you can also use them in ComfyUI's web UI.

## [ComfyUI_Ib_CustomNodes](https://github.com/Chaoses-Ib/ComfyUI_Ib_CustomNodes)
```python
def LoadImageFromPath(
    image: str = r'ComfyUI_00001_-assets\ComfyUI_00001_.png [output]'
) -> tuple[Image, Mask]

def PILToImage(
    images: PilImage
) -> Image

def PILToMask(
    images: PilImage
) -> Image

def ImageToPIL(
    images: Image
) -> PilImage
```

## [ComfyUI Nodes for External Tooling](https://github.com/Chaoses-Ib/comfyui-tooling-nodes)
```python
def ETNLoadImageBase64(
    image: str
) -> tuple[Image, Mask]

def ETNLoadMaskBase64(
    mask: str
) -> Mask

def ETNSendImageWebSocket(
    images: Image
)

def ETNApplyMaskToImage(
    image: Image,
    mask: Mask
) -> Image

def ETNCropImage(
    image: Image,
    x: int = 0,
    y: int = 0,
    width: int = 512,
    height: int = 512
) -> Image
```

## [Civitai Comfy Nodes](https://github.com/Chaoses-Ib/civitai_comfy_nodes)
```python
def CivitAICheckpointLoader(
    ckpt_air: str = '{model_id}@{model_version}',
    ckpt_name: CivitAICheckpointLoader.ckpt_name = 'none',
    download_chunks: int | None = 4,
    download_path: CivitAICheckpointLoader.download_path | None = r'models\checkpoints'
) -> tuple[Model, Clip, Vae]

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