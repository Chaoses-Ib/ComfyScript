import click

from . import *

@click.command(help='Transpile workflow to ComfyScript.')
@click.argument('workflow', type=click.File('r'))
@click.option('--api', type=click.STRING, default='http://127.0.0.1:8188/', show_default=True)
@click.option('--bootstrap', is_flag=True, default=False, show_default=True, help='Wrap the script with bootstrap imports and workflow context.')
def cli(workflow, api: str, bootstrap: bool):
    workflow = workflow.read()
    script = WorkflowToScriptTranspiler(workflow, api).to_script(bootstrap=bootstrap)
    print(script)

cli()