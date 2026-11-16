"""Execute the teaching notebook in a project-local kernel and save actual outputs."""
import json
import argparse
import os
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]

def setup_kernel(state_dir=None):
    base=Path(state_dir).resolve() if state_dir is not None else ROOT/'.jupyter'
    kernel = base / 'kernels/smart-parking-python'
    kernel.mkdir(parents=True, exist_ok=True)
    (kernel/'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'Python (Smart Parking)', 'language': 'python'}), encoding='utf-8')
    os.environ['JUPYTER_PATH'] = str(base) + os.pathsep + os.environ.get('JUPYTER_PATH','')
    os.environ['JUPYTER_RUNTIME_DIR'] = str(base/'runtime')
    os.environ['IPYTHONDIR'] = str(base/'ipython') if state_dir is not None else str(ROOT/'.ipython')
    os.environ['MPLCONFIGDIR'] = str(base/'matplotlib') if state_dir is not None else str(ROOT/'.cache/matplotlib')
    if state_dir is not None:os.environ['JUPYTER_CONFIG_DIR']=str(base/'config')
    (base/'runtime').mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('notebook',nargs='?',default='01_real_data_audit.ipynb');args=parser.parse_args()
    setup_kernel()
    path = (ROOT/'notebooks'/args.notebook).resolve()
    if not path.is_relative_to((ROOT/'notebooks').resolve()):raise ValueError('Notebook must be inside this project')
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    NotebookClient(notebook, timeout=180, kernel_name='smart-parking-python',
                   resources={'metadata':{'path':str(ROOT)}}).execute()
    nbformat.write(notebook, path)
    print('Notebook executed and saved successfully:', path)
