"""Record timing coverage, consumed final evidence and the historical report view."""
import csv,json,math,re,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
from smart_parking.forecast_holdouts import assert_forecast_dates_closed
PHASE='FORECAST-PHASE-20261025T101202713070Z';FINAL='FORECAST-FINAL-20261025T101729300425Z'
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T100726Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def table_read(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as stream:
        r=csv.DictReader(stream);return r.fieldnames,list(r)
def table_write(p,fields,rows):
    with (ROOT/p).open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL if p=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);w.writeheader();w.writerows(rows)
def append(p,text):
    title='25 October 2026 / clock coverage and one-time later-date forecast evaluation'
    path=ROOT/p;old=path.read_text(encoding='utf-8')
    if title not in old:path.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();phase=read('experiments/results/'+PHASE+'/run.json');final=read('experiments/results/'+FINAL+'/run.json');f=final['final_evaluation']
    assert phase['metrics']['validation_gate_passed'] and f['final_gate_passed']
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 123 tests',tests) and tests.rstrip().endswith('OK')
    assert read(E.relative_to(ROOT)/'forecast_widget_checks.json')['round_trip_restores_original_text']
    replay=read(E.relative_to(ROOT)/'window_refactor_replay.json');assert all(r['all_fields_equal'] for r in replay['comparisons'])
    for p,h in final['source_hashes'].items():assert digest(ROOT/p)==h
    for p,h in phase['source_hashes'].items():
        assert digest(ROOT/p)==(replay['current_sha256'] if p=='src/smart_parking/forecasting.py' else h)
    production=read('experiments/evidence/HEARTBEAT-20261025T093726Z/production_unchanged.json')
    for p,h in production.items():assert digest(ROOT/p)==h
    write(E.relative_to(ROOT)/'production_unchanged.json',production)
    assert digest(ROOT/'data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json')=='00719ea0aa0636f188c9ed391e47bb0d850c356d685d1798cd3c1b130562d278'
    reserved=read('data/manifests/forecast_fresh_dates_v1.json');ids={int(r['source_row']) for r in reserved['metadata']}
    predictions=read('experiments/results/'+FINAL+'/test_predictions.json');assert len(predictions)==1853
    for r in predictions:
        assert set(r['input_source_rows']+[r['target_source_row']])<=ids
        assert r['origin'][:10] in reserved['reserved_dates'] and r['target_time'][:10] in reserved['reserved_dates']
        assert all(0<=r[k]<=r['capacity'] and math.isfinite(r[k]) for k in ['actual_occupied','candidate_occupied','persistence_occupied','original_lstm_occupied'])
        assert all(datetime.fromisoformat(at)<=datetime.fromisoformat(r['origin']) for at in r['input_source_times'])
        assert datetime.fromisoformat(r['target_source_time'])>datetime.fromisoformat(r['origin'])
    for key,metric in [('candidate_occupied','candidate_mae_spaces'),('persistence_occupied','persistence_mae_spaces'),('original_lstm_occupied','original_lstm_mae_spaces')]:
        actual=sum(abs(r[key]-r['actual_occupied']) for r in predictions)/len(predictions)
        assert abs(actual-f['metrics'][metric])<1e-10
    with (ROOT/'experiments/results'/FINAL/'observations.csv').open(newline='') as stream:csv_rows=list(csv.DictReader(stream))
    assert len(csv_rows)==len(predictions) and all(float(a['candidate_occupied'])==b['candidate_occupied'] for a,b in zip(csv_rows,predictions))
    try:assert_forecast_dates_closed(ROOT/'data/manifests/forecast_fresh_dates_v1.json',root=ROOT)
    except ValueError as error:assert 'overlaps' in str(error)
    else:raise AssertionError('Final dates must now be consumed')
    claims=list((ROOT/'data/forecast_holdout_claims').glob('*.claim.json'));assert len(claims)==1
    claim=read(claims[0].relative_to(ROOT));outcome=read(claims[0].with_suffix('.outcome.json').relative_to(ROOT))
    assert claim['run_id']==FINAL and outcome['status']=='completed; dates consumed'
    write(E.relative_to(ROOT)/'final_output_checks.json',dict(recorded_metrics_recomputed_from_saved_predictions=True,csv_json_rows_match=1853,all_prediction_source_rows_in_reserved_ids=True,all_times_causal=True,all_outputs_bounded=True,
        claimed_source_dates=claim['source_dates'],claim_sha256=digest(claims[0]),outcome=outcome,real_final_repeated=False,model_inference_repeated_for_checks=False))
    write(E.relative_to(ROOT)/'software_checks.json',dict(tests_passed=123,failures=0,new_tests=13,scope='6 durable-claim,2 phase,2 exact-membership,3 archived-report tests; all synthetic software fixtures',final_image_manifest_unchanged=True,production_weights_unchanged=True))
    write('models/forecast_phase_evaluation.json',dict(**phase,post_refactor_replay=replay))
    card=read('models/forecast_final_evaluation.json');assert card['run_json_sha256']==digest(ROOT/'experiments/results'/FINAL/'run.json') and card['predictions_sha256']==digest(ROOT/'experiments/results'/FINAL/'test_predictions.json')
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()];receipt=[r for r in receipts if r['source_id']=='SRC-LIVE-001'][-1]
    raw=read(receipt['local_path']);rows=parse_feed(raw);raw_count=sum(len(p['carpark_info']) for item in raw['items'] for p in item['carpark_data'])
    assert digest(ROOT/receipt['local_path'])==receipt['sha256'] and len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})==len(rows)
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_observations=len(rows),raw_records=raw_count,invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        feed_age_seconds=(datetime.fromisoformat(live['checked_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds(),interpretation='1099 earlier frozen persistence forecasts matched later observations;105 old missing targets expired. Separate Singapore source, not neural/camera accuracy.'))
    fields,registry=table_read('experiments/EXPERIMENT_REGISTRY.csv')
    for ident,r in [(PHASE,phase),(FINAL,final)]:
        if any(row['experiment_id']==ident for row in registry):continue
        metrics=r['metrics'] if ident==PHASE else r['final_evaluation']['metrics']
        record=dict(experiment_id=ident,run_type='Training-count phase selection and frozen broader development evaluation' if ident==PHASE else 'One-time guarded existing-source later-date forecast evaluation',started_at=r['started_at'],finished_at=r['finished_at'],source_ids='SRC-DS-003',split_ids='birmingham-global-days-v1; train-only chosen grid offset10; development' if ident==PHASE else 'Reserved Dec12–19/2016; all8dates now consumed',configuration='experiments/results/'+ident+'/protocol.json',architecture='Frozen group-relative TrendGuardedOccupancyLSTM; phase10 causal as-of grid',model_version=r['checkpoint_sha256'],epochs=0,batch_size=512,random_seed=r['seed'],hardware='CPU; Torch4 / BLAS1 / OMP2 / MKL2',execution_environment='Python3.12.10; existing Torch2.14.0+cpu',training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(metrics),logs='experiments/results/'+ident,checkpoints='experiments/results/FORECAST-GROUP-ROBUST-20261025T094258007427Z/candidate.pt',code_revision_basis=r['code_revision_basis'],implementation_sha256=r['source_hashes']['scripts/audit_forecast_phase.py' if ident==PHASE else 'scripts/evaluate_forecast_final.py'],conclusions='2539windows/10dates, MAE35.036 vs43.790, gate pass; no training/final labels' if ident==PHASE else '1853windows/8dates/29eligibleparks; MAE31.724 vs39.072 persistence and87.720 original; final gate pass; real target lead10.02–29.12min; no universal/live accuracy or production-weight promotion')
        registry.append({k:record.get(k,'') for k in fields})
    table_write('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==24
    assert all(sum(r['experiment_id']==ident for r in registry)==1 for ident in state['completed_run_ids'])
    state.update(scheduled_wakeups_completed=15,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['forecast_temporal_final']=dict(run_id=FINAL,phase_run=PHASE,windows=1853,dates=8,eligible_parks=29,metrics=f['metrics'],final_gate_passed=True,reserved_dates_consumed=True,production_weights_promoted=False,report_view_available=True,horizon='Actual target readings10.02–29.12min; not exact30min')
    state['qualified_development_forecast'].update(later_date_evaluated=True,final_run_id=FINAL,final_gate_passed=True,production_promoted=False)
    state['qualified_development_forecast'].pop('independent_final_evaluated',None)
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;12 scored issue cohorts; no neural/camera live accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Forecast Dec12–19 dates are CONSUMED under durable claim. Never tune on or re-evaluate changed methods using them, or original Dec8–11 consumed windows. Preserve all claims, protocols and checkpoints. New changed forecast methods need genuinely fresh final data; do not relabel training/development as final.',
        'Historical final forecast gate now passes. Later-date report is available in app without replacing original production weights or rerunning inference. Verify visible UI/native acceptance; any future runtime model-input integration needs an explicit source-consistent timing/provenance design and regression checks. No neural Singapore/camera transfer.',
        'Prioritize parking-region segmentation acceptance (broader0.797653 fails, shared image final6 still closed), then occupancy training-only robustness (one false vacancy remains). Do not tune on consumed final outputs. MetaPKLot stays inspection-only until scope/identity verified.',
        'Next scheduled Singapore collection: score frozen10:09 forecasts against actual later fresh same-capacity targets only. Current13501scored/4696expired/1288pending at10:09. Counter24; separate100-run live checkpoint at100.',
        'Continue legitimately labelled traffic-flow footage, visible/native dialog checks, physical/fresh offline run, report compilation, dated final-report/presentation update and student practice. Existing slide deck and notebooks are historical snapshots; new explanation docs/FORECAST_FINAL_EVALUATION.md.'
    ]
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-003':
            item['forecast_temporal_final']=state['forecast_temporal_final'];item['fresh_date_reservation'].update(evaluated=True,consumed=True,final_run_id=FINAL)
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    overview='''Completed a training-count-only clock-offset study and one protected later-date
forecast evaluation. Phase10 (minutes10/40) gives14333 training windows vs787 at
phase0; no prediction errors used for phase selection. The frozen original candidate,
without retraining, passes broader development:2539windows/all10dates/28eligible
parks, MAE35.036354 vs43.790469 persistence,19.99%reduction, no park gate failure.
Six-phase pure-window refactor replay preserves every training/development field;
extra phase development counts were inspected only after phase10 was frozen.

Durable whole-source/date guard binds reservation, model, protocol and source SHA;
exclusive claim is flushed before any numeric final row is parsed. Synthetic tests
cover overlap across manifests, failed/interrupted callback consumption, bad gates,
changed weights/protocol/source and post-callback source mutation. Real final ran
once on the exact3844reserved source IDs; Dec8–11 old consumed windows excluded.
Claim and outcome retained in data/forecast_holdout_claims. Dec12–19 is CONSUMED;
no tuning or changed-method scoring may reuse these dates.

FORECAST-FINAL-20261025T101729300425Z:1853windows/all8dates/29eligibleparks;
candidate MAE31.723523 vs persistence39.071775 and original LSTM87.719680 on the
SAME rows.18.8071%error reduction vs persistence; frozen final gate passes, no
eligible park>10%regression. Existing-source temporal holdout, not external/blinded
collection or universal accuracy. Actual target readings10.02–29.12min after issue,
mostly15–25min; not exact30min. Correlated overlapping windows; all lead-bin/source
times and row-level evidence retained. Metrics/CSV-JSON rows replay from saved
predictions; no model inference or final evaluation repeated during output checks.

App offers an optional Later-date check report next to Original experiment. It
reads hash-checked archived predictions, clears stale charts on switch and explains
the historical source and actual lead times. Original default and3production
checkpoints remain unchanged. Hidden native Tk/Matplotlib rendering and round-trip
report switch passed; no screenshot/visible/native-user acceptance claimed.

123software checks pass. Two completed trials advance counter24; no jobs active;
next separate100-run live checkpoint100. Shared image final6 remains closed and
segmentation/occupancy/flow/offline/report/student/university limitations persist.
New easy result/data guide:docs/FORECAST_FINAL_EVALUATION.md. Earlier notebooks,
slides and reported scores remain their dated cohorts; do not substitute new MAE.

Official10:09 snapshot19 saved immutable rawJSON, normalized CSV, URL/receipt/SHA.
1099 earlier frozen persistence targets newly matched;13501scored, MAE4.190578;
4696expired missing targets,1288pending,74.19%resolved matching.1230new forecasts
frozen. This separate Singapore result does not score the neural/camera models.'''
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/TEST_RESULTS.md','123 tests pass;13new synthetic software cases. Training/development pure-window replay exact at6offsets. One real phase evaluation and one guarded final evaluation; final1853rows/8dates/29eligibleparks, gate pass. Saved metrics/CSV source/timing/bounds checks pass. All3production hashes and image-final manifest unchanged. Native hidden report switching/chart rendering passed; no visible acceptance. Exact evidence: HEARTBEAT-20261025T100726Z.')
    append('docs/UI_TEST_LOG.md','Optional Later-date check added to historical forecast tab. Hidden native Tk/Matplotlib chart rendering passed for both actual archived reports; switching clears stale charts and round-trip restores original text. New label shows31.72/39.07MAE and actual10.0–29.1min lead, not live. No model rerun or raw final re-read for display. No screenshot/visible layout or physical-user acceptance claimed.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant implemented/tested timing offsets, pure window extraction, durable source/date claims and exact final membership parsing; performed one training-only coverage choice/development trial and one frozen final trial; added a hash-checked historical report view and beginner result guide. No final tuning, repeated final scoring, production-weight replacement, live neural transfer or student mastery claim.')
    append('docs/PROJECT_CONSTRAINTS.md','Forecast Dec12–19/2016 is now consumed under data/forecast_holdout_claims: one successful frozen evaluation, gate passed. Preserve immutable reservation and durable claims/outcomes. Never tune on or evaluate changed methods on these dates, even after code fixes. Original Dec8–11 also consumed. Displaying archived results is allowed; changed forecasting methods need genuinely fresh final data. Image final six remain separately closed.')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Eighteen authorized public snapshots acquired','Nineteen authorized public snapshots acquired').replace('Eleven prospective persistence cohorts scored','Twelve prospective persistence cohorts scored').replace('12,402 matched later outcomes, MAE4.109','13,501 matched later outcomes, MAE4.191').replace('110 tests pass; network-disabled-process image check passes','123 tests pass; network-disabled-process image check passes').replace('new group-relative30.197 vs baseline40.220 passes development gates; fresh final pending, no promotion','frozen group-relative final31.724 vs persistence39.072 on1853later-date windows, gate passes; optional archived report, original weights retained')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','Later-date forecast passes frozen final gate on1853windows/8dates/29eligibleparks:31.724MAE vs39.072persistence and87.720original LSTM. Real reading lead10.02–29.12min; no exact30min/live-neural claim. Dates consumed; archived report view added, original default/weights retained.123software checks; counter24. Live19snapshots/13501matched persistence outcomes, MAE4.190578. Remaining system limitations above still apply.')
    append('docs/RESEARCH_LOG.md','Reused SRC-DS-003 under existing UCI attribution/rights; no new source or library. Phase choice uses training coverage only. One-time temporal evaluation on previously unscored source dates retains initial-ingestion/blinding and variable-horizon limitations. Official Singapore remains distinct, with its authorized licence/receipts. No private video/CCTV, external publication or paid service used.')
    append('docs/FORECAST_ROBUSTNESS_GUIDE.md','Later update: the timing-coverage study and one-time reserved-date evaluation have now completed. The earlier322window scores above remain their historical cohort. Read docs/FORECAST_FINAL_EVALUATION.md for the1853window result, actual10.02–29.12min target leads, consumed-date restrictions and app report instructions.')
    fields,requirements=table_read('docs/REQUIREMENTS.csv')
    for item in requirements:
        if item['requirement_id']=='SEQ-02':item.update(actual_evidence=item['actual_evidence']+'; models/forecast_final_evaluation.json; forecast_reports.py; FORECAST-FINAL-20261025T101729300425Z',test_result='Frozen later-date gate passes:1853windows/8dates/29eligibleparks, MAE31.724 vs39.072 persistence;123software tests; archived report rendering',open_problems='Variable actual horizon10.02–29.12min; existing-source correlated temporal holdout; consumed dates; no live/camera neural transfer or runtime-weight promotion',next_action='Use saved report for explanation; verify visible UI; new changed models require genuinely fresh final data')
    table_write('docs/REQUIREMENTS.csv',fields,requirements)
    fields,sources=table_read('data/source_manifest.csv')
    for item in sources:
        if item['source_id']=='SRC-DS-003' and FINAL not in item['used_by']:item['used_by']+='; '+PHASE+'; '+FINAL+' (Dec12–19 temporal dates consumed); archived app report'
    table_write('data/source_manifest.csv',fields,sources)
    print(json.dumps(dict(counter=24,tests=123,final_gate_passed=True,metrics=f['metrics'],dates_consumed=True),indent=2))
