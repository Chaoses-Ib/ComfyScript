import torch

import os
import hashlib
from pathlib import Path

from PIL import Image, ImageOps
import numpy as np

import folder_paths

class LoadImageFromPath:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"image": ("STRING", {"default": r"ComfyUI_00001_-assets\ComfyUI_00001_.png [output]"})},
                }

    CATEGORY = "image"

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    def load_image(self, image):
        image_path = LoadImageFromPath._resolve_path(image)

        i = Image.open(image_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
        return (image, mask)

    def _resolve_path(image) -> Path:
        image_path = Path(folder_paths.get_annotated_filepath(image))
        return image_path

    @classmethod
    def IS_CHANGED(s, image):
        image_path = LoadImageFromPath._resolve_path(image)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(s, image):
        image_path = LoadImageFromPath._resolve_path(image)
        if not image_path.exists():
            return "Invalid image path: {}".format(image_path)

        return True