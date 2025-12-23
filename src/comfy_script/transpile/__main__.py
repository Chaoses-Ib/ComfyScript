from typing import TextIO
import click

from . import *

@click.command(help='Transpile workflow to ComfyScript.')
@click.argument('workflow', type=click.File('r', encoding='utf-8'))
@click.option('--api', type=click.STRING, default='http://127.0.0.1:8188/', show_default=True)
@click.option('--runtime', is_flag=True, default=False, show_default=True, help='Wrap the script with runtime imports and workflow context.')
@click.option('--use-keyword-args', is_flag=True, default=False, show_default=True, help='Generate keyword arguments instead of positional arguments.')
def cli(workflow: TextIO, api: str, runtime: bool, use_keyword_args: bool):
    workflow = workflow.read()
    script = WorkflowToScriptTranspiler(workflow, api, use_keyword_args=use_keyword_args).to_script(runtime=runtime)
    print(script)

cli()