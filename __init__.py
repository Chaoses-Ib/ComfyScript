__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

success = True

import sys
from pathlib import Path

if sys.version_info < (3, 9):
    success = False
    print('\033[34mComfyScript: \033[91mPython 3.9+ is required.\033[0m')

root = Path(__file__).resolve().parent

sys.path.insert(0, str(root / 'src'))
import comfy_script.nodes
from comfy_script.nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
success &= comfy_script.nodes.success

# Load comfyui-legacy custom nodes
import importlib.metadata
import importlib.util
import traceback

import nodes
for entry_point in importlib.metadata.entry_points(group='comfyui_legacy.custom_nodes'):
    try:
        spec = importlib.util.find_spec(entry_point.module)
        nodes.load_custom_node(spec.submodule_search_locations[0])
    except Exception as e:
        print(f'ComfyScript: Failed to load legacy custom nodes from {entry_point}: {e}')
        traceback.print_exc()

if success:
    print('\033[34mComfyScript: \033[92mLoaded\033[0m')
