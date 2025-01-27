'''
> I hope one day I can make conversions like these built-in. But unfortunately ComfyUI doesn't have build-in nodes to output primitive values. I didn't find a suitable custom node pack that is not bloated to install with ComfyScript, either.  
> But I can add some utility functions at least. Let them lookup the node list and see if there are any nodes available, if not, raise an exception and let the user to install some nodes.  
> It's pretty limited as the function can only execute the workflow to get that one value. Perhaps I can make it more flexible by allow functions to add callback to process the node output, though it's a bit hacky.

TODO: Real mode support
'''

from typing import TYPE_CHECKING
import PIL.Image

if TYPE_CHECKING:
    from comfy_script.runtime.nodes import *

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

def get_images(value: 'Image', *, save: bool = False) -> list[PIL.Image.Image | None]:
    '''
    Example:
    ```
    util.get_images(EmptyImage(batch_size=2))
    util.get_images(EmptyImage(batch_size=2), save=True)
    ```
    '''
    if save:
        SaveImage: 'type[SaveImage]' = node.nodes['SaveImage']
        result = SaveImage(value).wait()
    else:
        PreviewImage: 'type[PreviewImage]' = node.nodes['PreviewImage']
        result = PreviewImage(value).wait()
    assert isinstance(result, data.ImageBatchResult), 'The value is not image'
    return result.wait()
