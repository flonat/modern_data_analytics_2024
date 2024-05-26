from pathlib import Path

GLOBAL_ROOT_PATH = Path(__file__).parents[1]
DATA_PATH = GLOBAL_ROOT_PATH / 'data'
TRANSFORMED_DATA_PATH = GLOBAL_ROOT_PATH / 'transformed_data'