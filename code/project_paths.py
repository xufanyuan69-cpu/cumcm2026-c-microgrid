"""Project-local inputs and generated outputs; never write into source templates."""
import os
from pathlib import Path
from shutil import copy2

ROOT = Path(__file__).resolve().parents[1]


def input_directory():
    return Path(os.environ.get('CUMCM_DATA_DIR', ROOT / 'data' / 'raw')).resolve()


def output_directory():
    path = Path(os.environ.get('CUMCM_OUTPUT_DIR', ROOT / 'results')).resolve()
    for source in (input_directory(), ROOT / 'data' / 'templates'):
        if path == source or source in path.parents:
            raise ValueError('Output directory must not be inside input data or templates.')
    path.mkdir(parents=True, exist_ok=True)
    return path


def analysis_directory():
    path = output_directory() / 'analysis_outputs'
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_template(name):
    candidates = (ROOT / 'data' / 'templates' / name,
                  input_directory() / '附件5' / name)
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        f'Missing {name}: place the original workbook in data/templates/ '
        'or in the input directory under 附件5/.')


def prepare_result(name):
    source = find_template(name)
    target = output_directory() / name
    if target.resolve() == source.resolve():
        raise ValueError('Output workbook must differ from input template.')
    copy2(source, target)
    return target
