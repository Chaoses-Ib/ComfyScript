from __future__ import annotations
import inspect
import json
import threading
import uuid

import asyncio
import nest_asyncio
import aiohttp

from . import nodes
from . import data

nest_asyncio.apply()

_endpoint = 'http://127.0.0.1:8188/'
_client_id = str(uuid.uuid4())
_save_script_source = True
_daemon_thread = None

async def _response_to_str(response: aiohttp.ClientResponse) -> str:
    try:
        msg = json.dumps(await response.json(), indent=2)
    except Exception as e:
        msg = str(e)
    return f'{response}{msg}'

def load(api_endpoint: str = _endpoint, vars: dict | None = None, daemon: bool = True, save_script_source: bool = True):
    asyncio.run(_load(api_endpoint, vars, daemon, save_script_source))
async def _load(api_endpoint: str = _endpoint, vars: dict | None = None, daemon: bool = True, save_script_source: bool = True):
    global _endpoint, _save_script_source, _daemon_thread

    _endpoint = api_endpoint
    _save_script_source = save_script_source

    async with aiohttp.ClientSession() as session:
        # http://127.0.0.1:8188/object_info
        async with session.get(f'{_endpoint}object_info') as response:
            if response.status == 200:
                nodes_info = await response.json()
            else:
                raise Exception(f'ComfyScript: Failed to load nodes: {await _response_to_str(response)}')

    print(f'Nodes: {len(nodes_info)}')

    nodes.load(nodes_info, vars)
    
    if daemon and _daemon_thread is None:
        _daemon_thread = threading.Thread(target=asyncio.run, args=(_watch(),), daemon=True)
        _daemon_thread.start()
        # TODO: Kill daemon thread if daemon turns to False

async def _watch():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f'{_endpoint}ws?clientId={_client_id}') as ws:
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
                                _print_progress(data['value'], data['max'])
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
        except Exception as e:
            print(f'ComfyScript: Failed to watch, will retry in 5 seconds: {e}')
        await asyncio.sleep(5)
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

def get_prompt(prompt: dict | data.NodeOutput | list[data.NodeOutput]) -> dict:
    if isinstance(prompt, data.NodeOutput):
        prompt = prompt.get_prompt()
    elif isinstance(prompt, list):
        prompt = data.get_outputs_prompt(prompt)
    return prompt

def queue(prompt: dict | data.NodeOutput | list[data.NodeOutput], source = None):
    if source is None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
    return asyncio.run(_queue(prompt, source))
async def _queue(prompt: dict | data.NodeOutput | list[data.NodeOutput], source = None):
    global _endpoint, _client_id
    
    prompt = get_prompt(prompt)
    # print(prompt)

    async with aiohttp.ClientSession() as session:
        extra_data = {}
        if _save_script_source:
            extra_data = {
                'extra_pnginfo': {
                    'ComfyScriptSource': source
                }
            }
        async with session.post(f'{_endpoint}prompt', json={
            'prompt': prompt,
            'extra_data': extra_data,
            'client_id': _client_id,
        }) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f'ComfyScript: Failed to queue prompt: {response}{await _response_to_str(response)}')

def _print_progress(iteration, total, prefix = '', suffix = '', decimals = 0, length = 50, fill = '█', printEnd = '\r'):
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

def wait(prompt_id: str):
    return asyncio.run(_wait(prompt_id))
async def _wait(prompt_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f'{_endpoint}ws?clientId={_client_id}') as ws:
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
                        _print_progress(data['value'], data['max'])
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break

def queue_wait(prompt: dict | data.NodeOutput | list[data.NodeOutput], source = None):
    '''
    Queue a prompt and wait for it to finish.
    '''
    if source is None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
    return asyncio.run(_queue_wait(prompt, source))
async def _queue_wait(prompt: dict | data.NodeOutput | list[data.NodeOutput], source = None):
    response = await _queue(prompt, source)
    print(response)
    await _wait(response['prompt_id'])

def interrupt_current():
    return asyncio.run(_interrupt_current())
async def _interrupt_current():
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{_endpoint}interrupt', json={
            'client_id': _client_id,
        }) as response:
            if response.status != 200:
                print(f'ComfyScript: Failed to interrupt current task: {await _response_to_str(response)}')

def clear_queue():
    return asyncio.run(_clear_queue())
async def _clear_queue():
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{_endpoint}queue', json={
            'clear': True,
            'client_id': _client_id,
        }) as response:
            if response.status != 200:
                print(f'ComfyScript: Failed to clear queue: {await _response_to_str(response)}')

def interrupt_all():
    return asyncio.run(_interrupt_all())
async def _interrupt_all():
    await _clear_queue()
    await _interrupt_current()

class TaskManager:
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

    async def __aenter__(self) -> TaskManager:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_value, traceback):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])

        nodes.Node.clear_output_hook()
        
        response = await _queue(self.outputs, source)
        # TODO: Fix multi-thread print
        # print(response)
        if self.wait_prompt:
            await _wait(response['prompt_id'])

    def __enter__(self) -> TaskManager:
        self.outputs = []
        nodes.Node.set_output_hook(self.__iadd__)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return asyncio.run(self.__aexit__(exc_type, exc_value, traceback))

__all__ = [
    'load',
    'queue',
    'queue_wait',
    'wait',
    'interrupt_current',
    'interrupt_all',
    'clear_queue',
    'get_prompt',
    'TaskManager'
]