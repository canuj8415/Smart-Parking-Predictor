"""Known-camera segmentation study with previously unused date holdouts.

This evaluates deployment views represented in training, not unseen-camera
generalization. A train-only camera geometry baseline is an explicit comparator.
"""
import csv,json,os,random,re,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from torchvision.transforms import functional as TF
from .training import ParkingUNet
from .layout import read_pklot_xml,union_mask
from .provenance import ROOT,digest

CAMERAS={'parking1a':'ufpr04','parking1b':'ufpr05','parking2':'pucpr'}

def reserve_frames(pairs,excluded_days):
    groups=defaultdict(lambda:defaultdict(list))
    for pair in pairs:
        try:datetime.strptime(pair['date'],'%Y-%m-%d')
        except ValueError:continue
        if pair['date'] in excluded_days:continue
        folder=Path(pair['image']).parts[4]
        if folder in CAMERAS:groups[CAMERAS[folder]][pair['date']].append(pair)
    selected=[]
    for camera in sorted(CAMERAS.values()):
        days=sorted(day for day,options in groups[camera].items() if len(options)>=2)
        if len(days)<8:raise ValueError('Insufficient fresh dates for '+camera)
        days=[days[i] for i in np.linspace(0,len(days)-1,8,dtype=int)]
        for j,day in enumerate(days):
            options=sorted(groups[camera][day],key=lambda r:r['image'])
            if len(options)<2:raise ValueError('Need two frames per reserved date')
            for i in [0,len(options)-1]:
                selected.append(dict(**options[i],camera_id=camera,split='train' if j<6 else 'validation' if j==6 else 'test'))
    day_sets={s:{r['date'] for r in selected if r['split']==s} for s in ['train','validation','test']}
    if any(day_sets[a]&day_sets[b] for a,b in [('train','validation'),('train','test'),('validation','test')]):raise ValueError('Capture dates overlap splits')
    return selected

def mask_metrics(predicted,actual):
    p=np.asarray(predicted,dtype=bool);a=np.asarray(actual,dtype=bool)
    intersection=int((p&a).sum());union=int((p|a).sum());size=int(p.sum()+a.sum())
    return dict(pixel_iou=intersection/union if union else 1.,dice=2*intersection/size if size else 1.,pixels=int(a.size))

def _load(rows):
    images=[];masks=[]
    for row in rows:
        image=Image.open(ROOT/row['image']).convert('RGB');layout=read_pklot_xml(ROOT/row['annotation'],image.size)
        if layout['camera_id']!=row['camera_id']:raise ValueError('Camera mapping mismatch')
        images.append(TF.to_tensor(image.resize((192,112))));masks.append(TF.to_tensor(union_mask(layout,(192,112))))
    return torch.stack(images),torch.stack(masks)

def train_known_camera(epochs=100,patience=15,seed=53,resume_preparation=False):
    lock=ROOT/'.cache/segmentation_candidate.lock';lock.parent.mkdir(exist_ok=True)
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(descriptor,str(os.getpid()).encode());os.close(descriptor)
    try:return _train(epochs,patience,seed,resume_preparation)
    finally:lock.unlink(missing_ok=True)

def _train(epochs,patience,seed,resume_preparation):
    manifest=ROOT/'data/manifests/segmentation_known_camera_v1.json'
    if manifest.exists() and not resume_preparation:raise FileExistsError('Reserved study already exists; do not silently reuse its final holdout')
    torch.set_num_threads(4);torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
    if resume_preparation:
        reservation=json.loads(manifest.read_text());run=reservation['run_id'];folder=ROOT/'experiments/results'/run
        if (folder/'candidate.pt').exists() or (folder/'selection_closed.json').exists():raise ValueError('Cannot resume preparation after model selection')
        rows=reservation['frames'];excluded=set(reservation['excluded_previously_used_dates'])
        initial=folder/'initial_protocol.json'
        if not initial.exists():initial.write_bytes((folder/'protocol.json').read_bytes())
    else:
        run='SEGMENTATION-KNOWN-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
        excluded={re.search(r'\d{4}-\d{2}-\d{2}',p.name).group() for p in (ROOT/'configs/layouts').glob('*.json') if re.search(r'\d{4}-\d{2}-\d{2}',p.name)}
        excluded.update(json.loads((ROOT/'models/segmentation_model_card.json').read_text())['final_test_dates'])
        pairs=json.loads((ROOT/'data/raw/pklot_subset/acquisition.json').read_text())['pairs'];rows=reserve_frames(pairs,excluded)
    hashes=[]
    for row in rows:row['image_sha256']=digest(ROOT/row['image']);hashes.append(row['image_sha256'])
    if len(hashes)!=len(set(hashes)):raise ValueError('Duplicate images in reserved study')
    reservation=dict(run_id=run,policy='Three known cameras; eight previously unselected dates each; six train, one validation, one final test date; first/last frames per date',excluded_previously_used_dates=sorted(excluded),frames=rows)
    if not resume_preparation:manifest.write_text(json.dumps(reservation,indent=2),encoding='utf-8')
    old_checkpoint=ROOT/'models/checkpoints/parking_unet.pt'
    protocol=dict(run_id=run,source_id='SRC-DS-001',source_url='https://web.inf.ufpr.br/vri/databases/parking-lot-database/',started_at=datetime.now(timezone.utc).isoformat(),seed=seed,
        hypothesis='Training on multiple dates from each deployment camera improves held-out-date region masks compared with the old unseen-camera split.',
        scope='Known-camera, new held-out dates only; not unseen-location or universal segmentation accuracy',
        architecture='Existing small U-Net 3-8-16-8-1',max_epochs=epochs,patience=patience,batch_size=4,learning_rate=.003,optimizer='Adam',
        loss='Train-only weighted BCE plus soft Dice',augmentation='Train-only brightness multiplier uniformly 0.85-1.15; masks unchanged',
        selection='Highest validation IoU at fixed probability threshold 0.5; early stopping patience 15',
        comparator='Original model and train-only majority parking mask per known camera',
        gate='Final candidate IoU >=0.75, every camera >=0.70 and aggregate within 0.05 of the train-only camera geometry baseline. No automatic production promotion.',
        manifest_sha256=digest(manifest),code_sha256=digest(Path(__file__)),layout_code_sha256=digest(ROOT/'src/smart_parking/layout.py'),training_model_code_sha256=digest(ROOT/'src/smart_parking/training.py'),old_checkpoint_sha256=digest(old_checkpoint),
        preparation_recovery='Same reserved frames retained; source XML point/Point case handling corrected before training' if resume_preparation else None,
        annotation_sha256={r['annotation']:digest(ROOT/r['annotation']) for r in rows})
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    (folder/'split_frames.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation'];test=[r for r in rows if r['split']=='test']
    x,y=_load(train);vx,vy=_load(val);positive=y.mean().item();weight=torch.tensor((1-positive)/max(.001,positive))
    def loss_fn(logits,target):
        probability=logits.sigmoid();intersection=(probability*target).sum((1,2,3))
        dice=1-((2*intersection+1)/(probability.sum((1,2,3))+target.sum((1,2,3))+1)).mean()
        return torch.nn.functional.binary_cross_entropy_with_logits(logits,target,pos_weight=weight)+dice
    geometry={camera:(y[[i for i,r in enumerate(train) if r['camera_id']==camera]].mean(0)>=.5) for camera in CAMERAS.values()}
    model=ParkingUNet();optimizer=torch.optim.Adam(model.parameters(),lr=.003);best=-1;state=None;best_epoch=0;stale=0;curves=[];clock=time.perf_counter()
    for epoch in range(1,epochs+1):
        model.train();order=torch.randperm(len(train));total=0
        for batch in order.split(4):
            augment=torch.empty(len(batch),1,1,1).uniform_(.85,1.15)
            optimizer.zero_grad();loss=loss_fn(model((x[batch]*augment).clamp(0,1)),y[batch]);loss.backward();optimizer.step();total+=loss.item()*len(batch)
        model.eval()
        with torch.inference_mode():prediction=model(vx).sigmoid()>=.5
        score=mask_metrics(prediction.numpy(),(vy>=.5).numpy())['pixel_iou'];curves.append(dict(epoch=epoch,training_loss=total/len(train),validation_iou=score))
        if score>best+.0001:best=score;best_epoch=epoch;state={k:v.detach().clone() for k,v in model.state_dict().items()};stale=0
        else:stale+=1
        if epoch%10==0:print(f'{run}: epoch {epoch}, validation IoU {score:.4f}, best {best:.4f}',flush=True)
        if stale>=patience:break
    model.load_state_dict(state);model.eval();checkpoint=folder/'candidate.pt';torch.save(dict(state_dict=state,run_id=run,input_size=[192,112]),checkpoint)
    (folder/'selection_closed.json').write_text(json.dumps(dict(closed_at=datetime.now(timezone.utc).isoformat(),best_epoch=best_epoch,validation_iou=best,checkpoint_sha256=digest(checkpoint)),indent=2),encoding='utf-8')
    # Final labels/images are loaded only AFTER selection and checkpoint sealing.
    tx,ty=_load(test);old=ParkingUNet();old.load_state_dict(torch.load(old_checkpoint,map_location='cpu',weights_only=True)['state_dict']);old.eval()
    with torch.inference_mode():candidate=model(tx).sigmoid()>=.5;previous=old(tx).sigmoid()>=.5
    actual=(ty>=.5).numpy();candidate=candidate.numpy();previous=previous.numpy();baseline=torch.stack([geometry[r['camera_id']] for r in test]).numpy()
    metrics={name:mask_metrics(p,actual) for name,p in [('candidate',candidate),('old_model',previous),('camera_geometry',baseline)]}
    per_camera={camera:{name:mask_metrics(p[[i for i,r in enumerate(test) if r['camera_id']==camera]],actual[[i for i,r in enumerate(test) if r['camera_id']==camera]]) for name,p in [('candidate',candidate),('old_model',previous),('camera_geometry',baseline)]} for camera in sorted(CAMERAS.values())}
    gate=metrics['candidate']['pixel_iou']>=.75 and all(r['candidate']['pixel_iou']>=.70 for r in per_camera.values()) and metrics['candidate']['pixel_iou']>=metrics['camera_geometry']['pixel_iou']-.05
    for i,row in enumerate(test):
        for label,array in [('candidate',candidate),('truth',actual),('geometry',baseline)]:Image.fromarray((array[i,0]*255).astype('uint8')).save(folder/f'{label}_{i}.png')
    report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),epochs_completed=len(curves),best_epoch=best_epoch,validation_iou=best,positive_weight=float(weight),
        frames_by_split={s:sum(r['split']==s for r in rows) for s in ['train','validation','test']},training_seconds=time.perf_counter()-clock,device='cpu',torch_version=str(torch.__version__),
        checkpoint_sha256=digest(checkpoint),metrics=metrics,per_camera=per_camera,quality_gate_passed=gate,production_model_changed=False,
        limitations=['Only six final frames across three represented cameras','Date-based fixed-camera masks can be solved by camera geometry; neural value must be compared with that baseline','Not comparable directly with earlier differently split IoU','No unseen-camera, individual-slot-ID or vehicle-mask metric'])
    for name,value in [('run.json',report),('curves.json',curves)]: (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    (ROOT/'models/segmentation_known_camera_candidate.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    p=ROOT/'data/automation_state.json';counter=json.loads(p.read_text());counter.setdefault('completed_run_ids',[]).append(run);counter['completed_recorded_runs_since_schedule']=len(counter['completed_run_ids']);counter['last_completed_run']=run;p.write_text(json.dumps(counter,indent=2),encoding='utf-8')
    return report
