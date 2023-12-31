import click

from . import *

@click.command(help='Transpile workflow to ComfyScript.')
@click.argument('workflow', type=click.File('r'))
@click.option('--api', type=click.STRING, default='http://127.0.0.1:8188/', help='Default: http://127.0.0.1:8188/')
def cli(workflow, api):
    workflow = workflow.read()
    script = WorkflowToScriptTranspiler(workflow, api).to_script()
    print(script)

cli()