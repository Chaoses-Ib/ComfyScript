from pathlib import Path

import pytest

import comfy_script.transpile as transpile

@pytest.mark.parametrize('workflow, script', [
    ('default.json',
r"""model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
conditioning = CLIPTextEncode('beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip)
conditioning2 = CLIPTextEncode('text, watermark', clip)
latent = EmptyLatentImage(512, 512, 1)
latent = KSampler(model, 156680208700286, 20, 8, 'euler', 'normal', conditioning, conditioning2, latent, 1)
image = VAEDecode(latent, vae)
SaveImage(image, 'ComfyUI')"""),
    ('bypass.json',
r"""image, _ = LoadImage('ComfyUI_temp_rcuxh_00001_.png')
image2 = ImageScaleToSide(image, 1024, 'Longest', 'nearest-exact', 'disabled')
PreviewImage(image2)
image3, _ = CRUpscaleImage(image2, '8x_NMKD-Superscale_150000_G.pth', 'rescale', 2, 1024, 'lanczos', 'true', 8)
segs = ImpactMakeTileSEGS(image3, 600, 1.5, 200, 100, 0, 'Reuse fast', None, None)
# _ = SEGSPreview(segs, True, 0.1, image3)
image4 = image3
PreviewImage(image4)
segs2 = segs
model, clip, vae = CheckpointLoaderSimple(r'XL\turbovisionxlSuperFastXLBasedOnNew_alphaV0101Bakedvae.safetensors')
lora_stack, _ = CRLoRAStack('On', r'xl\LCMTurboMix_LCM_Sampler.safetensors', 1, 1, 'On', r'xl\xl_more_art-full_v1.safetensors', 1, 1, 'On', r'xl\add-detail-xl.safetensors', 1, 1, None)
model, clip, _ = CRApplyLoRAStack(model, clip, lora_stack)
conditioning = CLIPTextEncode('Shot Size - extreme wide shot,( Marrakech market at night time:1.5), Moroccan young beautiful woman, smiling, exotic, (loose hijab:0.1)', clip)
conditioning2 = CLIPTextEncode('(worst quality, low quality, normal quality:2), blurry, depth of field, nsfw', clip)
basic_pipe = ToBasicPipe(model, clip, vae, conditioning, conditioning2)
image5, _, _, _ = DetailerForEachPipe(image3, segs2, 1024, True, 1024, 403808226377311, 10, 3, 'lcm', 'ddim_uniform', 0.1, 50, True, True, basic_pipe, '', 0, 1, None, None, True, 50)
PreviewImage(image5)
PreviewImage(image)
""")
])
def test_workflow(workflow, script):
    with open(Path(__file__).parent / workflow) as f:
        assert transpile.WorkflowToScriptTranspiler(f.read()).to_script() == script