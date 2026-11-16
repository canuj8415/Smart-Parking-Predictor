"""Audit source timestamps on development windows with frozen saved predictions.

No training, model selection, new predictions or final-test scoring occurs.
"""
import csv,hashlib,json,subprocess,sys,time,types
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.forecasting import build_windows
from smart_parking.provenance import digest

BASE='c757d7f'
CANDIDATE='FORECAST-TREND-GUARD-20261024T164720136309Z'

if __name__=='__main__':
    started=datetime.now(timezone.utc);clock=time.perf_counter()
    run='FORECAST-TIMING-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    reference_bytes=subprocess.check_output(['git','show',BASE+':src/smart_parking/forecasting.py'],cwd=ROOT)
    predictions_path=ROOT/'experiments/results'/CANDIDATE/'validation_predictions.json'
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-DS-003',seed='Not applicable: deterministic metadata audit of frozen predictions',
        hypothesis='Retaining actual as-of sensor timestamps reveals the effective target lead while leaving all earlier model inputs, targets, membership and saved prediction scores unchanged',
        scope='Train/validation only; prior selected candidate remains development-only; no new final/test predictions or selection',
        prespecified_bins_minutes=[10,15,20,25,30],bin_policy='Left-inclusive/right-exclusive; final bin includes30',
        source_manifest_sha256=digest(ROOT/'data/splits/birmingham-global-days-v1/manifest.csv'),reference_git_revision=BASE,
        reference_window_code_sha256=hashlib.sha256(reference_bytes).hexdigest(),candidate_run_id=CANDIDATE,frozen_predictions_sha256=digest(predictions_path),
        code_sha256=digest(Path(__file__)),window_code_sha256=digest(ROOT/'src/smart_parking/forecasting.py'),
        gate='Exact equality of all original train/validation window fields; all inputs as-of <=20m; actual target later than issue; unique exact join of frozen predictions; no retraining or gate/promotion change',
        caveats=['Source timezone unspecified: preserve original wall-clock times','Nominal grid horizon is30min; as-of target is a prior real reading, not a measured value at the grid instant','Stratified development errors are descriptive, not new independent accuracy evidence'])
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    sources={p:dict(sha256=digest(ROOT/p),source=(ROOT/p).read_text(encoding='utf-8')) for p in ['scripts/audit_forecast_timing.py','src/smart_parking/forecasting.py']}
    sources['reference_window_module']=dict(sha256=hashlib.sha256(reference_bytes).hexdigest(),source=reference_bytes.decode())
    (folder/'implementation_sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    reference=types.ModuleType('smart_parking.forecasting_reference');reference.__package__='smart_parking';reference.__file__='sealed_reference_forecasting.py'
    exec(compile(reference_bytes,reference.__file__,'exec'),reference.__dict__)
    old=reference.build_windows(splits=('train','validation'));new=build_windows(splits=('train','validation'))
    for split in old:
        assert len(old[split])==len(new[split])
        for before,after in zip(old[split],new[split]):
            assert {k:after[k] for k in before}==before
            origin=datetime.fromisoformat(after['origin']);target=datetime.fromisoformat(after['target_time'])
            assert (target-origin).total_seconds()/60==30
            assert 0<=after['target_age_minutes']<=20 and 10<=after['actual_target_lead_minutes']<=30
            for grid,source,age in zip(after['input_grid_times'],after['input_source_times'],after['input_ages_minutes']):
                assert 0<=age<=20 and datetime.fromisoformat(source)<=datetime.fromisoformat(grid)<=origin
            assert datetime.fromisoformat(after['target_source_time'])>origin
    source_sets={s:{i for row in values for i in row['input_source_rows']+[row['target_source_row']]} for s,values in new.items()}
    assert not source_sets['train']&source_sets['validation']
    def key(row):return row['car_park_id'],row['origin'],row['target_time'],row['capacity']
    frozen=json.loads(predictions_path.read_text());lookup={key(row):row for row in frozen}
    assert len(lookup)==len(frozen)==len(new['validation'])
    joined=[]
    for row in new['validation']:
        saved=lookup[key(row)]
        assert abs(saved['actual_occupied']-row['y']*row['capacity'])<.001
        assert abs(saved['persistence_occupied']-row['baseline']*row['capacity'])<.001
        joined.append({**{k:v for k,v in row.items() if k!='x'},**saved})
    def metrics(values):
        return dict(windows=len(values),**{name:float(np.mean([abs(r[column]-r['actual_occupied']) for r in values])) if values else None
            for name,column in [('candidate_mae_spaces','candidate_occupied'),('persistence_mae_spaces','persistence_occupied'),('previous_lstm_mae_spaces','previous_lstm_occupied')]})
    strata=[]
    for low,high in zip([10,15,20,25],[15,20,25,30]):
        group=[r for r in joined if low<=r['actual_target_lead_minutes'] and (r['actual_target_lead_minutes']<high or high==30 and r['actual_target_lead_minutes']<=high)]
        strata.append(dict(actual_target_lead_bin=f'{low}-{high}min',**metrics(group)))
    distributions={}
    for split,values in new.items():
        distributions[split]={}
        for field in ['actual_target_lead_minutes','source_to_source_horizon_minutes','target_age_minutes']:
            numbers=[r[field] for r in values]
            distributions[split][field]=dict(min=min(numbers),median=float(np.median(numbers)),max=max(numbers))
    original=json.loads(predictions_path.with_name('run.json').read_text())
    aggregate=metrics(joined)
    assert abs(aggregate['candidate_mae_spaces']-original['metrics']['candidate_validation_mae_slots'])<1e-5
    assert abs(aggregate['persistence_mae_spaces']-original['metrics']['persistence_validation_mae_slots'])<1e-5
    report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
        window_counts={s:len(v) for s,v in new.items()},original_fields_exactly_unchanged=True,training_validation_source_rows_disjoint=True,
        source_time_invariants_passed=True,distributions=distributions,validation_aggregate=aggregate,validation_by_actual_lead=strata,
        candidate_validation_gate_passed=original['metrics']['validation_gate_passed'],production_changed=False,final_test_evaluated=False,model_training_performed=False)
    (folder/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (folder/'validation_timing.json').write_text(json.dumps(joined,indent=2),encoding='utf-8')
    with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
        fields=['car_park_id','origin','target_time','target_source_time','target_age_minutes','actual_target_lead_minutes','source_to_source_horizon_minutes','actual_occupied','candidate_occupied','persistence_occupied']
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(joined)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text());state['completed_run_ids'].append(run)
    state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run
    state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(json.dumps(dict(run_id=run,window_counts=report['window_counts'],distributions=distributions,validation_by_actual_lead=strata,aggregate=aggregate),indent=2),flush=True)
