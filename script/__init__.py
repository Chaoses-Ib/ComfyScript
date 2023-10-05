from typing import Union
import json
from types import SimpleNamespace
import networkx as nx

from . import astutil
from . import passes

import nodes

class WorkflowToScriptTranspiler:
    def __init__(self, workflow: Union[str, dict]):
        if type(workflow) is not str:
            workflow = json.dumps(workflow)
        workflow = json.loads(workflow, object_hook=lambda d: SimpleNamespace(**d))
        # serializedLGraph: https://github.com/comfyanonymous/ComfyUI/blob/2ef459b1d4d627929c84d11e5e0cbe3ded9c9f48/web/types/litegraph.d.ts#L332
        assert workflow.version == 0.4

        G = nx.MultiDiGraph()
        for node in workflow.nodes:
            # TODO: Directly add node?
            G.add_node(node.id, v=node)
        
        links = {}
        for link in workflow.links:
            (id, u, u_slot, v, v_slot, value_type) = link
            G.add_edge(u, v, key=id, u_slot=u_slot, v_slot=v_slot, type=value_type)
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

    def _get_input_types(self, node_type: str) -> dict:
        # registerNodeType: Reroute, PrimitiveNode, Note
        if node_type == 'Reroute':
            return {
                'required': {
                    '': ('*',)
                }
            }
        elif node_type == 'PrimitiveNode':
            return {
                'required': {
                    'value': ('*',)
                }
            }
        elif node_type == 'Note':
            return {
                'required': {
                    '': ('STRING',)
                }
            }
        else:
            return nodes.NODE_CLASS_MAPPINGS[node_type].INPUT_TYPES()
    
    def _get_widget_value_names(self, node_type: str) -> list[str]:
        widget_value_names = []
        input_types = self._get_input_types(node_type)
        for group in 'required', 'optional':
            group: dict = input_types.get(group)
            if group is None:
                continue
            for name, config in group.items():
                # str | list[str]
                # https://github.com/comfyanonymous/ComfyUI/blob/4103f7fad5be7e22ed61843166b72b7c41671d75/web/scripts/widgets.js
                if type(config[0]) != str or config[0] in ('INT', 'FLOAT', 'STRING', 'BOOLEAN'):
                    widget_value_names.append(name)
                    if name in ('seed', 'noise_seed') and config[0] == 'INT':
                        # Naturally filtered out by _keyword_args_to_positional()
                        widget_value_names.append('control_after_generate')
                elif node_type == 'PrimitiveNode':
                    widget_value_names.append(name)
                    # Only PrimitiveNode with INT output has control_after_generate, but we don't know the output type here.
                    widget_value_names.append('control_after_generate')

                # https://github.com/comfyanonymous/ComfyUI/blob/2ef459b1d4d627929c84d11e5e0cbe3ded9c9f48/web/extensions/core/uploadImage.js
                if len(config) > 1 and type(config[1]) == dict and config[1].get('image_upload') == True:
                    # Naturally filtered out by _keyword_args_to_positional()
                    widget_value_names.append('upload')

        # print(node_type, input_types, widget_value_names)
        return widget_value_names
    
    def _widget_values_to_dict(self, node_type: str, widget_values: list) -> dict:
        # https://github.com/comfyanonymous/ComfyUI/blob/4103f7fad5be7e22ed61843166b72b7c41671d75/web/scripts/widgets.js
        widget_value_names = self._get_widget_value_names(node_type)
        return {name: value for name, value in zip(widget_value_names, widget_values)}

    def _keyword_args_to_positional(self, node_type: str, kwargs: dict) -> list:
        args = []
        # CPython 3.6+: Dictionaries preserve insertion order, meaning that keys will be produced in the same order they were added sequentially over the dictionary. (validated in setup_script())
        input_types = self._get_input_types(node_type)
        # TODO: Keep optional group as kwargs?
        # TODO: Keep as kwargs if there are values of the same type?
        for group in 'required', 'optional':
            group: dict = input_types.get(group)
            if group is None:
                continue
            for name in group:
                if value := kwargs.get(name):
                    args.append(value)
        return args

    def _node_to_assign_st(self, node):
        G = self.G
        links = self.links

        v = node['v']
        # print(v.id)

        class_id = self._declare_id(astutil.str_to_class_id(v.type))
        
        args = {}
        # inputs can override widgets_values
        if hasattr(v, 'widgets_values'):
            widget_values = self._widget_values_to_dict(v.type, v.widgets_values)
            for name, value in widget_values.items():
                # `value is str` doesn't work
                # TODO: BOOLEAN, not used in any node?
                if type(value) is str:
                    args[name] = {'exp': astutil.to_str(value), 'value': value}
                else:
                    # int, float
                    args[name] = {'exp': str(value), 'value': value}
        if hasattr(v, 'inputs'):
            # If a node's output is not used, it is allowed to have dangling inputs, in which case the link is None.
            # TODO: This breaks the order and arg positions.
            v.inputs.sort(key=lambda input: G.edges[links[input.link]]['v_slot'] if input.link else 0xFFFFFFFF)
            for input in v.inputs:
                if input.link is None:
                    continue

                (node_u, node_v, link_id) = links[input.link]
                edge = G.edges[node_u, node_v, link_id]

                u = G.nodes[node_u]
                u_slot = edge['u_slot']
                output_ids = u.get('output_ids')
                if output_ids is None:
                    # Multiplexer nodes' inputs are filtered
                    args[input.name] = { 'exp': '_', 'type': input.type }
                else:
                    output_links = u['v'].outputs[u_slot].links

                    args[input.name] = {
                        'exp': output_ids[u_slot],
                        'type': input.type,
                        'move': output_links is None or len(output_links) == 1
                    }
        args_dict = args
        args = self._keyword_args_to_positional(v.type, args_dict)

        args_of_any_type = [arg for arg in args if arg.get('type', None) == '*']

        vars = []
        vars_used = False
        if hasattr(v, 'outputs'):
            # Unused outputs have no slot_index.
            # sort() is stable.
            v.outputs.sort(key=lambda output: getattr(output, 'slot_index', 0xFFFFFFFF))
            for output in v.outputs:
                # Outputs used before have slot_index, but no links.
                if output.links is not None and len(output.links) > 0:
                    # Used outputs may also have no slot_index.
                    # TODO: How is the slot determined? Only valid for single output nodes?
                    if hasattr(output, 'slot_index'):
                        slot_index = output.slot_index
                    elif len(v.outputs) == 1:
                        slot_index = 0
                    else:
                        print(f"Ib Custom Nodes: Failed to determine slot_index of output {output.name} of node {v.id}.")
                        continue

                    # Variable reuse: If an input is only used by current node, and current node outputs a same type output, then the output should take the input's var name.
                    # e.g. Reroute, CLIPSetLastLayer, TomePatchModel, CRLoadLoRA

                    # TODO: Name resolution
                    # 1. The name of the input that uses this output
                    # 2. The name reused from the input that has the same type
                    # 3. The type of the output
                    # How to make this transitive?
                    
                    args_of_same_type = [arg for arg in args if arg.get('type') == output.type and arg['exp'] != '_']
                    if len(args_of_same_type) == 1 and args_of_same_type[0]['move']:
                        id = args_of_same_type[0]['exp']
                    elif len(v.outputs) == 1 and len(args_of_any_type) == 1:
                        # e.g. Reroute
                        id = args_of_any_type[0]['exp']
                    else:
                        id = self._assign_id(astutil.str_to_var_id(
                            getattr(v, 'title', '') + output.name if output.name != '' else output.type
                        ))

                    node.setdefault('output_ids', {})[slot_index] = id

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
        
        ctx = passes.AssignContext(
            v=v,
            args_dict=args_dict,
            args=args,
            vars=vars,
            c=c,
        )
        for pass_ in passes.ASSIGN_PASSES:
            pass_(ctx)
            if ctx.c == '':
                break
        return ctx.c
    
    def _topological_generations_ordered_dfs(self, end_nodes: Union[list[int], None] = None):
        G = self.G
        links = self.links

        if end_nodes is None:
            end_nodes = [v for v, d in G.out_degree() if d == 0]

            # Coordinate system:
            # O → X
            # ↓
            # Y
            # The most top-left node has the smallest (x + y).
            end_nodes.sort(key=lambda v: sum(G.nodes[v]['v'].pos))

        visited = set()
        def visit(node):
            if node in visited:
                return
            visited.add(node)

            # inputs are sorted by slot_index
            v = G.nodes[node]['v']
            if hasattr(v, 'inputs'):
                inputs = v.inputs
                if hasattr(v, 'widgets_values'):
                    inputs = passes.multiplexer_node_input_filter(v, self._widget_values_to_dict(v.type, v.widgets_values))
                for input in inputs:
                    # If a node's output is not used, it is allowed to have dangling inputs, in which case the link is None.
                    if input.link is not None:
                        (node_u, _node_v, _link_id) = links[input.link]
                        yield from visit(node_u)
            
            yield node
        
        for v in end_nodes:
            yield from visit(v)
    
    def to_script(self, end_nodes = None) -> str:
        # From leaves to roots or roots to leaves?
        # ComfyUI now executes workflows from leaves to roots, but there is a PR to change this to from roots to leaves with topological sort: https://github.com/comfyanonymous/ComfyUI/pull/931
        # To minimize future maintenance cost and suit the mental model better, we choose **from roots to leaves** too.

        self.ids = {}
        c = ''
        for node in self._topological_generations_ordered_dfs(end_nodes):
            # TODO: Add line breaks if a node has multiple inputs
            c += self._node_to_assign_st(self.G.nodes[node])
        return c
    
__all__ = [
    'WorkflowToScriptTranspiler',
]