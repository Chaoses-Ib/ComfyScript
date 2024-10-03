'''
An example script for setting up and running ComfyUI and ComfyScript with Modal.

Be careful if you want to replace the official ComfyUI with the comfyui package, Modal does not work well with it: https://github.com/Chaoses-Ib/ComfyScript/issues/69

Authors: @the-dream-machine, @Chaoses-Ib
'''

import subprocess
import modal

image = (
    modal.Image.debian_slim(python_version="3.12.5")
    .apt_install("git")
    .pip_install("comfy-cli==1.1.6")
    # use comfy-cli to install the ComfyUI repo and its dependencies
    .run_commands("comfy --skip-prompt install --nvidia")
    # download all models and custom nodes required in your workflow
    .run_commands(
        "comfy --skip-prompt model download --url https://civitai.com/api/download/models/290640 --relative-path models/checkpoints"
    )
    .run_commands(
        "cd /root/comfy/ComfyUI/custom_nodes && git clone https://github.com/Chaoses-Ib/ComfyScript.git",
        "cd /root/comfy/ComfyUI/custom_nodes/ComfyScript && python -m pip install -e '.[default]'",
    )
)

app = modal.App("pony_diffusion_2")

# Optional: serve the UI
@app.function(
    allow_concurrent_inputs=10,
    concurrency_limit=1,
    container_idle_timeout=30,
    timeout=1800,
    gpu="T4",
)
@modal.web_server(8000, startup_timeout=60)
def ui():
    _web_server = subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)

@app.cls(gpu="T4", container_idle_timeout=120, image=image)
class Model:
    @modal.build()
    def build(self):
        print("🛠️ Building container...")

    @modal.enter()
    def enter(self):
        print("✅ Entering container...")
        from comfy_script.runtime import load
        load()

    @modal.exit()
    def exit(self):
        print("🧨 Exiting container...")

    @modal.method()
    def generate_image(self, prompt:str):
        print("🎨 Generating image...")
        from comfy_script.runtime import Workflow
        from comfy_script.runtime.nodes import CheckpointLoaderSimple, CLIPTextEncode, EmptyLatentImage, KSampler, VAEDecode, SaveImage, CivitAICheckpointLoader
        from PIL import Image

        with Workflow():
            model, clip, vae = CivitAICheckpointLoader('https://civitai.com/models/101055?modelVersionId=128078')
            # model, clip, vae = CheckpointLoaderSimple("ponyDiffusionV6XL_v6StartWithThisOne.safetensors")
            conditioning = CLIPTextEncode('beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip)
            conditioning2 = CLIPTextEncode('text, watermark', clip)
            latent = EmptyLatentImage(512, 512, 1)
            latent = KSampler(model, 156680208700286, 20, 8, 'euler', 'normal', conditioning, conditioning2, latent, 1)
            image = VAEDecode(latent, vae)
            result = SaveImage(image, 'ComfyUI')
        images: list[Image.Image] = result.wait().wait()
        return images

@app.local_entrypoint()
def main(prompt: str):
    Model().generate_image.remote(prompt)