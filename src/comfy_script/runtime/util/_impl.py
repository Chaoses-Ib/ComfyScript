'''
> I hope one day I can make conversions like these built-in. But unfortunately ComfyUI doesn't have build-in nodes to output primitive values. I didn't find a suitable custom node pack that is not bloated to install with ComfyScript, either.  
> But I can add some utility functions at least. Let them lookup the node list and see if there are any nodes available, if not, raise an exception and let the user to install some nodes.  
> It's pretty limited as the function can only execute the workflow to get that one value. Perhaps I can make it more flexible by allow functions to add callback to process the node output, though it's a bit hacky.

TODO: Real mode support
- Auto resolve node module
- Unify `.wait()`
'''

from typing import TYPE_CHECKING
import PIL.Image

if TYPE_CHECKING:
    from comfy_script.runtime.nodes import *
    import comfy_script.runtime.real.nodes as real

from .. import node
from .. import data

def get_int(value: 'Int') -> int:
    '''
    Example:
    ```
    # `Integer` is from Derfuu_ComfyUI_ModdedNodes
    util.get_int(Integer(123))
    ```
    Required custom nodes: ComfyUI-Crystools
    '''
    ShowAnyToJSONCrystools: 'type[ShowAnyToJSONCrystools] | None' = node.get('Show any to JSON [Crystools]')
    if ShowAnyToJSONCrystools:
        json = ShowAnyToJSONCrystools(value)
        return int(json.wait()._output['text'][0])
    raise Exception('Please install ComfyUI-Crystools or get the value with other output nodes')

def get_float(value: 'Float') -> float:
    '''
    Example:
    ```
    # `Float_` is from Derfuu_ComfyUI_ModdedNodes
    util.get_float(Float_(1.23))
    ```
    Required custom nodes: ComfyUI-Crystools
    '''
    ShowAnyToJSONCrystools: 'type[ShowAnyToJSONCrystools] | None' = node.get('Show any to JSON [Crystools]')
    if ShowAnyToJSONCrystools:
        json = ShowAnyToJSONCrystools(value)
        return float(json.wait()._output['text'][0])
    raise Exception('Please install ComfyUI-Crystools or get the value with other output nodes')

def get_str(value: 'str | String') -> str:
    '''
    Example:
    ```
    # `Text` is from Derfuu_ComfyUI_ModdedNodes
    util.get_str(Text('Hello, World!'))
    ```
    Required custom nodes: ComfyUI-Crystools / ComfyUI-Custom-Scripts / ComfyUI_tinyterraNodes
    '''
    ShowTextPysssss: 'type[ShowTextPysssss] | None' = node.get('ShowText|pysssss')
    if ShowTextPysssss:
        return ShowTextPysssss(value).wait()._output['text'][0]

    ShowAnyToJSONCrystools: 'type[ShowAnyToJSONCrystools] | None' = node.get('Show any to JSON [Crystools]')
    if ShowAnyToJSONCrystools:
        json = ShowAnyToJSONCrystools(value)
        return json.wait()._output['text'][0]
    
    TtNTextDebug: 'type[TtNTextDebug] | None' = node.get('ttN textDebug')
    if TtNTextDebug:
        return ''.join(TtNTextDebug(text=value).wait()._output['text'])

    raise Exception('Please install ComfyUI-Crystools / ComfyUI-Custom-Scripts / ComfyUI_tinyterraNodes or get the value with other output nodes')

def get_images(value: 'Image | real.Image', *, save: bool = False) -> list[PIL.Image.Image | None]:
    '''
    Example:
    ```
    # Returns list[PIL.Image.Image | None]
    util.get_images(EmptyImage(batch_size=2))
    util.get_images(EmptyImage(batch_size=2), save=True)
    ```

    Required custom nodes:
    - Virtual mode: None
    - Real mode: ComfyUI_Ib_CustomNodes (installed with ComfyScript by default)
    '''
    if not isinstance(value, data.NodeOutput):
        from ..real import node
        ImageToPIL: 'type[ImageToPIL]' = node.nodes['ImageToPIL']
        return ImageToPIL(value)

    if save:
        SaveImage: 'type[SaveImage]' = node.nodes['SaveImage']
        result = SaveImage(value).wait()
    else:
        # ComfyUI has no built-in API to get images without saving them to the disk (except for previews).
        # TODO: ETNSendImageWebSocket
        PreviewImage: 'type[PreviewImage]' = node.nodes['PreviewImage']
        result = PreviewImage(value).wait()
    assert isinstance(result, data.ImageBatchResult), 'The value is not image'
    return result.wait()


def concat_images(*images: 'Image') -> 'Image':
    '''
    Example:
    ```
    util.concat_images(gen_image(), gen_image())
    util.concat_images(*[gen_image() for _ in range(2)])

    images = util.get_images(util.concat_images(
        EmptyImage(batch_size=2),
        EmptyImage(batch_size=2)
    ))
    print(len(images))
    # 4
    ```
    '''
    ImageBatch: 'type[ImageBatch]' = node.nodes['ImageBatch']

    assert len(images) > 0
    image = images[0]
    for img in images[1:]:
        image = ImageBatch(image, img)
    return image

def save_image_and_get_paths(image: 'Image', prefix: str | None = None, *, temp: bool = False, type: bool = True) -> list[str]:
    '''
    - `prefix`: `ComfyUI` by default. Ignored if `temp` is `True`.

    Example:
    ```
    paths = util.save_image_and_get_paths(EmptyImage(batch_size=2), 'prefix')
    print(paths)
    # ['prefix_00001_.png [output]', 'prefix_00002_.png [output]']

    paths = util.save_image_and_get_paths(EmptyImage(batch_size=2), temp=True)
    print(paths)
    # ['ComfyUI_temp_sirba_00001_.png [temp]', 'ComfyUI_temp_sirba_00002_.png [temp]']
    ```
    With `load_image_from_paths`:
    ```
    paths = util.save_image_and_get_paths(EmptyImage(batch_size=2), temp=True)
    ...
    images = util.get_images(util.load_image_from_paths(paths))
    print(len(images))
    # 2
    ```
    '''
    if not temp:
        SaveImage: 'type[SaveImage]' = node.nodes['SaveImage']
        result = SaveImage(image, prefix).wait()
    else:
        PreviewImage: 'type[PreviewImage]' = node.nodes['PreviewImage']
        result = PreviewImage(image).wait()

    images: list[dict] = result._output['images']
    if type:
        return list([f'{d["filename"]} [{d["type"]}]' for d in images])
    else:
        return list([d['filename'] for d in images])

def load_image_from_paths(paths: list[str]) -> 'Image':
    '''
    Example:
    ```
    images = util.get_images(util.load_image_from_paths([
        'ComfyUI_00001_.png [output]',
        'ComfyUI_00002_.png [output]',
        r'D:/ComfyUI/output/ComfyUI_00001_.png',
    ]))
    print(len(images))
    # 3
    ```
    With `save_image_and_get_paths`:
    ```
    paths = util.save_image_and_get_paths(EmptyImage(batch_size=2), temp=True)
    ...
    images = util.get_images(util.load_image_from_paths(paths))
    print(len(images))
    # 2
    ```
    Required custom nodes: ComfyUI_Ib_CustomNodes (installed with ComfyScript by default)
    '''
    LoadImageFromPath: 'type[LoadImageFromPath] | None' = node.get('LoadImageFromPath')
    if LoadImageFromPath:
        return concat_images(*[LoadImageFromPath(path)[0] for path in paths])
    raise Exception('Please install ComfyUI_Ib_CustomNodes or load the images with other nodes')

__all__ = [
    'get_int',
    'get_float',
    'get_str',
    'get_images',
    'concat_images',
    'save_image_and_get_paths',
    'load_image_from_paths',
]