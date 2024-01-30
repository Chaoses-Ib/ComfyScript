from pathlib import Path

import folder_paths

folder_paths.add_model_folder_path('custom_nodes', Path(__file__).resolve().parent / 'nodes')