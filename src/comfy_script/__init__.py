# import_as_node = False

# import inspect

# frame = inspect.currentframe()
# if frame is not None:
#     while (frame := frame.f_back) is not None:
#         if frame.f_globals.get('__package__') == 'importlib':
#             continue
#         if 'NODE_CLASS_MAPPINGS' in frame.f_globals:
#             import_as_node = True
#         break
# del frame

# if import_as_node:
#     from .nodes import *