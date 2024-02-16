import json
import os
from pathlib import PurePath
import sys
import traceback

import asyncio
import nest_asyncio
import aiohttp

nest_asyncio.apply()

endpoint = 'http://127.0.0.1:8188/'

def set_endpoint(api_endpoint: str):
    global endpoint
    if not api_endpoint.startswith('http://'):
        api_endpoint = 'http://' + api_endpoint
    if not api_endpoint.endswith('/'):
        api_endpoint += '/'
    endpoint = api_endpoint

async def response_to_str(response: aiohttp.ClientResponse) -> str:
    try:
        msg = json.dumps(await response.json(), indent=2)
    except Exception as e:
        msg = str(e)
    return f'{response}{msg}'

async def _get_nodes_info() -> dict:
    # Don't use `import nodes` with `except ImportError`, `nodes` may be in `sys.path` but not loaded (#15)
    nodes = sys.modules.get('nodes')
    if nodes is not None and 'NODE_CLASS_MAPPINGS' in vars(nodes) and 'NODE_DISPLAY_NAME_MAPPINGS' in vars(nodes):
        # https://github.com/comfyanonymous/ComfyUI/blob/1b103e0cb2d7aeb05fc8b7e006d4438e7bceca20/server.py#L393-L422
        def node_info(node_class):
            obj_class = nodes.NODE_CLASS_MAPPINGS[node_class]
            info = {}
            info['input'] = obj_class.INPUT_TYPES()
            info['output'] = obj_class.RETURN_TYPES
            info['output_is_list'] = obj_class.OUTPUT_IS_LIST if hasattr(obj_class, 'OUTPUT_IS_LIST') else [False] * len(obj_class.RETURN_TYPES)
            info['output_name'] = obj_class.RETURN_NAMES if hasattr(obj_class, 'RETURN_NAMES') else info['output']
            info['name'] = node_class
            info['display_name'] = nodes.NODE_DISPLAY_NAME_MAPPINGS[node_class] if node_class in nodes.NODE_DISPLAY_NAME_MAPPINGS.keys() else node_class
            info['description'] = obj_class.DESCRIPTION if hasattr(obj_class,'DESCRIPTION') else ''
            info['category'] = 'sd'
            if hasattr(obj_class, 'OUTPUT_NODE') and obj_class.OUTPUT_NODE == True:
                info['output_node'] = True
            else:
                info['output_node'] = False

            if hasattr(obj_class, 'CATEGORY'):
                info['category'] = obj_class.CATEGORY
            
            # For internal use
            info['_cls'] = obj_class

            return info
        out = {}
        for x in nodes.NODE_CLASS_MAPPINGS:
            try:
                out[x] = node_info(x)
            except Exception as e:
                print(f"[ERROR] An error occurred while retrieving information for the '{x}' node.", file=sys.stderr)
                traceback.print_exc()
        return out

    async with aiohttp.ClientSession() as session:
    # http://127.0.0.1:8188/object_info
        async with session.get(f'{endpoint}object_info') as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f'ComfyScript: Failed to get nodes info: {await response_to_str(response)}')

def get_nodes_info() -> dict:
    return asyncio.run(_get_nodes_info())

async def _get_embeddings() -> list[str]:
    folder_paths = sys.modules.get('folder_paths')
    if folder_paths is not None and 'get_filename_list' in vars(folder_paths):
        embeddings = folder_paths.get_filename_list("embeddings")
        return list(map(lambda a: os.path.splitext(a)[0], embeddings))
    
    async with aiohttp.ClientSession() as session:
    # http://127.0.0.1:8188/embeddings
        async with session.get(f'{endpoint}embeddings') as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f'ComfyScript: Failed to get embeddings: {await response_to_str(response)}')

def get_embeddings() -> list[str]:
    return asyncio.run(_get_embeddings())

class WorkflowJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PurePath):
            return str(o)
        return super().default(o)

__all__ = [
    'endpoint'
    'set_endpoint',
    '_get_nodes_info',
    'get_nodes_info',
    '_get_embeddings',
    'get_embeddings'
]