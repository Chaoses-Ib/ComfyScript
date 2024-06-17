import importlib

if importlib.util.find_spec('solara') is not None:
    from . import solara