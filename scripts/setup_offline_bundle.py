"""Build a new package-local Python environment using only included wheels."""
import argparse,hashlib,json,os,platform,subprocess,sys,venv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def isolated_environment(root,environ=None):
    root=Path(root).resolve();temporary=(root/'outputs/setup/tmp').resolve()
    if not temporary.is_relative_to(root):raise ValueError('Bootstrap temporary path must stay inside the demo')
    temporary.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in (os.environ if environ is None else environ).items() if not k.upper().startswith('PIP_') and k.upper() not in {'PYTHONHOME','PYTHONPATH','PYTHONSTARTUP','TEMP','TMP'}}
    env.update(PIP_CONFIG_FILE=os.devnull,PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1',TEMP=str(temporary),TMP=str(temporary))
    return env
def main():
    if len(sys.argv)>1 and sys.argv[1]=='--install-child':
        from package_offline_guard import install
        install(ROOT,ROOT/'outputs/setup/install_audit.json')
        from pip._internal.cli.main import main as pip
        raise SystemExit(pip(['install','--no-index','--no-cache-dir','--only-binary=:all:','--require-hashes','--no-input','--disable-pip-version-check',
            '--find-links',str(ROOT/'dependencies/offline_app/v1/wheels'),'--find-links',str(ROOT/'dependencies/offline_jupyter/v1/wheels'),
            '-r',str(ROOT/'dependencies/offline_jupyter/v1/requirements-app-jupyter-lock.txt')]))
    parser=argparse.ArgumentParser();parser.add_argument('--destination',default='.venv');args=parser.parse_args()
    if sys.platform!='win32' or sys.version_info[:2]!=(3,12) or platform.architecture()[0]!='64bit':raise RuntimeError('Use64-bit Windows Python3.12 for this installer profile.')
    destination=(ROOT/args.destination).resolve()
    if not destination.is_relative_to(ROOT) or destination==ROOT:raise ValueError('Choose a new environment folder inside this demo.')
    if destination.exists():raise FileExistsError('Preserve existing environment; choose another new destination.')
    manifest=json.loads((ROOT/'BUNDLE_MANIFEST.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        path=(ROOT/row['path']).resolve()
        if not path.is_relative_to(ROOT) or sha(path)!=row['sha256']:raise ValueError('Bundle checksum/path failed:'+row['path'])
    output=ROOT/'outputs/setup';output.mkdir(parents=True,exist_ok=True)
    env=isolated_environment(ROOT)
    venv.EnvBuilder(with_pip=False,system_site_packages=False).create(destination)
    assert 'include-system-site-packages = false' in (destination/'pyvenv.cfg').read_text(encoding='utf-8')
    python=destination/'Scripts/python.exe'
    with (output/'bootstrap_stdout.txt').open('w',encoding='utf-8') as out,(output/'bootstrap_stderr.txt').open('w',encoding='utf-8') as err:
        bootstrap=subprocess.run([str(python),'-I','-m','ensurepip','--upgrade','--default-pip'],cwd=ROOT,env=env,stdout=out,stderr=err,timeout=120)
    if bootstrap.returncode:raise RuntimeError('Bundled pip bootstrap failed;bootstrap logs and partial environment retained. Choose a new destination for a later rebuild.')
    with (output/'install_stdout.txt').open('w',encoding='utf-8') as out,(output/'install_stderr.txt').open('w',encoding='utf-8') as err:
        process=subprocess.run([str(python),'-I',str(Path(__file__).resolve()),'--install-child'],cwd=ROOT,env=env,stdout=out,stderr=err,timeout=900)
    if process.returncode:raise RuntimeError('Offline installation failed; environment/logs retained. Choose a new destination for any later rebuild.')
    report=json.loads((output/'install_audit.json').read_text(encoding='utf-8'));assert not report['denied']
    checked=subprocess.run([str(python),'-m','pip','check','--disable-pip-version-check'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
    if checked.returncode:raise RuntimeError('Dependency check failed:'+checked.stdout+checked.stderr)
    result=dict(status='passed',python=str(python),python_relative=python.relative_to(ROOT).as_posix(),packages=107,
        no_index_hash_locked_install=True,dependency_check=checked.stdout,network_audit=report,
        pip_bootstrap='Explicit isolated child with captured stdout/stderr and package-local temporary directory',
        bootstrap_temporary_directory=env['TEMP'],pip_cache_disabled=True,
        existing_base_python_reused=True,new_machine_or_physical_offline_verified=False)
    (ROOT/'OFFLINE_ENVIRONMENT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
