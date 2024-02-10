# Transpiler
## CLI
Requirement:
```sh
python -m pip install click~=8.1
```
(or `pip install -e ".[default,cli]"` or `pip install "comfy-script[default,cli]"` when installing)

Usage:
```sh
Usage: python -m comfy_script.transpile [OPTIONS] WORKFLOW

  Transpile workflow to ComfyScript.

Options:
  --api TEXT  Default: http://127.0.0.1:8188/
  --help      Show this message and exit.
```

Example:
```powershell
python -m comfy_script.transpile "D:\workflow.json"
```