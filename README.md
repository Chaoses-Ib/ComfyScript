# ComfyUI_Ib_CustomNodes
- ComfyScript

  Translate ComfyUI's workflows to human-readable Python scripts.

  CLI:
  ```sh
  python -m script from-workflow "D:\workflow.json"
  ```

- Load Image From Path

  ComfyUI's built-in `Load Image` node can only load uploaded images, which produces duplicated files in the input directory and cannot reload the image when the source file is changed. `Load Image From Path` instead loads the image from the source path and does not have such problems.

  One use of this node is to work with Photoshop's [Quick Export](https://helpx.adobe.com/photoshop/using/export-artboards-layers.html#:~:text=in%20Photoshop.-,Quick%20Export%20As,-Use%20the%20Quick) to quickly perform img2img/inpaint on the edited image.

  The image path can be in the following format:
  - Absolute path:

    `D:\ComfyUI\output\ComfyUI_00001_-assets\ComfyUI_00001_.png`

  - Relative to the input directory:
  
    `ComfyUI_00001_-assets\ComfyUI_00001_.png [output]`

  - Relative to the output directory:
  
    `ComfyUI_00001_-assets\ComfyUI_00001_.png [input]`

  - Relative to the temp directory:
  
    `ComfyUI_00001_-assets\ComfyUI_00001_.png [temp]`