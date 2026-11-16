"""Preserve the qualified development candidate and bounded next actions."""
import csv,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
RUN='FORECAST-GROUP-ROBUST-20261025T094258007427Z'
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T093726Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def table_read(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as s:
        reader=csv.DictReader(s);return reader.fieldnames,list(reader)
def table_write(p,fields,rows):
    with (ROOT/p).open('w',encoding='utf-8',newline='') as s:
        writer=csv.DictWriter(s,fieldnames=fields,quoting=csv.QUOTE_ALL if p=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);writer.writeheader();writer.writerows(rows)
def append(p,text):
    title='25 October 2026 / training-only robust forecast selection'
    path=ROOT/p;old=path.read_text(encoding='utf-8')
    if title not in old:path.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();result=read('experiments/results/'+RUN+'/run.json');folder=ROOT/'experiments/results'/RUN
    assert result['metrics']['validation_gate_passed'] and digest(folder/'candidate.pt')==result['checkpoint_sha256']
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 110 tests',tests) and tests.rstrip().endswith('OK')
    guard=read(E.relative_to(ROOT)/'post_reservation_replay.json');assert guard['all_train_validation_fields_equal_to_frozen_implementation'] and guard['checkpoint_replay_exact_for_all_322_predictions']
    for p,h in result['source_hashes'].items():
        if p=='src/smart_parking/forecasting.py':assert digest(ROOT/p)==guard['guarded_window_code_sha256']
        else:assert digest(ROOT/p)==h,p
    production=read('experiments/evidence/HEARTBEAT-20261025T090725Z/production_unchanged.json')
    for p,h in production.items():assert digest(ROOT/p)==h
    write(E.relative_to(ROOT)/'production_unchanged.json',production)
    final_image='data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json'
    assert digest(ROOT/final_image)=='00719ea0aa0636f188c9ed391e47bb0d850c356d685d1798cd3c1b130562d278'
    reserved=read('data/manifests/forecast_fresh_dates_v1.json');assert reserved['reserved_rows']==3844 and reserved['selected_checkpoint_sha256']==result['checkpoint_sha256']
    predictions=read('experiments/results/'+RUN+'/validation_predictions.json')
    for key,metric in [('candidate_occupied','candidate_mae_spaces'),('persistence_occupied','persistence_mae_spaces')]:
        actual=sum(abs(r[key]-r['actual_occupied']) for r in predictions)/len(predictions)
        assert abs(actual-result['metrics'][metric])<1e-10
    write('models/forecast_group_robust_candidate.json',dict(**result,post_trial_loader_guard=guard,
        production_promoted=False,independent_final_evaluated=False,fresh_date_reservation='data/manifests/forecast_fresh_dates_v1.json'))
    write(E.relative_to(ROOT)/'software_checks.json',dict(tests_passed=110,failed=0,exact_checkpoint_replay=True,legacy_test_loader_blocked=True,
        production_unchanged=True,image_final_unchanged=True,fresh_forecast_numeric_outcomes_evaluated=False,
        new_forecast_tests=7,independent_runs=1,inner_fits=3,all_training_refits=1,
        note='Fold-specific seeds are not independent seed replications. Training-only selection reached the 80-epoch cap; no convergence claim.'))
    live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()];receipt=[r for r in receipts if r['source_id']=='SRC-LIVE-001'][-1]
    payload=read(receipt['local_path']);rows=parse_feed(payload);raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert digest(ROOT/receipt['local_path'])==receipt['sha256'] and len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})==len(rows)
    assert all(0<=r['available']<=r['capacity'] and r['occupied']+r['available']==r['capacity'] for r in rows)
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_observations=len(rows),raw_records=raw_count,invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=True,
        feed_age_seconds=(datetime.fromisoformat(live['checked_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds(),
        interpretation='1130 earlier frozen persistence forecasts newly scored against later matching targets. No neural/camera accuracy. 125 former pending targets expired without fabricated scores.'))
    fields,registry=table_read('experiments/EXPERIMENT_REGISTRY.csv')
    if not any(r['experiment_id']==RUN for r in registry):
        record=dict(experiment_id=RUN,run_type='Bounded real-data group-relative LSTM training with nested training-only selection',started_at=result['started_at'],finished_at=result['finished_at'],source_ids='SRC-DS-003',split_ids=result['split_id'],configuration='experiments/results/'+RUN+'/protocol.json',architecture=result['architecture'],model_version=RUN,optimizer='Adam',learning_rate=.001,epochs=result['selected_epoch'],batch_size='Full fitting prefix',random_seed='Fold seeds 81/82/83; refit 84',hardware='CPU; Torch4 / OMP2 / MKL2 / BLAS1',execution_environment='Python3.12.10; Torch'+result['torch_version'],training_duration=result['duration_seconds'],loss_curves='experiments/results/'+RUN+'/curves.json',evaluation_metrics=json.dumps(result['metrics']),logs='experiments/results/'+RUN,checkpoints='experiments/results/'+RUN+'/candidate.pt',code_revision_basis=result['code_revision_basis'],implementation_sha256=result['source_hashes']['scripts/train_robust_forecast.py'],conclusions='Development gate passes: MAE30.197 vs persistence40.220; 26 eligible parks no >10% regressions. 322 correlated windows/4dates; no independent final/live neural score or promotion.')
        registry.append({k:record.get(k,'') for k in fields})
    table_write('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==22
    assert all(sum(r['experiment_id']==ident for r in registry)==1 for ident in state['completed_run_ids'])
    state.update(scheduled_wakeups_completed=14,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['qualified_development_forecast']=dict(run_id=RUN,validation_mae_spaces=result['metrics']['candidate_mae_spaces'],persistence_mae_spaces=result['metrics']['persistence_mae_spaces'],validation_gate_passed=True,selected_epoch=80,independent_final_evaluated=False,production_promoted=False,fresh_reservation='data/manifests/forecast_fresh_dates_v1.json',note='Older 20.9015 aggregate winner remains recorded but fails its per-park gate.')
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; 11 scored issue cohorts, separate source from neural study.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'New forecast candidate passes development gates; preserve checkpoint and reservation. Before any numeric future-date evaluation, implement/test exclusive overlap-aware durable source/date claims that consume dates on failure. Do not use the original consumed Dec8–11 test windows for changed-method scoring.',
        'Investigate causal window coverage using TRAINING only: 787 windows on 10/51 source train dates and 322 development windows on 4/10 dates. Predetermine any alternate phase/raw-origin protocol and gates before applying to reserved Dec12–19 rows. No adequacy/accuracy claim if admissible final windows are absent. Do not tune on future labels.',
        'Run only prespecified confirmation if justified; current single procedure has 3 inner fits plus 1 refit, not 4 independent trials. Epoch 80 hit the cap. Older lower-aggregate candidate fails group gates; app production remains original.',
        'Next scheduled source collection should score frozen 09:38 forecasts only using later fresh matching readings. At 09:38: 12402 scored, 4591 expired, 1262 pending. Counter 22; separate 100-run live checkpoint remains at 100.',
        'Continue parking-region acceptance (0.797653 fails), occupancy robustness (one false vacancy remains), legitimate labelled flow footage, visible/native-dialog tests, physical/fresh offline, report compilation and student explanations. Image final six stay closed; MetaPKLot remains inspection-only.'
    ]
    notebook=read('notebooks/05_forecast_robustness.ipynb');cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    executed=all(c['execution_count'] is not None and not any(o['output_type']=='error' for o in c['outputs']) for c in cells)
    state['forecast_lesson']=dict(path='notebooks/05_forecast_robustness.ipynb',executed=executed,code_cells=len(cells))
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-003':item['qualified_development_forecast']=state['qualified_development_forecast'];item['fresh_date_reservation']=dict(dates=reserved['reserved_dates'],rows=3844,parks=29,evaluated=False)
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    lesson_note='Lesson05 executed with four code cells and no saved errors.' if executed else 'Lesson05 source saved; kernel execution remains unconfirmed.'
    overview='''One predeclared group-relative LSTM procedure completed: three expanding training-only
folds choose a common epoch count, then a seed84 refit uses all 787 training windows.
The objective is half mean/half worst-park MAE divided by fitting-prefix persistence
MAE (floor one space); unknown parks use a fitting-only median scale. No new features.
Selection reached the fixed 80-epoch cap, not proven convergence. Four model fits are
one recorded experiment, not independent seed confirmation. Runtime 5.281 seconds.

Frozen checkpoint precedes development-target loading. On 322 reused development
windows/4 dates, candidate MAE30.197154 vs persistence40.220497 spaces, a 24.92098%
reduction. The existing >=5% overall/<=10% per-park regression gate passes: 26 parks
have >=10 windows; another has3. All27 show lower observed MAE. Earlier aggregate
winner20.9015 remains lower overall but failed its group gate; no causal single-factor
claim because objective and selection procedure both changed. No final/live neural
accuracy or production promotion. Actual target readings lead19.32–29.37 minutes.

New reservation seals 3844 source-row identifiers on Dec12–19/2016, 29 car parks,
absent from the only archived original test-prediction artifact (Dec8–11). This is
existing Birmingham data, not a newly blinded external source. No numeric future
outcomes were parsed for reservation/scoring. Whole source-manifest hash, original
prediction hash and selected checkpoint/result hash are pinned. A full durable
overlap-aware date claim is still required before final scoring. Legacy test loading
now refuses before opening numeric data while the reservation exists. Training and
development windows are byte-for-value equal to the sealed original implementation;
checkpoint replay reproduces every322 saved predictions exactly. Source snapshots
retain the pre-guard implementation, with the guard delta documented separately.

Coverage is limited: 10/51 source training dates and4/10 development dates yielded
these fixed-grid windows. Future final admissibility is not assumed. Diagnose any
alternate causal time/phase protocol using training/development alone, freeze it,
then evaluate reserved data once under the future guard. Preserve the current model.

110 software tests pass;3 production hashes and image-final reservation unchanged.
Counter22; no jobs active; next separate100-run live checkpoint100. New easy guide:
docs/FORECAST_ROBUSTNESS_GUIDE.md. LESSON_NOTE

Official09:38 snapshot18 saved immutable raw JSON, receipt, checksum and normalized
history.1130 earlier frozen persistence forecasts newly matched later targets:
12402 scored total, MAE4.108853 spaces;4591 expired missing targets,1262 pending,
72.98% resolved target matching.1157 new forecasts frozen. No neural/camera/live-flow
accuracy implied. All earlier snapshots/failures/checkpoints remain. Remaining core
model, final-data, UI/offline/report/university/student limitations are in state.'''.replace('LESSON_NOTE',lesson_note)
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/TEST_RESULTS.md','110 tests pass. Seven new objective/split/output/final-loader checks use synthetic fixtures. Frozen checkpoint exactly replays all322 real development predictions; train/development window fields unchanged by final-loader guard. Model metrics: MAE30.197154 vs persistence40.220497; gate passes. This is reused development, not final/live accuracy. 3 production hashes and image-final manifest unchanged. Evidence: HEARTBEAT-20261025T093726Z; '+RUN+'. '+lesson_note)
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant designed/implemented the predeclared group-relative objective and training-only blocked selection, trained and recorded one experiment, audited/replayed metrics, reserved later date metadata, added a guarded refusal for legacy test loading, wrote the guide/lesson, and collected the authorized source snapshot. No student independent contribution/mastery, converged training, external final or live-neural claim. '+lesson_note)
    append('docs/PROJECT_CONSTRAINTS.md','Forecast Dec12–19/2016 source rows are reserved by data/manifests/forecast_fresh_dates_v1.json. Do not use them for training/development/calibration. Legacy test loading is blocked; implement/test a durable overlap-aware one-time temporal claim before final evaluation. Freeze a suitable causal window protocol using training/development only first; missing admissible windows mean unavailable evidence. Original Dec8–11 final windows are already consumed. Current candidate passes reused-development gates only; production unchanged.')
    append('docs/RESEARCH_LOG.md','Reused UCI Parking Birmingham SRC-DS-003 and existing official Singapore SRC-LIVE-001 with their recorded licences/receipts. No newly downloaded training dataset or new library. Training-only normalized group objective and blocked selection are project-designed; no external algorithm attribution invented. Later date reservation uses source identifiers/timestamps only; coverage and original-ingestion limitations recorded.')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Seventeen authorized public snapshots acquired','Eighteen authorized public snapshots acquired').replace('Ten prospective persistence cohorts scored','Eleven prospective persistence cohorts scored').replace('11,272 matched later outcomes, MAE4.045','12,402 matched later outcomes, MAE4.109').replace('103 tests pass; network-disabled-process image check passes','110 tests pass; network-disabled-process image check passes').replace('Original loses to persistence; new candidate validation MAE 20.902, but per-park gates fail and no production promotion','Original loses; earlier lowest development MAE20.902 fails group gates; new group-relative30.197 vs baseline40.220 passes development gates; fresh final pending, no promotion')
    if executed:s=s.replace('Four executed teaching notebooks, zero saved errors','Five executed teaching notebooks, zero saved errors')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','New group-relative forecast passes reused-development gate: MAE30.197 vs40.220 persistence on322windows/4dates. New 8-date/3844-row reservation stays unevaluated; causal coverage and durable final-claim work pending. Production unchanged. 110 software checks; counter22. '+lesson_note+' Latest live18snapshots/12402matched persistence outcomes, MAE4.108853,72.98%resolved matching.')
    fields,requirements=table_read('docs/REQUIREMENTS.csv')
    for item in requirements:
        if item['requirement_id']=='SEQ-02':item.update(actual_evidence=item['actual_evidence']+'; models/forecast_group_robust_candidate.json; data/manifests/forecast_fresh_dates_v1.json',test_result='Group-relative candidate MAE30.197 vs40.220 persistence; 26 eligible parks pass development gate; exact frozen replay; no final/live neural result',open_problems='Reused development on4dates; window coverage sparse; fresh-date preprocessing and durable one-time final guard pending; no promotion',next_action='Training-only coverage study; freeze final protocol; guard one evaluation of reserved future dates; preserve all failures')
    table_write('docs/REQUIREMENTS.csv',fields,requirements)
    fields,sources=table_read('data/source_manifest.csv')
    for item in sources:
        if item['source_id']=='SRC-DS-003' and RUN not in item['used_by']:item['used_by']+='; '+RUN+'; metadata-only reserved future dates; lesson05'
    table_write('data/source_manifest.csv',fields,sources)
    print(json.dumps(dict(counter=22,tests=110,development_gate=True,notebook_executed=executed,live_scores=live['scores_total']),indent=2))
