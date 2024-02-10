# Documentation
## Workflow information retrieval
It is possible to retrieve any wanted information by running the script with some stubs. For example, to get all positive prompt texts, one can define:

```python
positive_prompts = []

def CLIPTextEncode(text, clip):
    return text

def KSampler(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent_image, denoise):
    positive_prompts.append(positive)
```
And use [`exec()`](https://docs.python.org/3/library/functions.html#exec) to run the script (stubs for other nodes can be automatically generated). This way, `Reroute`, `PrimitiveNode`, and other special nodes won't be a problem stopping one from getting the information.

It is also possible to generate a JSON by this. However, since JSON can only contain tree data and the workflow is a DAG, some information will have to be discarded, or the input have to be replicated at many positions.