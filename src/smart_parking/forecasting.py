"""Capacity-normalized LSTM forecasts on causal, gap-checked historical windows."""
import csv
import json
import math
import random
import time
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader,TensorDataset
from .provenance import ROOT,digest

class OccupancyLSTM(nn.Module):
    def __init__(self):
        super().__init__();self.lstm=nn.LSTM(3,24,batch_first=True);self.output=nn.Linear(24,1)
    def forward(self,x):
        sequence,_=self.lstm(x)
        return torch.sigmoid(self.output(sequence[:,-1])).squeeze(-1)

def build_windows(root=ROOT,length=6,horizon_steps=1,splits=('train','validation','test'),grid_offset_minutes=0):
    """At each half-hour boundary, use only a prior real observation <=20m old.

    The resulting grid is explicitly derived by causal carry-forward, not new
    sensor measurements. Windows must stay in one day/entity/split/capacity.
    """
    groups=defaultdict(list)
    if not isinstance(grid_offset_minutes,int) or isinstance(grid_offset_minutes,bool) or not 0<=grid_offset_minutes<30:
        raise ValueError('Grid offset must be an integer from 0 to 29 minutes')
    if not splits or set(splits)-{'train','validation','test'}:raise ValueError('Invalid forecast splits')
    path=Path(root)/'data/splits/birmingham-global-days-v1/manifest.csv'
    if 'test' in splits and (Path(root)/'data/manifests/forecast_fresh_dates_v1.json').exists():
        raise ValueError('Fresh forecast dates are reserved. Use a separate guarded one-time final evaluator; legacy test-window loading is blocked.')
    with path.open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            if row['split'] not in splits:continue
            key=(row['car_park_id'],row['capture_date'],row['split'],int(row['capacity']))
            groups[key].append((datetime.fromisoformat(row['timestamp']),int(row['occupancy']),int(row['source_row'])))
    return windows_from_groups(groups,length=length,horizon_steps=horizon_steps,splits=splits,grid_offset_minutes=grid_offset_minutes)


def windows_from_groups(groups,*,length=6,horizon_steps=1,splits=('train','validation'),grid_offset_minutes=0):
    """Pure as-of construction; callers control access to already parsed records."""
    if not isinstance(grid_offset_minutes,int) or isinstance(grid_offset_minutes,bool) or not 0<=grid_offset_minutes<30:
        raise ValueError('Grid offset must be an integer from 0 to 29 minutes')
    windows={s:[] for s in splits}
    for (park,day,split,capacity),records in sorted(groups.items()):
        records.sort();times=[r[0] for r in records]
        start=times[0].replace(minute=(times[0].minute//30)*30,second=0,microsecond=0)
        start+=timedelta(minutes=grid_offset_minutes)
        if start>times[0]:start-=timedelta(minutes=30)
        grid=[];at=start
        while at<=times[-1]:
            index=bisect_right(times,at)-1
            if index>=0 and timedelta(0)<=at-times[index]<=timedelta(minutes=20):
                observed,count,row=records[index];hour=at.hour+at.minute/60
                grid.append(dict(time=at,source_time=observed,source_age_minutes=(at-observed).total_seconds()/60,source_row=row,occupancy=count,
                    feature=[count/capacity,math.sin(2*math.pi*hour/24),math.cos(2*math.pi*hour/24)]))
            else:grid.append(None)
            at+=timedelta(minutes=30)
        for end in range(length-1,len(grid)-horizon_steps):
            block=grid[end-length+1:end+horizon_steps+1]
            if any(r is None for r in block):continue
            past=block[:length];target=block[-1]
            # Target must use a genuinely later sensor observation.
            if target['source_row'] in {p['source_row'] for p in past}:continue
            windows[split].append(dict(x=[p['feature'] for p in past],y=target['occupancy']/capacity,
                capacity=capacity,baseline=past[-1]['occupancy']/capacity,car_park_id=park,
                origin=past[-1]['time'].isoformat(),target_time=target['time'].isoformat(),
                target_source_row=target['source_row'],input_source_rows=[p['source_row'] for p in past],
                input_grid_times=[p['time'].isoformat() for p in past],input_source_times=[p['source_time'].isoformat() for p in past],
                input_ages_minutes=[p['source_age_minutes'] for p in past],target_source_time=target['source_time'].isoformat(),
                target_age_minutes=target['source_age_minutes'],actual_target_lead_minutes=(target['source_time']-past[-1]['time']).total_seconds()/60,
                source_to_source_horizon_minutes=(target['source_time']-past[-1]['source_time']).total_seconds()/60))
    return windows

def tensors(rows):
    return torch.tensor(np.array([r['x'] for r in rows]),dtype=torch.float32),torch.tensor([r['y'] for r in rows],dtype=torch.float32)

def train_forecast(epochs=18,horizon_steps=1):
    torch.set_num_threads(4);torch.manual_seed(42);np.random.seed(42);random.seed(42)
    windows=build_windows(horizon_steps=horizon_steps)
    if any(len(windows[s])<10 for s in windows):raise ValueError('Insufficient independent chronological windows')
    xtrain,ytrain=tensors(windows['train']);xval,yval=tensors(windows['validation'])
    model=OccupancyLSTM();optimizer=torch.optim.Adam(model.parameters(),lr=.003)
    loader=DataLoader(TensorDataset(xtrain,ytrain),batch_size=128,shuffle=True,generator=torch.Generator().manual_seed(42))
    run='LSTM-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    best=float('inf');best_state=None;curves=[];start=time.perf_counter()
    for epoch in range(epochs):
        model.train();total=0
        for x,y in loader:
            optimizer.zero_grad();prediction=model(x);loss=nn.functional.mse_loss(prediction,y)
            loss.backward();optimizer.step();total+=loss.item()*len(y)
        model.eval()
        with torch.inference_mode():validation=nn.functional.mse_loss(model(xval),yval).item()
        curves.append(dict(epoch=epoch+1,train_mse=total/len(ytrain),validation_mse=validation))
        if validation<best:best=validation;best_state={k:v.detach().clone() for k,v in model.state_dict().items()}
        print(f'LSTM epoch {epoch+1}: train {curves[-1]["train_mse"]:.5f} validation {validation:.5f}',flush=True)
    model.load_state_dict(best_state);model.eval();xtest,ytest=tensors(windows['test'])
    with torch.inference_mode():pred=model(xtest).numpy()
    actual=ytest.numpy();capacities=np.array([r['capacity'] for r in windows['test']])
    baseline=np.array([r['baseline'] for r in windows['test']])
    predictions=[{**{k:v for k,v in r.items() if k!='x'},'actual_occupied':float(y*c),'predicted_occupied':float(p*c),
                  'persistence_occupied':float(b*c)} for r,y,p,b,c in zip(windows['test'],actual,pred,baseline,capacities)]
    metrics=dict(mae_slots=float(np.mean(np.abs(pred-actual)*capacities)),
        persistence_mae_slots=float(np.mean(np.abs(baseline-actual)*capacities)),
        normalized_mae=float(np.mean(np.abs(pred-actual))),test_windows=len(pred),
        training_seconds=time.perf_counter()-start)
    checkpoint=ROOT/f'models/checkpoints/lstm_{horizon_steps*30}min.pt';checkpoint.parent.mkdir(parents=True,exist_ok=True)
    bundle=dict(state_dict=best_state,architecture='LSTM(3,24)+Linear+Sigmoid',run_id=run,
        horizon_minutes=horizon_steps*30,sequence_length=6,source_id='SRC-DS-003',
        preprocessing='30-minute causal as-of grid, max source age 20 minutes; same-day windows; no future fill',
        seed=42,metrics=metrics)
    torch.save(bundle,checkpoint)
    config=dict(run_id=run,source_id='SRC-DS-003',split_id='birmingham-global-days-v1',
        epochs=epochs,learning_rate=.003,batch_size=128,seed=42,horizon_minutes=horizon_steps*30,
        sequence_length=6,window_counts={s:len(v) for s,v in windows.items()},
        input_manifest_sha256=digest(ROOT/'data/splits/birmingham-global-days-v1/manifest.csv'),
        code_sha256=digest(Path(__file__)),checkpoint_sha256=digest(checkpoint),
        torch_version=torch.__version__,device='cpu',metrics=metrics,
        limitations=['Derived causal grid, not raw uniform sensor measurements','Birmingham historical domain only',
                     'No proven transfer to Singapore live feed or camera-derived occupancy','Approximate capacity-normalized cross-entity model',
                     'Held-out results may be worse than persistence; do not claim superiority unless measured'])
    for name,value in [('run.json',config),('curves.json',curves),('test_predictions.json',predictions)]:
        (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    # Model metadata is small and tracked independently of weight binaries.
    (ROOT/f'models/lstm_{horizon_steps*30}min_model_card.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    return config

def load_forecast(horizon_minutes=30):
    path=ROOT/f'models/checkpoints/lstm_{horizon_minutes}min.pt'
    if not path.exists():raise FileNotFoundError('Train the historical LSTM first.')
    bundle=torch.load(path,map_location='cpu',weights_only=True)
    model=OccupancyLSTM();model.load_state_dict(bundle['state_dict']);model.eval()
    return model,bundle
