import re

# TODO: Switch nodes
# How to prevent var rename?
# e.g. ModelMergeSimple, CRModelInputSwitch

def reroute_elimination(v, args, vars, c):
    if v.type != 'Reroute':
        return c
    assert re.fullmatch(r'(?:# )?(?:_ = Reroute\(\S+\)|(\S+) = Reroute\(\1\))\s*', c), c
    return ''

def primitive_node_elimination(v, args, vars, c):
    # TODO: Embed primitive into args if only used by one node?
    if v.type != 'PrimitiveNode':
        return c
    new_c = re.sub(r' = PrimitiveNode\(([\S\s]+)\)(\s*)$', r' = \1\2', c)
    assert new_c != c, c
    return new_c

SWITCH_NODES = {
    'CLIPSetLastLayer': [{'stop_at_clip_layer': -1}],
    'CR Apply ControlNet': [{'switch': 'Off'}, {'strength': 0}],
    'CR Load LoRA': [{'switch': 'Off'}, {'strength_model': 0, 'strength_clip': 0}],
    'TomePatchModel': [{'ratio': 0}],
}
def switch_node_elimination(v, args_dict: dict, args, vars, c):
    switch_inputs = SWITCH_NODES.get(v.type)
    if switch_inputs is None:
        return c
    # print('switch_node_elimination:', v.type, args_dict)
    for switch_input in switch_inputs:
        for k, v in switch_input.items():
            # Only widget values are considered
            if args_dict[k].get('value') == v:
                return ''
    return c

__all__ = [
    'reroute_elimination',
    'primitive_node_elimination',
    'switch_node_elimination',
]