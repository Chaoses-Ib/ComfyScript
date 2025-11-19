# Transpiler
The transpiler can translate ComfyUI's workflows to ComfyScript.

## Installing as custom nodes
When ComfyScript is installed as custom nodes,
`SaveImage` and similar nodes will be hooked to
automatically save the script as the image's metadata.
The script will also be printed to the terminal.

To control these features, see
[settings.example.toml](../settings.example.toml).

## From Python code
```python
from comfy_script.transpile import WorkflowToScriptTranspiler

# PNG / Web UI JSON / API JSON
script = WorkflowToScriptTranspiler.from_file(
  r'tests/transpile/default.json',
  comfyui_api='http://127.0.0.1:8188/'
).to_script()
print(script)
# model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
# ...
# SaveImage(image, 'ComfyUI')
```

## CLI
The command line interface.

<!--
Requirement:
```sh
python -m pip install click~=8.1
```
(or `pip install -e ".[default,cli]"` or `pip install "comfy-script[default,cli]"` when installing)
-->

Usage:
```sh
Usage: python -m comfy_script.transpile [OPTIONS] WORKFLOW

  Transpile workflow to ComfyScript.

Options:
  --api TEXT  [default: http://127.0.0.1:8188/]
  --runtime   Wrap the script with runtime imports and workflow context.
  --help      Show this message and exit.
```

Example:
```powershell
python -m comfy_script.transpile "D:\workflow.json"
```
Or without installing ComfyScript, directly with uv:
```sh
uvx --from "comfy-script[default]" python -m comfy_script.transpile "D:\workflow.json"
```
Output:
```python
model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
conditioning = CLIPTextEncode('beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip)
conditioning2 = CLIPTextEncode('text, watermark', clip)
latent = EmptyLatentImage(512, 512, 1)
latent = KSampler(model, 156680208700286, 20, 8, 'euler', 'normal', conditioning, conditioning2, latent, 1)
image = VAEDecode(latent, vae)
SaveImage(image, 'ComfyUI')
```

Wrap the script with runtime imports and workflow context:
```powershell
python -m comfy_script.transpile "tests\transpile\default.json" --runtime
```
Output:
```python
from comfy_script.runtime import *
load()
from comfy_script.runtime.nodes import *

with Workflow():
    model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
    conditioning = CLIPTextEncode('beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip)
    conditioning2 = CLIPTextEncode('text, watermark', clip)
    latent = EmptyLatentImage(512, 512, 1)
    latent = KSampler(model, 156680208700286, 20, 8, 'euler', 'normal', conditioning, conditioning2, latent, 1)
    image = VAEDecode(latent, vae)
    SaveImage(image, 'ComfyUI')
```

Save the code to `script.py`:
```powershell
python -m comfy_script.transpile "tests\transpile\default.json" --runtime > script.py
```

## MetadataViewer
Jupyter Notebook / web,
see [MetadataViewer](UI/Solara.md#metadataviewer).
