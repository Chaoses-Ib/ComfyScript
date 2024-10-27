from typing import Any

nodes: dict[str, Any] = {}
'''A dict of loaded nodes keyed by their raw names. Compared to `comfy_script.runtime.real.nodes` module, `nodes` is more suitable for programmatic access.

Example:
```
from comfy_script.runtime.real import *
load()

print(node.nodes)
# {'KSampler': <Node KSampler>,
#  'CheckpointLoaderSimple': <Node CheckpointLoaderSimple>,
#  'CLIPTextEncode': <Node CLIPTextEncode>,
#  ...

# or: node.get('CheckpointLoaderSimple')
loader = node.nodes['CheckpointLoaderSimple']
model, clip, vae = loader('v1-5-pruned-emaonly.ckpt')
```

With type hint:
```
from comfy_script.runtime.real.nodes import CheckpointLoaderSimple

loader: type[CheckpointLoaderSimple] = node.nodes['CheckpointLoaderSimple']
model, clip, vae = loader('v1-5-pruned-emaonly.ckpt')
```

With compile-time-only type hint:
```
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comfy_script.runtime.real.nodes import CheckpointLoaderSimple

loader: 'type[CheckpointLoaderSimple]' = node.nodes['CheckpointLoaderSimple']
model, clip, vae = loader('v1-5-pruned-emaonly.ckpt')
```
'''

def get(name: str) -> Any | None:
    return nodes.get(name, None)

__all__ = [
    'nodes',
    'get'
]