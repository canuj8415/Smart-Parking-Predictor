"""Save exact refreshed-demo evidence and preserve all earlier package versions."""
import csv,json,re,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed

E=ROOT/'experiments/evidence/HEARTBEAT-20261025T194536Z'
RUN='DEMO-BUNDLE-20261025T194803443600Z'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('This dated heartbeat is already recorded')
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');run=read('experiments/results/'+RUN+'/run.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==37
    assert state['scheduled_wakeups_completed']==24 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['integration_gate_passed'] and not run['accuracy_evaluated'] and not run['model_training_performed']
    assert all(digest(ROOT/path)==h for path,h in run['source_hashes'].items())
    tests=(E/'unit_tests.txt').read_text(encoding='utf-8-sig');assert 'Ran 181 tests' in tests and tests.rstrip().endswith('OK')
    result=ROOT/'experiments/results'/RUN;package=ROOT/run['package'];manifest=read(package.relative_to(ROOT)/'BUNDLE_MANIFEST.json')
    assert len(manifest['files'])==189 and sum(row['bytes'] for row in manifest['files'])==545111075
    assert all(digest(package/row['path'])==row['sha256'] for row in manifest['files'])
    assert not (package/'INCOMPLETE').exists() and (package/'READY.json').exists()
    assert digest(package/'VALIDATION_REPORT.json')==run['validation_sha256']
    assert digest(package/'BUNDLE_MANIFEST.json')==run['manifest_sha256']
    assert (result/'validation_stderr.txt').stat().st_size==0
    validation=run['validation']
    assert validation['svd_app_rank_switching_passed'] and validation['packaged_notebook_python_cells']==4
    assert validation['strict_live_fixture_checks_passed'] and validation['normal_python_network_attempts']==0
    assert validation['original_workspace_fallback_blocked'] and validation['explicit_network_block_probe_passed']
    compatibility=read(E.relative_to(ROOT)/'live_compatibility.json')
    assert compatibility['snapshots']==30 and compatibility['repeated_snapshot_records']==72690
    assert compatibility['source_current_sha256']==digest(ROOT/'src/smart_parking/live.py')
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/path)==h for path,h in production.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    previous=read('reports/demo_package_latest.json')
    assert previous['run_id']=='DEMO-BUNDLE-20261025T160503964992Z'
    pointer=dict(run_id=RUN,path=run['package'],manifest_sha256=run['manifest_sha256'],validation_sha256=run['validation_sha256'],
        files=189,bytes=545111075,guide='docs/DEMO_PACKAGE_GUIDE.md',runtime_reused=True,
        physical_offline_or_fresh_install_verified=False,visible_manual_acceptance=False,
        previous_run=previous['run_id'],included_notebooks=['08_image_patterns_and_svd.ipynb'],
        notebook_validation_scope='Python cells executed in copied process with inline magic/show suppressed; no copied-folder Jupyter kernel acceptance',
        latest_live_guards_included=True,svd_lesson_included=True,newer_source_changes_not_in_bundle=[])
    write('reports/demo_package_latest.json',pointer)
    write('models/local_demo_package.json',dict(pointer,validation=validation))
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(row for row in reversed(receipts) if row['source_id']=='SRC-LIVE-001');assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    live=read('data/processed/singapore_prospective/summary.json');payload=read(receipt['local_path']);rows=parse_feed(payload)
    assert live['scores_total']==23891 and live['scores_added']==1041
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    cohorts=sum(c['scored']>0 for c in live['forecast_coverage']['cohorts'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        interpretation='1041earlier frozen persistence forecasts match later actual targets; no camera/neural accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['local_demo_bundle']=pointer
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=30,
            prospective_baseline_scored_outcomes=23891,prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state.update(last_updated_at=now,scheduled_wakeups_completed=25,local_demo_bundle=pointer,
        latest_live_schema_integration=RUN,
        last_live_baseline_score=dict(outcomes=23891,mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Refreshed189-file/545111075-byte local demo passes isolated-copy integration,including SVD and selected notebook08Python cells. See reports/demo_package_latest.json/docs/DEMO_PACKAGE_GUIDE.md. Reused installed runtime; full fresh installation,copied-folder Jupyter kernel,visible/manual-dialog and physical-offline acceptance still pending. Earlier packages intact.',
        'New top-level JSON array/null feed rejection preserves invalid raw bytes separately; malformed fixtures do not replace cache/history. All30 real snapshots/72690 repeated records match prior parser outputs.181software tests;37completed trials,not per-frame/cell counts. All original weights/base tracker and consumed finals preserved.',
        'Prioritize legitimate fresh fixed-camera vehicle-counting labels or remaining reproducible installation acceptance. Source14HTMLonly/client403; no bypass/login/dataset assets. Source13inspection-only; coordinate/label/rights unresolved. Never reuse consumed DAVIS/image/Birmingham finals for changed-method tuning.',
        'Eight notebooks executed in main project; only08in selected demo. Student practice/rehearsal and university primary documents/official template remain missing. Technical report16:35,Excel15:32 and older slides retain dated metrics; no routine regeneration just for counters.',
        'Last official collection19:48UTC:30snapshots,23891matched persistence outcomes/MAE4.050312,7872expired/1296pending,75.22%resolved matching. Next sensible30mincollection after20:18UTC. Counter37; separate100-run checkpoint100. No active jobs.'
    ];write('data/automation_state.json',state)
    title='## 25 October 2026 / refreshed relocated demo with live guards and Jupyter lesson'
    note='''A new copied demo passes one recorded integration trial:189files/545,111,075bytes
at outputs/demo_packages/DEMO-BUNDLE-20261025T194803443600Z. All copied hashes
verified before/after; original Python source/data fallback blocked. Original
weights/raw assets and all earlier demo folders remain unchanged. Reused installed
Python runtime and copied Windows decoder; no automatic package installation.

Actual hidden-native checks:both detectors and paired exports on the existing
training-only100-slot image, separate semantic preview/export, two archived
forecast charts,cached official live view,2D/3D arithmetic,progress export and
two already-seen licensed street-video samples. SVD app ranks16/48and selected
notebook08fourordinary Python cells pass inside the copy with inline magic/show
suppressed. Full Jupyter execution remains verified in main project only; copied
kernel/manual dialogs/visible layout/fresh install/physical disconnection/new
machine/cross-platform acceptance remain unverified. Zero normal Python network
attempts; explicit block probe passes; shutdown stderr empty. OS networking and
unrelated apps untouched. Only notebook08is included,not the full8notebook/data set.

Live JSON arrays/null now fail validation and preserve rejected bytes separately,
without replacing the accepted cache/history. Extended synthetic rejection cases
pass. All181software tests pass; all30real snapshots/72,690repeated lot records
exactly match prior valid parser output. Synthetic fixtures are software checks,
not live observations or camera/forecast accuracy. Counter36->37for one completed
integration trial,not perframe/rank/notebook cell. No scientific model evaluation.

Actual19:48UTC official snapshot30 matches1041previously frozen persistence
targets:23,891matched total,MAE4.050312spaces,7872expired/1296pending,
75.22%resolved target matching. Matching coverage is not accuracy. Raw JSON,
normalized CSV,provider/retrieval timestamps,URL,SHA,bounds/duplicate evidence
retained. No neural/camera live score; the earlier gap remains honestly unscored.

Current pointers updated; source catalog52. Earlier report/Excel/slides and failed
studies preserved with their dated scope. No active jobs; next100-run milestone100.
Next:legitimate fresh labelled counting evidence,reproducible installation/native
manual/physical-offline acceptance,and student practice. Whole project completion,
universal accuracy,student mastery and official academic compliance unclaimed.'''
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        path=ROOT/name;text=path.read_text(encoding='utf-8');assert title not in text
        path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    path=ROOT/'docs/UI_TEST_LOG.md';path.write_text(path.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nRefreshed copied app passes actual hidden-native detector/export/forecast/cached-live/SVD/progress/video routes; selected notebook08Python cells execute without original-source fallback or normal Python networking. Mocked dialogs and suppressed notebook display; visible/manual/fresh-offline/kernel acceptance unverified. Source outputs and empty stderr retained in the latest demo run.\n',encoding='utf-8')
    path=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=path.read_text(encoding='utf-8').replace('Twenty-nine authorized public snapshots acquired','Thirty authorized public snapshots acquired')
    text=re.sub(r'\| Live-source forecasting \| [^|]+\| [^\n]+',f'| Live-source forecasting | {cohorts} prospective persistence cohorts scored | 23,891 matched later outcomes, MAE4.050; actual variable target windows; no neural/camera live accuracy |',text,count=1)
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    path=ROOT/'docs/DEMO_PACKAGE_GUIDE.md';text=path.read_text(encoding='utf-8')
    text=text.replace(previous['run_id'],RUN).replace('184 hash-verified files','189 hash-verified files')
    text=text.replace('convolution lab\n   and Sources','convolution/SVD lab and selected notebook08\n   and Sources')
    text+='\n\n'+title+'\n\nLatest package includes the live.pyguards,SVD module,guide and executed notebook08. Its4Python cells were checked inside the copy with inline magic/show suppressed; no copied-folder Jupyter-kernel acceptance. Use reports/demo_package_latest.json for exact byte hashes. Main-project8notebooks remain separate; old package versions preserved.\n'
    path.write_text(text,encoding='utf-8')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['OFF-01','PKG-01']:
            row.update(status='In progress',actual_evidence='docs/DEMO_PACKAGE_GUIDE.md; reports/demo_package_latest.json; models/local_demo_package.json; '+RUN,
                test_result='181software tests;189hash-verified copied assets; actual relocated hidden-native routes/exports,SVD and notebook08Python cells pass with blocked network/original-root fallback; empty shutdown stderr',
                open_problems='Existing runtime reused; full training/runtime distribution,copied-folder Jupyter kernel,fresh install/physical disconnection/visible-manual-dialog/new-machine and official acceptance pending',
                next_action='Complete remaining explicit acceptance gates; preserve source rights,earlier packages,raw data,weights and failure evidence')
    with path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=37,software_tests=181,source_records=52,
        package=pointer,all189asset_hashes_verified=True,original_weights_and_base_flow_unchanged=True,
        no_raw_final_reread=True,copied_notebook_cells=4,normal_python_network_attempts=0,
        shutdown_stderr_empty=True,live_snapshot_count=30,live_matched_outcomes=23891,no_active_jobs=True))
    print(json.dumps(dict(completed_trials=37,files=189,bytes=545111075,live_outcomes=23891),indent=2))


if __name__=='__main__':main()
