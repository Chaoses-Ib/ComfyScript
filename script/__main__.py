import click

from . import *

@click.group()
def cli():
    pass

@cli.command(help='Transpile workflow to ComfyScript.')
@click.argument('workflow', type=click.File('r'))
def from_workflow(workflow):
    workflow = workflow.read()
    script = WorkflowToScriptTranspiler(workflow).to_script()
    print(script)

cli()