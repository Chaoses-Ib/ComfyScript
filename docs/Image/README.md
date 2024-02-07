# Images
## Loading
### [From path](https://github.com/Chaoses-Ib/ComfyUI_Ib_CustomNodes#load-image-from-path)
```python
def LoadImageFromPath(
    image: str = r'ComfyUI_00001_-assets\ComfyUI_00001_.png [output]'
) -> tuple[Image, Mask]
```
One use of this node is to work with Photoshop's [Quick Export](https://helpx.adobe.com/photoshop/using/export-artboards-layers.html#:~:text=in%20Photoshop.-,Quick%20Export%20As,-Use%20the%20Quick) to quickly perform img2img/inpaint on the edited image. Update: For working with Photoshop, [comfyui-photoshop](https://github.com/NimaNzrii/comfyui-photoshop) is more convenient and supports waiting for changes. See [tutorial at r/comfyui](https://www.reddit.com/r/comfyui/comments/18jygtn/new_ai_news_photoshop_to_comfyui_v1_is_finally/).

### [From Base64](https://github.com/Acly/comfyui-tooling-nodes)
```python
def ETNLoadImageBase64(
    image: str
) -> tuple[Image, Mask]

def ETNLoadMaskBase64(
    mask: str
) -> Mask
```

### From empty
```python
def EmptyImage(
    width: int = 512,
    height: int = 512,
    batch_size: int = 1,
    color: int = 0
) -> Image
```

### [From Photoshop](https://github.com/NimaNzrii/comfyui-photoshop) (not built-in)
```python
def PhotoshopToComfyUI(
    password: str = '12341234',
    wait_for_photoshop_changes: bool = False
) -> tuple[Image, Int, Int]
```
See [tutorial at r/comfyui](https://www.reddit.com/r/comfyui/comments/18jygtn/new_ai_news_photoshop_to_comfyui_v1_is_finally/).

### [From `PIL.Image.Image`](https://github.com/Chaoses-Ib/ComfyUI_Ib_CustomNodes) (real mode)
```python
def PILToImage(
    images: PilImage
) -> Image

def PILToMask(
    images: PilImage
) -> Image
```

### From `input` directory
```python
def LoadImage(
    image: LoadImage.image = 'ComfyUI_00001_.png'
) -> tuple[Image, Mask]

def LoadImageMask(
    image: LoadImageMask.image = 'ComfyUI_00001_.png',
    channel: LoadImageMask.channel = 'alpha'
) -> Mask
```

## Saving
### To `output` directory
```python
def SaveImage(
    images: Image,
    filename_prefix: str = 'ComfyUI'
)
```

### To `temp` directory
```python
def PreviewImage(
    images: Image
)
```

### [To client](https://github.com/Acly/comfyui-tooling-nodes)
```python
def ETNSendImageWebSocket(
    images: Image
)
```
Sends an output image over the client WebSocket connection as PNG binary data.

### [To `PIL.Image.Image`](https://github.com/Chaoses-Ib/ComfyUI_Ib_CustomNodes) (real mode)
```python
def ImageToPIL(
    images: Image
) -> PilImage
```

### To animate
```python
def SaveAnimatedWEBP(
    images: Image,
    filename_prefix: str = 'ComfyUI',
    fps: float = 6.0,
    lossless: bool = True,
    quality: int = 80,
    method: SaveAnimatedWEBP.method = 'default'
)

def SaveAnimatedPNG(
    images: Image,
    filename_prefix: str = 'ComfyUI',
    fps: float = 6.0,
    compress_level: int = 4
)
```

## Masking
Creating:
```python
def SolidMask(
    value: float = 1.0,
    width: int = 512,
    height: int = 512
) -> Mask

def ImageToMask(
    image: Image,
    channel: ImageToMask.channel = 'red'
) -> Mask

def ImageColorToMask(
    image: Image,
    color: int = 0
) -> Mask

def MaskToImage(
    mask: Mask
) -> Image
```

[Applying](https://github.com/Acly/comfyui-tooling-nodes):
```python
def ETNApplyMaskToImage(
    image: Image,
    mask: Mask
) -> Image
```

## Batching
```python
def ImageBatch(
    image1: Image,
    image2: Image
) -> Image

def RebatchImages(
    images: Image,
    batch_size: int = 1
) -> Image

def RepeatImageBatch(
    image: Image,
    amount: int = 1
) -> Image
```