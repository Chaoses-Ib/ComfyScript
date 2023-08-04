from .image import *

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

NODE_CLASS_MAPPINGS = {
    "LoadImageFromPath": LoadImageFromPath
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromPath": "Load Image From Path"
}

print("\033[34mIb Custom Nodes: \033[92mLoaded\033[0m")
