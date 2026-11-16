"""Validation-only residual LSTM experiment; never overwrites production models."""
import csv,json,os,random,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from torch import nn
from .forecasting import build_windows,tensors,OccupancyLSTM
from .provenance import ROOT,digest

class ResidualOccupancyLSTM(nn.Module):
    def __init__(self):
        super().__init__();self.lstm=nn.LSTM(3,24,batch_first=True);self.output=nn.Linear(24,1)
        nn.init.zeros_(self.output.weight);nn.init.zeros_(self.output.bias)
    def forward(self,x):
        sequence,_=self.lstm(x)
        correction=.25*torch.tanh(self.output(sequence[:,-1]).squeeze(-1))
        return (x[:,-1,0]+correction).clamp(0,1)

class TrendGuardedOccupancyLSTM(ResidualOccupancyLSTM):
    """Limit the learned correction to the observed past-hour direction/range."""
    def forward(self,x):
        proposed=super().forward(x)-x[:,-1,0]
        trend=x[:,-1,0]-x[:,-3,0]
        correction=torch.minimum(torch.maximum(proposed,trend.clamp(max=0)),trend.clamp(min=0))
        return (x[:,-1,0]+correction).clamp(0,1)

def train_candidate(epochs=80,patience=12,seed=44,variant='residual'):
    if variant not in {'residual','trend_guard'}:raise ValueError('Unknown forecast candidate variant')
    lock=ROOT/'.cache/forecast_candidate.lock';lock.parent.mkdir(exist_ok=True)
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(descriptor,str(os.getpid()).encode());os.close(descriptor)
    try:return _train(epochs,patience,seed,variant)
    finally:lock.unlink(missing_ok=True)

def _train(epochs,patience,seed,variant):
    torch.set_num_threads(4);torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
    prefix='FORECAST-RESIDUAL-' if variant=='residual' else 'FORECAST-TREND-GUARD-'
    run=prefix+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
    architecture='LSTM(3,24), zero-initialized Linear(24,1), bounded residual plus last occupancy'
    if variant=='trend_guard':architecture+='; correction clipped to observed past-hour occupancy trend interval'
    hypothesis='Learning a bounded correction to persistence reduces validation MAE compared with absolute occupancy prediction.'
    if variant=='trend_guard':hypothesis='Constraining corrections to the recent observed trend reduces cross-car-park regressions under temporal distribution shift.'
    protocol=dict(run_id=run,started_at=started,variant=variant,hypothesis=hypothesis,
        evaluation_scope='Development validation only; no final-test predictions or metrics computed',
        gate='At least 5% lower validation MAE than persistence, with <=10% per-park MAE regression on parks having >=10 validation windows. Passing does not authorize production promotion before fresh final evaluation.',
        architecture=architecture,
        max_epochs=epochs,patience=patience,seed=seed,learning_rate=.001,batch_size=128,optimizer='Adam',
        loss='Capacity-weighted absolute occupancy error; weights derived from training capacities',
        source_id='SRC-DS-003',source_url='https://archive.ics.uci.edu/dataset/482/parking+birmingham',
        horizon_minutes=30,sequence_length=6,split_id='birmingham-global-days-v1',
        input_manifest_sha256=digest(ROOT/'data/splits/birmingham-global-days-v1/manifest.csv'),
        code_sha256=digest(Path(__file__)),window_code_sha256=digest(ROOT/'src/smart_parking/forecasting.py'))
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    windows=build_windows(splits=('train','validation'))
    x,y=tensors(windows['train']);vx,vy=tensors(windows['validation'])
    capacities=np.array([r['capacity'] for r in windows['validation']]);actual=vy.numpy()
    baseline=np.array([r['baseline'] for r in windows['validation']])
    train_rows={i for r in windows['train'] for i in r['input_source_rows']+[r['target_source_row']]}
    val_rows={i for r in windows['validation'] for i in r['input_source_rows']+[r['target_source_row']]}
    if train_rows&val_rows:raise ValueError('Training/validation source-row overlap')
    if max(r['target_time'] for r in windows['train'])>=min(r['origin'] for r in windows['validation']):raise ValueError('Chronological split failure')
    old_path=ROOT/'models/checkpoints/lstm_30min.pt';old=OccupancyLSTM()
    old.load_state_dict(torch.load(old_path,map_location='cpu',weights_only=True)['state_dict']);old.eval()
    with torch.inference_mode():old_pred=old(vx).numpy()
    def mae(pred):return float(np.mean(np.abs(pred-actual)*capacities))
    model=(ResidualOccupancyLSTM() if variant=='residual' else TrendGuardedOccupancyLSTM());optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    train_cap=torch.tensor([r['capacity'] for r in windows['train']],dtype=torch.float32)
    weights=train_cap/train_cap.median();best=mae(baseline);best_epoch=0;stale=0
    best_state={k:v.detach().clone() for k,v in model.state_dict().items()};curves=[]
    for epoch in range(1,epochs+1):
        model.train();total=0;order=torch.randperm(len(y))
        for ids in order.split(128):
            optimizer.zero_grad();loss=(torch.abs(model(x[ids])-y[ids])*weights[ids]).mean()
            loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();total+=loss.item()*len(ids)
        model.eval()
        with torch.inference_mode():pred=model(vx).numpy()
        score=mae(pred);curves.append(dict(epoch=epoch,training_weighted_mae=total/len(y),validation_mae_slots=score))
        if score<best-.001:
            best=score;best_epoch=epoch;best_state={k:v.detach().clone() for k,v in model.state_dict().items()};stale=0
        else:stale+=1
        if epoch%5==0:print(f'{run}: epoch {epoch}, validation MAE {score:.3f}, best {best:.3f}',flush=True)
        if stale>=patience:break
    model.load_state_dict(best_state);model.eval()
    with torch.inference_mode():pred=model(vx).numpy()
    predictions=[]
    for r,a,p,b,o,c in zip(windows['validation'],actual,pred,baseline,old_pred,capacities):
        predictions.append(dict(car_park_id=r['car_park_id'],origin=r['origin'],target_time=r['target_time'],capacity=int(c),
            actual_occupied=float(a*c),candidate_occupied=float(p*c),persistence_occupied=float(b*c),previous_lstm_occupied=float(o*c),
            **{key:r[key] for key in ['input_source_rows','target_source_row','input_grid_times','input_source_times','input_ages_minutes',
                'target_source_time','target_age_minutes','actual_target_lead_minutes','source_to_source_horizon_minutes']}))
    per_park=[]
    for park in sorted({r['car_park_id'] for r in predictions}):
        rows=[r for r in predictions if r['car_park_id']==park]
        avg=lambda key:float(np.mean([abs(r[key]-r['actual_occupied']) for r in rows]))
        per_park.append(dict(car_park_id=park,windows=len(rows),candidate_mae=avg('candidate_occupied'),persistence_mae=avg('persistence_occupied')))
    improvement=1-mae(pred)/mae(baseline)
    gate=improvement>=.05 and all(r['candidate_mae']<=r['persistence_mae']*1.1 for r in per_park if r['windows']>=10)
    checkpoint=folder/'candidate.pt';torch.save(dict(state_dict=best_state,run_id=run,architecture=protocol['architecture']),checkpoint)
    result=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),epochs_completed=len(curves),best_epoch=best_epoch,
        training_seconds=time.perf_counter()-clock,device='cpu',torch_version=str(torch.__version__),
        window_counts={s:len(v) for s,v in windows.items()},test_evaluated=False,production_model_changed=False,
        metrics=dict(candidate_validation_mae_slots=mae(pred),persistence_validation_mae_slots=mae(baseline),
            previous_lstm_validation_mae_slots=mae(old_pred),improvement_vs_persistence=improvement,validation_gate_passed=gate),
        checkpoint_sha256=digest(checkpoint),per_park=per_park,
        limitations=['Single-seed development experiment','Validation selected best epoch and is not an independent final test',
            'Birmingham history only; no Singapore/camera transfer demonstrated','Existing final test untouched and no production promotion'])
    for name,value in [('run.json',result),('curves.json',curves),('validation_predictions.json',predictions)]:
        (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (folder/'validation_predictions.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(predictions[0]));writer.writeheader();writer.writerows(predictions)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    recorded=state.setdefault('completed_run_ids',[])
    if run not in recorded:
        recorded.append(run);state['completed_recorded_runs_since_schedule']=len(recorded)
    state.update(last_completed_run=run,last_updated_at=result['finished_at'],active_training_jobs=[])
    state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    return result
