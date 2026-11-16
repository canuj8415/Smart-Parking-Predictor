"""Persist the completed fixed gate-video trial and this wake's continuation."""
import csv,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
RUN='GATE-VIDEO-20261024T231251838602Z';FOLDER=ROOT/'experiments/results'/RUN
EVIDENCE=ROOT/'experiments/evidence/HEARTBEAT-20261024T230924Z'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f);return r.fieldnames,list(r)
def table(path,fields,values):
    with (ROOT/path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL if path=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL)
        w.writeheader();w.writerows(values)
def append(path,text):
    heading='25October2026 / explicit gate counting and notebook04'
    target=ROOT/path;old=target.read_text(encoding='utf-8')
    if heading not in old:target.write_text(old.rstrip()+'\n\n## '+heading+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    from smart_parking.live import parse_feed
    now=datetime.now(timezone.utc).isoformat();r=read(FOLDER.relative_to(ROOT)/'run.json')
    live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(s) for s in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
    receipt=[s for s in receipts if s['source_id']=='SRC-LIVE-001'][-1]
    raw=read(receipt['local_path']);valid=parse_feed(raw)
    assert all(0<=s['available']<=s['capacity'] for s in valid)
    keys=[(s['car_park_id'],s['lot_type'],s['observed_at']) for s in valid]
    assert len(set(keys))==len(keys)
    assert hashlib.sha256((ROOT/receipt['local_path']).read_bytes()).hexdigest()==receipt['sha256']
    provider_age=(datetime.fromisoformat(receipt['accessed_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds()
    checkpoint=dict(summary=live,receipt=receipt,accepted_lot_observations=len(valid),raw_lot_records=sum(len(p['carpark_info']) for p in raw['items'][0]['carpark_data']),
        accepted_car_parks=len({s['car_park_id'] for s in valid}),duplicate_observation_keys=0,provider_age_at_collection_seconds=provider_age,
        interpretation='No recorded collection between21:41 and23:09UTC; no scores fabricated for missed target windows. Persistence only; no neural/camera accuracy.')
    write(EVIDENCE.relative_to(ROOT)/'live_checkpoint.json',checkpoint)
    prior=read('experiments/evidence/HEARTBEAT-20261024T213922Z/production_unchanged.json')
    for p,h in prior.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    write(EVIDENCE.relative_to(ROOT)/'production_unchanged.json',prior)
    tests=(EVIDENCE/'unit_tests.txt').read_text(encoding='utf-8-sig')
    assert re.search(r'Ran 77 tests',tests) and tests.rstrip().endswith('OK')
    write(EVIDENCE.relative_to(ROOT)/'software_checks.json',dict(checked_at=now,tests_passed=77,failures=0,scope='Software fixtures and regression checks, not camera/model accuracy'))
    notebook=read('notebooks/04_vehicle_gate_flow.ipynb');cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    assert len(cells)==7 and all(c['execution_count'] for c in cells)
    assert not [o for c in cells for o in c['outputs'] if o['output_type']=='error']
    write('models/gate_counter_method_card.json',dict(method='Sequence-local mutual-nearest box-centre association plus finite directed gate',
        trained=False,source_ids=['SRC-VID-001','SRC-MOD-001'],run_id=RUN,config=r['gate_config'],
        validation_scope='Synthetic counting rules plus real-video export/replay integration. No labelled real positive crossing validated.',
        processed_real_frames=25,real_predictions=r['summary']['flow_diagnostics'],accuracy_evaluated=False,
        current_desktop_gate_editor=False,api_and_local_file_cli_available=True,limitations=r['limitations'],
        protocol=str((FOLDER/'protocol.json').relative_to(ROOT)),implementation_hashes=r['source_hashes']))
    fields,registry=rows('experiments/EXPERIMENT_REGISTRY.csv')
    if not any(v['experiment_id']==RUN for v in registry):
        value=dict(experiment_id=RUN,run_type='Fixed-gate real-video integration; no counting-accuracy labels',started_at=r['started_at'],finished_at=r['finished_at'],
            source_ids='SRC-VID-001;SRC-MOD-001',split_ids=r['split'],configuration=str((FOLDER/'protocol.json').relative_to(ROOT)),architecture=r['model'],model_version=RUN,
            epochs=0,batch_size=1,random_seed=r['seed'],hardware='CPU4 threads; BLAS1/OMP2/MKL2',execution_environment='Python3.12.10; Torch2.14.0+cpu',
            training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(dict(real_frames=25,predicted_entries=0,predicted_exits=0,accuracy_evaluated=False,export_consistency_passed=True,sparse_gap_resets=17)),
            logs=str(FOLDER.relative_to(ROOT)),checkpoints='Existing unchanged detector weights',code_revision_basis=r['code_revision_basis'],
            implementation_sha256=r['source_hashes']['scripts/validate_gate_video.py'],conclusions='25half-second samples exported consistently;0crossings predicted, no labelled positive-real-crossing/accuracy evidence;2s replay resets17times. No final images opened.')
        registry.append({k:value.get(k,'') for k in fields})
    table('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=checkpoint['accepted_car_parks'],observations=len(valid),raw_lot_records=checkpoint['raw_lot_records'],
            provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
        if item['source_id']=='SRC-VID-001':item['gate_integration']=dict(run_id=RUN,processed_frames=25,decoded_frames=361,accuracy_evaluated=False,real_predicted_crossings=0,source_unchanged=True)
    write('data/dataset_inventory.json',inventory)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==15
    state.update(scheduled_wakeups_completed=8,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[],gate_video_validation=RUN,
        trigger_handling_note='One productive completed execution for pending22:09/22:39/23:09triggers; no collections or completed experiments claimed for the intervening triggers')
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;5scored issue cohorts. Coverage is target matching, not accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Collect one official source-compliant snapshot next wake.1286forecasts frozen23:09UTC need actual later20-45min targets; prior gaps remain missing. Counter15; next separate100-run live checkpoint100.',
        'Gate API/CLI and notebook04 work; real fixed trial predicted0crossings and establishes export consistency only. Need independently labelled positive/negative crossing footage, association robustness and a desktop gate editor before deployment claims. Do not retune the same clip to manufacture positive counts.',
        'Higher-resolution region candidate commonIoU0.79629 still fails acceptance; preserve all weights and closed shared final6. Avoid repeated tuning on six development images; plan broader legitimate development data.',
        'MetaPKLot SRC-DS-010 remains inspection-only, no annotation JSON parsed. Verify exact-file rights/ROI/image identity before development-only filtering, excluding reserved/consumed finals. Source archive original preserved.',
        'Continue forecast robustness, native-save/fresh-offline checks and final report/presentation. Notebook04 executed7cells; first missing-pandas attempt recorded and removed dependency. Old report/guide/Excel remain dated; compilation/official university documents incomplete.'
    ]
    write('data/automation_state.json',state)
    overview='''Implemented explicit finite-gate crossing predictions in Python video API and
local-file CLI, separate from occupancy. Directed line, two-observation side
confirmation, deadband, class-agnostic duplicate suppression, mutual-nearest
association with ambiguity rejection, missing-observation reset and0.75s gap
reset are configured and exported. This is simple box-centre tracking, not
re-identification or calibrated detector/flow accuracy. Desktop gate editor is
not implemented; existing desktop occupancy workflow remains separate.

GATE-VIDEO-20261024T231251838602Z used the original licensed street recording,
unchanged detector, fixed horizontal line(100,700)->(1900,700), and25samples
at0.5s across0-12s (361decoded frames). Predicted0entries/0exits,0gap resets,
14duplicate-box suppressions. CSV/JSON cumulative counts/events agree. No
positive real crossing was validated and no human flow labels exist: accuracy
NOT EVALUABLE.0predictions do not establish0physical crossings. Runtime126.33s,
median inference3.997s, detector load2.126s; offline only. Replay of the earlier
18two-second samples resets on17gaps and abstains; no claim of correct zero flow.
All protocol/settings/source/code hashes and implementation bytes retained.

77software checks pass, including10new counting-rule fixtures and1video/export
integration fixture. These synthetic cases are not model scores or separate
counted experiments. Notebook04executed7code cells without saved errors; synthetic
entry/exit lesson and actual25tracking records replay exactly. Both plots visually
checked. First notebook attempt failed because optional pandas was absent; tables
were replaced with escaped HTML using existing Python/IPython. No package added.

One new real-video validation trial brings counter15; next100-run checkpoint100.
No trainers/validation jobs remain;3production checkpoint hashes unchanged.
Region models/final6 and inspection-only MetaPKLot annotations were not opened
or retuned. New source use is only the already licensed street clip.

Eleventh official Singapore snapshot23:09:58UTC:1286new frozen forecasts,
0new scores because no recorded snapshot falls in the old target windows.
9893issued/5601scored;3006expired missing targets and1286pending at collection.
Resolved matching65.07%, matched-only persistenceMAE2.0114265 unchanged; missing
outcomes have no invented scores. This is aggregate persistence, not neural or
camera accuracy. RawJSON/normalized history/receipt/checksum preserved; accepted
and raw lot-row counts are now recorded separately. No unrecorded22:09/22:39
collection, work or cause of the gap is invented.

New teaching guide: docs/GATE_FLOW_GUIDE.md; executed notebook:
notebooks/04_vehicle_gate_flow.ipynb. Official documents, final report/presentation,
report compilation, native save/physical offline and labelled parking-video
evaluation remain incomplete. Exact continuation: data/automation_state.json.'''
    for path in ['docs/AUTONOMOUS_PROGRESS.md','docs/PROJECT_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(path,overview)
    append('docs/TEST_RESULTS.md','77software checks pass. Fixed real gate-video trial:25half-second samples,361decoded frames,0predicted crossings; CSV/JSON agree. No positive real crossing or accuracy demonstrated. Notebook04executed7cells; first optional-pandas failure/remediation retained; two plots visually checked. Evidence: experiments/evidence/HEARTBEAT-20261024T230924Z/ and GATE-VIDEO-20261024T231251838602Z/.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant independently implemented the simple gate association/counting rules, API/CLI integration,11new software fixtures, fixed real-video validation and teaching notebook04/guide. Actual0crossing result and missing-pandas notebook failure retained. No ground-truth flow accuracy or student independent authorship/mastery is implied. No package, private footage or new dataset annotation used.')
    append('docs/MODEL_PROVENANCE.md','GateCounter is an independently implemented geometric association/counting method, not a newly trained neural model. It consumes existing Faster R-CNN detections; no new pretrained assets or copied third-party algorithm code. Protocol/source snapshots and limitations: models/gate_counter_method_card.json; GATE-VIDEO-20261024T231251838602Z/.')
    append('docs/THIRD_PARTY_SOURCES.md','SRC-VID-001 original Street traffic, Editor, Wikimedia Commons, CC BY3.0: https://commons.wikimedia.org/wiki/File:Street_traffic.webm . Additional derived overlays/notebook figures add detector boxes, gate and IDs, with attribution retained. Original recording/checksum unchanged; no endorsement. Real tracking outputs are predictions, not new ground truth.')
    fields,sources=rows('data/source_manifest.csv')
    for s in sources:
        if s['source_id']=='SRC-VID-001' and 'gate-video' not in s['used_by']:
            s['used_by']+='; fixed half-second gate-video integration; notebook04 attributed derived overlays, no accuracy'
    table('data/source_manifest.csv',fields,sources)
    fields,requirements=rows('docs/REQUIREMENTS.csv')
    for q in requirements:
        if q['requirement_id']=='FLOW-01':q.update(status='In progress',actual_evidence='src/smart_parking/flow.py; models/gate_counter_method_card.json; notebook04; GATE-VIDEO-20261024T231251838602Z',
            test_result='Finite-gate API/CLI;11new software checks; real25frame exports consistent,0predicted crossings; no labelled real positive crossing/accuracy',
            open_problems='Simple association may fragment tracks; labelled gate benchmark/desktop editor and official scope pending',next_action='Reserve independently labelled crossing footage; frozen validation; add desktop editor with UI verification')
        if q['requirement_id']=='VID-01':q['actual_evidence']+='; GATE-VIDEO-20261024T231251838602Z';q['test_result']='Original timestamp repair retained; configured gate25half-second samples and exports verified;77software checks pass; no real-video accuracy labels'
    table('docs/REQUIREMENTS.csv',fields,requirements)
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8')
    s=s.replace('Three executed teaching notebooks','Four executed teaching notebooks').replace('Nine authorized public snapshots acquired','Eleven authorized public snapshots acquired').replace('Four prospective persistence cohorts scored','Five prospective persistence cohorts scored').replace('4,486 matched later outcomes, MAE2.013','5,601 matched later outcomes, MAE2.011').replace('62 tests pass; network-disabled-process image check passes','77 tests pass; network-disabled-process image check passes')
    s=s.replace('| Vehicle flow | Debounced occupancy transitions | Actual entrance/exit crossing tracking/counting not implemented or claimed |','| Vehicle flow | Configured finite-gate API/CLI implemented | Synthetic counting rules and real25frame export check pass;0real predicted crossings; no labelled positive real crossing/accuracy; desktop editor pending |')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','Latest gate method and notebook04 are implemented/tested within the scope above; accuracy remains unmeasured. Live11snapshots/5601matched outcomes;65.07%resolved target matching as of23:09UTC. No region promotion or final-data use.')
    print(json.dumps(dict(counter=15,tests=77,accepted_live_observations=len(valid),raw_lot_records=checkpoint['raw_lot_records'],completed_run=RUN),indent=2))
