from pathlib import Path
from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix='COMFY_SCRIPT',
    root_path=Path(__file__).resolve().parent,
    settings_files=['settings.toml', '.secrets.toml'],
    validators=[
        Validator('transpile.hook.enabled', default=True),
        Validator('transpile.hook.save_script', default=True),
        Validator('transpile.hook.print_script', default=True),
    ],
)

# See `settings.example.toml` for details.