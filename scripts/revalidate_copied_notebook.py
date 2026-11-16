"""Revalidate frozen copied notebook with approved local loopback;keep failures."""
import csv,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):
    import hashlib
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    import psutil
    e=ROOT/'experiments/evidence/HEARTBEAT-20261026T183901Z';cleanup=read(e/'diagnostic_cleanup.json');assert cleanup['matching_count']==0
    s=read(ROOT/'data/automation_state.json');assert s['completed_recorded_runs_since_schedule']==85
    assert all(j['run_id']=='NOTEBOOK-DIAGNOSTIC-20261026T184229200431Z' for j in s['active_validation_jobs'])
    # Confirmation supersedes conservative pending-PID state;failure report stays unchanged.
    s['active_validation_jobs']=[];dump(ROOT/'data/automation_state.json',s)
    started=datetime.now(timezone.utc);rid='OFFLINE-NOTEBOOK-ACCEPTANCE-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/rid;folder.mkdir(exist_ok=False)
    package=(ROOT/'outputs/offline_demo_packages/COMBINED-DEMO-20261026T181455268229Z').resolve()
    prior=ROOT/'experiments/results/COMBINED-DEMO-20261026T181455268229Z/run.json'
    component=ROOT/'experiments/results/OFFLINE-TRANSACTIONS-20261026T183029251864Z/run.json'
    assert read(prior)['checks']==dict(install=dict(returncode=0),app=dict(returncode=0)) and read(component)['component_gate_passed']
    manifest=read(package/'BUNDLE_MANIFEST.json');assert all(sha(package/r['path'])==r['sha256'] for r in manifest['files'])
    inputs=[package/'BUNDLE_MANIFEST.json',package/'BUNDLE_SCOPE.json',package/'scripts/verify_offline_bundle.py',package/'scripts/package_offline_guard.py',package/'notebooks/08_image_patterns_and_svd.ipynb',package/'.venv/pyvenv.cfg',prior,component]
    protocol=dict(run_id=rid,prepared_at=started.isoformat(),seed=149,source_ids=['SRC-DS-001','SRC-PKG-004'],
        hypothesis='The frozen copied notebook verifier can complete with explicitly approved local loopback transport while retaining the original external-network/workspace-fallback guard and all frozen payload bytes.',
        execution_context='Requires exec_command require_escalated for authorized local loopback;nonloopback audit remains enabled',package=package.relative_to(ROOT).as_posix(),maximum_seconds=180,
        gates=['Existing451payload hashes unchanged','Prior107-package install/app/transaction/version acceptance records remain hash-bound','Frozen notebook verifier executes real copied kernel with inline PNG and no saved errors','Controller/kernel Python fallback and nonloopback denials zero','Original source notebook unchanged','No model/final/future-target evaluation'],
        input_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in inputs},source_hashes={'scripts/revalidate_copied_notebook.py':sha(__file__)},
        protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        original_failure_retained=True,new_install=False,model_calls=0,whole_package_promotion='Only after all composite gates pass;original failed report never overwritten')
    dump(folder/'protocol.json',protocol);dump(folder/'source_snapshot.json',dict(sha256=sha(__file__),source=Path(__file__).read_text(encoding='utf-8')));dump(folder/'protocol_binding.json',dict(sha256=sha(folder/'protocol.json')))
    moved=[]
    for relative in ['outputs/notebook_check','.notebook_state']:
        old=(package/relative).resolve();new=old.with_name(old.name+'_failed_'+rid)
        assert old.is_relative_to(package) and new.resolve().is_relative_to(package) and not new.exists()
        if old.exists():old.rename(new);moved.append(dict(original=old.relative_to(package).as_posix(),preserved_as=new.relative_to(package).as_posix()))
    dump(folder/'preserved_generated_paths.json',moved)
    temporary=package/'outputs/notebook_revalidation_temp'/rid;temporary.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if k.upper() not in {'PYTHONHOME','PYTHONPATH','PYTHONSTARTUP','TEMP','TMP','TMPDIR','JUPYTER_PATH','JUPYTER_RUNTIME_DIR','JUPYTER_CONFIG_DIR','IPYTHONDIR','MPLCONFIGDIR'}}
    env.update(TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    s=read(ROOT/'data/automation_state.json');s['active_validation_jobs']=[dict(run_id=rid,phase='Approved local-loopback frozen verifier',cancel_file=str(folder/'CANCEL'))];dump(ROOT/'data/automation_state.json',s)
    child=None;failure=None;remaining=[];cleanup_actions=[];clock=time.monotonic();notebook=None
    try:
        with (folder/'stdout.txt').open('w',encoding='utf-8') as stdout,(folder/'stderr.txt').open('w',encoding='utf-8') as stderr:
            command=[str(package/'.venv/Scripts/python.exe'),'-I',str(package/'scripts/verify_offline_bundle.py'),'notebook']
            child=subprocess.Popen(command,cwd=package,env=env,stdout=stdout,stderr=stderr);dump(folder/'child_identity.json',dict(pid=child.pid,command=command))
            while child.poll() is None:
                if time.monotonic()-clock>180 or (folder/'CANCEL').exists():raise TimeoutError('Bounded approved-loopback verification stopped')
                time.sleep(.25)
            assert child.returncode==0,'Frozen verifier exit '+str(child.returncode)
        notebook=read(package/'NOTEBOOK_VALIDATION.json');assert notebook['actual_kernel_executed'] and notebook['inline_png_outputs']>=1 and not notebook['kernel_audit']['denied']
        controller=read(package/'outputs/notebook_check/controller_audit.json');assert not controller['denied']
        assert all(sha(package/r['path'])==r['sha256'] for r in manifest['files'])
        assert all(sha(ROOT/p)==h for p,h in {**protocol['input_hashes'],**protocol['protected_hashes']}.items())
    except BaseException as error:failure=repr(error)
    finally:
        if child is not None and child.poll() is None:
            owned=[]
            try:owned=psutil.Process(child.pid).children(recursive=True)
            except psutil.Error as error:cleanup_actions.append(dict(error=repr(error)));remaining.append('Unknown descendants require confirmation')
            for process in reversed(owned):
                try:process.terminate();cleanup_actions.append(dict(pid=process.pid,action='terminate_owned_child'))
                except psutil.Error as error:cleanup_actions.append(dict(pid=process.pid,error=repr(error)))
            child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:remaining.append(child.pid)
            alive=psutil.wait_procs(owned,timeout=10)[1]
            remaining.extend(p.pid for p in alive)
        accepted=failure is None and notebook is not None and not remaining
        result=dict(run_id=rid,started_at=started.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-clock,protocol_sha256=sha(folder/'protocol.json'),
            corrected_context_notebook_gate_passed=accepted,composite_software_gate_passed=accepted,notebook_validation=notebook,failure=failure,remaining_owned_pids=remaining,cleanup=cleanup_actions,
            prior_failed_report='experiments/results/COMBINED-DEMO-20261026T181455268229Z/run.json',prior_component='experiments/results/OFFLINE-TRANSACTIONS-20261026T183029251864Z/run.json',
            original_payload_unchanged=True,new_install=False,model_calls=0,scientific_accuracy_evaluated=False,physical_or_newmachine_or_manual_acceptance=False)
        dump(folder/'run.json',result)
        if notebook is not None:dump(folder/'NOTEBOOK_VALIDATION.json',notebook)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Frozen copied notebook acceptance in approved local-loopback context',started_at=result['started_at'],finished_at=result['finished_at'],source_ids=';'.join(protocol['source_ids']),split_ids='Existing TRAIN-image notebook08 only',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Unchanged copied verifier/kernel;local TEMP and approved loopback;original audit guard',random_seed=149,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(result),logs=folder.relative_to(ROOT).as_posix(),checkpoints='No model changes',code_revision_basis='d1d0b99 plus sealed context acceptance controller',implementation_sha256=sha(__file__),conclusions='Context acceptance='+str(accepted)+';original failure preserved;not physical/manual/newmachine or scientific accuracy')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(ROOT/'data/automation_state.json');s['completed_run_ids'].append(rid);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=rid;s['active_validation_jobs']=[dict(run_id=rid,remaining_owned_pids=remaining)] if remaining else [];dump(ROOT/'data/automation_state.json',s)
        dump(ROOT/'experiments/evidence/HEARTBEAT-20261026T183901Z/acceptance_run_pointer.json',dict(run_id=rid,report=(folder/'run.json').relative_to(ROOT).as_posix()))
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()
