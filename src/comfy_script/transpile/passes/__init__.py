from dataclasses import dataclass
import re

@dataclass
class AssignContext:
    node: dict
    v: dict
    args_dict: dict[str]
    args: list
    vars: list
    c: str

REROUTE_NODES = ('Reroute', 'Reroute (rgthree)')
def reroute_elimination(ctx: AssignContext):
    if ctx.v.type not in REROUTE_NODES:
        return
    assert re.fullmatch(r'(?:# )?(?:_ = [A-Za-z_0-9]+\(\S+\)|(\S+) = [A-Za-z_0-9]+\(\1\))\s*', ctx.c), ctx.c
    ctx.c = ''

def bypass_move_elimination(ctx: AssignContext):
    if not re.fullmatch(r'(?:# )?(.+?) = \1\s*', ctx.c):
        return
    ctx.c = ''

def primitive_node_elimination(ctx: AssignContext):
    # TODO: Embed primitive into args if only used by one node?
    if ctx.v.type != 'PrimitiveNode':
        return
    new_c = re.sub(r' = PrimitiveNode\(([\S\s]+)\)(\s*)$', r' = \1\2', ctx.c)
    assert new_c != ctx.c, ctx.c
    ctx.c = new_c

JS_NODES = [
    *REROUTE_NODES,
    'PrimitiveNode',
    'Note'
]

SWITCH_NODES = {
    'HypernetworkLoader': [{'strength': 0}],
    'CLIPSetLastLayer': [{'stop_at_clip_layer': -1}],
    'ConditioningSetArea': [{'strength': 0}],
    'ConditioningSetAreaPercentage': [{'strength': 0}],
    'ConditioningSetMask': [{'strength': 0}],
    'ControlNetApply': [{'strength': 0}],
    'ControlNetApplyAdvanced': [{'strength': 0}],
    'CR Apply ControlNet': [{'switch': 'Off'}, {'strength': 0}],
    'CR Color Tint': [{'strength': 0}],
    'CR Load LoRA': [{'switch': 'Off'}, {'strength_model': 0, 'strength_clip': 0}],
    'LatentMultiply': [{'multiplier': 1}],
    'TomePatchModel': [{'ratio': 0}],
    'unCLIPConditioning': [{'strength': 0}],
}
def switch_node_elimination(ctx: AssignContext):
    switch_inputs = SWITCH_NODES.get(ctx.v.type)
    if switch_inputs is None:
        return
    # print('switch_node_elimination:', ctx.v.type, ctx.args_dict)
    for switch_input in switch_inputs:
        for k, v in switch_input.items():
            # Only widget values are considered
            if ctx.args_dict[k].get('value') == v:
                ctx.c = ''
                return
    return

MULTIPLEXER_NODES = {
    'CLIPMergeSimple': ('CLIP', {
        'clip1': {'ratio': 1},
        'clip2': {'ratio': 0},
    }),
    'ConditioningAverage': ('CONDITIONING', {
        'conditioning_to': {'conditioning_to_strength': 1},
        'conditioning_from': {'conditioning_to_strength': 0},
    }),
    'CR Clip Input Switch': ('CLIP', {
        'clip1': {'Input': 1},
        'clip2': {'Input': 2},
    }),
    'CR Conditioning Input Switch': ('CONDITIONING', {
        'conditioning1': {'Input': 1},
        'conditioning2': {'Input': 2},
    }),
    'CR ControlNet Input Switch': ('CONTROL_NET', {
        'control_net1': {'Input': 1},
        'control_net2': {'Input': 2},
    }),
    'CR Image Input Switch': ('IMAGE', {
        'image1': {'Input': 1},
        'image2': {'Input': 2},
    }),
    'CR Image Input Switch (4 way)': ('IMAGE', {
        'image1': {'Input': 1},
        'image2': {'Input': 2},
        'image3': {'Input': 3},
        'image4': {'Input': 4},
    }),
    'CR Latent Input Switch': ('LATENT', {
        'latent1': {'Input': 1},
        'latent2': {'Input': 2},
    }),
    'CR Model Input Switch': ('MODEL', {
        'model1': {'Input': 1},
        'model2': {'Input': 2},
    }),
    'CR Pipe Switch': ('PIPE_LINE', {
        'pipe1': {'Input': 1},
        'pipe2': {'Input': 2},
    }),
    'ImageBlend': ('IMAGE', {
        'image1': {'blend_mode': 'normal', 'blend_factor': 0},
        'image2': {'blend_mode': 'normal', 'blend_factor': 1},
    }),
    'LatentBlend': ('LATENT', {
        # `blend_mode` was removed in https://github.com/comfyanonymous/ComfyUI/commit/fa962e86c1cdc3bb9dd57ac028fba0e577346983
        'samples1': {'blend_mode': 'normal', 'blend_factor': 1},
        'samples2': {'blend_mode': 'normal', 'blend_factor': 0},
    }),
    'ModelMergeBlocks': ('MODEL', {
        'model1': {'input': 1, 'middle': 1, 'out': 1},
        'model2': {'input': 0, 'middle': 0, 'out': 0},
    }),
    'ModelMergeSimple': ('MODEL', {
        'model1': {'ratio': 1},
        'model2': {'ratio': 0},
    }),
}
def multiplexer_node_input_filter(node, widget_values: dict):
    v = node['v']
    multiplexer_inputs = MULTIPLEXER_NODES.get(v.type)
    if multiplexer_inputs is None:
        return v.inputs
    for input_name, values in multiplexer_inputs[1].items():
        for k, value in values.items():
            # Input may be removed. If so, its value should not matter and be ignored.
            if k in widget_values and widget_values[k] != value:
                break
        else:
            node['multiplexer_node_elimination'] = True
            return filter(lambda input: input.type != multiplexer_inputs[0] or input.name == input_name, v.inputs)
    return v.inputs
def multiplexer_node_elimination(ctx: AssignContext):
    if ctx.node.get('multiplexer_node_elimination') is not True:
        return
    assert ctx.v.type in MULTIPLEXER_NODES
    assert '_' in ctx.c, ctx.c
    ctx.c = ''

ASSIGN_PASSES = (
    reroute_elimination,
    bypass_move_elimination,
    primitive_node_elimination,
    switch_node_elimination,
    multiplexer_node_elimination,
)

__all__ = [
    'AssignContext'
    'ASSIGN_PASSES',
    'multiplexer_node_input_filter',
]