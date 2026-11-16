"""One bounded group-relative LSTM trial; all epoch selection stays in training."""
import csv,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.forecasting import build_windows,tensors
from smart_parking.forecast_experiment import TrendGuardedOccupancyLSTM
from smart_parking.forecast_robust import blocked_folds,fit_risk_scales,group_relative_loss,occupied_space_predictions
from smart_parking.provenance import digest
from smart_parking.checkpointing import save_checkpoint_atomic

def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def seeded_model(seed):torch.manual_seed(seed);return TrendGuardedOccupancyLSTM()

def main():
    torch.set_num_threads(4);np.random.seed(81)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another recorded job is active')
    lock=ROOT/'.cache/forecast_candidate.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    started=datetime.now(timezone.utc);run='FORECAST-GROUP-ROBUST-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    files=['scripts/train_robust_forecast.py','src/smart_parking/forecast_robust.py','src/smart_parking/forecast_experiment.py','src/smart_parking/forecasting.py','src/smart_parking/checkpointing.py']
    hashes={p:digest(ROOT/p) for p in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-DS-003',split_id='birmingham-global-days-v1',
        seed=81,fold_seeds=[81,82,83],refit_seed=84,max_epochs=80,patience=12,minimum_improvement=.0001,optimizer='Adam',learning_rate=.001,batch_size='full fitting prefix',
        hypothesis='A half mean/half worst-park relative MAE objective and training-only blocked epoch selection reduce per-park regressions compared with capacity-dominated residual training. Two procedure changes; not a single-factor causal ablation.',
        architecture='Existing TrendGuardedOccupancyLSTM; no new features or park-ID input',
        objective='0.5 mean park normalized MAE + 0.5 maximum park normalized MAE; risk denominator is fitting-prefix persistence MAE in spaces floored at 1; unseen park denominator is median fitted park risk',
        selection='Three expanding whole-date folds at 40/60/80/100 percent of training dates; choose common epoch by mean held-prefix objective, including epoch zero. Refit all training at that fixed epoch count; open development only after checkpoint frozen.',
        output='Apply float32 model correction relative to float32 origin to original source occupancy count, clip to [0,capacity]; zero correction exactly matches persistence',
        gate='Same >=5% aggregate development MAE improvement and <=10% per-park MAE regression for parks with >=10 windows; no production promotion or final evaluation',
        code_revision_basis='6fb0e7a plus exact sealed source snapshots',source_hashes=hashes,
        split_manifest_sha256=digest(ROOT/'data/splits/birmingham-global-days-v1/manifest.csv'),
        scope='Birmingham training and reused development only. Existing final is consumed and never loaded here. No Singapore/camera transfer or independent final accuracy claim.')
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_training_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    clock=time.perf_counter()
    try:
        train=build_windows(splits=('train',))['train'];folds=blocked_folds(train);fold_data=[];audit=[]
        for i,(fit,tune) in enumerate(folds):
            x,y=tensors(fit);vx,vy=tensors(tune);scales=fit_risk_scales(fit);model=seeded_model(81+i)
            fold_data.append((model,torch.optim.Adam(model.parameters(),lr=.001),x,y,vx,vy,fit,tune,scales))
            audit.append(dict(fold=i+1,fit_windows=len(fit),tuning_windows=len(tune),fit_dates=sorted({r['origin'][:10] for r in fit}),tuning_dates=sorted({r['origin'][:10] for r in tune}),
                risk_scales=scales,unseen_tuning_parks=sorted({r['car_park_id'] for r in tune}-{r['car_park_id'] for r in fit}),
                fit_source_rows=sorted({j for r in fit for j in r['input_source_rows']+[r['target_source_row']]}),tuning_source_rows=sorted({j for r in tune for j in r['input_source_rows']+[r['target_source_row']]})))
        dump(folder/'training_fold_audit.json',audit)
        def score_folds():
            values=[]
            for model,_,_,_,vx,vy,_,tune,scales in fold_data:
                model.eval()
                with torch.inference_mode():values.append(float(group_relative_loss(model(vx),vy,tune,scales)))
            return values
        initial=score_folds();best=float(np.mean(initial));best_epoch=0;stale=0;curves=[dict(epoch=0,inner_fold_scores=initial,mean_inner_objective=best)]
        for epoch in range(1,81):
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested; no completed trial counted')
            losses=[]
            for model,opt,x,y,_,_,fit,_,scales in fold_data:
                model.train();opt.zero_grad();loss=group_relative_loss(model(x),y,fit,scales);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step();losses.append(float(loss.detach()))
            scores=score_folds();score=float(np.mean(scores));curves.append(dict(epoch=epoch,fitting_objectives=losses,inner_fold_scores=scores,mean_inner_objective=score))
            dump(folder/'curves.json',curves)
            if score<best-.0001:
                best=score;best_epoch=epoch;stale=0
                save_checkpoint_atomic(dict(run_id=run,epoch=epoch,fold_states=[m.state_dict() for m,*_ in fold_data]),folder/'inner_best.pt')
            else:stale+=1
            if epoch%10==0:print(f'{run}: inner epoch {epoch}, selected {best_epoch}, objective {best:.5f}',flush=True)
            if stale>=12:break
        dump(folder/'frozen_epoch_selection.json',dict(selected_epoch=best_epoch,initial_inner_objective=float(np.mean(initial)),selected_inner_objective=best,inner_epochs_completed=len(curves)-1,development_targets_opened=False))
        model=seeded_model(84);opt=torch.optim.Adam(model.parameters(),lr=.001);x,y=tensors(train);scales=fit_risk_scales(train);refit=[]
        for epoch in range(1,best_epoch+1):
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
            model.train();opt.zero_grad();loss=group_relative_loss(model(x),y,train,scales);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step();refit.append(dict(epoch=epoch,training_objective=float(loss.detach())))
            save_checkpoint_atomic(dict(run_id=run,epoch=epoch,state_dict=model.state_dict(),risk_scales=scales),folder/'refit_latest.pt')
        dump(folder/'refit_curves.json',refit)
        checkpoint=folder/'candidate.pt';save_checkpoint_atomic(dict(run_id=run,state_dict=model.state_dict(),selected_epoch=best_epoch,risk_scales=scales,output=protocol['output']),checkpoint)
        frozen_hash=digest(checkpoint);dump(folder/'frozen_before_development.json',dict(checkpoint_sha256=frozen_hash,selected_epoch=best_epoch,at=datetime.now(timezone.utc).isoformat(),development_targets_opened=False))
        validation=build_windows(splits=('validation',))['validation'];vx,vy=tensors(validation)
        train_ids={i for r in train for i in r['input_source_rows']+[r['target_source_row']]};val_ids={i for r in validation for i in r['input_source_rows']+[r['target_source_row']]}
        assert not train_ids&val_ids and max(r['target_time'] for r in train)<min(r['origin'] for r in validation)
        model.eval()
        with torch.inference_mode():pred=occupied_space_predictions(validation,model(vx),vx)
        predictions=[dict(**{k:v for k,v in r.items() if k!='x'},actual_occupied=r['y']*r['capacity'],candidate_occupied=p,persistence_occupied=r['baseline']*r['capacity']) for r,p in zip(validation,pred)]
        avg=lambda rows,key:float(np.mean([abs(r[key]-r['actual_occupied']) for r in rows]))
        per_park=[dict(car_park_id=p,windows=len(q),candidate_mae=avg(q,'candidate_occupied'),persistence_mae=avg(q,'persistence_occupied')) for p in sorted({r['car_park_id'] for r in predictions}) for q in [[r for r in predictions if r['car_park_id']==p]]]
        candidate=avg(predictions,'candidate_occupied');baseline=avg(predictions,'persistence_occupied');improvement=1-candidate/baseline
        failed=[r['car_park_id'] for r in per_park if r['windows']>=10 and r['candidate_mae']>r['persistence_mae']*1.1]
        assert digest(checkpoint)==frozen_hash and all(digest(ROOT/p)==h for p,h in hashes.items())
        result=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,selected_epoch=best_epoch,inner_epochs_completed=len(curves)-1,
            window_counts=dict(train=len(train),validation=len(validation)),checkpoint_sha256=frozen_hash,metrics=dict(candidate_mae_spaces=candidate,persistence_mae_spaces=baseline,improvement_vs_persistence=improvement,validation_gate_passed=improvement>=.05 and not failed),
            per_park=per_park,failed_parks=failed,actual_target_lead_minutes=dict(min=min(r['actual_target_lead_minutes'] for r in validation),max=max(r['actual_target_lead_minutes'] for r in validation)),
            final_evaluated=False,production_changed=False,torch_version=str(torch.__version__))
        dump(folder/'run.json',result);dump(folder/'validation_predictions.json',predictions)
        with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(predictions[0]));writer.writeheader();writer.writerows(predictions)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,selected_epoch=best_epoch,metrics=result['metrics'],failed_parks=failed,duration=result['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False));state=json.loads(state_path.read_text());raise
    finally:
        state['active_training_jobs']=[];dump(state_path,state);lock.unlink(missing_ok=True)

if __name__=='__main__':main()
