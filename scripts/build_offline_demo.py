"""Build one immutable selected-demo+107-wheel payload and validate a fresh copy."""
import csv,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.demo_snapshot import select_snapshot
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
    state_path=ROOT/'data/automation_state.json';state=read(state_path)
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another job is active')
    started=datetime.now(timezone.utc);run='COMBINED-DEMO-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;package=ROOT/'outputs/offline_demo_packages'/run
    folder.mkdir(parents=True,exist_ok=False);package.mkdir(parents=True,exist_ok=False)
    previous=read('reports/demo_package_latest.json');prior_manifest=read(Path(previous['path'])/'BUNDLE_MANIFEST.json')
    assert sha(ROOT/previous['path']/'BUNDLE_MANIFEST.json')==previous['manifest_sha256']
    acceptance_contract=read('data/manifests/copied_package_acceptance_v1.json')
    assert acceptance_contract['previous_pointer_sha256']==sha(ROOT/'reports/demo_package_latest.json')
    assert acceptance_contract['vision_sha256']==sha(ROOT/'src/smart_parking/vision.py')
    assert acceptance_contract['occupancy_patch_sha256']==sha(ROOT/'src/smart_parking/occupancy_patches.py')
    prior_scope=read(Path(previous['path'])/'BUNDLE_SCOPE.json')
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    reservation=read('data/manifests/singapore_forecast_reservation_v1.json')
    snapshot=select_snapshot(ROOT,prior_manifest,prior_scope,reservation,receipts)
    saved_live_relative=snapshot['path'];saved_live=ROOT/saved_live_relative
    plan={}
    def add(relative,role='Updated selected demonstration payload',source='PROJECT'):
        p=(ROOT/relative).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file():raise FileNotFoundError(str(relative))
        key=p.relative_to(ROOT).as_posix();plan[key]=dict(path=key,role=role,source_id=source,bytes=p.stat().st_size,sha256=sha(p))
    for row in prior_manifest['files']:
        # Only the selected newest snapshot goes into this NEW copy. Older
        # snapshots and existing package bytes remain intact in their folders.
        if row['path'].startswith('data/raw/singapore_live/'):continue
        add(row['path'],row['role'],row['source_id'])
    add(saved_live_relative,'Saved official snapshot; provider time and staleness retained','SRC-LIVE-001')
    for p in (ROOT/'src/smart_parking').glob('*.py'):add(p.relative_to(ROOT),'Current Python product source')
    for name in ['setup_offline_bundle.py','verify_offline_bundle.py','verify_refreshed_package.py','package_offline_guard.py','start_jupyter.py','execute_notebook.py','offline_jupyter_guard.py']:
        add('scripts/'+name,'Offline copied-folder installation/notebook support')
    for p in ['README.md','docs/OFFLINE_APP_SETUP.md','docs/OFFLINE_JUPYTER_SETUP.md','docs/DEMO_PACKAGE_GUIDE.md','docs/FORECAST_REPORTS_GUIDE.md']:
        add(p,'Project-wide context guide; copied START_HERE gives package-specific commands')
    for p in ['docs/RESULT_EXPORTS_GUIDE.md','tests/__init__.py','tests/test_export_transactions.py']:
        add(p,'Transactional export guide/synthetic fault tests;not scientific evaluation')
    add('data/manifests/copied_package_acceptance_v1.json','Frozen current source/count/install acceptance contract')
    for p in ['docs/OCCUPANCY_MEMORY_GUIDE.md','models/occupancy_patch_validation.json','models/assignment_api_validation.json']:
        add(p,'Historical memory/API qualification context;full referenced TRAIN assets are not included')
    for relative,sid in [('dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json','SRC-PKG-003'),('dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json','SRC-PKG-004')]:
        manifest=read(relative);add(relative,'Publisher-hash and embedded licence/notice manifest',sid);add(manifest['lock_path'],'Original hash-locked requirements',sid)
        for e in manifest['entries']:
            assert sha(ROOT/e['path'])==e['sha256'];add(e['path'],'Original offline installer with full embedded notices',sid)
            add(e['metadata_path'],'Original official release metadata','SRC-PKG-002' if sid=='SRC-PKG-003' else sid)
    for p in (ROOT/'data/research').glob('SRC-DOC-0*_jupyter_reference_20261025.json'):add(p.relative_to(ROOT),'Authored official documentation consultation notes',p.name.split('_')[0])
    size=sum(e['bytes'] for e in plan.values())
    if size>1024**3:raise ValueError('Selected payload exceeds1GiBbound')
    if shutil.disk_usage(package).free<size+3*1024**3:raise RuntimeError('Reserve payload+3GiBfor new environment/checks')
    selected_notebooks=sorted(p for p in plan if p.startswith('notebooks/') and p.endswith('.ipynb'))
    project_notebooks=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'notebooks').glob('*.ipynb'))
    excluded_notebooks=sorted(set(project_notebooks)-set(selected_notebooks))
    paths=['scripts/build_offline_demo.py','scripts/setup_offline_bundle.py','scripts/verify_offline_bundle.py','scripts/package_offline_guard.py',
        'scripts/verify_relocated_demo.py','scripts/start_jupyter.py','scripts/execute_notebook.py','src/smart_parking/app.py',
        'src/smart_parking/vision.py','src/smart_parking/forecast_reports.py','src/smart_parking/exports.py',
        'src/smart_parking/demo_snapshot.py','src/smart_parking/occupancy_patches.py','src/smart_parking/package_acceptance.py',
        'scripts/verify_refreshed_package.py','data/manifests/copied_package_acceptance_v1.json',
        'scripts/verify_offline_bundle.py','tests/test_demo_snapshot.py','tests/test_export_transactions.py','tests/test_package_acceptance.py']
    hashes={p:sha(ROOT/p) for p in paths}
    protected=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    protected.update(read('experiments/evidence/HEARTBEAT-20261027T040910Z/checks.json')['frozen_hashes_unchanged'])
    for group in ['holdout_claims','forecast_holdout_claims','sequence_holdout_claims']:
        protected.update({p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'data'/group).rglob('*.json')})
    scope=prior_scope
    scope.update(created_at=started.isoformat(),scope=f'Selected local academic app+notebook demonstration with107offline wheels;existing base Python/OS required. Full datasets and{len(excluded_notebooks)}other notebooks absent.',
        previous_demo=previous['run_id'],installer_wheels=107,external_distribution_authorized=False,
        project_notebooks_at_build=len(project_notebooks),selected_notebooks=selected_notebooks,excluded_notebooks=excluded_notebooks,
        cached_live_snapshot=saved_live_relative,cached_live_sha256=sha(saved_live),cached_live_provider_timestamp=snapshot['provider_timestamp'],
        cached_live_selection=snapshot,transactional_exports_included=True,export_implementation_sha256=sha(ROOT/'src/smart_parking/exports.py'),
        bounded_assignment_included=True,occupancy_patch_sha256=acceptance_contract['occupancy_patch_sha256'])
    protocol=dict(run_id=run,started_at=started.isoformat(),seed=165,source_ids=['SRC-DS-001','SRC-DS-003','SRC-LIVE-001','SRC-VID-001','SRC-MOD-001','SRC-MOD-002','SRC-MOD-003','SRC-PKG-001','SRC-PKG-002','SRC-PKG-003','SRC-PKG-004'],
        hypothesis='The refreshed copied demo includes bounded assignment,current source/assets/notices and107hash-locked wheels,installs a new package-local environment offline,and preserves fixed TRAIN app counts and actual Jupyter execution without original-workspace fallback.',
        package=package.relative_to(ROOT).as_posix(),payload=list(plan.values()),payload_bytes=size,payload_files=len(plan),source_hashes=hashes,protected_hashes=protected,
        code_revision_basis='404d3ba plus sealed bounded-assignment/current-copy acceptance sources',previous_demo=previous['run_id'],
        selected_notebooks=selected_notebooks,excluded_notebooks=excluded_notebooks,
        cached_live_snapshot=saved_live_relative,cached_live_sha256=sha(saved_live),cached_live_provider_timestamp=snapshot['provider_timestamp'],
        cached_live_selection=snapshot,maximum_wall_seconds=1080,
        gates=['All copied original payload bytes match','Fresh package-local107-package install using no-index/hash-lock','Both detector/export/cached-live/archived forecast/SVD/video routes pass',
            'Both forecast variants keep correct method labels and actual PNG/CSV/JSON export identities;selection changes invalidate old snapshots',
            'Actual copied-folder Jupyter kernel executes notebook08with inline plot','Python original-workspace fallback/non-loopback access denied','Payload hashes unchanged after checks',
            'Thirteen synthetic transaction/failure cases pass inside newly installed copied environment','Copied cached feed snapshot receipt/provider strictly predate reserved forecasting period',
            'Current bounded assignment import and fixed TRAIN image/model/count identities preserved;all107versions match;existing venv overwrite refused;separate fallback/DNS controls denied'],
        limitations=['Existing base Windows/Python/Tk reused; no new-machine/physical-disconnection claim','Hidden native windows/mocked dialogs;no visible browser/manual/student acceptance',
            'Only training image/already-seen licensed video/archived forecasts;no model accuracy or final-data replay','Python audit layer does not isolate native extension IO',
            f'Selected local academic demo; full datasets/{len(excluded_notebooks)}other notebooks and external redistribution clearance absent'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    dump(package/'BUNDLE_SCOPE.json',scope)
    (package/'INCOMPLETE').write_text('Do not use until READY.json exists and all stated checks pass.\n',encoding='utf-8')
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    clock=time.perf_counter();checks={};failure=None;cancelled=False
    try:
        for index,row in enumerate(plan.values()):
            if (folder/'CANCEL').exists():raise InterruptedError('Copy cancellation requested')
            target=package/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/row['path'],target)
            if sha(target)!=row['sha256']:raise ValueError('Copied payload hash mismatch:'+row['path'])
            if index%40==0:dump(folder/'progress.json',dict(phase='copy',copied=index+1,total=len(plan)))
        manifest=dict(schema_version=1,run_id=run,created_at=started.isoformat(),files=list(plan.values()),
            installed_runtime_in_payload=False,python_base_included=False,installer_wheels=107,all_original_notices_retained=True)
        dump(package/'BUNDLE_MANIFEST.json',manifest);dump(folder/'bundle_manifest.json',manifest)
        guide='''# Start this copied Smart Parking demo

This folder combines selected app/notebook data, saved models, a saved live
snapshot and all107original app+Jupyter installer wheels. The original project,
failed studies and earlier packages were preserved. This is a local academic
demonstration,not a published or complete-training-data distribution.

Use an existing64-bit Windows Python3.12 from a compatible installation. In
PowerShell opened in THIS copied folder, run:

```powershell
python scripts/setup_offline_bundle.py
& '.\\.venv\\Scripts\\python.exe' run_app.py
& '.\\.venv\\Scripts\\python.exe' scripts/start_jupyter.py --offline --notebook '08_image_patterns_and_svd.ipynb'
```

Setup creates a NEW `.venv` and uses only included wheels with exact SHA256
hashes and --no-index. It refuses to overwrite an existing environment. If the
verified `.venv` is already present,skip setup and use the two launch commands.
For a deliberate rebuild,choose another new package-local destination with
`--destination .venv_rebuild`. No system Python,existing project environment,
network settings or unrelated apps are changed. Windows/base Python/Tk itself
is not included;this is not a new-machine/physical-offline demonstration.

The app's Load real sample uses one explicitly recorded TRAINING image of100
spaces. Try both detectors,exports,separate learned-region preview,archived
forecast views,saved live snapshot,2D/3D laboratory and image-pattern lesson.
These are software demonstrations,not new independent accuracy tests. Saved
live readings retain their timestamp/staleness;3Duses a labelled teaching volume.

Only notebook08and its training image are included. The other7notebooks and full
training datasets are absent. README/docs/source register describe the wider
project;only BUNDLE_MANIFEST.json lists this selected payload. Source URLs,
creator/licence records,publisher hashes and original embedded notices remain
with the installers. Do not treat local use as external redistribution clearance.

READY.json and COMBINED_VALIDATION.json describe the actual copied-folder
checks. A local environment was newly installed; actual hidden app routes and a
genuine Jupyter kernel were tested. Visible dialogs/browser rehearsal,physical
disconnection,new machine,student explanation and official university acceptance
remain separate. None of this proves universal100%accuracy.
'''
        guide=guide.replace('The other7notebooks',f'The other{len(excluded_notebooks)}notebooks')
        guide += ('\n## Forecast results in this copy\n\nChoose Original experiment or Later-date check, then Show held-out forecast. '
            'The legend identifies Original LSTM or Group-relative residual LSTM. Save forecast results writes the displayed PNG,CSV,reportJSON and checksum metadata. '
            'These are archived Birmingham reports,not new live forecasts. See docs/FORECAST_REPORTS_GUIDE.md.\n\n'
            f'The cached Singapore snapshot is {saved_live_relative}, provider time {scope["cached_live_provider_timestamp"]}. '
            'It stays saved/cached and may be stale when opened;no camera accuracy follows from it.\n')
        guide += ('\nThis refreshed copy includes complete-directory result publishing and payload checksums. '
            'Handled save failures preserve earlier exports;see docs/RESULT_EXPORTS_GUIDE.md. '
            'The cached feed is intentionally an older pre-reservation snapshot;no pending learned forecast targets are packaged. '
            'EXPORT_TRANSACTION_VALIDATION.json records thirteen synthetic fault/integrity checks in this copied environment.\n')
        guide += ('\nThe current bounded occupancy assignment is included. Original model weights and parking decision thresholds are unchanged. '
            'CURRENT_ACCEPTANCE_VALIDATION.json records copied source imports, original training-example counts,107 locked package versions and scoped fallback/DNS probes. '
            'Memory measurements in docs/OCCUPANCY_MEMORY_GUIDE.md refer to their dated software fixture,not a universal camera or model bound.\n')
        (package/'START_HERE.md').write_text(guide,encoding='utf-8')
        env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
        local_temp=package/'outputs/runtime_tmp';local_temp.mkdir(parents=True,exist_ok=False)
        env.update(TEMP=str(local_temp),TMP=str(local_temp))
        fresh=package/'.venv/Scripts/python.exe'
        commands=[('install',[sys.executable,'-I',str(package/'scripts/setup_offline_bundle.py')],720),
            ('app',[str(fresh),'-I',str(package/'scripts/verify_offline_bundle.py'),'app'],360),
            ('notebook',[str(fresh),'-I',str(package/'scripts/verify_offline_bundle.py'),'notebook'],240),
            ('transactions',[str(fresh),'-I',str(package/'scripts/verify_offline_bundle.py'),'transactions'],90),
            ('current_acceptance',[str(fresh),'-I',str(package/'scripts/verify_refreshed_package.py')],180)]
        for name,command,limit in commands:
            dump(folder/'progress.json',dict(phase=name,copied=len(plan),total=len(plan)))
            with (folder/(name+'_stdout.txt')).open('w',encoding='utf-8') as out,(folder/(name+'_stderr.txt')).open('w',encoding='utf-8') as err:
                child=subprocess.Popen(command,cwd=package,env=env,stdout=out,stderr=err);deadline=time.monotonic()+min(limit,max(0,1080-(time.perf_counter()-clock)))
                while child.poll() is None:
                    if time.monotonic()>deadline or (folder/'CANCEL').exists():
                        subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=20);child.wait(timeout=20)
                        raise InterruptedError('Cancelled/timed-out owned copied-demo process tree')
                    time.sleep(.3)
            checks[name]=dict(returncode=child.returncode)
            dump(folder/'progress.json',dict(phase=name,checks=checks))
            if child.returncode:raise RuntimeError(name+'check failed;logs and partial copy preserved')
        assert all(sha(package/p)==r['sha256'] for p,r in plan.items())
        assert all(sha(ROOT/p)==h for p,h in {**hashes,**protected}.items())
    except (InterruptedError,KeyboardInterrupt) as error:failure=str(error);cancelled=True
    except Exception as error:failure=type(error).__name__+': '+str(error)
    finally:
        accepted=failure is None and len(checks)==5 and all(c['returncode']==0 for c in checks.values())
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,checks=checks,failure=failure,
            combined_demo_gate_passed=accepted,fresh_package_environment=str(package/'.venv'),model_training_performed=False,scientific_accuracy_evaluated=False,
            cancelled=cancelled,original_assets_and_claims_unchanged=all(sha(ROOT/p)==h for p,h in protected.items()))
        for key,path in [('offline_environment','OFFLINE_ENVIRONMENT.json'),('app_validation','VALIDATION_REPORT.json'),('notebook_validation','NOTEBOOK_VALIDATION.json'),('transaction_validation','EXPORT_TRANSACTION_VALIDATION.json'),('current_acceptance','CURRENT_ACCEPTANCE_VALIDATION.json')]:
            if (package/path).exists():report[key]=read(package/path);shutil.copyfile(package/path,folder/path)
        dump(folder/'run.json',report);dump(package/'COMBINED_VALIDATION.json',report)
        if accepted:
            (package/'INCOMPLETE').unlink();dump(package/'READY.json',dict(run_id=run,gate_passed=True,report_sha256=sha(package/'COMBINED_VALIDATION.json'),
                scope='Fresh copied-folder selected demo only;remaining manual/physical/academic gates separate'))
        state=read(state_path);state['active_validation_jobs']=[]
        if not cancelled:
            registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
            with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
            row=dict(experiment_id=run,run_type='Combined copied offline installer/demo validation',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids=';'.join(protocol['source_ids']),
                split_ids='Training-only image/already-seen street clip/archived forecast outputs;no raw final data',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Fresh package-local107-package venv plus frozen product',
                epochs=0,batch_size=1,random_seed=165,hardware='CPU; Windows;base Python reused',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],
                evaluation_metrics=json.dumps(dict(combined_demo_gate_passed=accepted,checks=checks,failure=failure)),logs=folder.relative_to(ROOT).as_posix(),checkpoints='Original weights unchanged',
                code_revision_basis=protocol['code_revision_basis'],implementation_sha256=hashes[paths[0]],conclusions='Copied offline gate='+str(accepted)+';no scientific accuracy,physical,new-machine,visible/manual or official completion claim')
            with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
            state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        dump(state_path,state);print(json.dumps(dict(run_id=run,package=str(package),payload_files=len(plan),payload_bytes=size,gate_passed=accepted,failure=failure),indent=2))
if __name__=='__main__':main()
