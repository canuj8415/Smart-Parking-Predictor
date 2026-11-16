"""Bounded phase/stack diagnostic in an existing copied runtime;no reinstall."""
import argparse,csv,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def dump(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def worker(root,out):
    import faulthandler,importlib
    root=Path(root).resolve();out=Path(out).resolve();assert out.is_relative_to(root/'outputs/notebook_diagnostics')
    def phase(name,**extra):
        event=dict(at=datetime.now(timezone.utc).isoformat(),phase=name,pid=os.getpid(),**extra)
        with (out/'phases.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(event)+'\n')
        dump(out/'latest_phase.json',event)
    trace=(out/'stacks.txt').open('w',encoding='utf-8');faulthandler.enable(file=trace);faulthandler.dump_traceback_later(30,repeat=True,file=trace)
    phase('worker_started',python=sys.executable,prefix=sys.prefix)
    sys.path.insert(0,str(root/'scripts'))
    from package_offline_guard import install
    save=install(root,out/'controller_audit.json');phase('audit_installed')
    modules={}
    try:
        for name in ['nbformat','nbclient','cv2','numpy','torch']:
            phase('import_start',module=name);modules[name]=importlib.import_module(name)
            assert Path(modules[name].__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
            phase('import_complete',module=name)
        from execute_notebook import setup_kernel
        state=out/'state';setup_kernel(state)
        startup=state/'ipython/profile_default/startup';startup.mkdir(parents=True,exist_ok=True)
        (startup/'00-diagnostic-audit.py').write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(root/'scripts'))+')\nfrom package_offline_guard import install\n_save_diagnostic=install('+repr(str(root))+','+repr(str(out/'kernel_audit.json'))+')\n',encoding='utf-8')
        phase('kernel_configured')
        nbformat=modules['nbformat'];source=root/'notebooks/08_image_patterns_and_svd.ipynb';before=sha(source);book=nbformat.read(source,as_version=4)
        for cell in book.cells:
            if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
        book.cells.insert(0,nbformat.v4.new_code_cell('import os,sys\nfrom pathlib import Path\nassert Path(sys.prefix)==Path('+repr(str(Path(sys.prefix)))+')\nprint("Diagnostic copied kernel:",os.getpid(),sys.executable)'))
        client=None
        def on_start(**kwargs):
            provisioner=getattr(getattr(client,'km',None),'provisioner',None);pid=getattr(provisioner,'pid',None)
            phase('kernel_started',kernel_pid=pid)
        def cell_start(cell,cell_index,**kwargs):phase('cell_start',cell_index=cell_index,cell_type=cell.cell_type)
        def cell_done(cell,cell_index,**kwargs):
            nbformat.write(book,out/'08_partial_executed.ipynb');phase('cell_executed',cell_index=cell_index,execution_count=cell.execution_count)
        client=modules['nbclient'].NotebookClient(book,timeout=60,startup_timeout=30,kernel_name='smart-parking-python',resources={'metadata':{'path':str(root)}},on_notebook_start=on_start,on_cell_start=cell_start,on_cell_executed=cell_done)
        phase('execute_entered');client.execute();phase('execute_returned')
        nbformat.write(book,out/'08_executed.ipynb');assert sha(source)==before
        pngs=sum('image/png' in item.get('data',{}) for cell in book.cells if cell.cell_type=='code' for item in cell.outputs)
        errors=[item for cell in book.cells if cell.cell_type=='code' for item in cell.outputs if item.output_type=='error']
        assert pngs>=1 and not errors
        save();kernel=read(out/'kernel_audit.json');assert not kernel['denied'] and not read(out/'controller_audit.json')['denied']
        dump(out/'worker_result.json',dict(status='passed',code_cells=sum(c.cell_type=='code' for c in book.cells),inline_png_outputs=pngs,original_notebook_unchanged=True,actual_kernel_executed=True,normal_forbidden_attempts=0,scope='Diagnostic copied runtime/local temp;not complete package acceptance or physical offline'))
        phase('worker_completed')
    except BaseException as error:
        phase('worker_error',error=repr(error));raise
    finally:
        save();faulthandler.cancel_dump_traceback_later();trace.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker-root');parser.add_argument('--out');args=parser.parse_args()
    if args.worker_root:return worker(args.worker_root,args.out)
    import psutil
    root=Path(__file__).resolve().parents[1];state_path=root/'data/automation_state.json';state=read(state_path)
    assert state['completed_recorded_runs_since_schedule']==84 and not state['active_training_jobs'] and not state['active_validation_jobs']
    started=datetime.now(timezone.utc);rid='NOTEBOOK-DIAGNOSTIC-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=root/'experiments/results'/rid;folder.mkdir(exist_ok=False);package=root/'outputs/offline_demo_packages/COMBINED-DEMO-20261026T181455268229Z'
    output=package/'outputs/notebook_diagnostics'/rid;output.mkdir(parents=True,exist_ok=False);controller=output/'controller.py';shutil.copyfile(__file__,controller)
    inputs=[package/'BUNDLE_MANIFEST.json',package/'BUNDLE_SCOPE.json',package/'notebooks/08_image_patterns_and_svd.ipynb',package/'scripts/package_offline_guard.py',package/'scripts/execute_notebook.py',package/'.venv/pyvenv.cfg']
    protocol=dict(run_id=rid,prepared_at=started.isoformat(),seed=148,source_ids=['SRC-DS-001','SRC-PKG-004'],hypothesis='Phase/stack/PID checkpoints with isolated local temporary and Jupyter paths can localize or resolve the copied notebook stall without reinstalling or modifying its frozen payload.',
        package=package.relative_to(root).as_posix(),output=output.relative_to(root).as_posix(),maximum_seconds=120,cell_timeout=60,kernel_startup_timeout=30,
        source_hashes={'scripts/diagnose_packaged_notebook.py':sha(__file__)},input_hashes={p.relative_to(root).as_posix():sha(p) for p in inputs},protected_hashes=read(root/'models/singapore_trend_development.json')['protected_hashes'],
        scope='One reused TRAIN-image teaching notebook;no detectors,model fitting,raw final or future Singapore data;whole package remains incomplete pending formal acceptance')
    dump(folder/'protocol.json',protocol);dump(folder/'source_snapshot.json',dict(sha256=sha(__file__),source=Path(__file__).read_text(encoding='utf-8')));dump(folder/'protocol_binding.json',dict(sha256=sha(folder/'protocol.json')))
    state['active_validation_jobs']=[dict(run_id=rid,phase='Bounded copied notebook diagnostic',cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    env={k:v for k,v in os.environ.items() if k.upper() not in {'PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','JUPYTER_PATH','JUPYTER_CONFIG_DIR','JUPYTER_RUNTIME_DIR','IPYTHONDIR','MPLCONFIGDIR','TEMP','TMP','TMPDIR'}}
    temporary=output/'tmp';temporary.mkdir();env.update(TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    child=None;failure=None;cleanup=[];remaining=[];clock=time.monotonic()
    try:
        with (folder/'stdout.txt').open('w',encoding='utf-8') as stdout,(folder/'stderr.txt').open('w',encoding='utf-8') as stderr:
            child=subprocess.Popen([str(package/'.venv/Scripts/python.exe'),'-I',str(controller),'--worker-root',str(package),'--out',str(output)],cwd=package,env=env,stdout=stdout,stderr=stderr)
            dump(folder/'child_identity.json',dict(pid=child.pid,launched_at=datetime.now(timezone.utc).isoformat(),controller=str(controller)))
            while child.poll() is None:
                if time.monotonic()-clock>120 or (folder/'CANCEL').exists():raise TimeoutError('Bounded copied-notebook diagnostic stopped')
                time.sleep(.25)
            if child.returncode:failure='Worker exited '+str(child.returncode)
    except BaseException as error:failure=repr(error)
    finally:
        if child is not None and child.poll() is None:
            descendants=[]
            try:descendants=psutil.Process(child.pid).children(recursive=True)
            except psutil.Error as error:cleanup.append(dict(operation='enumerate_owned_children',error=repr(error)))
            for process in reversed(descendants):
                try:process.terminate();cleanup.append(dict(pid=process.pid,operation='terminate_owned_descendant'))
                except psutil.Error as error:cleanup.append(dict(pid=process.pid,error=repr(error)))
            child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:remaining.append(child.pid)
            for process in descendants:
                try:
                    if process.is_running():remaining.append(process.pid)
                except psutil.Error:pass
        if (output/'latest_phase.json').exists():dump(folder/'latest_phase.json',read(output/'latest_phase.json'))
        for name in ['phases.jsonl','stacks.txt','controller_audit.json','kernel_audit.json','worker_result.json']:
            if (output/name).exists():shutil.copyfile(output/name,folder/name)
        outcome=read(output/'worker_result.json') if (output/'worker_result.json').exists() else None
        result=dict(run_id=rid,started_at=started.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-clock,protocol_sha256=sha(folder/'protocol.json'),
            worker_result=outcome,failure=failure,returncode=None if child is None else child.returncode,remaining_owned_pids=remaining,cleanup=cleanup,
            diagnostic_notebook_passed=failure is None and outcome is not None,whole_package_promoted=False,model_training=False,learned_target_decoding=False)
        dump(folder/'run.json',result)
        registry=root/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Bounded copied notebook phase/stack diagnostic;no reinstall',started_at=result['started_at'],finished_at=result['finished_at'],source_ids=';'.join(protocol['source_ids']),split_ids='Existing TRAIN-image teaching notebook08 only',configuration=(folder/'protocol.json').relative_to(root).as_posix(),architecture='Fresh copied runtime,isolated temp/state,original audit guard',random_seed=148,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(result),logs=folder.relative_to(root).as_posix(),checkpoints='No model changes',code_revision_basis='d1d0b99 plus sealed diagnostic source',implementation_sha256=sha(__file__),conclusions='Diagnostic only;whole copied package not promoted;actual readiness requires separate acceptance')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        state['active_validation_jobs']=[dict(run_id=rid,remaining_owned_pids=remaining,phase='Cleanup requires confirmation')] if remaining else [];dump(state_path,state);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
