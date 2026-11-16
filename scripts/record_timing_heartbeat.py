"""Record the completed timing audit without changing any model checkpoints."""
import csv,hashlib,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.live import parse_feed
RUN='FORECAST-TIMING-20261024T234223029035Z';FOLDER=ROOT/'experiments/results'/RUN
EVIDENCE=ROOT/'experiments/evidence/HEARTBEAT-20261024T233924Z'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,obj):(ROOT/path).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f);return r.fieldnames,list(r)
def table(path,fields,values):
    with (ROOT/path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL if path=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);w.writeheader();w.writerows(values)
def append(path,text):
    title='25October2026 / actual forecast target times'
    p=ROOT/path;old=p.read_text(encoding='utf-8')
    if title not in old:p.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();r=read(FOLDER.relative_to(ROOT)/'run.json')
    tests=(EVIDENCE/'unit_tests.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 81 tests',tests) and tests.rstrip().endswith('OK')
    write(EVIDENCE.relative_to(ROOT)/'software_checks.json',dict(checked_at=now,tests_passed=81,failures=0,scope='Four new synthetic source-timing fixtures and full software regression suite; not model accuracy'))
    weights=read('experiments/evidence/HEARTBEAT-20261024T230924Z/production_unchanged.json')
    for p,h in weights.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    write(EVIDENCE.relative_to(ROOT)/'production_unchanged.json',weights)
    live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(x) for x in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
    receipt=[x for x in receipts if x['source_id']=='SRC-LIVE-001'][-1];raw=read(receipt['local_path']);accepted=parse_feed(raw)
    assert len({(x['car_park_id'],x['lot_type'],x['observed_at']) for x in accepted})==len(accepted)
    assert hashlib.sha256((ROOT/receipt['local_path']).read_bytes()).hexdigest()==receipt['sha256']
    live_evidence=dict(summary=live,receipt=receipt,accepted_lot_observations=len(accepted),accepted_car_parks=len({x['car_park_id'] for x in accepted}),
        raw_lot_records=sum(len(p['carpark_info']) for p in raw['items'][0]['carpark_data']),duplicate_keys=0,
        provider_age_at_collection_seconds=(datetime.fromisoformat(receipt['accessed_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds(),
        bounds_valid=True,neural_accuracy_evaluated=False,camera_accuracy_evaluated=False)
    write(EVIDENCE.relative_to(ROOT)/'live_checkpoint.json',live_evidence)
    write('models/forecast_timing_audit.json',r)
    fields,registry=rows('experiments/EXPERIMENT_REGISTRY.csv')
    if not any(x['experiment_id']==RUN for x in registry):
        value=dict(experiment_id=RUN,run_type='Historical source-timestamp audit of frozen development predictions; no training',started_at=r['started_at'],finished_at=r['finished_at'],
            source_ids='SRC-DS-003',split_ids='birmingham-global-days-v1 train787/validation322; no final scoring',configuration=str((FOLDER/'protocol.json').relative_to(ROOT)),
            architecture='Metadata-only causal-grid window extension; frozen trend-guard predictions reused',model_version=r['candidate_run_id'],epochs=0,random_seed=r['seed'],hardware='CPU; deterministic metadata comparisons',
            execution_environment='Python3.12.10',training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(dict(distributions=r['distributions'],aggregate=r['validation_aggregate'],candidate_gate_passed=False)),
            logs=str(FOLDER.relative_to(ROOT)),checkpoints='No new or changed checkpoint',code_revision_basis='c757d7f reference plus exact source snapshots',implementation_sha256=r['code_sha256'],
            conclusions='All original train/validation fields unchanged; actual validation target lead19.32-29.37min. Prior candidate gate remains failed; no final/live-model evaluation.')
        registry.append({k:value.get(k,'') for k in fields})
    table('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-003':item['source_timing_audit']=dict(run_id=RUN,train_windows=787,validation_windows=322,original_fields_unchanged=True,final_evaluated=False,validation_actual_target_lead_minutes=r['distributions']['validation']['actual_target_lead_minutes'])
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=live_evidence['accepted_car_parks'],observations=len(accepted),raw_lot_records=live_evidence['raw_lot_records'],provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==16
    state.update(scheduled_wakeups_completed=9,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[],forecast_timing_audit=RUN)
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;6scored issue cohorts. Coverage is target matching, not accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Next wake collect one authorized official snapshot for1150forecasts frozen23:40UTC and93remaining23:09entries; score only actual later valid targets. Counter16, next separate100-run milestone100.',
        'Forecast source times now retained and future candidate exports include them. Audit verified exact original train/validation fields; validation target lead19.32-29.37min, not exact30. Keep original scores/checkpoints/gate failures unchanged. Use prespecified actual-time horizons and broader chronological development before another robustness hypothesis; no test tuning.',
        'Region candidate commonIoU0.79629 still fails acceptance; shared final6closed. MetaPKLot is inspection-only pending exact-file rights/ROI/image-identity checks. Avoid repeat sweeps on six development images.',
        'Gate counter has only synthetic positive-crossing evidence and real export integration with0predicted crossings; independently labelled footage and desktop gate editor remain needed. Existing notebook04 is a dated reproducible lesson.',
        'Continue report/presentation, reproducible notebooks, native-save/fresh-offline checks and student explanations. App wording updated for nominal grid targets; no new desktop visual check. University documents/report compilation still unavailable/unconfirmed.'
    ]
    write('data/automation_state.json',state)
    overview='''FORECAST-TIMING-20261024T234223029035Z audited787train/322development windows
against the sealed c757d7f window implementation and frozen prior trend-candidate
predictions. Every ORIGINAL field, including features/targets/entity/source-row
membership, is exactly unchanged. New metadata retains input grid/source times,
ages, target source time, target age, actual lead from forecast origin and
reading-to-reading interval. All input readings as-of<=20minutes; targets are
genuinely after issue; training/validation source rows disjoint. Future candidate
exports retain these fields. No model retraining or final/test scoring.

Actual development target lead19.3167-29.3667min, median28.7667; source-to-source
interval19.9833-40.05min. Grid lead remains30min. Prior aggregate candidateMAE
20.9015035 and persistence40.220498 unchanged. Prespecified timing strata:
10-15min n0/no score;15-20min n8 candidate16.9459 vs persistence7.1250;
20-25min n1 10.5240 vs13.0000;25-30min n313 21.0358 vs41.1534. Small/empty
groups are disclosed, not model-selection gates or independent test evidence.
Prior candidate still FAILS per-park gate. No promotion or live-model claim.

App now says30-minute GRID targets and explains earlier as-of source readings.
Updated wording has software regression checks; no new desktop visual check.
81software tests pass, including4synthetic timing/age/causality fixtures. Original
3production checkpoint hashes unchanged. Protocol, exact source/code snapshots,
row-level timing JSON/CSV and visually checked reproducible figure retained.
New plain-language explanation: docs/FORECAST_TIMING_GUIDE.md. Old notebooks,
report/Excel/PDF remain dated snapshots, not silently reissued scores.

Twelfth official Singapore snapshot23:40:38UTC added1193actual later matched
outcomes and1150new frozen forecasts. Cumulative11043issued/6794scored across
6scored issue cohorts; persistenceMAE2.6390933spaces.3006expired missing,
93in-window and1150before-window at collection; matching6794/9800=69.33%of
resolved forecasts, not accuracy. No missing-score invention, neural Singapore
accuracy or camera/flow metric. RawJSON/history/receipt/checksum retained.

Counter16completed experiments/validation trials, not16training jobs; this wake
adds one deterministic temporal provenance audit. Next100-run checkpoint100.
No trainers/validation jobs active. Region finals and MetaPKLot annotation JSON
were not opened. Exact next actions in data/automation_state.json; report,
presentation, official compliance, labelled parking-video and native/offline
acceptance work remain unfinished.'''
    for p in ['docs/AUTONOMOUS_PROGRESS.md','docs/PROJECT_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/TEST_RESULTS.md','81software tests pass. Source-timing audit verifies exact original787train/322development fields against sealed prior code, causal source ages and disjoint split rows. New metadata is additive; saved scores/3production hashes unchanged. Actual validation target lead19.32-29.37min. No final/model training/live-neural evaluation. Evidence: FORECAST-TIMING-20261024T234223029035Z and HEARTBEAT-20261024T233924Z/.')
    append('docs/UI_TEST_LOG.md','Forecast tab wording/title now distinguishes30-minute grid targets from earlier real target readings. Automated software suite passes; this wake did not open the desktop or visually inspect the changed text. Existing native-save/offline limitations remain.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant implemented additive source-timestamp metadata/future exports, ran the deterministic train/validation timing audit,4new synthetic timing fixtures and81software regressions, clarified app wording, produced/reviewed a descriptive chart and beginner guide, continued live collection and records. No student mastery, new training, final score or live neural accuracy is implied.')
    append('docs/MODEL_PROVENANCE.md','Forecast timing metadata is additive and does not alter the model architecture/features/targets or checkpoints. FORECAST-TIMING-20261024T234223029035Z verifies exact old development fields and frozen score joins. Original model cards retain their historical code hashes; models/forecast_timing_audit.json records the new audit separately.')
    fields,sources=rows('data/source_manifest.csv')
    for s in sources:
        if s['source_id']=='SRC-DS-003' and 'source-time provenance' not in s['used_by']:s['used_by']+='; train/development source-time provenance audit, no final re-evaluation'
    table('data/source_manifest.csv',fields,sources)
    fields,requirements=rows('docs/REQUIREMENTS.csv')
    for q in requirements:
        if q['requirement_id']=='DATA-04':q.update(actual_evidence=q['actual_evidence']+'; models/forecast_timing_audit.json',test_result='Exact old787train/322development windows retained; source-time/age metadata verified. Actual validation lead19.32-29.37min on nominal30min grid;81software checks pass')
        if q['requirement_id']=='SEQ-02':q['open_problems']='Original LSTM worse than baseline; new candidate still fails per-park gate; grid horizon differs from actual target reading lead; no new final score'
    table('docs/REQUIREMENTS.csv',fields,requirements)
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Eleven authorized public snapshots acquired','Twelve authorized public snapshots acquired').replace('Five prospective persistence cohorts scored','Six prospective persistence cohorts scored').replace('5,601 matched later outcomes, MAE2.011','6,794 matched later outcomes, MAE2.639').replace('77 tests pass; network-disabled-process image check passes','81 tests pass; network-disabled-process image check passes')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','Historical source timing verified without changing training/development features or targets. Actual development target lead19.32-29.37min, not exact30. App wording clarified; no new desktop visual check.81software checks pass;3production weights unchanged. Latest live baseline6794outcomes/MAE2.63909,69.33%resolved target matching at23:40UTC; no neural/camera live accuracy.')
    print(json.dumps(dict(counter=16,software_checks=81,live_scored=live['scores_total'],live_mae=live['baseline_mae_spaces']),indent=2))
