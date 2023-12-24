__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

success = True

try:
    from .image import *
    NODE_CLASS_MAPPINGS['LoadImageFromPath'] = LoadImageFromPath
    NODE_DISPLAY_NAME_MAPPINGS['LoadImageFromPath'] = "Load Image From Path"
except ImportError:
    success = False
    print(
f'''\033[34mIb Custom Nodes: \033[91mFailed to load LoadImageFromPath due to missing dependencies. If you need it, try to run:
python -m pip install -r "{Path(__file__).resolve().parent / 'requirements.txt'}"
\033[0m''')

def setup_script():
    from .script import transpile

    import inspect
    import sys
    import traceback
    
    import PIL
    import nodes

    if sys.version_info < (3, 6):
        print('Ib Custom Nodes: Python 3.6+ is required to preserve insertion order of input types.')

    pnginfo_add_text_original = PIL.PngImagePlugin.PngInfo.add_text
    def pnginfo_add_text_hook(self, key, value, zip=False):
        if key == 'workflow':
            workflow = value
            try:
                end_nodes = None
                frame = inspect.currentframe()
                while frame := frame.f_back:
                    if 'unique_id' in frame.f_locals:
                        end_nodes = [int(frame.f_locals['unique_id'])]
                        break
                else:
                    print('Ib Custom Nodes: Failed to resolve the id of current node.')

                comfy_script = transpile.WorkflowToScriptTranspiler(workflow).to_script(end_nodes)
                print('ComfyScript:', comfy_script, sep='\n')

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
        if extra_pnginfo is None or ('workflow' not in extra_pnginfo and 'ComfyScriptSource' not in extra_pnginfo):
            print("Ib Custom Nodes: Failed to save ComfyScript because workflow is not in extra_pnginfo")
        elif 'ComfyScriptSource' in extra_pnginfo:
            # Values in extra_pnginfo will be serialized as JSON
            pnginfo_init_original = PIL.PngImagePlugin.PngInfo.__init__
            def pnginfo_init_hook(self, _comfyscript_source=extra_pnginfo['ComfyScriptSource']):
                pnginfo_init_original(self)
                self.add_text('ComfyScriptSource', _comfyscript_source)
            PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_hook
            del extra_pnginfo['ComfyScriptSource']
            r = save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
            PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_original
            return r
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
    from pathlib import Path
    print(
f'''\033[34mIb Custom Nodes: \033[91mFailed to setup script translation due to missing dependencies. If you need this, try to run:
python -m pip install -r "{Path(__file__).resolve().parent / 'script' / 'transpile' / 'requirements.txt'}"
\033[0m''')

if success:
    print('\033[34mIb Custom Nodes: \033[92mLoaded\033[0m')
