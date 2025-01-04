def prompt_to_workflow(prompt: dict, nodes_info: dict) -> dict:
    nodes = {}
    for id, prompt_node in prompt.items():
        node_type = prompt_node['class_type']
        info = nodes_info[node_type]
        
        info_flatten_inputs = {}
        for group in 'required', 'optional':
            if group := info['input'].get(group):
                info_flatten_inputs.update(group)

        inputs = []
        widgets_values = {}
        for name, value in prompt_node['inputs'].items():
            if isinstance(value, list):
                if name in info_flatten_inputs:
                    value_type = info_flatten_inputs[name][0]
                    inputs.append({
                        'name': name,
                        'type': value_type,
                        # Intermediate
                        'link': value,
                    })
                else:
                    # Ignore hidden inputs
                    # In real mode they are probably ill-formed
                    pass
            else:
                # TODO: https://github.com/comfyanonymous/ComfyUI/issues/2275
                widgets_values[name] = value

        outputs = []
        for i in range(len(info['output'])):
            outputs.append({
                'name': info['output_name'][i],
                'type': info['output'][i],
                # Intermediate
                'links': []
            })

        nodes[id] = {
            'id': id,
            'type': node_type,
            'pos': [len(nodes) * 150, 0],
            'size': {'0': 100, '1': 100},
            'flags': {},
            'order': len(nodes),
            'mode': 0,
            'inputs': inputs,
            'outputs': outputs,
            'properties': {},
            'widgets_values': widgets_values
        }

    links = []
    for id, prompt_node in prompt.items():
        node = nodes[id]
        for i, input in enumerate(node['inputs']):
            link = input.get('link')
            if link is None:
                continue

            link_id = len(links)
            u = link[0]
            u_slot = link[1]
            v = id
            v_slot = i
            value_type = input['type']
            links.append([link_id, u, u_slot, v, v_slot, value_type])

            input['link'] = link_id
            nodes[u]['outputs'][u_slot]['links'].append(link_id)

    return {
        # 'last_node_id': nodes.values()[-1]['id'],
        'last_link_id': len(links),
        'nodes': list(nodes.values()),
        'links': links,
        'groups': [],
        'config': {},
        'extra': {},
        'version': 0.4
    }

__all__ = ['prompt_to_workflow']