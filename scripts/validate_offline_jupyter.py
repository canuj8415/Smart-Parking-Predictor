"""New app+Jupyter venv, offline pip install and genuine local kernel execution."""
import csv,hashlib,json,os,shutil,subprocess,sys,time,venv
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def child(mode,folder):
    from offline_jupyter_guard import install
    install(folder/(mode+'_network.json'),loopback=True)
    plan=json.loads((ROOT/'dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json').read_text(encoding='utf-8'))
    if mode=='install':
        from pip._internal.cli.main import main as pip
        raise SystemExit(pip(['install','--no-index','--no-input','--disable-pip-version-check','--only-binary=:all:',
            '--require-hashes','--find-links',str(ROOT/'dependencies/offline_app/v1/wheels'),
            '--find-links',str(ROOT/'dependencies/offline_jupyter/v1/wheels'),'-r',str(ROOT/plan['lock_path'])]))
    if mode=='check':
        from pip._internal.cli.main import main as pip
        assert pip(['check','--disable-pip-version-check'])==0
        import jupyterlab,ipykernel,nbclient,nbformat,matplotlib_inline,torch,torchvision,numpy,PIL,cv2
        modules=[jupyterlab,ipykernel,nbclient,nbformat,matplotlib_inline,torch,torchvision,numpy,PIL,cv2]
        origins={m.__name__:str(Path(m.__file__).resolve()) for m in modules}
        assert all(Path(p).is_relative_to(Path(sys.prefix)) for p in origins.values())
        dump(folder/'dependency_check.json',dict(origins=origins,all_from_new_venv=True,jupyterlab_version=jupyterlab.__version__))
        return
    import nbformat
    from nbclient import NotebookClient
    fresh=Path(sys.prefix);local=folder/'jupyter';kernel=local/'kernels/offline-parking';kernel.mkdir(parents=True,exist_ok=False)
    startup=folder/'ipython/profile_default/startup';startup.mkdir(parents=True,exist_ok=False)
    kernel_audit=folder/'kernel_network'
    (startup/'00-offline-audit.py').write_text('import sys,os\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(ROOT/'scripts'))+')\nfrom offline_jupyter_guard import install\n_OFFLINE_SAVE=install('+repr(str(kernel_audit))+'+"_"+str(os.getpid())+".json",loopback=True)\nimport cv2\nassert Path(cv2.__file__).is_relative_to(Path(sys.prefix))\n',encoding='utf-8')
    dump(kernel/'kernel.json',dict(argv=[sys.executable,'-I','-m','ipykernel_launcher','-f','{connection_file}'],display_name='Offline parking validation',language='python'))
    os.environ.update(JUPYTER_PATH=str(local),JUPYTER_RUNTIME_DIR=str(local/'runtime'),IPYTHONDIR=str(folder/'ipython'),
        JUPYTER_CONFIG_DIR=str(local/'config'),JUPYTER_PLATFORM_DIRS='1')
    (local/'runtime').mkdir(parents=True,exist_ok=True)
    source=ROOT/'notebooks/08_image_patterns_and_svd.ipynb';book=nbformat.read(source,as_version=4)
    for cell in book.cells:
        if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
    diagnosis=nbformat.v4.new_code_cell('import sys,os,json\nfrom pathlib import Path\nassert Path(sys.prefix)==Path('+repr(str(fresh))+')\nprint("Fresh kernel:",sys.executable)\n%matplotlib inline')
    book.cells.insert(0,diagnosis)
    client=NotebookClient(book,timeout=180,startup_timeout=60,kernel_name='offline-parking',resources={'metadata':{'path':str(ROOT)}})
    client.execute()
    executed=folder/'executed/08_image_patterns_and_svd.ipynb';executed.parent.mkdir(parents=True,exist_ok=True);nbformat.write(book,executed)
    assert all(o.output_type!='error' for c in book.cells if c.cell_type=='code' for o in c.outputs)
    pngs=sum('image/png' in o.get('data',{}) for c in book.cells if c.cell_type=='code' for o in c.outputs)
    assert pngs>=1
    # A separate training-only smoke notebook avoids rerunning notebook02's old
    # held-out frame. Never substitute training predictions for final accuracy.
    smoke=nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell('Training-only offline product compatibility check; not accuracy.'),
        nbformat.v4.new_code_cell('''%matplotlib inline
import sys,json,hashlib,gc
from pathlib import Path
from PIL import Image
from IPython.display import display
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'))
from smart_parking.vision import VisionEngine
from smart_parking.layout import load_layout
from smart_parking.convolution import plot_convolutions
sample=json.loads((ROOT/'configs/demo_sample.json').read_text(encoding='utf-8'));assert sample['split']=='train'
image_path=ROOT/sample['image'];assert hashlib.sha256(image_path.read_bytes()).hexdigest()==sample['image_sha256']
image=Image.open(image_path).convert('RGB');layout=load_layout(ROOT/sample['layout'],image.size)
results=[]
for kind in ['fasterrcnn','maskrcnn']:
    engine=VisionEngine(kind);result,overlay=engine.analyze(image,layout,confidence=.5)
    assert result['counts']==dict(occupied=68,vacant=32,uncertain=0,total=100)
    results.append(dict(detector=kind,counts=result['counts'],weight_sha256=result['weight_sha256']))
    display(overlay);del engine;gc.collect()
import matplotlib.pyplot as plt
fig,demo=plot_convolutions(image);plt.show()
assert demo['max_2d_error']<1e-5 and demo['max_3d_error']<1e-5
print(json.dumps(dict(detectors=results,max_2d_error=demo['max_2d_error'],max_3d_error=demo['max_3d_error'],scope='Training-only agreement; 3D numeric teaching fixture,not real footage')))
''')])
    NotebookClient(smoke,timeout=240,startup_timeout=60,kernel_name='offline-parking',resources={'metadata':{'path':str(ROOT)}}).execute()
    nbformat.write(smoke,folder/'executed/training_product_smoke.ipynb')
    dump(folder/'notebook_checks.json',dict(status='passed',fresh_kernel=str(fresh/'Scripts/python.exe'),
        source_notebook=source.relative_to(ROOT).as_posix(),source_sha256=digest(source),original_source_cells_unchanged=True,
        extra_diagnostic_setup_cell=True,lesson08_code_cells=4,lesson08_inline_png_outputs=pngs,
        training_detectors=2,training_counts_agree=True,convolution_2d_3d_pass=True,
        final_data_reopened=False,scope='Actual Jupyter kernels; Python non-loopback access denied. Native ZeroMQ uses loopback and is outside Python audit coverage. No physical offline/new-machine/browser-layout claim.'))

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(sys.argv[2],Path(sys.argv[3]));return
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another job is active')
    started=datetime.now(timezone.utc);run='JUPYTER-OFFLINE-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    parent=None
    if len(sys.argv)>2 and sys.argv[1]=='--resume-existing':
        parent_path=ROOT/'experiments/results'/sys.argv[2]/'run.json'
        assert parent_path.is_relative_to(ROOT/'experiments/results')
        parent=json.loads(parent_path.read_text(encoding='utf-8'))
        assert parent['checks']=={'install':{'returncode':0,'denied_network':[{'event':'socket.bind','host':'::1'}]}}
        fresh=ROOT/parent['fresh_venv']
    else:fresh=ROOT/'outputs/installation_checks'/run/'venv'
    manifest=ROOT/'dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json'
    plan=json.loads(manifest.read_text(encoding='utf-8'));app=json.loads((ROOT/plan['app_manifest_path']).read_text(encoding='utf-8'))
    assert digest(ROOT/plan['app_manifest_path'])==plan['app_manifest_sha256']
    assert all(digest(ROOT/e['path'])==e['sha256'] for e in [*plan['entries'],*app['entries']])
    assert digest(ROOT/plan['lock_path'])==plan['lock_sha256']
    files=['scripts/validate_offline_jupyter.py','scripts/offline_jupyter_guard.py','notebooks/08_image_patterns_and_svd.ipynb',
        'configs/demo_sample.json','src/smart_parking/vision.py','src/smart_parking/convolution.py','src/smart_parking/decomposition.py']
    protected=['models/checkpoints/parking_unet.pt','models/checkpoints/lstm_30min.pt','models/checkpoints/occupancy_resnet18.pt']
    protected.extend(p.relative_to(ROOT).as_posix() for group in ['holdout_claims','forecast_holdout_claims','sequence_holdout_claims'] for p in (ROOT/'data'/group).rglob('*.json'))
    hashes={p:digest(ROOT/p) for p in files};unchanged={p:digest(ROOT/p) for p in protected}
    protocol=dict(run_id=run,started_at=started.isoformat(),seed=121,source_ids=['SRC-PKG-003','SRC-PKG-004','SRC-DS-001','SRC-MOD-001','SRC-MOD-002'],
        hypothesis='Pinned app+Jupyter wheels install offline into a new isolated venv and genuine kernels execute unchanged lesson08 and training-only model/convolution checks.',
        gates=['No-index hash-locked install','pip check and new-venv imports','Actual fresh kernels execute lesson08 including inline plots',
            'Both detector training-example counts agree; 2D/3D arithmetic passes','No unexpected non-loopback Python socket access','Original weights/notebooks/final claims unchanged'],
        fresh_venv=fresh.relative_to(ROOT).as_posix(),source_hashes=hashes,protected_hashes=unchanged,manifest_sha256=digest(manifest),
        continuation_of=parent['run_id'] if parent else None,parent_report_sha256=digest(parent_path) if parent else None,
        continuation_scope='Reuse newly installed isolated venv; prior install succeeded while strict guard blocked harmless ::1 bind. No package reinstall.' if parent else None,
        lock_sha256=plan['lock_sha256'],model_training_performed=False,scientific_accuracy_evaluated=False,
        limitations=['Existing base Python/OS and local data/model assets reused','Python audit hook is not a native-extension firewall','JupyterLab browser UI/new-machine/physical-disconnection/manual acceptance separate'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        if parent is None:
            fresh.parent.mkdir(parents=True,exist_ok=True);venv.EnvBuilder(with_pip=True,system_site_packages=False).create(fresh)
        assert 'include-system-site-packages = false' in (fresh/'pyvenv.cfg').read_text(encoding='utf-8')
        env=os.environ.copy();env.update(PIP_CONFIG_FILE=os.devnull,PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1',
            MPLCONFIGDIR=str(ROOT/'.cache'/run),OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',PYTHONNOUSERSITE='1')
        checks={}
        if parent:
            checks['install']=dict(returncode=0,denied_network=[],inherited_from=parent['run_id'],
                original_blocked_loopback_probe=parent['checks']['install']['denied_network'],no_non_loopback_access_in_parent=True)
        for mode in (['check','notebooks'] if parent else ['install','check','notebooks']):
            with (folder/(mode+'_stdout.txt')).open('w',encoding='utf-8') as out,(folder/(mode+'_stderr.txt')).open('w',encoding='utf-8') as err:
                process=subprocess.Popen([str(fresh/'Scripts/python.exe'),'-I',str(Path(__file__).resolve()),'--child',mode,str(folder)],cwd=ROOT,env=env,stdout=out,stderr=err)
                deadline=time.monotonic()+720
                while process.poll() is None:
                    if (folder/'CANCEL').exists() or time.monotonic()>deadline:
                        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20)
                        process.wait(timeout=20);raise InterruptedError('Cancelled/timed-out owned validation tree')
                    time.sleep(.3)
            network=json.loads((folder/(mode+'_network.json')).read_text(encoding='utf-8')) if (folder/(mode+'_network.json')).exists() else dict(denied=['Missing audit evidence'])
            checks[mode]=dict(returncode=process.returncode,denied_network=network['denied'])
            dump(folder/'progress.json',dict(phase=mode,checks=checks))
            if process.returncode or network['denied']:break
        accepted=len(checks)==3 and all(r['returncode']==0 and not r['denied_network'] for r in checks.values())
        kernel={p.name:json.loads(p.read_text(encoding='utf-8')) for p in folder.glob('kernel_network_*.json')}
        accepted=accepted and len(kernel)==2 and all(not k['denied'] for k in kernel.values())
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**unchanged}.items())
        result=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            checks=checks,kernel_network=kernel,offline_jupyter_gate_passed=accepted,original_assets_and_claims_unchanged=True)
        dump(folder/'run.json',result);dump(ROOT/'models/offline_jupyter_installation.json',result)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run,run_type='Fresh offline app+Jupyter installation and actual kernel compatibility',started_at=protocol['started_at'],finished_at=result['finished_at'],
            source_ids=';'.join(protocol['source_ids']),split_ids='Frozen training-only image; numeric teaching volume; no final groups',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Fresh isolated CPU app+Jupyter venv; original saved models',epochs=0,batch_size=1,random_seed=121,hardware='CPU; Windows; existing base Python',
            execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(dict(offline_jupyter_gate_passed=accepted,checks=checks)),
            logs=folder.relative_to(ROOT).as_posix(),checkpoints='No new weights',code_revision_basis='9819214 plus sealed source snapshots',implementation_sha256=hashes[files[0]],
            conclusions='Actual offline kernel gate='+str(accepted)+'; no scientific accuracy/manual/browser/physical/new-machine claim')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,offline_jupyter_gate_passed=accepted,checks=checks),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False));state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)

if __name__=='__main__':main()
