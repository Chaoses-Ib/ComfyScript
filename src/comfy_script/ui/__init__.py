import importlib

if importlib.util.find_spec('ipywidgets') is not None:
    from . import ipy

if importlib.util.find_spec('solara') is not None:
    try:
        from . import solara
    except:
        # Solara didn't support Python 3.14
        print('ComfyScript: Failed to import solara')
