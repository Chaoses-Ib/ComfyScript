'''These nodes are the nodes provided by ComfyScript, not the nodes loaded by  ComfyUI, which should be in `runtime` package.'''

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

success = True

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

from pathlib import Path

def setup():
    from .. import transpile

    import inspect
    import traceback
    import json
    from warnings import warn
    
    import PIL.PngImagePlugin

    # pnginfo_add_text_original = PIL.PngImagePlugin.PngInfo.add_text
    # def pnginfo_add_text_hook(self, key, value, zip=False):
    #     try:
    #         if key == 'workflow':
    #             workflow = value
    #             end_nodes = None
    #             frame = inspect.currentframe()
    #             while frame := frame.f_back:
    #                 if 'unique_id' in frame.f_locals:
    #                     end_nodes = [int(frame.f_locals['unique_id'])]
    #                     break
    #             else:
    #                 print('ComfyScript: Failed to resolve the id of current node.')

    #             comfy_script = transpile.WorkflowToScriptTranspiler(workflow).to_script(end_nodes)
    #             print('ComfyScript:', comfy_script, sep='\n')

    #             chunks = self.chunks
    #             self.chunks = []
    #             pnginfo_add_text_original(self, 'ComfyScript', comfy_script, zip)
    #             self.chunks.extend(chunks)
    #         elif key == 'ComfyScriptSource':
    #             value = json.loads(value)
    #             # print(value)

    #             chunks = self.chunks
    #             self.chunks = []
    #             r = pnginfo_add_text_original(self, key, value, zip)
    #             self.chunks.extend(chunks)
    #             return r
    #     except Exception:
    #         # Print stack trace, but do not block the original saving
    #         traceback.print_exc()
    #     return pnginfo_add_text_original(self, key, value, zip)
    # PIL.PngImagePlugin.PngInfo.add_text = pnginfo_add_text_hook
        
    class HookedPngInfo(PIL.PngImagePlugin.PngInfo):
        def __new__(cls):
            return object.__new__(cls)

        def __init__(self):
            self._chunks = []
            self._texts = {}

        def add(self, cid, data, after_idat=False):
            chunk = [cid, data]
            if after_idat:
                chunk.append(True)
            self._chunks.append(tuple(chunk))

        def add_text(self, key, value, zip=False):
            self._texts[key] = value, zip
        
        @property
        def chunks(self):
            if self._texts:
                chunks = self._chunks
                self._chunks = []

                print_script = settings.transpile.hook.print_script
                save_script = settings.transpile.hook.save_script
                prefer_api_format = settings.transpile.hook.prefer_api_format
                if print_script is True or save_script is True:
                    if 'workflow' in self._texts or 'prompt' in self._texts:
                        try:
                            end_nodes = None
                            # TODO: UNIQUE_ID
                            frame = inspect.currentframe()
                            while frame := frame.f_back:
                                if 'unique_id' in frame.f_locals:
                                    end_nodes = [frame.f_locals['unique_id']]
                                    break
                            else:
                                print('ComfyScript: Failed to resolve the id of current node.')

                            if not prefer_api_format and 'workflow' in self._texts:
                                workflow, zip = self._texts['workflow']
                                try:
                                    comfy_script = transpile.WorkflowToScriptTranspiler(workflow).to_script(end_nodes)
                                except Exception:
                                    traceback.print_exc()

                                    msg = 'Failed to transpile workflow in web UI format, fallbacking to API format... If this fixes the problem, you can suppress this warning by setting `transpile.hook.prefer_api_format` to `true` in a `settings.toml`, see `settings.example.toml` for details. Please report this issue in https://github.com/Chaoses-Ib/ComfyScript/issues .'
                                    warn(msg)
                                    workflow, zip = self._texts['prompt']
                                    comfy_script = transpile.WorkflowToScriptTranspiler(workflow).to_script(end_nodes)
                            else:
                                workflow, zip = self._texts['prompt']
                                comfy_script = transpile.WorkflowToScriptTranspiler(workflow).to_script(end_nodes)
                            
                            if print_script is True:
                                # TODO: Syntax highlight?
                                print('ComfyScript:', comfy_script, sep='\n')

                            if save_script is True:
                                super().add_text('ComfyScript', comfy_script, zip)
                        except Exception:
                            # Print stack trace, but do not block the original saving
                            traceback.print_exc()
                    else:
                        print("ComfyScript: Failed to save ComfyScript because neither of workflow and prompt is in extra_pnginfo")
                
                if 'ComfyScriptSource' in self._texts:
                    try:
                        source, zip = self._texts['ComfyScriptSource']
                        source = json.loads(source)
                        # print(source)
                        super().add_text('ComfyScriptSource', source, zip)
                        del self._texts['ComfyScriptSource']
                    except Exception:
                        # Print stack trace, but do not block the original saving
                        traceback.print_exc()

                for key, (value, zip) in self._texts.items():
                    super().add_text(key, value, zip)

                self._chunks.extend(chunks)
                self._texts.clear()
            return self._chunks
    # PIL.PngImagePlugin.PngInfo = HookedPngInfo
    PIL.PngImagePlugin.PngInfo.__new__ = lambda _cls: HookedPngInfo.__new__(HookedPngInfo)

    # import nodes
    # SaveImage = nodes.NODE_CLASS_MAPPINGS['SaveImage']
    # save_images_orginal = getattr(SaveImage, SaveImage.FUNCTION)
    # def save_images_hook(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
    #     # print(extra_pnginfo)
    #     if extra_pnginfo is None or ('workflow' not in extra_pnginfo and 'ComfyScriptSource' not in extra_pnginfo):
    #         print("ComfyScript: Failed to save ComfyScript because workflow is not in extra_pnginfo")
    #     # elif 'ComfyScriptSource' in extra_pnginfo:
    #     #     # Values in extra_pnginfo will be serialized as JSON
    #     #     pnginfo_init_original = PIL.PngImagePlugin.PngInfo.__init__
    #     #     comfy_script_source = extra_pnginfo['ComfyScriptSource']
    #     #     def pnginfo_init_hook(self):
    #     #         pnginfo_init_original(self)
    #     #         self.add_text('ComfyScriptSource', comfy_script_source)
    #     #     PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_hook
    #     #     del extra_pnginfo['ComfyScriptSource']
    #     #     r = save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
    #     #     extra_pnginfo['ComfyScriptSource'] = comfy_script_source
    #     #     PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_original
    #     #     return r
    #     # elif 'workflow' in extra_pnginfo:
    #     #     workflow = extra_pnginfo['workflow']
    #     #     try:
    #     #         comfy_script = transpile.WorkflowToScriptTranspiler(workflow).to_script()
    #     #         # print(comfy_script)
                
    #     #         # Values in extra_pnginfo will be serialized as JSON
    #     #         # extra_pnginfo['ComfyScript'] = comfy_script
    #     #         pnginfo_init_original = PIL.PngImagePlugin.PngInfo.__init__
    #     #         def pnginfo_init_hook(self):
    #     #             pnginfo_init_original(self)
    #     #             self.add_text('ComfyScript', comfy_script)
    #     #         PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_hook
    #     #         r = save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
    #     #         PIL.PngImagePlugin.PngInfo.__init__ = pnginfo_init_original
    #     #         return r
    #     #     except Exception:
    #     #         # Print stack trace, but do not block the original saving
    #     #         traceback.print_exc()
    #     return save_images_orginal(self, images, filename_prefix, prompt, extra_pnginfo)
    # setattr(SaveImage, SaveImage.FUNCTION, save_images_hook)

try:
    from ..config import settings
    if settings.transpile.hook.enabled is True:
        setup()
except ImportError as e:
    success = False
    print(
f'''\033[34mComfyScript: \033[91mFailed to setup script translation due to missing dependencies: {e}.
If you need this feature, try to run:
python -m pip install -r "{Path(__file__).resolve().parents[3] / 'requirements.txt'}"
\033[0m''')