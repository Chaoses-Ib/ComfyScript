def _outputs_to_paths(outputs: list[dict], type: bool = True) -> list[str]:
    '''
    - `outputs`:
      e.g.
      ```
      [{'filename': 'ComfyUI_00001_.latent',
      'subfolder': 'latents',
      'type': 'output'}]
      ```
    '''
    if type:
        return list([f'{d["subfolder"]}/{d["filename"]} [{d["type"]}]' for d in outputs])
    else:
        return list([f'{d["subfolder"]}/{d["filename"]}' for d in outputs])
