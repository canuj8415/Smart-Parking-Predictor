"""One claimed evaluation of the frozen model on the reserved eight later dates."""
import csv,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.forecast_holdouts import evaluate_forecast_once,assert_forecast_dates_closed
from smart_parking.forecast_final_data import reserved_groups
from smart_parking.forecasting import windows_from_groups,tensors,OccupancyLSTM
from smart_parking.forecast_experiment import TrendGuardedOccupancyLSTM
from smart_parking.forecast_robust import occupied_space_predictions
from smart_parking.provenance import digest
REFERENCE='FORECAST-GROUP-ROBUST-20261025T094258007427Z'
DEVELOPMENT='FORECAST-PHASE-20261025T101202713070Z'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    torch.set_num_threads(4);torch.manual_seed(92)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another recorded job is active')
    evidence=ROOT/'experiments/evidence/HEARTBEAT-20261025T100726Z'
    tests=(evidence/'unit_tests.txt').read_text(encoding='utf-8-sig');assert 'Ran 120 tests' in tests and tests.rstrip().endswith('OK')
    replay=json.loads((evidence/'window_refactor_replay.json').read_text());assert all(r['all_fields_equal'] for r in replay['comparisons'])
    development_path=ROOT/'experiments/results'/DEVELOPMENT/'run.json';development=json.loads(development_path.read_text())
    assert development['metrics']['validation_gate_passed'] and development['selected_offset_minutes']==10
    reserved=ROOT/'data/manifests/forecast_fresh_dates_v1.json';reservation=assert_forecast_dates_closed(reserved,root=ROOT)
    checkpoint=ROOT/'experiments/results'/REFERENCE/'candidate.pt';original=ROOT/'models/checkpoints/lstm_30min.pt'
    assert digest(checkpoint)==reservation['selected_checkpoint_sha256']==development['checkpoint_sha256']
    assert digest(original)=='27dc324e0037a00147832dd1d84a3de1b75600e2600c9f429e47da84dac9bc39'
    started=datetime.now(timezone.utc);run='FORECAST-FINAL-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    files=['scripts/evaluate_forecast_final.py','src/smart_parking/forecast_holdouts.py','src/smart_parking/forecast_final_data.py','src/smart_parking/forecasting.py','src/smart_parking/forecast_robust.py','src/smart_parking/forecast_experiment.py']
    hashes={p:digest(ROOT/p) for p in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-DS-003',seed=92,
        hypothesis='The checkpoint frozen before development retains baseline superiority and park-level reliability on eight later dates absent from original recorded test predictions, using the phase fixed by training-only coverage.',
        reservation_sha256=digest(reserved),checkpoint_sha256=digest(checkpoint),production_checkpoint_sha256=digest(original),source_manifest_sha256=reservation['source_manifest_sha256'],
        development_run=DEVELOPMENT,development_result_sha256=digest(development_path),selected_offset_minutes=10,sequence_length=6,horizon_steps=1,max_input_source_age_minutes=20,
        target_rule='Same-day/entity/split/capacity half-hour grid at minute10/40; as-of past readings only; target is genuinely later source reading, with actual source timestamps/ages/horizons exported. No exact30-minute sensor claim.',
        comparators=['Persistence on identical target rows','Original production LSTM with fixed archived weights, same input/target rows'],
        final_gate='>=5% aggregate MAE improvement vs persistence; <=10% per-park regression where n>=10; >=100 final windows; >=80% reserved dates; >=20 eligible parks. No automatic production promotion or re-selection after outcomes.',
        reporting='MAE in spaces; source-row lineage, dates/parks, actual horizons, per-park and prespecified actual-target-lead bins [10,15,20,25,30]. Correlated windows; no IID accuracy claim.',
        membership='Parse exactly all3844 pinned source-row IDs inside durable claim callback. No Dec8–11 original consumed test windows.',
        source_hashes=hashes,code_revision_basis='ade1959 plus sealed phase/guard/refactor snapshots',
        limitations=['Existing-source temporal holdout, not newly blinded external collection','Phase selection used training counts; model fit only original training windows','One frozen model; no seed confirmation or live/camera transfer','A failed or interrupted callback consumes all eight dates and is never retried'])
    protocol_path=folder/'protocol.json';dump(protocol_path,protocol)
    selection_path=folder/'frozen_selection.json';dump(selection_path,dict(validation_gate_passed=True,checkpoint_sha256=digest(checkpoint),reservation_sha256=digest(reserved),final_protocol_sha256=digest(protocol_path),development_result_sha256=digest(development_path)))
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'),warning='Any failure after durable final claim consumes dates')];dump(state_path,state);clock=time.perf_counter()
    try:
        def evaluate(metadata):
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested; final claim consumed')
            groups=reserved_groups(ROOT/reservation['source_manifest'],metadata)
            rows=windows_from_groups(groups,splits=('test',),grid_offset_minutes=10)['test']
            if not rows:return dict(windows=0,final_gate_passed=False,metrics=None,reason='No admissible source-consistent final windows')
            model=TrendGuardedOccupancyLSTM();model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['state_dict']);model.eval()
            production=OccupancyLSTM();production.load_state_dict(torch.load(original,map_location='cpu',weights_only=True)['state_dict']);production.eval()
            predictions=[]
            for at in range(0,len(rows),512):
                if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested; final claim consumed')
                batch=rows[at:at+512];x,y=tensors(batch)
                with torch.inference_mode():candidate=occupied_space_predictions(batch,model(x),x);old=production(x).tolist()
                predictions.extend(dict(**{k:v for k,v in r.items() if k!='x'},actual_occupied=r['y']*r['capacity'],candidate_occupied=p,persistence_occupied=r['baseline']*r['capacity'],original_lstm_occupied=o*r['capacity']) for r,p,o in zip(batch,candidate,old))
            dump(folder/'test_predictions.json',predictions)
            with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
                w=csv.DictWriter(stream,fieldnames=list(predictions[0]));w.writeheader();w.writerows(predictions)
            avg=lambda values,key:sum(abs(r[key]-r['actual_occupied']) for r in values)/len(values) if values else None
            per_park=[dict(car_park_id=p,windows=len(q),candidate_mae=avg(q,'candidate_occupied'),persistence_mae=avg(q,'persistence_occupied'),original_lstm_mae=avg(q,'original_lstm_occupied')) for p in sorted({r['car_park_id'] for r in predictions}) for q in [[r for r in predictions if r['car_park_id']==p]]]
            candidate=avg(predictions,'candidate_occupied');baseline=avg(predictions,'persistence_occupied');improvement=1-candidate/baseline if baseline else None
            failed=[r['car_park_id'] for r in per_park if r['windows']>=10 and r['candidate_mae']>1.1*r['persistence_mae']]
            coverage=len({r['origin'][:10] for r in rows})/len(reservation['reserved_dates']);eligible=sum(r['windows']>=10 for r in per_park)
            bins=[]
            for low,high in zip([10,15,20,25],[15,20,25,30]):
                q=[r for r in predictions if low<=r['actual_target_lead_minutes'] and (r['actual_target_lead_minutes']<high or high==30 and r['actual_target_lead_minutes']<=30)]
                bins.append(dict(low_inclusive_minutes=low,high_minutes=high,last_upper_inclusive=high==30,windows=len(q),candidate_mae=avg(q,'candidate_occupied'),persistence_mae=avg(q,'persistence_occupied')))
            return dict(windows=len(rows),dates=sorted({r['origin'][:10] for r in rows}),eligible_parks=eligible,source_date_coverage=coverage,
                metrics=dict(candidate_mae_spaces=candidate,persistence_mae_spaces=baseline,original_lstm_mae_spaces=avg(predictions,'original_lstm_occupied'),improvement_vs_persistence=improvement),
                per_park=per_park,failed_parks=failed,actual_target_lead_bins=bins,actual_target_lead_minutes=dict(min=min(r['actual_target_lead_minutes'] for r in rows),max=max(r['actual_target_lead_minutes'] for r in rows)),
                final_gate_passed=improvement is not None and improvement>=.05 and not failed and len(rows)>=100 and coverage>=.8 and eligible>=20)
        evaluated=evaluate_forecast_once(reserved,selection_path,checkpoint,protocol_path,run,evaluate,expected_manifest_sha256=protocol['reservation_sha256'],expected_protocol_sha256=digest(protocol_path),root=ROOT)
        assert all(digest(ROOT/p)==h for p,h in hashes.items()) and digest(original)==protocol['production_checkpoint_sha256']
        result=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,final_evaluation=evaluated,production_changed=False,reserved_dates_consumed=True)
        dump(folder/'run.json',result)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,windows=evaluated['windows'],metrics=evaluated['metrics'],gate=evaluated['final_gate_passed'],failed_parks=evaluated.get('failed_parks',[]),duration=result['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False,warning='Check durable claim; never retry consumed dates'));state=json.loads(state_path.read_text());raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)

if __name__=='__main__':main()
