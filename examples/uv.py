# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "comfy-script[default]",
# ]
# ///
# The above is only needed when using uv and without --with "comfy-script[default]"
from comfy_script.runtime import *
# ComfyUI server/path
# or: load(r'path/to/ComfyUI')
load('http://127.0.0.1:8188/')
from comfy_script.runtime.nodes import *

with Workflow(wait=True):
    image = EmptyImage()
    images = util.get_images(image, save=True)
