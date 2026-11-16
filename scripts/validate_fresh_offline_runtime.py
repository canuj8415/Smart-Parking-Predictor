"""Install a hash-locked app profile offline, then validate existing frozen assets."""
import csv,hashlib,json,os,subprocess,sys,time,venv
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def child(mode,folder):
    import runpy
    attempts=[]
    def audit(event,args):
        if event in {'socket.connect','socket.getaddrinfo'}:
            attempts.append(event);raise PermissionError('Network blocked by offline installation validation')
    sys.addaudithook(audit)
    try:
        if mode=='install':
            manifest=json.loads((ROOT/'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json').read_text(encoding='utf-8'))
            sys.argv=['pip','install','--no-index','--require-hashes','--disable-pip-version-check',
                '--find-links',str(ROOT/'dependencies/offline_app/v1/wheels'),'-r',str(ROOT/manifest['lock_path'])]
            runpy.run_module('pip',run_name='__main__')
        elif mode=='dependency_check':
            sys.argv=['pip','check'];runpy.run_module('pip',run_name='__main__')
        elif mode=='preflight':
            sys.argv=[str(ROOT/'run_app.py'),'--check-environment'];runpy.run_path(str(ROOT/'run_app.py'),run_name='__main__')
        elif mode=='app':
            validate_app(folder)
        else:raise ValueError('Unknown offline validation mode')
    finally:dump(folder/(mode+'_network.json'),dict(attempts=attempts,sys_prefix=sys.prefix,base_prefix=sys.base_prefix))


def validate_app(folder):
    import gc,importlib
    from unittest.mock import patch
    modules={name:importlib.import_module(name) for name in ['torch','torchvision','numpy','PIL','matplotlib','cv2']}
    fresh=Path(sys.prefix).resolve()
    assert fresh!=Path(sys.base_prefix).resolve()
    origins={name:str(Path(module.__file__).resolve()) for name,module in modules.items()}
    assert all(Path(path).is_relative_to(fresh) for path in origins.values())
    # Preload the freshly installed decoder too. The normal package can otherwise
    # prefer its identical bundled decoder; this is an explicit dependency check.
    sys.path.insert(0,str(ROOT/'src'));import torch
    torch.set_num_threads(4)
    from smart_parking.app import ParkingApp
    from smart_parking.forecast_reports import ORIGINAL,LATER
    from smart_parking.video import process_video
    from smart_parking.provenance import digest as project_digest
    app=ParkingApp();app.withdraw();errors=[];outputs=ROOT/'outputs/fresh_runtime_validation'/folder.name;outputs.mkdir(parents=True,exist_ok=False)
    results=[]
    def wait():
        until=time.monotonic()+120
        while app.busy and time.monotonic()<until:app.update();time.sleep(.02)
        if app.busy:raise TimeoutError('Fresh-runtime app operation exceeded120seconds')
        if errors:raise RuntimeError(';'.join(errors))
    try:
        with patch('smart_parking.app.messagebox.showerror',side_effect=lambda title,message:errors.append(str(message))):
            app.load_demo();assert app.image is not None
            for kind in ['fasterrcnn','maskrcnn']:
                app.engine=None;gc.collect();app.kind.set(kind);app.analyze();wait()
                counts=app.result['counts'];assert counts==dict(occupied=68,vacant=32,uncertain=0,total=100)
                destination=outputs/kind;destination.mkdir()
                with patch('smart_parking.app.filedialog.askdirectory',return_value=str(destination)):app.save_results()
                export=next(destination.glob('parking_*'));meta=json.loads((export/'export_metadata.json').read_text(encoding='utf-8'))
                assert project_digest(export/'analysis.json')==meta['analysis_record_sha256']
                assert project_digest(export/'overlay.png')==meta['analysis_overlay_sha256']
                results.append(dict(detector=kind,counts=counts,weight_sha256=app.result['weight_sha256'],scope='Frozen training-example prediction agreement,not accuracy'))
            prior=app.result;app.semantic_mask();wait();assert app.result is prior and app.display_kind=='experimental_semantic_mask'
            for view in [ORIGINAL,LATER]:app.forecast_view.set(view);app.load_parks();app.show_forecast();assert view in app.forecast_info.get()
            app.refresh_live(False);wait();assert app.live_rows and 'snapshot' in app.live_info.get().lower()
            app.show_lab();app.svd_rank.set('16');app.show_svd();assert app.svd_report['rank']==16
            gate=json.loads((ROOT/'experiments/results/GATE-VIDEO-20261024T231251838602Z/protocol.json').read_text(encoding='utf-8'))
            report=process_video(ROOT/gate['source_attribution']['local_path'],app.get_engine('fasterrcnn'),None,outputs/'video',
                every_seconds=.5,max_frames=2,confidence=.5,flow_config=gate['gate_config'])
            assert report['processed_frames']==2 and not errors
        dump(folder/'app_validation.json',dict(status='passed',dependency_origins=origins,all_six_dependencies_from_fresh_venv=True,
            decoder_preloaded_from_fresh_venv=True,detectors=results,semantic_preview_separate=True,archived_forecast_views=2,
            cached_live_rows=len(app.live_rows),svd_rank16=True,video_samples=2,hidden_native=True,
            scope='Fresh app-only venv with existing base Python/Tk and existing saved model/data assets; no Jupyter install,new machine,physical-offline or scientific accuracy claim'))
    finally:app.destroy()


def main():
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(sys.argv[2],Path(sys.argv[3]));return
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another job active')
    started=datetime.now(timezone.utc);run='OFFLINE-INSTALL-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    fresh=ROOT/'outputs/installation_checks'/run/'venv';manifest_path=ROOT/'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert len(manifest['entries'])==24 and all(digest(ROOT/e['path'])==e['sha256'] for e in manifest['entries'])
    assert digest(ROOT/manifest['lock_path'])==manifest['lock_sha256']
    files=['scripts/validate_fresh_offline_runtime.py','run_app.py','src/smart_parking/environment.py','src/smart_parking/app.py','src/smart_parking/vision.py','src/smart_parking/live.py']
    hashes={p:digest(ROOT/p) for p in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),seed=120,
        source_ids=['SRC-PKG-003','SRC-DS-001','SRC-DS-003','SRC-LIVE-001','SRC-VID-001','SRC-MOD-001','SRC-MOD-002'],
        hypothesis='A complete hash-locked24-wheel CPU app profile installs into a new venv without networking and retains frozen training-example app behavior without shared-runtime mutation.',
        source_hashes=hashes,wheelhouse_manifest_sha256=digest(manifest_path),lock_sha256=manifest['lock_sha256'],fresh_venv=fresh.relative_to(ROOT).as_posix(),
        gates=['Hash-locked --no-index install succeeds','pip check and prerequisite discovery pass','Zero network attempts in every probe',
               'Sixcore packages import from fresh venv','Both detector counts match frozen training sample68occupied/32vacant/0uncertain',
               'Paired exports,semantic preview,archived forecasts,cached live,SVD and2local video samples pass'],
        model_training_performed=False,accuracy_evaluated=False,
        limitations=['Existing base Python/Tk and original model/data assets reused','App-only profile; Jupyter dependencies/kernel acceptance separate',
                     'Decoder preloaded from fresh venv to test that artifact; ordinary project can prefer its bundled decoder',
                     'Hidden native widgets/mocked dialogs; no physical network/new-machine/manual acceptance'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        fresh.parent.mkdir(parents=True,exist_ok=True);venv.EnvBuilder(with_pip=True,system_site_packages=False).create(fresh)
        assert 'include-system-site-packages = false' in (fresh/'pyvenv.cfg').read_text(encoding='utf-8')
        env=os.environ.copy();env.update(PIP_CONFIG_FILE=os.devnull,PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1',
            MPLCONFIGDIR=str(ROOT/'.cache'/run),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
        checks={}
        for mode in ['install','dependency_check','preflight','app']:
            with (folder/(mode+'_stdout.txt')).open('w',encoding='utf-8') as out,(folder/(mode+'_stderr.txt')).open('w',encoding='utf-8') as err:
                process=subprocess.Popen([str(fresh/'Scripts/python.exe'),'-I',str(Path(__file__).resolve()),'--child',mode,str(folder)],cwd=ROOT,env=env,stdout=out,stderr=err)
                deadline=time.monotonic()+600
                while process.poll() is None:
                    if (folder/'CANCEL').exists() or time.monotonic()>deadline:
                        process.terminate();process.wait(timeout=15);raise InterruptedError('Cancelled or timed-out owned offline validation child')
                    time.sleep(.25)
            audit=json.loads((folder/(mode+'_network.json')).read_text(encoding='utf-8'))
            checks[mode]=dict(returncode=process.returncode,network_attempts=audit['attempts'])
            dump(folder/'progress.json',dict(phase=mode,checks=checks))
            if process.returncode or audit['attempts']:break
        accepted=len(checks)==4 and all(r['returncode']==0 and not r['network_attempts'] for r in checks.values())
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        assert all(digest(ROOT/e['path'])==e['sha256'] for e in manifest['entries'])
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            checks=checks,offline_app_installation_gate_passed=accepted,shared_environment_changed=False,
            app_validation=json.loads((folder/'app_validation.json').read_text(encoding='utf-8')) if (folder/'app_validation.json').exists() else None)
        dump(folder/'run.json',report);dump(ROOT/'models/offline_app_installation.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run,run_type='Fresh hash-locked offline app installation and frozen-asset integration',started_at=protocol['started_at'],finished_at=report['finished_at'],
            source_ids=';'.join(protocol['source_ids']),split_ids='Training-only image/already-seen licensed video/archived reports; no raw final data',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='NewCPUapp venv; existing frozen models/assets',epochs=0,batch_size=1,random_seed=120,hardware='CPU; Windows; base Python reused',execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(dict(offline_app_installation_gate_passed=accepted,checks=checks)),logs=folder.relative_to(ROOT).as_posix(),
            checkpoints='No new weights; original assets unchanged',code_revision_basis='aadb9a0 plus sealed source snapshots',implementation_sha256=hashes[files[0]],
            conclusions='App-only offline installation/integration gate='+str(accepted)+'; Jupyter/new-machine/physical/manual acceptance separate; no accuracy scoring')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,offline_app_installation_gate_passed=accepted,checks=checks),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False,fresh_venv_preserved=str(fresh)))
        state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
