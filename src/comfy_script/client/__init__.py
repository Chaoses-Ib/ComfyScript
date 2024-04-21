from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from io import BytesIO
import json
import os
from pathlib import PurePath
import struct
import sys
import traceback
from typing import Callable

import asyncio
from warnings import warn
from PIL import Image
import nest_asyncio
import aiohttp
from yarl import URL

nest_asyncio.apply()

class Client:
    def __init__(
        self,
        base_url: str | URL = 'http://127.0.0.1:8188/',
        *,
        session_factory: Callable[[], aiohttp.ClientSession] = aiohttp.ClientSession
    ):
        '''
        - `base_url`: The base URL of the ComfyUI server API.

          e.g. `'http://127.0.0.1:8188/'`

        - `session_factory`: A callable factory that returns a new [`aiohttp.ClientSession`](https://docs.aiohttp.org/en/latest/client_reference.html#aiohttp.ClientSession) object. 

          e.g. `lambda: aiohttp.ClientSession(auth=aiohttp.BasicAuth('Aladdin', 'open sesame'))`
        '''
        if base_url is None:
            base_url = 'http://127.0.0.1:8188/'
        elif not isinstance(base_url, str):
            base_url = str(base_url)
        
        if not base_url.startswith('http://'):
            base_url = 'http://' + base_url
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url

        # Do not pass base_url to ClientSession, as it only supports absolute URLs without path part
        self._session_factory = session_factory
    
    def session(self) -> aiohttp.ClientSession:
        '''Because `aiohttp.ClientSession` is not event-loop-safe (thread-safe), a new session should be created for each request to avoid potential issues. Also, `aiohttp.ClientSession` cannot be closed in a sync manner.'''
        return self._session_factory()

client: Client = Client()
'''The global client object.'''

async def response_to_str(response: aiohttp.ClientResponse) -> str:
    try:
        msg = json.dumps(await response.json(), indent=2)
    except Exception as e:
        msg = str(e)
    return f'{response}{msg}'

async def _get_nodes_info() -> dict:
    '''
    When used with standalone runtime:
    - The result may contain tuples intead of lists.
    '''
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

    async with client.session() as session:
        # http://127.0.0.1:8188/object_info
        async with session.get(f'{client.base_url}object_info') as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f'ComfyScript: Failed to get nodes info: {await response_to_str(response)}')

def get_nodes_info() -> dict:
    '''
    When used with standalone runtime:
    - The result may contain tuples intead of lists.
    '''
    return asyncio.run(_get_nodes_info())

async def _get_embeddings() -> list[str]:
    folder_paths = sys.modules.get('folder_paths')
    if folder_paths is not None and 'get_filename_list' in vars(folder_paths):
        embeddings = folder_paths.get_filename_list("embeddings")
        return list(map(lambda a: os.path.splitext(a)[0], embeddings))
    
    async with client.session() as session:
        # http://127.0.0.1:8188/embeddings
        async with session.get(f'{client.base_url}embeddings') as response:
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

class BinaryEventTypes(IntEnum):
    # See ComfyUI::server.BinaryEventTypes
    PREVIEW_IMAGE = 1
    UNENCODED_PREVIEW_IMAGE = 2
    '''Only used internally in ComfyUI.'''

@dataclass
class BinaryEvent:
    type: BinaryEventTypes | int
    data: bytes

    @staticmethod
    def from_bytes(data: bytes) -> BinaryEvent:
        # See ComfyUI::server.encode_bytes()
        type_int = struct.unpack('>I', data[:4])[0]
        try:
            type = BinaryEventTypes(type_int)
        except ValueError:
            warn(f'Unknown binary event type: {data[:4]}')
            type = type_int
        data = data[4:]
        return BinaryEvent(type, data)
    
    def to_object(self) -> Image.Image | bytes:
        if self.type == BinaryEventTypes.PREVIEW_IMAGE:
            return _PreviewImage.from_bytes(self.data).image
        return self

class _PreviewImageFormat(IntEnum):
    '''`format.name` is compatible with PIL.'''
    JPEG = 1
    PNG = 2

@dataclass
class _PreviewImage:
    format: _PreviewImageFormat
    image: Image.Image

    @staticmethod
    def from_bytes(data: bytes) -> _PreviewImage:
        # See ComfyUI::LatentPreviewer
        format_int = struct.unpack('>I', data[:4])[0]
        format = None
        try:
            format = _PreviewImageFormat(format_int).name
        except ValueError:
            warn(f'Unknown image format: {data[:4]}')

        image = Image.open(BytesIO(data[4:]), formats=(format,) if format is not None else None)

        return _PreviewImage(format, image)

__all__ = [
    'client',
    'Client',
    '_get_nodes_info',
    'get_nodes_info',
    '_get_embeddings',
    'get_embeddings'
]