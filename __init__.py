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
    
    import PIL
    import nodes

    pnginfo_add_text_original = PIL.PngImagePlugin.PngInfo.add_text
    def pnginfo_add_text_hook(self, key, value, zip=False):
        if key == 'workflow':
            workflow = value
            try:
                comfy_script = script.WorkflowToScriptTranspiler(workflow).to_script()
                # print(comfy_script)

                chunks = self.chunks
                self.chunks = []
                self.add_text('ComfyScript', comfy_script)
                self.chunks.extend(chunks)
            except Exception:
                # Print stack trace, but do not block the original saving
                traceback.print_exc()
        return pnginfo_add_text_original(self, key, value, zip)
    PIL.PngImagePlugin.PngInfo.add_text = pnginfo_add_text_hook

    SaveImage = nodes.NODE_CLASS_MAPPINGS['SaveImage']
    save_images_orginal = getattr(SaveImage, SaveImage.FUNCTION)
    def save_images_hook(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        # print(extra_pnginfo)
        if extra_pnginfo is None or 'workflow' not in extra_pnginfo:
            print("Ib Custom Nodes: Failed to save ComfyScript because workflow is not in extra_pnginfo")
        # else:
        #     workflow = extra_pnginfo['workflow']
        #     try:
        #         comfy_script = script.WorkflowToScriptTranspiler(workflow).to_script()
        #         # print(comfy_script)
                
        #         # Values in extra_pnginfo will be serialized as JSON
        #         # extra_pnginfo['ComfyScript'] = comfy_script
        #         pnginfo_init_original = PIL.PngImagePlugin.PngInfo.__init__
        #         def pnginfo_init_hook(self):
        #             pnginfo_init_original(self)
        #             self.add_text('ComfyScript', comfy_script)
        #         PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_hook
        #         r = save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
        #         PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_original
        #         return r
        #     except Exception:
        #         # Print stack trace, but do not block the original saving
        #         traceback.print_exc()
        return save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
    setattr(SaveImage, SaveImage.FUNCTION, save_images_hook)

setup_script()

print("\033[34mIb Custom Nodes: \033[92mLoaded\033[0m")
