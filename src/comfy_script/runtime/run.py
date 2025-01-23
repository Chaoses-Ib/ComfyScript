_redirect___main___file_warn = False

def _redirect___main___file(main_file: str):
    '''
    Redirect `__main__.__file__` to `ComfyUI/main.py` to keep compatibility with some nodes.

    e.g. ComfyUI-Text_Image-Composite (#89), ComfyUI-3D-Pack, ComfyUI_Custom_Nodes_AlekPet,  ComfyUI_MagicQuill, ComfyUI_FizzNodes, zhangp365/ComfyUI-utils-nodes, hinablue/ComfyUI_3dPoseEditor, whmc76/ComfyUI-Openpose-Editor-Plus, ...
    '''
    # GitHub: "import __main__" comfyui language:Python NOT "add_comfyui_directory_to_sys_path"
    import wrapt

    class MainWrapper(wrapt.ObjectProxy):
        _main_file = main_file
        # _enabled = True

        @property
        def __file__(self):
            pass

        @__file__.getter
        def __file__(self):
            # if not MainWrapper._enabled:
            #     return self.__wrapped__.__file__

            global _redirect___main___file_warn
            if _redirect___main___file_warn:
                # e.g. ComfyUI-Inspire-Pack.ConcatConditioningsWithMultiplier.INPUT_TYPES()
                print("ComfyScript: __main__.__file__ is redirected to ComfyUI/main.py to keep compatibility with some nodes")
                _redirect___main___file_warn = False

            # MainWrapper._enabled = False
            # import traceback
            # traceback.print_stack()
            # MainWrapper._enabled = True

            return MainWrapper._main_file

    import __main__
    import sys
    sys.modules['__main__'] = MainWrapper(sys.modules['__main__'])

    # del __main__
    # import __main__
    # print(__main__.__file__)
