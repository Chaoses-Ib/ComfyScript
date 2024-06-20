from __future__ import annotations
import asyncio
import io
from PIL import Image

from . import Result

class ImageBatchResult(Result):
    # TODO: Lazy cell
    async def _get_image(self, image: dict) -> Image.Image | None:
        async with client.client.session() as session:
            async with session.get(f'{client.client.base_url}view', params=image) as response:
                if response.status == 200:
                    return Image.open(io.BytesIO(await response.read()))
                else:
                    print(f'ComfyScript: Failed to get image: {await client.response_to_str(response)}')
                    return
    
    def __await__(self) -> list[Image.Image | None]:
        async def f(self):
            return [await self._get_image(image) for image in self._output['images']]
        return f(self).__await__()
    
    def wait(self) -> list[Image.Image | None]:
        return asyncio.run(self)
    
    async def get(self, i: int) -> Image.Image | None:
        return await self._get_image(self._output['images'][i])
    
    def __getitem__(self, i: int) -> Image.Image | None:
        return asyncio.run(self.get(i))
    
    def display(self, rows: int | None = 1, cols: int | None = None, height: int | None = None, width: int | None = None, **kwds):
        Images(self).display(rows, cols, height, width, **kwds)

    def _ipython_display_(self):
        self.display()

# TODO: Deprecate this?
from ...ui.ipy import ImageViewer as Images

from ... import client

__all__ = [
    'ImageBatchResult',
    'Images',
]