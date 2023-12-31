# Runtime
## Async support
The runtime is internally asynchronous, but only exposes synchronous APIs for the following reasons:
- To make the script more friendly to Python newbies
- To avoid being infectious
  
  Some libraries, such as ipywidgets, do not support async yet.
- To make scripts shorter

If you want to use the asynchronous APIs, you need to:
- Prefix all APIs support async with an underscore and await
  
  For example:
  - `load()` → `await runtime._load()`
  - `queue.cancel_all()` → `await queue._cancel_all()`
  - `obj.display()` (and `display(obj)`) → `await obj._display()`
- Replace `with Workflow` with `async with Workflow`
- Replace `obj.wait()` with `await obj`, `obj.wait_result()` with `await obj.result()`
- Replace `ImageBatchResult[i]` with `await ImageBatchResult.get(i)`

## Other differences from ComfyUI's web UI
- No limitations on input precision and range.

  For example, in the web UI, `ImageScaleBy`'s `scale_by` has a minimum precision of 0.01, it is not possible to use a value like `0.375`, but only `0.38` (even if the workflow is generated by ComfyScript). But in ComfyScript, there is no such limitations.