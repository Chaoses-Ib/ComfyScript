# Documentation
## Installation
See [README](../README.md#installation) for basic ways to install.

### Only ComfyScript package
Install/update:
```sh
python -m pip install -U "comfy-script[default]"
```

Some features will be unavaliable when only ComfyScript is installed, e.g. real mode runtime, standalone virtual mode runtime.

### Only nodes with ComfyUI
<details>

Install [ComfyUI](https://github.com/comfyanonymous/ComfyUI) first. And then:
```sh
cd ComfyUI/custom_nodes
git clone https://github.com/Chaoses-Ib/ComfyScript.git
cd ComfyScript
python -m pip install -r requirements.txt
```

Update:
```sh
cd ComfyUI/custom_nodes/ComfyScript
git pull
python -m pip install -r requirements.txt
```

If you want, you can still import the package with a hardcoded path:
```python
import sys
# Or just '../src' if used in the examples directory
sys.path.insert(0, r'D:\...\ComfyUI\custom_nodes\ComfyScript\src')

import comfy_script
```

</details>

## Workflow information retrieval
It is possible to retrieve any wanted information by running the script with some stubs. For example, to get all positive prompt texts, one can define:

```python
positive_prompts = []

def CLIPTextEncode(text, clip):
    return text

def KSampler(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent_image, denoise):
    positive_prompts.append(positive)
```
And use [`exec()`](https://docs.python.org/3/library/functions.html#exec) to run the script (stubs for other nodes can be automatically generated). This way, `Reroute`, `PrimitiveNode`, and other special nodes won't be a problem stopping one from getting the information.

It is also possible to generate a JSON by this. However, since JSON can only contain tree data and the workflow is a DAG, some information will have to be discarded, or the input have to be replicated at many positions.