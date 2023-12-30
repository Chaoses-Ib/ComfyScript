from __future__ import annotations
import inspect
import json
import threading
from typing import Iterable
import uuid

import asyncio
import nest_asyncio
import aiohttp

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
        self._tasks = {}
        self._watch_thread = None
        self._watch_display_node = None
        self._watch_display_task = None

    async def _get_history(self, prompt_id: str) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{_endpoint}history/{prompt_id}') as response:
                if response.status == 200:
                    json = await response.json()
                    # print(json)
                    return json.get(prompt_id)
                else:
                    print(f'ComfyScript: Failed to get history: {await _response_to_str(response)}')

    async def _watch(self):
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(f'{_endpoint}ws', params={'clientId': _client_id}) as ws:
                        queue_remaining = 0
                        async for msg in ws:
                            # print(msg.type)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                msg = msg.json()
                                # print(msg)
                                if msg['type'] == 'status':
                                    data = msg['data']
                                    new_queue_remaining = data['status']['exec_info']['queue_remaining']
                                    if queue_remaining != new_queue_remaining:
                                        queue_remaining = new_queue_remaining
                                        print(f'Queue remaining: {queue_remaining}')
                                elif msg['type'] == 'execution_start':
                                    pass
                                elif msg['type'] == 'executing':
                                    data = msg['data']
                                    if data['node'] is None:
                                        prompt_id = data['prompt_id']
                                        task: Task = self._tasks.get(prompt_id)
                                        if task is not None:
                                            history = await self._get_history(prompt_id)
                                            outputs = {}
                                            if history is not None:
                                                outputs = history['outputs']
                                            task._set_result_threadsafe(None, outputs, self._watch_display_task)
                                            if self._watch_display_task:
                                                print(f'Queue remaining: {queue_remaining}')
                                            del self._tasks[prompt_id]
                                        
                                        if new_queue_remaining == 0:
                                            for task in self._tasks.values():
                                                print(f'ComfyScript: The queue is empty but {task} has not been executed')
                                                task._set_result_threadsafe(None, {})
                                            self._tasks.clear()
                                elif msg['type'] == 'executed':
                                    data = msg['data']
                                    prompt_id = data['prompt_id']
                                    task: Task = self._tasks.get(prompt_id)
                                    if task is not None:
                                        task._set_result_threadsafe(data['node'], data['output'], self._watch_display_node)
                                        if self._watch_display_node:
                                            print(f'Queue remaining: {queue_remaining}')
                                elif msg['type'] == 'progress':
                                    data = msg['data']
                                    _print_progress(data['value'], data['max'])
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                pass
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

    def start_watch(self, display_node: bool = True, display_task: bool = True):
        '''
        - `display_node`: When an output node is finished, display its result.
        - `display_task`: When a task is finished (all output nodes are finished), display all the results.

        `load()` will `start_watch()` by default.
        '''

        if display_node or display_task:
            try:
                import IPython
                self._watch_display_node = display_node
                self._watch_display_task = display_task
            except ImportError:
                print('ComfyScript: IPython is not available, cannot display task results')

        if self._watch_thread is None:
            self._watch_thread = threading.Thread(target=asyncio.run, args=(queue._watch(),), daemon=True)
            self._watch_thread.start()

    async def _put(self, workflow: data.NodeOutput | Iterable[data.NodeOutput] | Workflow, source = None) -> Task | None:
        global _endpoint, _client_id
        
        if isinstance(workflow, data.NodeOutput) or isinstance(workflow, Iterable):
            prompt, id = Workflow(outputs=workflow)._get_prompt_and_id()
        elif isinstance(workflow, Workflow):
            prompt, id = workflow._get_prompt_and_id()
        else:
            raise TypeError(f'ComfyScript: Invalid workflow type: {workflow}')
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
                    task = Task(response['prompt_id'], response['number'], id)
                    self._tasks[task.prompt_id] = task
                    return task
                else:
                    print(f'ComfyScript: Failed to queue prompt: {response}{await _response_to_str(response)}')
    
    def put(self, workflow: data.NodeOutput | Iterable[data.NodeOutput] | Workflow, source = None) -> Task | None:
        if source is None:
            outer = inspect.currentframe().f_back
            source = ''.join(inspect.findsource(outer)[0])
        return asyncio.run(self._put(workflow, source))
    
    def __iadd__(self, workflow: data.NodeOutput | Iterable[data.NodeOutput] | Workflow):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        return self.put(workflow, source)
    
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
    def __init__(self, prompt_id: str, number: int, id: data.IdManager):
        self.prompt_id = prompt_id
        self.number = number
        self._id = id
        self._new_outputs = {}
        self._fut = asyncio.Future()

    def __str__(self):
        return f'Task {self.number} ({self.prompt_id})'
    
    def __repr__(self):
        return f'Task(n={self.number}, id={self.prompt_id})'
    
    def _set_result_threadsafe(self, node_id: str | None, output: dict, display_result: bool = False) -> None:
        if node_id is not None:
            self._new_outputs[node_id] = output
            if display_result:
                from IPython.display import display
                display(data.Result.from_output(output), clear=True)
        else:
            self.get_loop().call_soon_threadsafe(self._fut.set_result, output)
            if display_result:
                from IPython.display import display
                images = []
                others = []
                # TODO: Sort by the parsed id
                for _id, output in sorted(output.items(), key=lambda item: item[0]):
                    result = data.Result.from_output(output)
                    if isinstance(result, data.ImagesResult):
                        images.append(result)
                    else:
                        others.append(result)
                if images or others:
                    display(clear=True)
                if images:
                    display(Images(*images))
                if others:
                    display(*others)
    
    async def _wait(self) -> list[data.Result]:
        outputs: dict = await self._fut
        return [data.Result.from_output(output) for output in outputs.values()]
    
    def __await__(self) -> list[data.Result]:
        return self._wait().__await__()

    def wait(self) -> list[data.Result]:
        return asyncio.run(self)
    
    async def result(self, output: data.NodeOutput) -> data.Result | None:
        id = self._id.get_id(output.node_prompt)
        if id is None:
            return None
        
        output = self._new_outputs.get(id)
        if output is not None:
            return data.Result.from_output(output)

        outputs: dict = await self._fut
        output = outputs.get(id)
        if output is not None:
            return data.Result.from_output(output)
        return None
    
    def wait_result(self, output: data.NodeOutput) -> data.Result | None:
        return asyncio.run(self.result(output))

    # def wait(self):
    #     return asyncio.run(self._wait())
    # async def _wait(self):
    #     async with aiohttp.ClientSession() as session:
    #         async with session.ws_connect(f'{_endpoint}ws?clientId={_client_id}') as ws:
    #             async for msg in ws:
    #                 if msg.type == aiohttp.WSMsgType.TEXT:
    #                     msg = msg.json()
    #                     # print(msg)
    #                     if msg['type'] == 'status':
    #                         data = msg['data']
    #                         if data['status']['exec_info']['queue_remaining'] == 0:
    #                             break
    #                     elif msg['type'] == 'executing':
    #                         data = msg['data']
    #                         if data['node'] is None and data['prompt_id'] == self.prompt_id:
    #                             break
    #                     elif msg['type'] == 'progress':
    #                         data = msg['data']
    #                         _print_progress(data['value'], data['max'])
    #                 elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
    #                     break

    # def __await__(self):
    #     return self._wait().__await__()

    def done(self) -> bool:
        """Return True if the task is done.

        Done means either that a result / exception are available, or that the
        task was cancelled.
        """
        return self._fut.done()
    
    def add_done_callback(self, callback, *, context = None) -> None:
        """Add a callback to be run when the task becomes done.

        The callback is called with a single argument - the future object. If
        the future is already done when this is called, the callback is
        scheduled with call_soon.

        `functools.partial()` can be used to pass parameters to the callback, e.g.:
        ```
        # Call 'print("Future:", fut)' when "fut" is done.
        task.add_done_callback(
            functools.partial(print, "Future:"))
        ```
        """
        return self._fut.add_done_callback(callback, context=context)
    
    def remove_done_callback(self, callback) -> int:
        """Remove all instances of a callback from the "call when done" list.

        Returns the number of callbacks removed.
        """
        return self._fut.remove_done_callback(callback)

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Return the event loop the task is bound to."""
        return self._fut.get_loop()

class Workflow:
    '''
    - `task: Task | None`: The last task associated with the workflow.
    '''
    def __init__(self, queue: bool = True, cancel_all: bool = False, cancel_remaining: bool = False, wait: bool = False, outputs: data.NodeOutput | Iterable[data.NodeOutput] | None = None):
        '''
        - `queue`: Put the workflow into the queue when exiting the context.
        - `cancel_all`: Call `queue.cancel_all()` before queueing the workflow, so that it can start immediately.
        - `cancel_remaining`: Call `queue.cancel_remaining()` before queueing the workflow, so that it can start after the current task finishes.
        - `wait`: Wait for the task to finish before exiting the context. No effect if `queue` is `False`.
        '''
        self._outputs = []
        if outputs is not None:
            self += outputs
        self._queue_when_exit = queue
        self._wait_when_exit = wait
        self._cancel_all_when_queue = cancel_all
        self._cancel_remaining_when_queue = cancel_remaining
        self.task = None
    
    def __iadd__(self, outputs: data.NodeOutput | Iterable[data.NodeOutput]):
        if isinstance(outputs, Iterable):
            self._outputs.extend(outputs)
        else:
            self._outputs.append(outputs)
        return self
    
    def _get_prompt_and_id(self) -> (dict, data.IdManager):
        return data._get_outputs_prompt_and_id(self._outputs)

    def api_format(self) -> dict:
        return self._get_prompt_and_id()[0]
    
    def api_format_json(self) -> str:
        return json.dumps(self.api_format(), indent=2)
    
    async def _queue(self, source = None) -> Task | None:
        global queue

        if self._cancel_all_when_queue:
            await queue._cancel_all()
        elif self._cancel_remaining_when_queue:
            await queue._cancel_remaining()

        self.task = await queue._put(self, source)
        for output in self._outputs:
            output.task = self.task
        return self.task
    
    def queue(self, source = None) -> Task | None:
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        return asyncio.run(self._queue(source))

    async def __aenter__(self) -> Workflow:
        return self.__enter__()

    def __enter__(self) -> Workflow:
        self._outputs = []
        nodes.Node.set_output_hook(self.__iadd__)
        return self
    
    async def _exit(self, source):
        nodes.Node.clear_output_hook()
        if self._queue_when_exit:
            if await self._queue(source):
                # TODO: Fix multi-thread print
                # print(task)
                if self._wait_when_exit:
                    await self.task

    async def __aexit__(self, exc_type, exc_value, traceback):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        await self._exit(source)
    
    def __exit__(self, exc_type, exc_value, traceback):
        outer = inspect.currentframe().f_back
        source = ''.join(inspect.findsource(outer)[0])
        asyncio.run(self._exit(source))

queue = TaskQueue()

from . import nodes
from . import data
from .data import *

__all__ = [
    'load',
    'TaskQueue',
    'queue',
    'Task',
    'Workflow',
]
__all__.extend(data.__all__)