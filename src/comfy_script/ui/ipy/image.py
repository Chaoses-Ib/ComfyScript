import asyncio
import itertools
import math
from typing import Iterable
from PIL import Image

class ImageViewer:
    '''Used to display multiple images in Jupyter Notebook.'''

    def __init__(self, *images: 'Image.Image | NodeOutput | ImageBatchResult | Iterable'):
        '''
        - `images`: `PIL.Image`, `NodeOutput`, `ImageBatchResult`, or iterables (`list`, `tuple`, ...) of them. Recursive iterables are also supported.
        '''
        self.images = images
    
    async def _flatten(images) -> list[Image.Image]:
        from comfy_script.runtime.data import NodeOutput
        from comfy_script.runtime.data.Images import ImageBatchResult

        if isinstance(images, Image.Image):
            return [images]

        if isinstance(images, NodeOutput):
            images = await images
        if isinstance(images, ImageBatchResult):
            return await images
        
        if isinstance(images, Iterable):
            return [*itertools.chain(*[await ImageViewer._flatten(image) for image in images])]
    
        raise TypeError(f'Invalid image type: {type(images)}')

    async def _display(
        self,
        rows: int | None = 1,
        cols: int | None = None,
        height: int | None = None,
        width: int | None = None,
        *,
        titles: list[str] | None = None,
        **kwds
    ):
        images = await ImageViewer._flatten(self.images)
        self.images = images
        if not images:
            return
        
        from IPython.display import display
        
        # Not use HTML if there is only one image or one column
        if height is None and width is None and titles is None:
            if len(images) == 1:
                display(images[0])
                return
            if cols == 1:
                display(*images)
                return
        
        import ipywidgets as widgets

        first_image = images[0]

        if rows is None:
            rows = math.ceil(len(images) / cols)
        elif cols is None:
            cols = math.ceil(len(images) / rows)

        if height is not None:
            if width is None:
                width = int(height * first_image.width / first_image.height)
            kwds['height'] = f'{(height + 2) * rows}px'
        if width is not None:
            kwds['width'] = f'{(width + 2) * cols}px'
        grid = widgets.GridspecLayout(rows, cols, **kwds)
        for i in range(rows):
            for j in range(cols):
                k = i * cols + j
                if k < len(images):
                    kwds = {}
                    if height is not None:
                        kwds['height'] = height
                    if width is not None:
                        kwds['width'] = width
                    image = widgets.Image(value=images[k]._repr_png_(), **kwds)
                    image.add_class('comfy-script-image')
                    if titles is not None:
                        grid[i, j] = widgets.VBox([image, widgets.Label(titles[k], layout=widgets.Layout(align_self='center'))])
                    else:
                        grid[i, j] = image

        # https://github.com/microsoft/vscode-jupyter/issues/7161
        display(widgets.HBox(children=[widgets.HTML('''<style>
.cell-output-ipywidget-background {
background-color: transparent !important;
}
:root {
--jp-widgets-color: var(--vscode-editor-foreground);
--jp-widgets-font-size: var(--vscode-editor-font-size);
}
.comfy-script-image {
padding: 2px;
}</style>'''), grid]))
        
    def display(
        self,
        rows: int | None = 1,
        cols: int | None = None,
        height: int | None = None,
        width: int | None = None,
        *,
        titles: list[str] | None = None,
        **kwds
    ):
        asyncio.run(self._display(rows, cols, height, width, titles=titles, **kwds))
    
    def _ipython_display_(self):
        self.display()