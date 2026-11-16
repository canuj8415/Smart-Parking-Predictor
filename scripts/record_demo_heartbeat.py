"""Save exact relocated-demo evidence, limits and continuation state once."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T154532Z'
FIRST='DEMO-BUNDLE-20261025T155935023256Z';LATEST='DEMO-BUNDLE-20261025T160503964992Z'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('This dated demo work is already recorded')
    now=datetime.now(timezone.utc).isoformat();run=read('experiments/results/'+LATEST+'/run.json');state=read('data/automation_state.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==34
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['integration_gate_passed'] and not run['accuracy_evaluated'] and not run['model_training_performed']
    assert 'Ran 167 tests' in (E/'unit_tests_after_shutdown.txt').read_text(encoding='utf-8-sig')
    assert (E/'unit_tests_after_shutdown.txt').read_text(encoding='utf-8-sig').rstrip().endswith('OK')
    assert (ROOT/'experiments/results'/LATEST/'validation_stderr.txt').stat().st_size==0
    for p,h in run['source_hashes'].items():assert digest(ROOT/p)==h
    package=ROOT/run['package'];manifest=read(package.relative_to(ROOT)/'BUNDLE_MANIFEST.json')
    assert len(manifest['files'])==184 and sum(r['bytes'] for r in manifest['files'])==544600770
    for row in manifest['files']:assert digest(package/row['path'])==row['sha256']
    assert not (package/'INCOMPLETE').exists() and (package/'READY.json').exists()
    val=run['validation'];assert val['normal_python_network_attempts']==0 and val['explicit_network_block_probe_passed']
    assert val['original_workspace_fallback_blocked'] and val['training_demo']['split']=='train'
    assert digest(package/'VALIDATION_REPORT.json')==run['validation_sha256']
    assert digest(package/'BUNDLE_MANIFEST.json')==run['manifest_sha256']
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as f:registry=list(csv.DictReader(f))
    assert all(sum(r['experiment_id']==ident for r in registry)==1 for ident in state['completed_run_ids'])
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in production.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    pointer=dict(run_id=LATEST,path=run['package'],manifest_sha256=run['manifest_sha256'],validation_sha256=run['validation_sha256'],
        files=184,bytes=544600770,guide='docs/DEMO_PACKAGE_GUIDE.md',runtime_reused=True,physical_offline_or_fresh_install_verified=False,
        previous_run=FIRST,previous_limitation='Scoped integration passed but nonfatal polling teardown warning; preserved and superseded by fixed version')
    write('reports/demo_package_latest.json',pointer);write('models/local_demo_package.json',dict(pointer,validation=val))
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');payload=read(receipt['local_path']);rows=parse_feed(payload)
    live=read('data/processed/singapore_prospective/summary.json');assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    assert len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})==len(rows)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        interpretation='1221earlier frozen persistence forecasts matched later observations; no neural/camera accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    inventory['local_demo_bundle']=pointer;write('data/dataset_inventory.json',inventory)
    state['last_updated_at']=now;state['scheduled_wakeups_completed']+=1;state['local_demo_bundle']=pointer
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Local demo latest='+LATEST+';184files/544600770bytes verified,167software tests. Existing Python runtime reused; hidden native/mocked dialogs/Python socket block only. Complete visible/manual-dialog, fresh installation and physical-offline acceptance without changing unrelated computer networking.',
        'Default sample now uses hash-bound training image/config, not a consumed final frame. Main/demo polygons remain geometry-only. First copied demo with nonfatal Tk teardown warning preserved; new version cancels polling callback and has empty stderr. Original weights and base tracker unchanged.',
        'Keep all consumed final groups closed: DAVIS car-roundabout, image camera/date and Birmingham finals. Flow final has zero reference crossings and fails acceptance; seek genuinely fresh labelled fixed-camera positive-crossing evidence/protocol, no retuning on consumed data.',
        'Compile/check saved report source using built-in LaTeX compiler if appropriate, then improve final report/presentation and student explanations. University primary documents still missing, official compliance unverified. Excel/progress15:32snapshot stays dated32trials/162tests; current technical ledger34/167.',
        'Next official collection on sensible30mincadence. At15:48UTC:20477matched persistence outcomes,MAE4.343507,6400expired/1394pending,76.19%resolved matching. No neural/camera live accuracy. Counter34; separate100-run checkpoint100.'
    ];write('data/automation_state.json',state)
    write(E.relative_to(ROOT)/'checks.json',dict(tests_passed=167,completed_trials=34,integration_trials=[FIRST,LATEST],latest_package=pointer,
        all184copied_hashes_verified=True,original_models_and_base_flow_unchanged=True,training_demo_only=True,no_raw_final_reread=True,
        first_shutdown_warning_preserved=True,latest_shutdown_stderr_empty=True,normal_python_network_attempts=0,
        original_workspace_data_fallback_blocked=True,hardware_disconnection_or_fresh_install=False,active_jobs=[]))
    note='''Two recorded software integration trials advanced counter32->34. First local
demo copy passed core gates but revealed a nonfatal orphaned Tk poll callback at
shutdown. Original package/protocol/source snapshots/stderr retained. The app now
cancels that callback once on destroy and requests video stop. Two regression
fixtures plus a second stricter relocated trial pass; latest stderr is empty.
No detector/classifier/forecast weights or base gate-counter policy changed.

Latest bundle:outputs/demo_packages/DEMO-BUNDLE-20261025T160503964992Z,
184files/544600770bytes, copied originals hash-verified before/after. Runtime reused
from installed Python3.12environment. Product modules/assets resolve inside copied
folder; reads back into original workspace denied. Python networking blocked:
zero normal attempts, explicit block probe passed. Actual hidden native app paths
verified:both detectors/paired exports on one hash-bound training image with100
geometry slots; separate semantic preview/export; two archived forecast charts;
cached live with STALElabel;2D/3D numeric lesson; progress tables; two local samples
of already-seen licensed street video. No raw final image/date/sequence decoded,
labels scored, model training or new accuracy claim. Both runs are software trials,
not per-frame/epoch counts.167software tests pass. No active jobs; checkpoint100.

Default Load real sample now uses explicitly recorded training data, not a consumed
final image. The prepared training manifest has no ufpr05rows, so the fixed policy
falls back to first training row:pucpr2012-09-11. Original image and geometry hashes
are in configs/demo_sample.json; no occupancy answers enter layout. No training
split/evaluation result changed. Launcher accepts explicit SMART_PARKING_PYTHON
or local/parent .venv; it does not install packages. Guide:docs/DEMO_PACKAGE_GUIDE.md;
pointer:reports/demo_package_latest.json; exact assets/validation retained.

This is a relocated local-demo check, not fresh offline installation, physical
disconnection/new-machine/cross-platform or visible/manual-dialog acceptance.
Windows networking/unrelated apps untouched. Full training datasets/Python runtime
not bundled; project-wide source catalog describes more than selected bundle.
Copies remain local, no publishing/purchases. Main/Jupyter remain Python. Dated
Excel15:32report intentionally remains32trials/162tests; newer ledger34/167. PKLot
licence action note corrected in original docs; bundled provenance is a dated copy.

Actual15:48UTC official Singapore snapshot26matches1221later persistence outcomes:
20477matched,MAE4.343507spaces;6400expired/1394pending,76.19%resolved matching,
not accuracy. Raw JSON/normalized CSV/URL/time/SHA retained. No neural/camera
accuracy. Next:visible/fresh-offline acceptance, meaningful fresh labelled crossing
evidence, report compilation/presentation and student explanation work. Missing
university sources block official compliance only; no whole-project completion.'''
    title='## 25 October 2026 / relocated local demo and shutdown cleanup'
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        p=ROOT/name;text=p.read_text(encoding='utf-8')
        if title not in text:p.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    p=ROOT/'docs/UI_TEST_LOG.md';p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nActual relocated hidden-native app workflows pass with mocked save dialogs. Both detector/semantic/forecast/cached-live/lab/progress routes tested under blocked Python networking and original-workspace fallback. Shutdown callback cleanup fixes observed stderr warning; strict second check has empty stderr. No visible/manual-dialog or physical-network acceptance claimed. See models/local_demo_package.json.\n',encoding='utf-8')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=p.read_text(encoding='utf-8').replace('162 tests pass; network-disabled-process','167 tests pass; relocated local-demo').replace('Twenty-five authorized public snapshots acquired','Twenty-six authorized public snapshots acquired').replace('Seventeen prospective persistence cohorts scored','Eighteen prospective persistence cohorts scored').replace('19,256 matched later outcomes, MAE4.407','20,477 matched later outcomes, MAE4.344')
    text+='\n\nRelocated demo:184files/about545MB,167tests,34recorded trials. Actual copied app/weights/training-sample/video/exports/archived-report routes pass with existing runtime, hidden widgets, blocked Python networking and no original-workspace fallback. Shutdown warning fixed. Full/fresh offline install, physical disconnection, visible/manual dialogs remain unverified. See docs/DEMO_PACKAGE_GUIDE.md.\n';p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/REQUIREMENTS.csv'
    with p.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['OFF-01','PKG-01']:
            row['status']='In progress';row['actual_evidence']='docs/DEMO_PACKAGE_GUIDE.md; reports/demo_package_latest.json; models/local_demo_package.json; '+LATEST
            row['test_result']='167software tests;184hash-verified copied assets; actual relocated hidden-native app routes/exports and blocked Python network/original-root fallback checks pass; shutdown warning fixed'
            row['open_problems']='Installed runtime reused; selected demo assets only, not full training/runtime distribution; fresh install/physical disconnection/visible-dialog/new-machine and official deliverable acceptance pending'
            row['next_action']='Complete remaining explicit acceptance gates; retain byte manifests, source rights, failed/scoped attempts and original data/weights'
    with p.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    print(json.dumps(dict(completed_trials=34,tests=167,package=str(package),bytes=544600770,latest_shutdown_stderr_empty=True),indent=2))


if __name__=='__main__':main()
