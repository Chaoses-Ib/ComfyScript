import solara
from PIL import Image

from ...transpile import WorkflowToScriptTranspiler

@solara.component
def MetadataViewer(comfyui_api: str = None):
    script, set_script = solara.use_state('')
    script_source, set_script_source = solara.use_state('')

    def on_file(file_info: solara.file_drop.FileInfo):
        # print(file_info)

        # Use WorkflowToScriptTranspiler.from_file()/from_image() if you don't need 'ComfyScriptSource' and 'parameters'
        file_obj = file_info['file_obj']
        first_byte = file_obj.read(1)
        file_obj.seek(0)
        if first_byte == b'{':
            workflow = file_obj.read().decode('utf-8')
            set_script(WorkflowToScriptTranspiler(workflow).to_script())
        else:
            image = Image.open(file_obj)
            
            # TODO: webp
            image_info = image.info
            if 'ComfyScript' in image_info:
                set_script(image_info['ComfyScript'])
            elif 'workflow' in image_info or 'prompt' in image_info:
                if 'workflow' in image_info:
                    workflow = image_info['workflow']
                elif 'prompt' in image_info:
                    workflow = image_info['prompt']
                set_script(WorkflowToScriptTranspiler(workflow).to_script())
            elif 'parameters' in image_info:
                set_script(image_info['parameters'])
        
            if 'ComfyScriptSource' in image_info:
                set_script_source(image_info['ComfyScriptSource'])
    
    solara.FileDrop("Drop an image here\n(In VS Code, one need to hold Shift before drag the image, otherwise the file will be opened in VS Code)", on_file=on_file)
    # TODO: https://github.com/widgetti/solara/issues/446
    solara.Markdown(f'''```python
{script}```''')
    if script_source != '':
        solara.Markdown(f'''```python
{script_source}```''')