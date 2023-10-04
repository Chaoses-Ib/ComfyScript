from . import script
from .image import *

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

NODE_CLASS_MAPPINGS = {
    "LoadImageFromPath": LoadImageFromPath
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromPath": "Load Image From Path"
}

def setup_script():
    import traceback
    
    import nodes

    SaveImage = nodes.NODE_CLASS_MAPPINGS['SaveImage']
    save_images_orginal = getattr(SaveImage, SaveImage.FUNCTION)
    def save_images_hook(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        # print(extra_pnginfo)
        if extra_pnginfo is None or 'workflow' not in extra_pnginfo:
            print("Ib Custom Nodes: Failed to save ComfyScript because workflow is not in extra_pnginfo")
        else:
            workflow = extra_pnginfo['workflow']
            try:
                comfy_script = script.WorkflowToScriptTranspiler(workflow).to_script()
                # print(comfy_script)
                # TODO: Prevent JSON serialization
                extra_pnginfo['ComfyScript'] = comfy_script
            except Exception:
                # Print stack trace, but do not block the original saving
                traceback.print_exc()
        return save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
    setattr(SaveImage, SaveImage.FUNCTION, save_images_hook)

setup_script()

print("\033[34mIb Custom Nodes: \033[92mLoaded\033[0m")
