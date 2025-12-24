'''hatch env run -e test pytest tests/transpile -- -vv'''
from pathlib import Path

import pytest

from comfy_script.transpile import *

@pytest.mark.parametrize('workflow, script', [
    ('default.json',
r"""model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
conditioning = CLIPTextEncode('beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip)
conditioning2 = CLIPTextEncode('text, watermark', clip)
latent = EmptyLatentImage(512, 512, 1)
latent = KSampler(model, 156680208700286, 20, 8, 'euler', 'normal', conditioning, conditioning2, latent, 1)
image = VAEDecode(latent, vae)
SaveImage(image, 'ComfyUI')
"""),
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
"""),
    ('rgthree-comfy.json',
r"""model, clip, vae = CheckpointLoaderSimple('v1-5-pruned-emaonly.ckpt')
# _ = CLIPTextEncode('n', clip)
conditioning = CLIPTextEncode('p', clip)
latent = EmptyLatentImage(512, 512, 1)
latent = KSampler(model, 0, 20, 8, 'euler', 'normal', conditioning, conditioning, latent, 1)
image = VAEDecode(latent, vae)
SaveImage(image, 'ComfyUI')
"""),
    ('SplitSigmasDenoise.api.json',
r"""noise = DisableNoise()
width, height, _, _, _, empty_latent, _ = CRAspectRatio(512, 768, 'custom', 'Off', 1, 1, 1)
model = UNETLoader('flux1-dev.safetensors', 'fp8_e4m3fn')
model = LoraLoaderModelOnly(model, 'a.safetensors', 0.7000000000000001)
model = LoraLoaderModelOnly(model, 'b.safetensors', 0.7000000000000001)
model = ModelSamplingFlux(model, 1.1500000000000001, 0.5, width, height)
clip = DualCLIPLoader('t5.safetensors', 'clip_l.safetensors', 'flux')
conditioning = CLIPTextEncode('prompt text', clip)
conditioning = FluxGuidance(conditioning, 3.5)
guider = BasicGuider(model, conditioning)
sampler = KSamplerSelect('deis')
sigmas = BasicScheduler(model, 'beta', 30, 1)
sigmas, low_sigmas = SplitSigmasDenoise(sigmas, 0.4)
noise2 = RandomNoise(149684926930931)
empty_latent, _ = SamplerCustomAdvanced(noise2, guider, sampler, sigmas, empty_latent)
empty_latent = InjectLatentNoise(empty_latent, 49328841076664, 0.3, 'true', None)
empty_latent, _ = SamplerCustomAdvanced(noise, guider, sampler, low_sigmas, empty_latent)
vae = VAELoader('ae.safetensors')
image = VAEDecode(empty_latent, vae)
SaveImage(image, 'ComfyUI')
""")
])
def test_workflow(workflow, script):
    format = FormatOptions(args=ArgsFormat.Pos)
    with open(Path(__file__).parent / workflow) as f:
        assert WorkflowToScriptTranspiler(f.read()).to_script(format=format) == script

@pytest.mark.parametrize('workflow, script', [
    ('default.json',
r"""model, clip, vae = CheckpointLoaderSimple(ckpt_name='v1-5-pruned-emaonly.ckpt')
conditioning = CLIPTextEncode(text='beautiful scenery nature glass bottle landscape, , purple galaxy bottle,', clip=clip)
conditioning2 = CLIPTextEncode(text='text, watermark', clip=clip)
latent = EmptyLatentImage(width=512, height=512, batch_size=1)
latent = KSampler(model=model, seed=156680208700286, steps=20, cfg=8, sampler_name='euler', scheduler='normal', positive=conditioning, negative=conditioning2, latent_image=latent, denoise=1)
image = VAEDecode(samples=latent, vae=vae)
SaveImage(images=image, filename_prefix='ComfyUI')
"""),
    ('bypass.json',
r"""image, _ = LoadImage(image='ComfyUI_temp_rcuxh_00001_.png')
image2 = ImageScaleToSide(image=image, side_length=1024, side='Longest', upscale_method='nearest-exact', crop='disabled')
PreviewImage(images=image2)
image3, _ = CRUpscaleImage(image=image2, upscale_model='8x_NMKD-Superscale_150000_G.pth', mode='rescale', rescale_factor=2, resize_width=1024, resampling_method='lanczos', supersample='true', rounding_modulus=8)
segs = ImpactMakeTileSEGS(image=image3, bbox_size=600, crop_factor=1.5, min_overlap=200, max_overlap=100, sub_batch_size_for_dilation=0, filter_segs_dilation='Reuse fast', mask_irregularity=None, irregular_mask_mode=None)
# _ = SEGSPreview(segs=segs, alpha_mode=True, falloff=0.1, image=image3)
image4 = image3
PreviewImage(images=image4)
segs2 = segs
model, clip, vae = CheckpointLoaderSimple(ckpt_name=r'XL\turbovisionxlSuperFastXLBasedOnNew_alphaV0101Bakedvae.safetensors')
lora_stack, _ = CRLoRAStack(switch_1='On', lora_name_1=r'xl\LCMTurboMix_LCM_Sampler.safetensors', model_weight_1=1, clip_weight_1=1, switch_2='On', lora_name_2=r'xl\xl_more_art-full_v1.safetensors', model_weight_2=1, clip_weight_2=1, switch_3='On', lora_name_3=r'xl\add-detail-xl.safetensors', model_weight_3=1, clip_weight_3=1, lora_stack=None)
model, clip, _ = CRApplyLoRAStack(model=model, clip=clip, lora_stack=lora_stack)
conditioning = CLIPTextEncode(text='Shot Size - extreme wide shot,( Marrakech market at night time:1.5), Moroccan young beautiful woman, smiling, exotic, (loose hijab:0.1)', clip=clip)
conditioning2 = CLIPTextEncode(text='(worst quality, low quality, normal quality:2), blurry, depth of field, nsfw', clip=clip)
basic_pipe = ToBasicPipe(model=model, clip=clip, vae=vae, positive=conditioning, negative=conditioning2)
image5, _, _, _ = DetailerForEachPipe(image=image3, segs=segs2, guide_size=1024, guide_size_for=True, max_size=1024, seed=403808226377311, steps=10, cfg=3, sampler_name='lcm', scheduler='ddim_uniform', denoise=0.1, feather=50, noise_mask=True, force_inpaint=True, basic_pipe=basic_pipe, wildcard='', cycle=0, inpaint_model=1, noise_mask_feather=None, scheduler_func_opt=None, detailer_hook=True, refiner_ratio=50)
PreviewImage(images=image5)
PreviewImage(images=image)
"""),
    ('rgthree-comfy.json',
r"""model, clip, vae = CheckpointLoaderSimple(ckpt_name='v1-5-pruned-emaonly.ckpt')
# _ = CLIPTextEncode(text='n', clip=clip)
conditioning = CLIPTextEncode(text='p', clip=clip)
latent = EmptyLatentImage(width=512, height=512, batch_size=1)
latent = KSampler(model=model, seed=0, steps=20, cfg=8, sampler_name='euler', scheduler='normal', positive=conditioning, negative=conditioning, latent_image=latent, denoise=1)
image = VAEDecode(samples=latent, vae=vae)
SaveImage(images=image, filename_prefix='ComfyUI')
"""),
    ('SplitSigmasDenoise.api.json',
r"""noise = DisableNoise()
width, height, _, _, _, empty_latent, _ = CRAspectRatio(width=512, height=768, aspect_ratio='custom', swap_dimensions='Off', upscale_factor=1, prescale_factor=1, batch_size=1)
model = UNETLoader(unet_name='flux1-dev.safetensors', weight_dtype='fp8_e4m3fn')
model = LoraLoaderModelOnly(model=model, lora_name='a.safetensors', strength_model=0.7000000000000001)
model = LoraLoaderModelOnly(model=model, lora_name='b.safetensors', strength_model=0.7000000000000001)
model = ModelSamplingFlux(model=model, max_shift=1.1500000000000001, base_shift=0.5, width=width, height=height)
clip = DualCLIPLoader(clip_name1='t5.safetensors', clip_name2='clip_l.safetensors', type='flux')
conditioning = CLIPTextEncode(text='prompt text', clip=clip)
conditioning = FluxGuidance(conditioning=conditioning, guidance=3.5)
guider = BasicGuider(model=model, conditioning=conditioning)
sampler = KSamplerSelect(sampler_name='deis')
sigmas = BasicScheduler(model=model, scheduler='beta', steps=30, denoise=1)
sigmas, low_sigmas = SplitSigmasDenoise(sigmas=sigmas, denoise=0.4)
noise2 = RandomNoise(noise_seed=149684926930931)
empty_latent, _ = SamplerCustomAdvanced(noise=noise2, guider=guider, sampler=sampler, sigmas=sigmas, latent_image=empty_latent)
empty_latent = InjectLatentNoise(latent=empty_latent, noise_seed=49328841076664, noise_strength=0.3, normalize='true')
empty_latent, _ = SamplerCustomAdvanced(noise=noise, guider=guider, sampler=sampler, sigmas=low_sigmas, latent_image=empty_latent)
vae = VAELoader(vae_name='ae.safetensors')
image = VAEDecode(samples=empty_latent, vae=vae)
SaveImage(images=image, filename_prefix='ComfyUI')
""")
])
def test_workflow_with_keyword_args(workflow, script):
    format = FormatOptions(args=ArgsFormat.Kwd)
    with open(Path(__file__).parent / workflow) as f:
        assert WorkflowToScriptTranspiler(f.read()).to_script(format=format) == script