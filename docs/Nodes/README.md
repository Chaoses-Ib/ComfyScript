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

## [ComfyUI Nodes for External Tooling](https://github.com/Acly/comfyui-tooling-nodes)
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