"""Save the desktop counting milestone and exact continuation evidence."""
import csv,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
RUN='DESKTOP-FLOW-20261025T091303623986Z'
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T090725Z'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,value):(ROOT/p).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def csv_read(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);return reader.fieldnames,list(reader)
def csv_write(p,fields,rows):
    with (ROOT/p).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL if p=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL)
        writer.writeheader();writer.writerows(rows)
def append(p,text):
    path=ROOT/p;old=path.read_text(encoding='utf-8');title='25 October 2026 / video-bound desktop entrance and exit setup'
    if title not in old:path.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();run=read('experiments/results/'+RUN+'/run.json')
    assert run['validation_passed'] and run['summary']['processed_frames']==3
    for p,h in run['source_hashes'].items():assert digest(ROOT/p)==h,p
    tests=(E/'unit_tests.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 103 tests',tests) and tests.rstrip().endswith('OK')
    prior=read('experiments/evidence/HEARTBEAT-20261025T083725Z/production_unchanged.json')
    for p,h in prior.items():assert digest(ROOT/p)==h
    write(E.relative_to(ROOT)/'production_unchanged.json',prior)
    final='data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json'
    assert digest(ROOT/final)=='00719ea0aa0636f188c9ed391e47bb0d850c356d685d1798cd3c1b130562d278'
    write(E.relative_to(ROOT)/'software_checks.json',dict(tests_passed=103,failures=0,
        checks='File/view binding, explicit direction, bounded export, stale source, cancellation, failed-run retention, busy controls and prior product regression checks',
        shared_final_manifest_unchanged=True,final_images_decoded=0,final_annotations_decoded=0,
        software_tests_are_accuracy_evidence=False))
    live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
    receipt=[r for r in receipts if r['source_id']=='SRC-LIVE-001'][-1];payload=read(receipt['local_path']);rows=parse_feed(payload)
    assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    assert len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})==len(rows)
    assert all(0<=r['available']<=r['capacity'] and r['occupied']+r['available']==r['capacity'] for r in rows)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    feed_age=(datetime.fromisoformat(live['checked_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds()
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_observations=len(rows),raw_records=raw_count,
        invalid_capacity_records_excluded=raw_count-len(rows),duplicates=0,bounds_valid=True,feed_age_seconds_at_retrieval=feed_age,
        interpretation='2198 newly scored outcomes belong to forecasts frozen at 08:25/08:40 and later real same-source targets. Persistence only, not neural, camera or flow accuracy.'))
    fields,registry=csv_read('experiments/EXPERIMENT_REGISTRY.csv')
    if not any(r['experiment_id']==RUN for r in registry):
        record=dict(experiment_id=RUN,run_type='Bounded desktop-route real-video integration validation',started_at=run['started_at'],finished_at=run['finished_at'],source_ids='SRC-VID-001;SRC-MOD-001',
            split_ids='Already-seen street clip; 3 samples at 0/0.5/1 seconds; integration only',configuration='experiments/results/'+RUN+'/protocol.json',architecture='Existing Faster R-CNN ResNet50 FPNv2 and unchanged finite gate tracker',model_version=run['detector_sha256'],
            epochs=0,batch_size=1,random_seed=run['seed'],hardware='CPU; torch4threads, OMP2/MKL2/BLAS1',execution_environment='Python3.12.10; Torch2.14.0+cpu',training_duration=run['duration_seconds'],
            evaluation_metrics=json.dumps(dict(processed_frames=3,export_consistency=True,source_bound=True,predicted_entries=0,predicted_exits=0,accuracy_evaluated=False)),
            logs='experiments/results/'+RUN,checkpoints='Existing unchanged pretrained weights',code_revision_basis=run['code_revision_basis'],implementation_sha256=run['source_hashes']['scripts/validate_desktop_flow.py'],conclusions='New desktop processing route passes bounded real-file integration; no labelled positive crossings or measured flow accuracy')
        registry.append({k:record.get(k,'') for k in fields})
    csv_write('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==21
    assert all(sum(r['experiment_id']==ident for r in registry)==1 for ident in state['completed_run_ids'])
    state.update(scheduled_wakeups_completed=13,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['desktop_flow']=dict(run_id=RUN,implemented=True,native_hidden_widget_checks=True,native_dialog_save_verified=False,visual_layout_verified=False,real_crossing_accuracy_evaluated=False,guide='docs/ENTRANCE_EXIT_GUIDE.md')
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; 10 scored issue cohorts. No neural/camera/flow accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Next scheduled collection: score the frozen 09:07 forecasts only against later fresh same-capacity observations in their 20–45 minute target window. At 09:07: 11272 scored, 4466 expired, 1360 pending. Counter 21; separate 100-run checkpoint remains at 100.',
        'Verify the new Entrance / exit tab visually and through actual native setup save/load dialogs when appropriate; hidden native widget checks are not human acceptance. Obtain legitimately licensed, independently labelled crossing footage before any accuracy claim. Keep notebook04 and older real-video results intact.',
        'Prioritize training-only diagnosis and a predeclared occupancy robustness design; one UFPR05 false vacancy remains. Do not tune thresholds using the observed development errors. Missing 396 source occupancy attributes remain unknown.',
        'Broader region IoU 0.797653 still fails acceptance; keep the shared final six closed. Forecast candidates still fail per-park gates. Preserve all source timestamps and checkpoints. MetaPKLot remains inspection-only.',
        'Continue report compilation, physical/fresh offline and native export-save checks, final materials and student explanations. University documents and independent student rehearsal remain outstanding.'
    ]
    write('data/automation_state.json',state)
    card=read('models/gate_counter_method_card.json');card['current_desktop_gate_editor']=True
    card['desktop_integration']=dict(run_id=RUN,guide='docs/ENTRANCE_EXIT_GUIDE.md',source_bound=True,source_hashes=run['source_hashes'],hidden_widget_checks=True,native_dialogs_mocked=True,visual_layout_verified=False,accuracy_evaluated=False)
    write('models/gate_counter_method_card.json',card)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
        if item['source_id']=='SRC-VID-001':item['desktop_integration_run']=RUN
    write('data/dataset_inventory.json',inventory)
    overview='''The Python desktop app now has an Entrance / exit tab: local-video first-frame
preview, two-point counting line, explicit entering direction, video-bound setup
save/load, bounded half-second sampling, cancellation and automatic local results.
Exact video and first-frame hashes prevent silently reusing a setup for another
view. Advanced tracker configurations are rejected by the simple editor rather
than silently changing their settings; the existing CLI retains those options.

103 software checks pass, including eight new setup/output tests. A hidden native
Tk check created the actual widgets, drew the line/reference arrow, verified busy
controls, saved/reloaded a setup through real app methods, and displayed a test
frame event. File dialogs were mocked; visual layout, physical dialog interaction
and a human rehearsal remain unverified. Fixture display counts are not model data.

DESKTOP-FLOW-20261025T091303623986Z used the already-seen licensed street video
and unchanged Faster R-CNN/ResNet50 weights. Three real samples at 0/0.5/1 seconds
passed source, model and CSV/JSON consistency gates; zero crossings were predicted,
six duplicate boxes suppressed. This configured street line is not a known parking
entrance. No independently labelled positive crossing or flow accuracy is claimed.
Source attribution, sealed protocol, exact implementation and all predictions are
saved. One completed integration trial advances the experiment counter to 21;
tests/frames/cancellation fixtures do not add experiments. No jobs remain active.

Official Singapore acquisition at 09:07:58 UTC saved the 17th immutable snapshot,
receipt/checksum and normalized history. It scored 2,198 earlier frozen forecasts
against later matching readings: 11,272 matched outcomes total, persistence MAE
4.045245 spaces. There are 4,466 expired missing targets and 1,360 pending targets;
71.62% resolved target matching is not accuracy. Another 1,235 forecasts were frozen
for later readings. No neural/camera/flow live accuracy is implied. The separate
100-run checkpoint remains at run 100.

Three production checkpoints and the shared final manifest are unchanged; final
images/labels remain undecoded. Region and forecast acceptance failures persist.
See docs/ENTRANCE_EXIT_GUIDE.md for student steps and exact output/data locations.
The next actions, remaining UI/offline/report/labelled-data limitations and model
evidence are saved in data/automation_state.json.'''
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/UI_TEST_LOG.md','Hidden native Tk widget inspection passed: actual new tab, counting-line/reference-arrow canvas, busy-control states, explicit direction, setup-file save/reload methods and frame-event display. Native file dialogs were mocked. No screenshot/visual review, physical save-dialog interaction or human rehearsal claimed. See experiments/evidence/HEARTBEAT-20261025T090725Z/native_widget_checks.json. Real processing route separately validated on three licensed video samples; accuracy unmeasured.')
    append('docs/TEST_RESULTS.md','103 software tests pass. Eight new tests cover exact file/view binding, invalid line/direction/limit, real synthetic-video export path, preserving prior outputs, stale source, cancellation before first prediction and explicit failure evidence. Synthetic fixtures are not camera accuracy. Three real video samples passed model/source/export integration gates; no ground-truth crossing labels. Three production hashes and final reservation unchanged.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant implemented the Python desktop counting editor and source-bound runner, added eight software tests, ran the bounded real-file integration trial, inspected hidden native Tk widgets, documented the student guide and updated source/live/progress records. No student mastery, visual acceptance, labelled counting accuracy or model training is claimed.')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Sixteen authorized public snapshots acquired','Seventeen authorized public snapshots acquired').replace('Eight prospective persistence cohorts scored','Ten prospective persistence cohorts scored').replace('9,074 matched later outcomes, MAE3.798','11,272 matched later outcomes, MAE4.045').replace('95 tests pass; network-disabled-process image check passes','103 tests pass; network-disabled-process image check passes').replace('desktop editor pending','desktop editor implemented; native visual/dialog checks pending')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','Entrance / exit tab implemented with file/view binding, explicit direction, setup save/load, bounded counting and cancellation. Hidden native widget checks and three-real-frame processing integration pass; visual/native-dialog acceptance and independently labelled flow accuracy remain pending. 103 tests pass; counter 21. Latest live: 17 snapshots, 11,272 matched persistence outcomes, MAE 4.045245; no neural live accuracy. Guide: docs/ENTRANCE_EXIT_GUIDE.md.')
    fields,requirements=csv_read('docs/REQUIREMENTS.csv')
    for item in requirements:
        if item['requirement_id']=='FLOW-01':item.update(actual_evidence='src/smart_parking/flow_setup.py; app.py; models/gate_counter_method_card.json; notebook04; '+RUN,test_result='Desktop editor and source-bound runner; 103 software checks; hidden native widget/save-reload methods; three real samples/export consistency',open_problems='No labelled positive real crossing accuracy; visual layout and actual native dialog acceptance pending; association may fragment tracks; official scope unverified',next_action='Verify visible tab/native dialogs and obtain independently labelled legitimate video before accuracy claims')
        if item['requirement_id']=='VID-01':item['open_problems']='No labelled parking-video occupancy/tracking benchmark; occupancy needs a matching layout, separate gate tab accepts video without occupancy layout'
    csv_write('docs/REQUIREMENTS.csv',fields,requirements)
    fields,sources=csv_read('data/source_manifest.csv')
    for item in sources:
        if item['source_id']=='SRC-VID-001' and RUN not in item['used_by']:item['used_by']+='; video-bound desktop integration '+RUN
    csv_write('data/source_manifest.csv',fields,sources)
    print(json.dumps(dict(run_id=RUN,counter=21,tests=103,live_scores=live['scores_total'],baseline_mae=live['baseline_mae_spaces']),indent=2))
