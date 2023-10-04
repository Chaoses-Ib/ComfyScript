import re

# TODO: Switch nodes
# e.g. TomePatchModel, CRLoadLoRA, CLIPSetLastLayer
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

__all__ = [
    'reroute_elimination',
    'primitive_node_elimination',
]