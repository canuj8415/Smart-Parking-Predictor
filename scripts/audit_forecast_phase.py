"""Select a grid phase by training coverage only, then check one frozen model."""
import csv,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.forecasting import build_windows,tensors
from smart_parking.forecast_experiment import TrendGuardedOccupancyLSTM
from smart_parking.forecast_robust import occupied_space_predictions
from smart_parking.forecast_holdouts import assert_forecast_dates_closed
from smart_parking.provenance import digest
REFERENCE='FORECAST-GROUP-ROBUST-20261025T094258007427Z'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    torch.set_num_threads(4);torch.manual_seed(91)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another recorded job is active')
    started=datetime.now(timezone.utc);run='FORECAST-PHASE-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    checkpoint=ROOT/'experiments/results'/REFERENCE/'candidate.pt';reference=json.loads((checkpoint.parent/'run.json').read_text())
    assert digest(checkpoint)==reference['checkpoint_sha256']
    files=['scripts/audit_forecast_phase.py','src/smart_parking/forecasting.py','src/smart_parking/forecast_robust.py','src/smart_parking/forecast_experiment.py','src/smart_parking/forecast_holdouts.py']
    hashes={p:digest(ROOT/p) for p in files};reserved=ROOT/'data/manifests/forecast_fresh_dates_v1.json'
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-DS-003',seed=91,
        hypothesis='Training-only coverage selection among six clock offsets reduces timing-phase exclusion; one fixed model must retain baseline superiority across the broader development coverage, rather than relying on the sparse original grid.',
        offset_candidates_minutes=[0,5,10,15,20,25],selection='Largest training-window count, tie smallest offset; no training or development prediction errors used for phase selection',
        architecture='Frozen previously trained trend-guarded group-relative LSTM; no refit or threshold changes',
        fixed_rules='Six half-hour as-of inputs, source age<=20min, same day/entity/split/capacity, genuinely later target; absolute target timestamps retained; target readings need not be exactly30min after issue',
        gate='>=5% aggregate MAE improvement and <=10% per-park regression for n>=10; additionally cover >=80% of development source dates and >=20 parks with n>=10. Diagnostic qualification only; no promotion/final evaluation.',
        reference_run=REFERENCE,checkpoint_sha256=digest(checkpoint),source_hashes=hashes,split_manifest_sha256=digest(ROOT/'data/splits/birmingham-global-days-v1/manifest.csv'),reservation_sha256=digest(reserved),
        code_revision_basis='ade1959 plus exact sealed source snapshots',scope='Training coverage and one selected-phase reused-development evaluation only. No numeric reserved-future outcomes or final candidate scoring.')
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        assert_forecast_dates_closed(reserved,root=ROOT)
        coverage=[];train_membership={}
        for phase in protocol['offset_candidates_minutes']:
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
            rows=build_windows(splits=('train',),grid_offset_minutes=phase)['train']
            coverage.append(dict(offset_minutes=phase,windows=len(rows),dates=len({r['origin'][:10] for r in rows}),parks=len({r['car_park_id'] for r in rows})))
            train_membership[phase]={i for r in rows for i in r['input_source_rows']+[r['target_source_row']]}
        phase=min(coverage,key=lambda r:(-r['windows'],r['offset_minutes']))['offset_minutes']
        dump(folder/'frozen_phase_selection.json',dict(selected_offset_minutes=phase,training_coverage=coverage,selection_rule=protocol['selection'],checkpoint_sha256=digest(checkpoint),development_opened=False,at=datetime.now(timezone.utc).isoformat()))
        validation=build_windows(splits=('validation',),grid_offset_minutes=phase)['validation']
        assert validation and not train_membership[phase]&{i for r in validation for i in r['input_source_rows']+[r['target_source_row']]}
        source_dates=set()
        with (ROOT/'data/splits/birmingham-global-days-v1/manifest.csv').open(newline='',encoding='utf-8') as stream:
            for r in csv.DictReader(stream):
                if r['split']=='validation':source_dates.add(r['capture_date'])
        model=TrendGuardedOccupancyLSTM();model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['state_dict']);model.eval();predictions=[]
        for at in range(0,len(validation),512):
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
            rows=validation[at:at+512];x,y=tensors(rows)
            with torch.inference_mode():pred=occupied_space_predictions(rows,model(x),x)
            predictions.extend(dict(**{k:v for k,v in r.items() if k!='x'},actual_occupied=r['y']*r['capacity'],candidate_occupied=p,persistence_occupied=r['baseline']*r['capacity']) for r,p in zip(rows,pred))
        avg=lambda rows,key:sum(abs(r[key]-r['actual_occupied']) for r in rows)/len(rows)
        per_park=[dict(car_park_id=p,windows=len(q),candidate_mae=avg(q,'candidate_occupied'),persistence_mae=avg(q,'persistence_occupied')) for p in sorted({r['car_park_id'] for r in predictions}) for q in [[r for r in predictions if r['car_park_id']==p]]]
        candidate=avg(predictions,'candidate_occupied');baseline=avg(predictions,'persistence_occupied');improvement=1-candidate/baseline
        failed=[r['car_park_id'] for r in per_park if r['windows']>=10 and r['candidate_mae']>1.1*r['persistence_mae']]
        date_coverage=len({r['origin'][:10] for r in predictions})/len(source_dates);eligible=sum(r['windows']>=10 for r in per_park)
        gate=improvement>=.05 and not failed and date_coverage>=.8 and eligible>=20
        assert digest(checkpoint)==reference['checkpoint_sha256'] and all(digest(ROOT/p)==h for p,h in hashes.items())
        assert_forecast_dates_closed(reserved,root=ROOT)
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,selected_offset_minutes=phase,training_coverage=coverage,
            metrics=dict(windows=len(predictions),candidate_mae_spaces=candidate,persistence_mae_spaces=baseline,improvement_vs_persistence=improvement,validation_gate_passed=gate,source_date_coverage=date_coverage,eligible_parks=eligible),
            per_park=per_park,failed_parks=failed,validation_dates=sorted({r['origin'][:10] for r in predictions}),actual_target_lead_minutes=dict(min=min(r['actual_target_lead_minutes'] for r in predictions),max=max(r['actual_target_lead_minutes'] for r in predictions)),
            final_evaluated=False,model_training_performed=False,production_changed=False)
        dump(folder/'run.json',report);dump(folder/'validation_predictions.json',predictions)
        with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(predictions[0]));writer.writeheader();writer.writerows(predictions)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,phase=phase,metrics=report['metrics'],failed_parks=failed,duration=report['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False));state=json.loads(state_path.read_text());raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)

if __name__=='__main__':main()
