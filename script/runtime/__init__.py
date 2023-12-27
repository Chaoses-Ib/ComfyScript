from __future__ import annotations
import asyncio
import inspect
import threading
import uuid
import aiohttp

from . import factory
from . import node
from . import data

endpoint = 'http://127.0.0.1:8188/'
client_id = str(uuid.uuid4())
daemon_thread = None

async def load(api_endpoint: str = endpoint, vars: dict = None, daemon: bool = True):
    global endpoint, daemon_thread

    endpoint = api_endpoint

    async with aiohttp.ClientSession() as session:
        # http://127.0.0.1:8188/object_info
        async with session.get(f'{endpoint}object_info') as response:
            assert response.status == 200
            nodes = await response.json()

    print(f'Nodes: {len(nodes)}')

    fact = factory.RuntimeFactory()
    for node_info in nodes.values():
        fact.add_node(node_info)
    
    # Reimport
    globals().update(fact.vars())
    __all__.extend(fact.vars().keys())
    if vars is None:
        # TODO: Or __builtins__?
        vars = inspect.currentframe().f_back.f_globals
        vars.update(fact.vars())

    # __init__.pyi
    with open(__file__ + 'i', 'w') as f:
        f.write(fact.type_stubs())
    
    if daemon and daemon_thread is None:
        daemon_thread = threading.Thread(target=asyncio.run, args=(watch(),), daemon=True)
        daemon_thread.start()
        # TODO: Kill daemon thread if daemon turns to False

async def watch():
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f'{endpoint}ws?clientId={client_id}') as ws:
                queue_remaining = 0
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        msg = msg.json()
                        # print(msg)
                        if msg['type'] == 'status':
                            data = msg['data']
                            new_queue_remaining = data['status']['exec_info']['queue_remaining']
                            if queue_remaining != new_queue_remaining:
                                queue_remaining = new_queue_remaining
                                print(f'Queue remaining: {queue_remaining}')
                        elif msg['type'] == 'progress':
                            data = msg['data']
                            print_progress(data['value'], data['max'])
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
        await asyncio.sleep(1)
    '''
    {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 0}}, 'sid': 'adc24049-b013-4a58-956b-edbc591dc6e2'}}
    {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 1}}}}
    {'type': 'execution_start', 'data': {'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'execution_cached', 'data': {'nodes': ['9', '15', '5', '8', '12', '13', '16', '6', '1', '14', '0', '2', '20', '11', '17', '7', '10', '19', '3', '4', '18'], 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'executing', 'data': {'node': '21', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'progress', 'data': {'value': 1, 'max': 15}}
    ...
    {'type': 'progress', 'data': {'value': 15, 'max': 15}}
    {'type': 'executing', 'data': {'node': '22', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'executing', 'data': {'node': '23', 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'executed', 'data': {'node': '23', 'output': {'images': [{'filename': 'C_00001_.png', 'subfolder': '', 'type': 'output'}]}, 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 0}}}}
    {'type': 'executing', 'data': {'node': None, 'prompt_id': '3328f0c8-9368-4070-90e7-087e854fe315'}}
    '''

async def queue_prompt(prompt: dict | data.NodeOutput | list[data.NodeOutput], source = None):
    global endpoint, client_id

    if source is None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
    
    if isinstance(prompt, data.NodeOutput):
        prompt = prompt.get_prompt()
    elif isinstance(prompt, list):
        prompt = data.get_outputs_prompt(prompt)
    # print(prompt)

    async with aiohttp.ClientSession() as session:
        async with session.post(f'{endpoint}prompt', json={
            'prompt': prompt,
            'extra_data': {
                'extra_pnginfo': {
                    'ComfyScriptSource': source
                }
            },
            'client_id': client_id,
        }) as response:
            assert response.status == 200
            return await response.json()

def print_progress(iteration, total, prefix = '', suffix = '', decimals = 0, length = 50, fill = '█', printEnd = '\r'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    
    From https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    """
    percent = ("{0:3." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix}{percent}%|{bar}| {iteration}/{total}{suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

async def wait_prompt(prompt_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f'{endpoint}ws?clientId={client_id}') as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    msg = msg.json()
                    # print(msg)
                    if msg['type'] == 'status':
                        data = msg['data']
                        if data['status']['exec_info']['queue_remaining'] == 0:
                            break
                    elif msg['type'] == 'executing':
                        data = msg['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break
                    elif msg['type'] == 'progress':
                        data = msg['data']
                        print_progress(data['value'], data['max'])
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break

async def exec_prompt(source = None):
    '''
    Queue a prompt and wait for it to finish.
    '''
    if source is None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
    
    response = await queue_prompt(source)
    print(response)
    await wait_prompt(response['prompt_id'])

async def interrupt_prompt():
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{endpoint}interrupt', json={
            'client_id': client_id,
        }) as response:
            assert response.status == 200

async def clear_queue():
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{endpoint}queue', json={
            'clear': True,
            'client_id': client_id,
        }) as response:
            assert response.status == 200

async def interrupt_all():
    await clear_queue()
    await interrupt_prompt()

class ComfyScript:
    def __init__(self, wait: bool = False):
        '''
        - `wait`: Wait for the prompt to finish before exiting the context manager.
        '''
        self.outputs = []
        self.wait_prompt = wait
    
    def __iadd__(self, other: data.NodeOutput | list[data.NodeOutput]):
        if isinstance(other, list):
            self.outputs.extend(other)
        else:
            self.outputs.append(other)
        return self

    async def __aenter__(self) -> ComfyScript:
        self.outputs = []
        node.Node.set_output_hook(self.__iadd__)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])

        node.Node.clear_output_hook()
        
        response = await queue_prompt(self.outputs, source)
        # TODO: Fix multi-thread print
        # print(response)
        if self.wait_prompt:
            await wait_prompt(response['prompt_id'])

__all__ = [
    'load',
    'queue_prompt',
    'wait_prompt',
    'exec_prompt',
    'interrupt_prompt',
    'clear_queue',
    'interrupt_all',
    'ComfyScript'
]