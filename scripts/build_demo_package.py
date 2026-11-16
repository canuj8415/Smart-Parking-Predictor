"""Create and verify one bounded relocated local-demo bundle, preserving originals."""
import csv,hashlib,importlib.metadata,json,os,platform,shutil,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.demo_assets import load_demo_assets,inside


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another recorded job active')
    started=datetime.now(timezone.utc);run_id='DEMO-BUNDLE-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    result_dir=ROOT/'experiments/results'/run_id;result_dir.mkdir(parents=True,exist_ok=False)
    package=(ROOT/'outputs/demo_packages'/run_id).resolve()
    if not package.is_relative_to((ROOT/'outputs/demo_packages').resolve()):raise ValueError('Invalid local package target')
    package.mkdir(parents=True,exist_ok=False)
    demo,_,_=load_demo_assets()
    gate=json.loads((ROOT/'experiments/results/GATE-VIDEO-20261024T231251838602Z/protocol.json').read_text(encoding='utf-8'))
    live=sorted((ROOT/'data/raw/singapore_live').glob('*.json'))[-1]
    plan={}
    def add(relative,role,source_id='PROJECT'):
        p=inside(ROOT,relative)
        if not p.is_file():raise FileNotFoundError(relative)
        plan[Path(relative).as_posix()]=dict(path=Path(relative).as_posix(),role=role,source_id=source_id,bytes=p.stat().st_size,sha256=digest(p))
    def tree(relative,role,source_id='PROJECT',python_only=False):
        for p in (ROOT/relative).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and (not python_only or p.suffix=='.py'):
                add(p.relative_to(ROOT).as_posix(),role,source_id)
    tree('src/smart_parking','Python product',python_only=True)
    tree('dependencies/python','Windows project-local video decoder','SRC-PKG-001')
    for p in ['run_app.py','launch_parking.cmd','requirements-app.txt','requirements-notebooks.txt','configs/demo_sample.json','scripts/verify_relocated_demo.py']:
        add(p,'Local demo launcher/configuration')
    add(demo['image'],'Original training-split demonstration image','SRC-DS-001');add(demo['layout'],'Geometry-only layout','SRC-DS-001')
    for name in ['fasterrcnn_resnet50_fpn_v2','maskrcnn_resnet50_fpn']:add('models/pretrained/'+name+'.pth','Frozen pretrained detector','SRC-MOD-001' if name.startswith('faster') else 'SRC-MOD-002')
    for name in ['occupancy_resnet18.pt','parking_unet.pt','lstm_30min.pt']:add('models/checkpoints/'+name,'Original project checkpoint')
    for name in ['vision_model_card.json','segmentation_model_card.json','lstm_30min_model_card.json','forecast_final_evaluation.json','davis_sequence_final.json','svd_lesson_validation.json']:
        add('models/'+name,'Archived model/result card')
    for name in ['lstm_30min_model_card.json','forecast_final_evaluation.json']:
        card=json.loads((ROOT/'models'/name).read_text(encoding='utf-8'))
        for p in ['run.json','test_predictions.json']:add('experiments/results/'+card['run_id']+'/'+p,'Archived forecast display only','SRC-DS-003')
    add(live.relative_to(ROOT).as_posix(),'Saved official availability snapshot','SRC-LIVE-001')
    add(gate['source_attribution']['local_path'],'Already-seen licensed street clip','SRC-VID-001')
    for p in ['data/source_manifest.csv','data/resource_receipts.jsonl','data/dataset_inventory.json']:add(p,'Original project-wide provenance')
    for p in ['docs/USER_GUIDE.md','docs/LICENSING_RECORD.md','docs/THIRD_PARTY_SOURCES.md','docs/MODEL_PROVENANCE.md',
              'docs/DATASET_PROVENANCE.md','docs/IMPLEMENTATION_STATUS.md','docs/EXCEL_PROGRESS_GUIDE.md','docs/IMAGE_COMPRESSION_LESSON.md','docs/INSTALLATION_READINESS.md']:
        add(p,'Project guide and attribution')
    add('notebooks/08_image_patterns_and_svd.ipynb','Executed training-image teaching notebook','SRC-DS-001')
    add('scripts/execute_notebook.py','Optional local Jupyter lesson executor')
    tree('docs/source_evidence','Inspected source statements')
    pointer=json.loads((ROOT/'reports/progress/latest.json').read_text(encoding='utf-8'));add('reports/progress/latest.json','Dated progress pointer')
    tree(Path(pointer['path']).parent.as_posix(),'Frozen progress inputs and results')
    add('outputs/01a16cf3-1f03-7631-8fac-d3d382c5b25c/smart_parking_progress_20261025.xlsx','Dated report')
    paths=['scripts/build_demo_package.py','scripts/verify_relocated_demo.py','src/smart_parking/demo_assets.py','src/smart_parking/app.py','src/smart_parking/vision.py','src/smart_parking/flow.py','src/smart_parking/video.py','src/smart_parking/live.py','src/smart_parking/decomposition.py']
    hashes={p:digest(ROOT/p) for p in paths}
    protocol=dict(run_id=run_id,started_at=started.isoformat(),seed=118,source_ids=['SRC-DS-001','SRC-DS-003','SRC-LIVE-001','SRC-VID-001','SRC-MOD-001','SRC-MOD-002','SRC-PKG-001','SRC-DOC-018'],
        hypothesis='The updated copied demo retains detector/export/forecast/video behavior while new SVD lesson, packaged notebook and strict live-input routes work without original-workspace fallback or implicit Python networking.',
        package=package.relative_to(ROOT).as_posix(),source_hashes=hashes,code_revision_basis='c0028cd plus exact sealed packaging/demo source snapshots',
        assets=list(plan.values()),total_bytes=sum(r['bytes'] for r in plan.values()),training_demo=demo,
        gates=['All copied asset hashes match','Package-local Python modules/assets used; original workspace fallback blocked',
               'Both actual detector routes and matched exports on training image','Semantic preview separate from analysis',
               'Both archived forecast views/cached live/lab/progress work','Two bounded local video samples',
               'Actual SVD app rank switching and packaged notebook computation pass','Synthetic malformed/conflicting feed inputs fail; duplicate input collapses',
               'No normal Python network attempts; explicit block probe fails','All asset hashes unchanged after validation','No invalid-command Tk teardown warning'],
        limitations=['Software integration only, no model accuracy or new final data','Installed Python runtime reused; no fresh offline installation',
            'Windows-specific copied video decoder; no cross-platform claim','Hidden native widgets/mocked dialogs; no physical disconnection or visible acceptance',
            'Project-wide source records describe more data than this selected bundle contains; originals not moved or deleted'])
    dump(result_dir/'protocol.json',protocol);dump(result_dir/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    dump(package/'BUNDLE_SCOPE.json',dict(original_project_root=str(ROOT),created_at=started.isoformat(),scope='Selected local runtime demo, not the full training dataset/runtime distribution',
        training_demo=demo,video=gate['source_attribution'],video_gate=gate['gate_config']))
    (package/'INCOMPLETE').write_text('Do not use until asset copy and validation are completed.\n',encoding='utf-8')
    state['active_validation_jobs']=[dict(run_id=run_id,cancel_file=str(result_dir/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        if shutil.disk_usage(package.parent).free<protocol['total_bytes']*1.2:raise RuntimeError('Insufficient free space for bounded local demo copy')
        for i,row in enumerate(plan.values()):
            if (result_dir/'CANCEL').exists():raise InterruptedError('Package cancellation requested')
            source=ROOT/row['path'];target=package/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            if digest(target)!=row['sha256']:raise ValueError('Copied bytes differ: '+row['path'])
            if i%50==0:dump(result_dir/'progress.json',dict(copied=i+1,total=len(plan)))
        dump(result_dir/'progress.json',dict(copied=len(plan),total=len(plan),phase='validating'))
        runtime={name:importlib.metadata.version(name) for name in ['torch','torchvision','numpy','Pillow','matplotlib']}
        dump(package/'BUNDLE_MANIFEST.json',dict(schema_version=1,run_id=run_id,created_at=started.isoformat(),files=list(plan.values()),
            runtime=dict(python=sys.version,platform=platform.platform(),observed_distribution_versions=runtime,redistributed_python_runtime=False)))
        (package/'START_HERE.md').write_text('''# Smart Parking local demo

This folder contains selected local data, original model weights, the Python app,
the Windows video decoder and archived results. Original project files were not
moved. The source registry describes the wider project; only files listed in
BUNDLE_MANIFEST.json are included here. Full training data and the Python runtime
are not included. This is a local academic demo, not a published distribution.

Use an installed Python environment with requirements-app.txt. Set the optional
SMART_PARKING_PYTHON variable to its python.exe, then run launch_parking.cmd, or
run python run_app.py directly. No automatic installation/download occurs.
The test reuses the originating machine's Python environment; a new computer or
fresh offline installation needs separately prepared compatible dependencies.

Load real sample uses a hash-bound training example, not a final holdout. It
demonstrates software behavior and does not measure independent accuracy.
Layouts contain geometry only. Try both detectors, save results, then inspect
the separate learned-mask preview, archived forecasts, saved live snapshot,
convolution lesson and Sources & guide progress buttons. Cached readings must
retain their source timestamp/stale label. Source/creator/licence records are
in data/source_manifest.csv and docs/. The licensed street clip is attributed
in BUNDLE_SCOPE.json. No source footage or model weights were edited.

Convolution lab also includes Try image compression (patterns1..160). Its
numerical storage/error lesson is separate from detector accuracy and JPEG size.
The selected executed notebook08 and its training image are included; the other
seven teaching notebooks/full training datasets are not part of this small demo.
Its ordinary Python cells were checked in the relocated process, with inline
display magic suppressed. Main-project Jupyter execution is separately recorded;
a fresh Jupyter/kernel setup in this copied folder is not verified.

VALIDATION_REPORT.json records the actual bounded relocated check. It is not
proof of physical network disconnection, manual dialogs, fresh installation or
universal model accuracy. Original image/forecast/DAVIS finals remain consumed.
''',encoding='utf-8')
        env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLCONFIGDIR=str(package/'.cache/matplotlib'))
        with (result_dir/'validation_stdout.txt').open('w',encoding='utf-8') as out,(result_dir/'validation_stderr.txt').open('w',encoding='utf-8') as err:
            completed=subprocess.run([sys.executable,'-I',str(package/'scripts/verify_relocated_demo.py')],cwd=package,env=env,stdout=out,stderr=err,timeout=600)
        if completed.returncode:raise RuntimeError('Relocated check failed; see preserved validation_stderr.txt')
        if 'invalid command name' in (result_dir/'validation_stderr.txt').read_text(encoding='utf-8'):
            raise RuntimeError('Native shutdown warning remains; preserve bundle and investigate')
        validation=json.loads((package/'VALIDATION_REPORT.json').read_text(encoding='utf-8'));assert validation['status']=='passed'
        (package/'INCOMPLETE').unlink()
        dump(package/'READY.json',dict(run_id=run_id,scope='Relocated local-demo validation passed using existing runtime; further acceptance remains',validation_sha256=digest(package/'VALIDATION_REPORT.json')))
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            validation=validation,validation_sha256=digest(package/'VALIDATION_REPORT.json'),manifest_sha256=digest(package/'BUNDLE_MANIFEST.json'),
            integration_gate_passed=True,accuracy_evaluated=False,model_training_performed=False,original_assets_changed=False)
        dump(result_dir/'run.json',report);shutil.copy2(package/'BUNDLE_MANIFEST.json',result_dir/'bundle_manifest.json')
        dump(result_dir/'progress.json',dict(copied=len(plan),total=len(plan),phase='complete'))
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=run_id,run_type='Relocated local demo integration validation; no accuracy scoring',started_at=protocol['started_at'],finished_at=report['finished_at'],
            source_ids=';'.join(protocol['source_ids']),split_ids='Training-only image plus archived reports/already-seen licensed video; no raw final data',configuration=(result_dir/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Existing frozen product + installed runtime + local bundle',epochs=0,batch_size=1,random_seed=protocol['seed'],hardware='CPU; Torch4/BLAS1/OMP2/MKL2',execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds'],evaluation_metrics='Software integration gate passed; no accuracy metric',logs=result_dir.relative_to(ROOT).as_posix(),checkpoints='Existing original weights unchanged',
            code_revision_basis=protocol['code_revision_basis'],implementation_sha256=hashes[paths[0]],conclusions='Copied local demo validated without original data/code fallback or normal Python network attempts; runtime reused; not fresh offline/native-visible acceptance')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run_id);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run_id
        print(json.dumps(dict(run_id=run_id,package=str(package),files=len(plan),bytes=protocol['total_bytes'],duration_seconds=report['duration_seconds'],integration_gate_passed=True),indent=2))
    except BaseException as error:
        dump(result_dir/'interrupted.json',dict(error=str(error),completed_run_counted=False,package_preserved=str(package)))
        state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
