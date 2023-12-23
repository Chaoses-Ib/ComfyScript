# ComfyUI_Ib_CustomNodes
- [ComfyScript](#comfyscript)
- [Load Image From Path](#load-image-from-path)

## ComfyScript
Translate ComfyUI's workflows to human-readable Python scripts.

When installed, `SaveImage` and similar nodes will be hooked to automatically save the script as images' metadata.

For example, here is a workflow in ComfyUI:

![](images/README/workflow.png)

ComfyScript translated from it:
```python
model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
conditioning = CLIPTextEncode('beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip)
conditioning2 = CLIPTextEncode('text, watermark', clip)
latent = EmptyLatentImage(512, 512, 1)
latent = KSampler(model, 156680208700286, 20, 8, 'euler', 'normal', conditioning, conditioning2, latent, 1)
image = VAEDecode(latent, vae)
SaveImage(image, 'ComfyUI')
```

If there two or more `SaveImage` nodes in one workflow, only the necessary inputs of each node will be translated to scripts. For example, here is a 2 pass txt2img (hires fix) workflow:

![](images/README/workflow2.png)

ComfyScript saved for each of the two saved image are respectively:
1. ```python
   model, clip, vae = CheckpointLoaderSimple('v2-1_768-ema-pruned.ckpt')
   conditioning = CLIPTextEncode('masterpiece HDR victorian portrait painting of woman, blonde hair, mountain nature, blue sky', clip)
   conditioning2 = CLIPTextEncode('bad hands, text, watermark', clip)
   latent = EmptyLatentImage(768, 768, 1)
   latent = KSampler(model, 89848141647836, 12, 8, 'dpmpp_sde', 'normal', conditioning, conditioning2, latent, 1)
   image = VAEDecode(latent, vae)
   SaveImage(image, 'ComfyUI')
   ```
2. ```python
   model, clip, vae = CheckpointLoaderSimple('v2-1_768-ema-pruned.ckpt')
   conditioning = CLIPTextEncode('masterpiece HDR victorian portrait painting of woman, blonde hair, mountain nature, blue sky', clip)
   conditioning2 = CLIPTextEncode('bad hands, text, watermark', clip)
   latent = EmptyLatentImage(768, 768, 1)
   latent = KSampler(model, 89848141647836, 12, 8, 'dpmpp_sde', 'normal', conditioning, conditioning2, latent, 1)
   latent2 = LatentUpscale(latent, 'nearest-exact', 1152, 1152, 'disabled')
   latent2 = KSampler(model, 469771404043268, 14, 8, 'dpmpp_2m', 'simple', conditioning, conditioning2, latent2, 0.5)
   image = VAEDecode(latent2, vae)
   SaveImage(image, 'ComfyUI')
   ```

<!--
CLI:
```sh
python -m script from-workflow "D:\workflow.json"
```
-->

### Execution
You can run the script with the runtime like this:
```python
from script import runtime
from script.runtime import *

# await runtime.load('http://127.0.0.1:8188/', locals())
await runtime.load()

async with ComfyScript():
    model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
    conditioning = CLIPTextEncode('beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip)
    conditioning2 = CLIPTextEncode('text, watermark', clip)
    latent = EmptyLatentImage(512, 512, 1)
    latent = KSampler(model, 156680208700286, 20, 8, 'euler', 'normal', conditioning, conditioning2, latent, 1)
    image = VAEDecode(latent, vae)
    SaveImage(image, 'ComfyUI')
```

A Jupyter Notebook is available at [runtime.ipynb](runtime.ipynb).

[Type stubs](https://typing.readthedocs.io/en/latest/source/stubs.html) will be generated at [script/runtime.pyi](script/runtime.pyi) after loading. Mainstream editors can use them to help with coding:

![](images/README/type-stubs.png)

## Load Image From Path
ComfyUI's built-in `Load Image` node can only load uploaded images, which produces duplicated files in the input directory and cannot reload the image when the source file is changed. `Load Image From Path` instead loads the image from the source path and does not have such problems.

One use of this node is to work with Photoshop's [Quick Export](https://helpx.adobe.com/photoshop/using/export-artboards-layers.html#:~:text=in%20Photoshop.-,Quick%20Export%20As,-Use%20the%20Quick) to quickly perform img2img/inpaint on the edited image. Update: For working with Photoshop, [comfyui-photoshop](https://github.com/NimaNzrii/comfyui-photoshop) is more convenient and supports waiting for changes. See [tutorial at r/comfyui](https://www.reddit.com/r/comfyui/comments/18jygtn/new_ai_news_photoshop_to_comfyui_v1_is_finally/).

The image path can be in the following format:
- Absolute path:

  `D:\ComfyUI\output\ComfyUI_00001_-assets\ComfyUI_00001_.png`

- Relative to the input directory:

  `ComfyUI_00001_-assets\ComfyUI_00001_.png [input]`

- Relative to the output directory:

  `ComfyUI_00001_-assets\ComfyUI_00001_.png [output]`

- Relative to the temp directory:

  `ComfyUI_00001_-assets\ComfyUI_00001_.png [temp]`