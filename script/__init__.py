import json
from types import SimpleNamespace
import networkx as nx

from . import astutil
from . import passes

class WorkflowToScriptTranspiler:
    def __init__(self, workflow: str):
        workflow = json.loads(workflow, object_hook=lambda d: SimpleNamespace(**d))
        assert workflow.version == 0.4

        G = nx.MultiDiGraph()
        for node in workflow.nodes:
            # TODO: Directly add node?
            G.add_node(node.id, v=node)
        
        links = {}
        for link in workflow.links:
            (id, u, u_slot, v, v_slot, type) = link
            G.add_edge(u, v, key=id, u_slot=u_slot, v_slot=v_slot, type=type)
            links[id] = (u, v, id)
        
        self.G = G
        self.links = links

    def _declare_id(self, id: str) -> str:
        if id not in self.ids:
            self.ids[id] = {}
        return id

    def _assign_id(self, name: str) -> str:
        if name in self.ids:
            i = 2
            while f'{name}{i}' in self.ids:
                i += 1
            name = f'{name}{i}'
        self.ids[name] = {}
        return name

    def _node_to_assign_st(self, node):
        G = self.G
        links = self.links

        v = node['v']
        # print(v.id)

        class_id = self._declare_id(astutil.str_to_class_id(v.type))
        
        # TODO: **Fix order of inputs**
        args = []
        if hasattr(v, 'inputs'):
            v.inputs.sort(key=lambda input: G.edges[links[input.link]]['v_slot'])
            for input in v.inputs:
                (node_u, node_v, link_id) = links[input.link]
                edge = G.edges[node_u, node_v, link_id]

                u = G.nodes[node_u]
                u_slot = edge['u_slot']

                args.append({
                    'exp': u['output_ids'][u_slot],
                    'type': input.type,
                    'move': len(u['v'].outputs[u_slot].links) == 1
                })
        if hasattr(v, 'widgets_values'):
            # https://github.com/comfyanonymous/ComfyUI/blob/2ef459b1d4d627929c84d11e5e0cbe3ded9c9f48/web/extensions/core/widgetInputs.js#L326-L375
            for value in v.widgets_values:
                # `value is str` doesn't work
                if type(value) is str:
                    args.append({'exp': astutil.to_str(value)})
                else:
                    # int, float
                    args.append({'exp': str(value)})

        args_of_any_type = [arg for arg in args if arg.get('type', None) == '*']

        vars = []
        vars_used = False
        if hasattr(v, 'outputs'):
            # Unused outputs have no slot_index.
            # sort() is stable.
            v.outputs.sort(key=lambda output: getattr(output, 'slot_index', 0xFFFFFFFF))
            for output in v.outputs:
                # Outputs used before have slot_index, but no links.
                if hasattr(output, 'slot_index') and len(output.links) > 0:
                    # Variable reuse: If an input is only used by current node, and current node outputs a same type output, then the output should take the input's var name.
                    # e.g. Reroute, CLIPSetLastLayer, TomePatchModel, CRLoadLoRA
                    
                    args_of_same_type = [arg for arg in args if arg.get('type', None) == output.type]
                    if len(args_of_same_type) == 1 and args_of_same_type[0]['move']:
                        id = args_of_same_type[0]['exp']
                    elif len(v.outputs) == 1 and len(args_of_any_type) == 1:
                        # e.g. Reroute
                        id = args_of_any_type[0]['exp']
                    else:
                        id = self._assign_id(astutil.str_to_var_id(
                            getattr(v, 'title', '') + output.name if output.name != '' else output.type
                        ))

                    node.setdefault('output_ids', {})[output.slot_index] = id

                    vars_used = True
                else:
                    id = '_'
                vars.append(id)

        c = ''
        # TODO: Dead code elimination
        if len(vars) > 0 and not vars_used:
            c += '# '
        if len(vars) != 0:
            c += f"{astutil.to_assign_target_list(vars)} = "
        c += f"{class_id}({', '.join(arg['exp'] for arg in args)})\n"
        
        # TODO: PrimitiveNode elimination
        c = passes.reroute_elimination(v, args, vars, c)
        return c
    
    def _topological_generations_ordered_dfs(self):
        G = self.G
        links = self.links

        zero_outdegree = [v for v, d in G.out_degree() if d == 0]

        # Coordinate system:
        # O → X
        # ↓
        # Y
        # The most top-left node has the smallest (x + y).
        zero_outdegree.sort(key=lambda v: sum(G.nodes[v]['v'].pos))

        visited = set()
        def visit(node):
            if node in visited:
                return
            visited.add(node)

            # inputs are sorted by slot_index
            v = G.nodes[node]['v']
            if hasattr(v, 'inputs'):
                for input in v.inputs:
                    (node_u, _node_v, _link_id) = links[input.link]
                    yield from visit(node_u)
            
            yield node
        
        for v in zero_outdegree:
            yield from visit(v)
    
    def to_script(self) -> str:
        # From leaves to roots or roots to leaves?
        # ComfyUI now executes workflows from leaves to roots, but there is a PR to change this to from roots to leaves with topological sort: https://github.com/comfyanonymous/ComfyUI/pull/931
        # To minimize future maintenance cost and suit the mental model better, we choose **from roots to leaves** too.

        # TODO: Allow specifying end nodes

        self.ids = {}
        c = ''
        for node in self._topological_generations_ordered_dfs():
            # TODO: Add line breaks if a node has multiple inputs
            c += self._node_to_assign_st(self.G.nodes[node])
        return c
    
__all__ = [
    'WorkflowToScriptTranspiler',
]