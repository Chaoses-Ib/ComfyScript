from __future__ import annotations
import inspect
import json
import threading
from typing import Iterable
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

async def _response_to_str(response: aiohttp.ClientResponse) -> str:
    try:
        msg = json.dumps(await response.json(), indent=2)
    except Exception as e:
        msg = str(e)
    return f'{response}{msg}'

def load(api_endpoint: str = _endpoint, vars: dict | None = None, watch: bool = True, save_script_source: bool = True):
    asyncio.run(_load(api_endpoint, vars, watch, save_script_source))
async def _load(api_endpoint: str = _endpoint, vars: dict | None = None, watch: bool = True, save_script_source: bool = True):
    global _endpoint, _save_script_source, queue

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
    
    # TODO: Stop watch if watch turns to False
    if watch:
        queue.start_watch()

def get_prompt(task: data.NodeOutput | Iterable[data.NodeOutput] | TaskBuilder | dict) -> dict:
    if isinstance(task, data.NodeOutput):
        prompt = task.get_prompt()
    elif isinstance(task, Iterable):
        prompt = data.get_outputs_prompt(task)
    elif isinstance(task, TaskBuilder):
        prompt = task.get_prompt()
    elif isinstance(task, dict):
        prompt = task
    else:
        raise TypeError(f'ComfyScript: Invalid task type: {type(task)}')
    return prompt

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

class TaskQueue:
    def __init__(self):
        self._watch_thread = None

    async def _watch(self):
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

    def start_watch(self):
        '''`load()` will `start_watch()` by default.'''
        if self._watch_thread is None:
            self._watch_thread = threading.Thread(target=asyncio.run, args=(queue._watch(),), daemon=True)
            self._watch_thread.start()

    async def _put(self, task: data.NodeOutput | Iterable[data.NodeOutput] | TaskBuilder | dict, source = None) -> Task | None:
        global _endpoint, _client_id
        
        prompt = get_prompt(task)
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
                    response = await response.json()
                    # print(response)
                    return Task(response['prompt_id'], response['number'])
                else:
                    print(f'ComfyScript: Failed to queue prompt: {response}{await _response_to_str(response)}')
    
    def put(self, task: data.NodeOutput | Iterable[data.NodeOutput] | TaskBuilder | dict, source = None) -> Task | None:
        if source is None:
            outer = inspect.currentframe().f_back
            source = ''.join(inspect.findsource(outer)[0])
        return asyncio.run(self._put(task, source))
    
    def __iadd__(self, task: data.NodeOutput | Iterable[data.NodeOutput] | TaskBuilder | dict):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        return self.put(task, source)
    
    def cancel_current(self):
        '''Interrupt the current task'''
        return asyncio.run(self._cancel_current())
    async def _cancel_current(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{_endpoint}interrupt', json={
                'client_id': _client_id,
            }) as response:
                if response.status != 200:
                    print(f'ComfyScript: Failed to interrupt current task: {await _response_to_str(response)}')

    def cancel_remaining(self):
        '''Clear the queue'''
        return asyncio.run(self._cancel_remaining())
    async def _cancel_remaining(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{_endpoint}queue', json={
                'clear': True,
                'client_id': _client_id,
            }) as response:
                if response.status != 200:
                    print(f'ComfyScript: Failed to clear queue: {await _response_to_str(response)}')

    def cancel_all(self):
        '''Interrupt the current task and clear the queue'''
        return asyncio.run(self._cancel_all())
    async def _cancel_all(self):
        await self._cancel_remaining()
        await self._cancel_current()

class Task:
    def __init__(self, prompt_id: str, number: int):
        self.prompt_id = prompt_id
        self.number = number
    
    def __str__(self):
        return f'Task {self.number} ({self.prompt_id})'
    
    def wait(self):
        return asyncio.run(self._wait())
    async def _wait(self):
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
                            if data['node'] is None and data['prompt_id'] == self.prompt_id:
                                break
                        elif msg['type'] == 'progress':
                            data = msg['data']
                            _print_progress(data['value'], data['max'])
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break

class TaskBuilder:
    def __init__(self, queue: bool = True, wait: bool = False):
        '''
        - `wait`: Wait for the prompt to finish before exiting the context manager.
        '''
        self._outputs = []
        self._queue = queue
        self._wait = wait
    
    def __iadd__(self, other: data.NodeOutput | Iterable[data.NodeOutput]):
        if isinstance(other, Iterable):
            self._outputs.extend(other)
        else:
            self._outputs.append(other)
        return self
    
    def get_prompt(self) -> dict:
        return get_prompt(self._outputs)

    async def __aenter__(self) -> TaskBuilder:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_value, traceback):
        global queue
        nodes.Node.clear_output_hook()
        if self._queue:
            outer = inspect.currentframe().f_back
            source = ''.join(inspect.findsource(outer)[0])            
            
            task: Task = await queue._put(self._outputs, source)
            if task:
                # TODO: Fix multi-thread print
                # print(task)
                if self._wait:
                    await task._wait()

    def __enter__(self) -> TaskBuilder:
        self._outputs = []
        nodes.Node.set_output_hook(self.__iadd__)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return asyncio.run(self.__aexit__(exc_type, exc_value, traceback))

queue = TaskQueue()

__all__ = [
    'load',
    'TaskQueue',
    'queue',
    'get_prompt',
    'Task',
    'TaskBuilder',
]