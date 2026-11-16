"""Start the notebook workspace using the selected Python environment."""
import argparse
import sys
from execute_notebook import ROOT, setup_kernel

def main(argv=None):
    parser=argparse.ArgumentParser(description='Open the Smart Parking notebook workspace.')
    parser.add_argument('--notebook',default='01_real_data_audit.ipynb')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--offline',action='store_true',help='Disable update checks and make extension management read-only.')
    parser.add_argument('--port',type=int,default=8888)
    parser.add_argument('--state-dir',help='Optional separate folder for kernel/runtime/config state.')
    args=parser.parse_args(argv)
    path=(ROOT/'notebooks'/args.notebook).resolve()
    if not path.is_relative_to((ROOT/'notebooks').resolve()) or not path.is_file():parser.error('Choose an existing notebook inside this project.')
    if not 1<=args.port<=65535:parser.error('Port must be between1and65535.')
    setup_kernel(args.state_dir)
    options=[str(path),'--ServerApp.root_dir='+str(ROOT),'--ServerApp.ip=127.0.0.1','--ServerApp.port='+str(args.port)]
    if args.no_browser:options.append('--no-browser')
    if args.offline:options.extend(['--LabApp.extension_manager=readonly','--LabApp.check_for_updates_class=jupyterlab.handlers.announcements.NeverCheckForUpdate'])
    # In-process launch keeps owned-server cleanup and Python socket auditing
    # effective; the selected interpreter also owns the project kernel spec.
    from jupyterlab.labapp import main as launch
    return launch(options)

if __name__ == '__main__':raise SystemExit(main())
