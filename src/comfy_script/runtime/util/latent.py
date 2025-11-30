'''
`Latent`-related utility functions.
'''
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comfy_script.runtime.nodes import *
    import comfy_script.runtime.real.nodes as real

from .. import node
from .. import data
from . import path

def concat_latents(*latents: 'Latent') -> 'Latent':
    '''
    - Note that unlike `Image`, batched `Latent` will still be saved to the same file.

    ## Example
    ```
    util.concat_latents(gen_latent(), gen_latent())
    util.concat_latents(*[gen_latent() for _ in range(2)])

    latents = util.save_latent_and_get_paths(util.concat_latents(
        EmptyLatentImage(batch_size=2),
        EmptyLatentImage(batch_size=2)
    ))
    print(len(latents))
    # 1
    ```
    '''
    LatentBatch: 'type[LatentBatch]' = node.nodes['LatentBatch']

    assert len(latents) > 0
    latent = latents[0]
    for i in latents[1:]:
        latent = LatentBatch(latent, i)
    return latent

def load_latent_from_path(path: str) -> 'Latent':
    '''
    ## Example
    ```
    with Workflow():
        latent = EmptyLatentImage(batch_size=4)
        latent_path = util.save_latent_and_get_path(latent)
    print(latent_path)

    with Workflow():
        latent = util.load_latent_from_path(latent_path)
        # Do something with the latent, for example:
        SaveLatent(latent, 'latents/loaded')
    ```
    '''
    LoadLatent: 'type[LoadLatent]' = node.nodes['LoadLatent']
    return LoadLatent(path)

def load_latent_from_paths(paths: list[str]) -> 'Latent':
    '''Load and concat latents from paths.
    '''
    return concat_latents(*[load_latent_from_path(path) for path in paths])

def save_latent(latent: 'Latent', prefix: str | None = None) -> data.Result:
    '''
    - Unfortunately, currently there is no official way to save latent to `temp` instead of `output`.
    '''
    SaveLatent: 'type[SaveLatent]' = node.nodes['SaveLatent']
    return SaveLatent(latent, prefix).wait()

def save_latent_and_get_path(latent: 'Latent', prefix: str | None = None, *, type: bool = True) -> str:
    '''
    - Note that unlike `Image`, batched `Latent` will still be saved to the same file.

    ## Example
    ```
    with Workflow():
        latent = EmptyLatentImage(batch_size=4)
        latent_path = util.save_latent_and_get_path(latent)
    print(latent_path)

    with Workflow():
        latent = util.load_latent_from_path(latent_path)
        # Do something with the latent, for example:
        SaveLatent(latent, 'latents/loaded')
    ```
    '''
    result = save_latent(latent, prefix)

    latents: list[dict] = result._output['latents']
    return path._outputs_to_paths(latents, type)[0]

__all__ = [
    'concat_latents',
    'load_latent_from_path',
    'load_latent_from_paths',
    'save_latent',
    'save_latent_and_get_path',
]
