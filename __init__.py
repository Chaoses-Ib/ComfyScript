__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

success = True

import sys
from pathlib import Path

if sys.version_info < (3, 9):
    success = False
    print('\033[34mComfyScript: \033[91mPython 3.9+ is required.\033[0m')

root = Path(__file__).resolve().parent

# Replaced by prestartup_script.py
# try:
#     print('\033[34mComfyScript: \033[93mLoading nodes...\033[0m')
#     # If there are conflicts, the later one will override the former one.

#     from .nodes import ComfyUI_Ib_CustomNodes
#     NODE_CLASS_MAPPINGS.update(ComfyUI_Ib_CustomNodes.NODE_CLASS_MAPPINGS)
#     NODE_DISPLAY_NAME_MAPPINGS.update(ComfyUI_Ib_CustomNodes.NODE_DISPLAY_NAME_MAPPINGS)
# except (ImportError, AttributeError) as e:
#     success = False
#     print(
# f'''\033[34mComfyScript: \033[91mFailed to load additional nodes due to missing submodules: {e}.
# If you need them, try to run:
# git -C "{root}" submodule update --init --recursive
# \033[0m''')

if not (root / 'nodes' / 'ComfyUI_Ib_CustomNodes' / '__init__.py').exists():
    success = False
    print(
f'''\033[34mComfyScript: \033[91mFailed to load additional nodes due to missing submodules. If you need them, try to run:
git -C "{root}" submodule update --init --recursive
\033[0m''')

sys.path.insert(0, str(root / 'src'))
import comfy_script.nodes
from comfy_script.nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
success &= comfy_script.nodes.success

if success:
    print('\033[34mComfyScript: \033[92mLoaded\033[0m')
