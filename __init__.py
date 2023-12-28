__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

success = True

from pathlib import Path

try:
    print('\033[34mComfyScript: \033[93mLoading nodes...\033[0m')
    # If there are conflicts, the later one will override the former one.

    from .nodes import ComfyUI_Ib_CustomNodes
    NODE_CLASS_MAPPINGS.update(ComfyUI_Ib_CustomNodes.NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(ComfyUI_Ib_CustomNodes.NODE_DISPLAY_NAME_MAPPINGS)
except ImportError:
    success = False
    print(
f'''\033[34mComfyScript: \033[91mFailed to load nodes due to missing submodules. If you need them, try to run:
git -C "{Path(__file__).resolve().parent}" submodule update --init --recursive
\033[0m''')

def setup_script():
    from .script import transpile

    import inspect
    import sys
    import traceback
    import json
    
    import PIL
    import nodes

    if sys.version_info < (3, 6):
        print('ComfyScript: Python 3.6+ is required to preserve insertion order of input types.')

    pnginfo_add_text_original = PIL.PngImagePlugin.PngInfo.add_text
    def pnginfo_add_text_hook(self, key, value, zip=False):
        try:
            if key == 'workflow':
                workflow = value
                end_nodes = None
                frame = inspect.currentframe()
                while frame := frame.f_back:
                    if 'unique_id' in frame.f_locals:
                        end_nodes = [int(frame.f_locals['unique_id'])]
                        break
                else:
                    print('ComfyScript: Failed to resolve the id of current node.')

                comfy_script = transpile.WorkflowToScriptTranspiler(workflow).to_script(end_nodes)
                print('ComfyScript:', comfy_script, sep='\n')

                chunks = self.chunks
                self.chunks = []
                pnginfo_add_text_original(self, 'ComfyScript', comfy_script, zip)
                self.chunks.extend(chunks)
            elif key == 'ComfyScriptSource':
                value = json.loads(value)
                # print(value)

                chunks = self.chunks
                self.chunks = []
                r = pnginfo_add_text_original(self, key, value, zip)
                self.chunks.extend(chunks)
                return r
        except Exception:
            # Print stack trace, but do not block the original saving
            traceback.print_exc()
        return pnginfo_add_text_original(self, key, value, zip)
    PIL.PngImagePlugin.PngInfo.add_text = pnginfo_add_text_hook

    SaveImage = nodes.NODE_CLASS_MAPPINGS['SaveImage']
    save_images_orginal = getattr(SaveImage, SaveImage.FUNCTION)
    def save_images_hook(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        # print(extra_pnginfo)
        if extra_pnginfo is None or ('workflow' not in extra_pnginfo and 'ComfyScriptSource' not in extra_pnginfo):
            print("ComfyScript: Failed to save ComfyScript because workflow is not in extra_pnginfo")
        # elif 'ComfyScriptSource' in extra_pnginfo:
        #     # Values in extra_pnginfo will be serialized as JSON
        #     pnginfo_init_original = PIL.PngImagePlugin.PngInfo.__init__
        #     comfy_script_source = extra_pnginfo['ComfyScriptSource']
        #     def pnginfo_init_hook(self):
        #         pnginfo_init_original(self)
        #         self.add_text('ComfyScriptSource', comfy_script_source)
        #     PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_hook
        #     del extra_pnginfo['ComfyScriptSource']
        #     r = save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
        #     extra_pnginfo['ComfyScriptSource'] = comfy_script_source
        #     PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_original
        #     return r
        # elif 'workflow' in extra_pnginfo:
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

try:
    setup_script()
except ImportError:
    success = False
    print(
f'''\033[34mComfyScript: \033[91mFailed to setup script translation due to missing dependencies. If you need this, try to run:
python -m pip install -r "{Path(__file__).resolve().parent / 'script' / 'transpile' / 'requirements.txt'}"
\033[0m''')

if success:
    print('\033[34mComfyScript: \033[92mLoaded\033[0m')
