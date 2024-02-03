# Additional Nodes
These nodes are installed to help with ComfyScript. But if you want, you can also use them in ComfyUI's web UI.

### [ComfyUI_Ib_CustomNodes](https://github.com/Chaoses-Ib/ComfyUI_Ib_CustomNodes)
#### [Load Image From Path](https://github.com/Chaoses-Ib/ComfyUI_Ib_CustomNodes#load-image-from-path)
```python
def LoadImageFromPath(
    image: str = r'ComfyUI_00001_-assets\ComfyUI_00001_.png [output]'
) -> tuple[Image, Mask]
```
One use of this node is to work with Photoshop's [Quick Export](https://helpx.adobe.com/photoshop/using/export-artboards-layers.html#:~:text=in%20Photoshop.-,Quick%20Export%20As,-Use%20the%20Quick) to quickly perform img2img/inpaint on the edited image. Update: For working with Photoshop, [comfyui-photoshop](https://github.com/NimaNzrii/comfyui-photoshop) is more convenient and supports waiting for changes. See [tutorial at r/comfyui](https://www.reddit.com/r/comfyui/comments/18jygtn/new_ai_news_photoshop_to_comfyui_v1_is_finally/).

### [ComfyUI Nodes for External Tooling](https://github.com/Acly/comfyui-tooling-nodes)
Nodes for sending and receiving images:
```python
def ETNLoadImageBase64(
    image: str
) -> tuple[Image, Mask]

def ETNLoadMaskBase64(
    mask: str
) -> Mask

# Sends an output image over the client WebSocket connection as PNG binary data.
def ETNSendImageWebSocket(
    images: Image
)
```
Nodes for working on regions:
```python
def ETNCropImage(
    image: Image,
    x: int = 0,
    y: int = 0,
    width: int = 512,
    height: int = 512
) -> Image

def ETNApplyMaskToImage(
    image: Image,
    mask: Mask
) -> Image
```