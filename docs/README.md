# Documentation
## Installation
See [README](../README.md#installation) for basic ways to install.

You can use the following command to install ComfyScript with the latest commit that may has not been released to PyPI yet:
```sh
python -m pip install "comfy-script[default] @ git+https://github.com/Chaoses-Ib/ComfyScript.git"
```

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

### Troubleshooting
#### ERROR: File "setup.py" or "setup.cfg" not found
Run `python -m pip install -U pip` to update pip.

#### ModuleNotFoundError: No module named 'hatchling'
Run `python -m pip install hatchling` . See [#41](https://github.com/Chaoses-Ib/ComfyScript/issues/41) for details.

#### ModuleNotFoundError: No module named 'editables'
Run `python -m pip install editables` . See [#41](https://github.com/Chaoses-Ib/ComfyScript/issues/41) for details.

#### ModuleNotFoundError: No module named 'comfy_extras.nodes_model_merging'
Installing ComfyUI package in the same venv used by official ComfyUI will break the official ComfyUI. Uninstalling ComfyUI package by `python -m pip uninstall comfyui` can fix this problem. See [ComfyUI#3702](https://github.com/comfyanonymous/ComfyUI/issues/3702) for details.

### VS Code
#### Notebook kernel list
If you cannot see the venv used by ComfyUI in VS Code Notebook's kernel list, you can either:
- Activate the venv and then launch VS Code from the terminal
  
  ```pwsh
  cd ComfyUI
  # Windows
  .\.venv\Scripts\activate
  # Linux
  source .venv/bin/activate

  # To let VS Code discover the venv, e.g.:
  cd ComfyUI/custom_nodes/ComfyScript
  code .
  ```
- Add the path to ComfyUI to VS Code's `python.venvFolders` setting

  e.g.
  ```json
  {
      "python.venvFolders": [
          "D:\\ComfyUI"
      ],
  }
  ```
  Note this setting is local only and will not be synced by default.

### Uninstallation
```sh
python -m pip uninstall comfy-script
```
And delete the `ComfyScript` directory if you have cloned it to `ComfyUI/custom_nodes`.

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

## Differences from [ComfyUI-to-Python-Extension](https://github.com/pydn/ComfyUI-to-Python-Extension)
For both virtual mode and real mode, the advantages of ComfyScript are:
- Better compatibility with custom nodes
- The syntax of ComfyScript is simpler and more suitable for reading and writing by hand
- [Type stubs](../README.md#runtime) and [enums](Runtime.md#enumerations) for better developer experience
- Can be used in Jupyter Notebook (and VS Code Notebook and Jupyter Lab)
- Jupyter Notebook widgets ([ImageViewer](UI/ipywidgets.md#imageviewer) and [MetadataViewer](UI/Solara.md#metadataviewer))
- Can convert web UI format workflows, while ComfyUI-to-Python-Extension can only handle API format workflows
- And... the name is shorter :)

For [virtual mode](Runtime.md#virtual-mode), also these:
- Can be used remotely, so you don't need to load ComfyUI every time, and can also use a cloud GPU server
- Can utilize ComfyUI's built-in node output cache mechanism, so it can execute faster with multiple runs
- Can preview generation ([#36](https://github.com/Chaoses-Ib/ComfyScript/issues/36))
- [Queue control functions](../README.md#runtime)
- Can [execute workflows asyncly](Runtime.md#async-support)

For [real mode](Runtime.md#real-mode), also these:
- Workflows will be automatically tracked and saved to image metadata, while in ComfyUI-to-Python-Extension you have to write the metadata manually if you want it

  This also means ComfyUI's web UI can directly load workflows from images generated by ComfyScript, but not from images generated by ComfyUI-to-Python-Extension by default. You can also [disable this behavior](Images/README.md#metadata) if you want.

- Can enable custom node output cache mechanism ([#34](https://github.com/Chaoses-Ib/ComfyScript/issues/34))

By the way, you can also run the code generated by ComfyUI-to-Python-Extension with ComfyScript's [naked mode](Runtime.md#naked-mode).

For disadvantages:
- No buttons in ComfyUI's web UI to convert workflows, instead, workflows will be converted and outputed when it's executed, and can be manually converted with [CLI](Transpiler.md#cli), Jupyter widget ([MetadataViewer](UI/Solara.md#metadataviewer)) and Python code
- ComfyScript is more complex, requiring more experiences with Python to read its source code (for learning or modifying)
- ComfyScript has more dependencies by default, though you can turn off all the dependencies or turn off the dependencies of specific features if you want ([pyproject.toml](../pyproject.toml))
- ComfyScript will run some code to convert the arguments at runtime, which may make debugging nodes harder, though in naked mode it won't