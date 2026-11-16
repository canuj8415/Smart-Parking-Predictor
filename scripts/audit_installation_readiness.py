"""Bounded clean-venv startup/offline-wheel audit; never modifies shared Python."""
import csv,hashlib,json,os,platform,subprocess,sys,time,venv
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def child(mode,folder):
    # Executed by the clean venv with -I. No shared site packages are admitted.
    import runpy
    attempts=[];imports=[]
    def audit(event,args):
        if event in {'socket.connect','socket.getaddrinfo'}:
            attempts.append(event);raise PermissionError('Network disabled by readiness probe')
        if event=='import' and args and args[0] in {'smart_parking.app','torch','torchvision','numpy'}:imports.append(args[0])
    sys.addaudithook(audit)
    try:
        if mode=='baseline':
            source=json.loads((folder/'baseline_launcher.json').read_text(encoding='utf-8'))['source']
            sys.argv=[str(ROOT/'run_app.py')]
            exec(compile(source,'prior-launcher','exec'),{'__name__':'__main__','__file__':str(ROOT/'run_app.py')})
        elif mode in {'check','launch'}:
            sys.argv=[str(ROOT/'run_app.py')]+(['--check-environment'] if mode=='check' else [])
            runpy.run_path(str(ROOT/'run_app.py'),run_name='__main__')
        elif mode=='pip':
            sys.argv=['pip','install','--dry-run','--no-index','--disable-pip-version-check',
                      '--find-links',str(ROOT/'dependencies/wheels'),'-r',str(ROOT/'requirements-app.txt')]
            runpy.run_module('pip',run_name='__main__')
        else:raise ValueError('Unknown probe')
    finally:
        dump(folder/(mode+'_audit.json'),dict(mode=mode,prefix=sys.prefix,base_prefix=sys.base_prefix,
            clean_venv=sys.prefix!=sys.base_prefix,network_attempts=attempts,heavy_import_attempts=imports,
            gui_started=False,models_loaded=False,scope='Existing base interpreter; clean venv/no system site-packages,not a new computer'))


def main():
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        child(sys.argv[2],Path(sys.argv[3]));return
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another job is active')
    started=datetime.now(timezone.utc);run='INSTALL-READINESS-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    fresh=ROOT/'outputs/installation_checks'/run/'venv'
    if not fresh.resolve().is_relative_to((ROOT/'outputs/installation_checks').resolve()):raise ValueError('Invalid fresh environment target')
    baseline=subprocess.check_output(['git','show','f0e6c93:run_app.py'],cwd=ROOT).decode('utf-8')
    files=['scripts/audit_installation_readiness.py','run_app.py','src/smart_parking/environment.py','tests/test_environment.py','requirements-app.txt']
    hashes={path:digest(ROOT/path) for path in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),seed=119,source_ids=['SRC-PKG-001'],
        hypothesis='On a clean venv with missing app packages, the new launcher reports a bounded setup failure before heavy imports,while the old launcher exposes a traceback;offline install acceptance must fail honestly when only the decoder wheel is available.',
        source_hashes=hashes,baseline_revision='f0e6c93',baseline_sha256=hashlib.sha256(baseline.encode()).hexdigest(),
        wheelhouse='dependencies/wheels',fresh_environment=str(fresh.relative_to(ROOT)),
        gates=['No system site-packages in fresh venv','Prior launcher raises dependency traceback',
               'New check and normal launcher exit2 with meaningful missing-component guidance before heavy imports',
               'Zero network attempts in every isolated child','Offline pip dry-run fails due missing torch wheel; no installation success claim'],
        model_training_performed=False,model_accuracy_evaluated=False,
        limitations=['Base Python interpreter reused; fresh virtual environment only','Offline dry-run is not a successful install',
                     'No fresh-machine/physical-network/native-visible acceptance'])
    dump(folder/'protocol.json',protocol);dump(folder/'baseline_launcher.json',dict(source=baseline,sha256=protocol['baseline_sha256']))
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        fresh.parent.mkdir(parents=True,exist_ok=True)
        # ensurepip uses the standard-library bundled wheels, without an index.
        venv.EnvBuilder(with_pip=True,system_site_packages=False).create(fresh)
        python=fresh/'Scripts/python.exe';assert python.is_file()
        assert 'include-system-site-packages = false' in (fresh/'pyvenv.cfg').read_text(encoding='utf-8')
        environment=os.environ.copy();environment.update(PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_CONFIG_FILE=os.devnull)
        checks={}
        for mode in ['baseline','check','launch','pip']:
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
            with (folder/(mode+'_stdout.txt')).open('w',encoding='utf-8') as out,(folder/(mode+'_stderr.txt')).open('w',encoding='utf-8') as err:
                completed=subprocess.run([str(python),'-I',str(Path(__file__).resolve()),'--child',mode,str(folder)],
                    cwd=ROOT,env=environment,stdout=out,stderr=err,timeout=90)
            checks[mode]=dict(returncode=completed.returncode,audit=json.loads((folder/(mode+'_audit.json')).read_text(encoding='utf-8')))
            assert checks[mode]['audit']['clean_venv'] and not checks[mode]['audit']['network_attempts']
        old_error=(folder/'baseline_stderr.txt').read_text(encoding='utf-8');new_error=(folder/'launch_stderr.txt').read_text(encoding='utf-8')
        assert checks['baseline']['returncode']!=0 and 'ModuleNotFoundError' in old_error
        assert checks['check']['returncode']==checks['launch']['returncode']==2
        report=json.loads((folder/'check_stdout.txt').read_text(encoding='utf-8'))
        assert 'torch' in report['missing_required'] and not report['prerequisites_found']
        assert not checks['check']['audit']['heavy_import_attempts'] and not checks['launch']['audit']['heavy_import_attempts']
        assert 'Missing components:' in new_error and 'Traceback' not in new_error
        assert checks['pip']['returncode']!=0
        pip_log=(folder/'pip_stdout.txt').read_text(encoding='utf-8')+(folder/'pip_stderr.txt').read_text(encoding='utf-8')
        assert 'torch' in pip_log and 'No matching distribution' in pip_log
        wheels=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in (ROOT/'dependencies/wheels').glob('*.whl')]
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        result=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            checks=checks,missing_components=report['missing_required'],available_local_wheels=wheels,
            launcher_diagnostic_gate_passed=True,offline_installation_gate_passed=False,
            missing_artifact='No matching torch==2.14.0 wheel in the selected offline wheelhouse',
            packages_installed_in_shared_environment=False,models_loaded=False,new_weights=False)
        dump(folder/'run.json',result)
        sys.path.insert(0,str(ROOT/'src'));dump(ROOT/'models/installation_readiness.json',result)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run,run_type='Clean-venv launcher negative control/offline installation readiness',
            started_at=protocol['started_at'],finished_at=result['finished_at'],source_ids='SRC-PKG-001',split_ids='Fresh empty virtual environment; no image/final data',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Standard-library dependency preflight and isolated Python/pip dry-run',
            model_version='No model',epochs=0,batch_size='not applicable',random_seed=119,hardware=platform.platform(),execution_environment=sys.version.split()[0],
            training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(dict(launcher_diagnostic_gate_passed=True,offline_installation_gate_passed=False,network_attempts=0)),
            logs=folder.relative_to(ROOT).as_posix(),checkpoints='No new weights',code_revision_basis='f0e6c93 plus sealed source snapshots',implementation_sha256=hashes[files[0]],
            conclusions='New launcher fails clearly before heavy imports in clean venv; only decoder wheel available, offline install gate FAILS; no new-machine/full-offline acceptance')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,launcher_diagnostic_gate_passed=True,offline_installation_gate_passed=False,missing=report['missing_required']),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False,fresh_environment_preserved=str(fresh)))
        state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
