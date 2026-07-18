#!/usr/bin/env python3
import sys
comfyui = sys.argv[1] if len(sys.argv) > 1 else None

from comfy_script.runtime import *
load(comfyui, args=ComfyUIArgs('--disable-all-custom-nodes'))
print('loaded')
from comfy_script.runtime.nodes import *

# Basic
with Workflow():
    image = EmptyImage()
    image = ImageBlur(image, 30)
    print(SaveImage(image, 'tests/virtual'))
