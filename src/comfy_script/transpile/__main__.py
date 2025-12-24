from typing import TextIO
import click

from . import *

@click.command(help='Transpile workflow to ComfyScript.')
@click.argument('workflow', type=click.File('r', encoding='utf-8'))
@click.option('--api', type=click.STRING, default='http://127.0.0.1:8188/', show_default=True)
@click.option('--runtime', is_flag=True, default=False, show_default=True, help='Wrap the script with runtime imports and workflow context.')
@click.option('--args',
    type=click.Choice(ArgsFormat, case_sensitive=False),
    default=ArgsFormat.Pos2OrKwd,
    show_default=True,
    help='Format node inputs as positional or keyword arguments.',
)
def cli(
    workflow: TextIO,
    api: str,
    runtime: bool,
    args: ArgsFormat,
):
    workflow_str = workflow.read()
    format = FormatOptions(
        runtime=runtime,
        args=args,
    )
    script = WorkflowToScriptTranspiler(workflow_str, api).to_script(format=format)
    print(script)

cli()