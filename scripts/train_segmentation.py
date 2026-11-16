"""Correct foreground collapse using train-only class weighting and a NEW holdout.

The first semantic run's test was inspected during debugging, so it is not reused
as final evidence. Additional previously unselected dates are reserved explicitly.
The already frozen classifier and its original holdout are not changed.
"""
import csv,json,random,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from torch import nn
from PIL import Image
from torchvision.transforms import functional as TF
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.training import ParkingUNet
from smart_parking.layout import read_pklot_xml,union_mask
from smart_parking.provenance import digest

if __name__=='__main__':
    torch.set_num_threads(4);torch.manual_seed(43);np.random.seed(43);random.seed(43)
    with (ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8',newline='') as stream:old=list(csv.DictReader(stream))
    used_days={r['date'] for r in old};acquisition=json.loads((ROOT/'data/raw/pklot_subset/acquisition.json').read_text())
    groups={}
    for pair in acquisition['pairs']:
        try:datetime.strptime(pair['date'],'%Y-%m-%d')
        except ValueError:continue
        if pair['date'] not in used_days:groups.setdefault(pair['date'],[]).append(pair)
    days=sorted(groups);selected_days=[days[i] for i in np.linspace(0,len(days)-1,5,dtype=int)]
    new=[]
    for day in selected_days:
        pairs=sorted(groups[day],key=lambda p:p['image'])
        for i in np.linspace(0,len(pairs)-1,min(2,len(pairs)),dtype=int):new.append(dict(**pairs[i],split='test'))
    rows=[r for r in old if r['split'] in {'train','validation'}]+new
    accepted=[];images=[];masks=[];rejected=[]
    for row in rows:
        try:
            image=Image.open(ROOT/row['image']).convert('RGB');layout=read_pklot_xml(ROOT/row['annotation'],image.size)
            images.append(TF.to_tensor(image.resize((192,112))));masks.append(TF.to_tensor(union_mask(layout,(192,112))));accepted.append(row)
        except ValueError as error:rejected.append(dict(image=row['image'],reason=str(error)))
    x=torch.stack(images);y=torch.stack(masks);idx={s:torch.tensor([i for i,r in enumerate(accepted) if r['split']==s]) for s in ['train','validation','test']}
    if not all(len(v)>0 for v in idx.values()):raise ValueError('Semantic split empty')
    if {r['date'] for r in new}&used_days:raise ValueError('New semantic holdout overlaps old dates')
    train_positive=y[idx['train']].mean().item();weight=torch.tensor((1-train_positive)/max(.001,train_positive))
    def loss_fn(logits,target):
        probability=logits.sigmoid();intersection=(probability*target).sum((1,2,3))
        dice=1-((2*intersection+1)/(probability.sum((1,2,3))+target.sum((1,2,3))+1)).mean()
        return nn.functional.binary_cross_entropy_with_logits(logits,target,pos_weight=weight)+dice
    model=ParkingUNet();optimizer=torch.optim.Adam(model.parameters(),lr=.003);best=float('inf');state=None;curves=[];start=time.perf_counter()
    for epoch in range(50):
        model.train();order=idx['train'][torch.randperm(len(idx['train']))];total=0
        for batch in order.split(4):
            optimizer.zero_grad();loss=loss_fn(model(x[batch]),y[batch]);loss.backward();optimizer.step();total+=loss.item()*len(batch)
        model.eval()
        with torch.inference_mode():validation=loss_fn(model(x[idx['validation']]),y[idx['validation']]).item()
        curves.append(dict(epoch=epoch+1,training_loss=total/len(order),validation_loss=validation))
        if validation<best:best=validation;state={k:v.clone() for k,v in model.state_dict().items()}
        if (epoch+1)%10==0:print('Weighted segmentation',epoch+1,'validation',validation,flush=True)
    model.load_state_dict(state);model.eval()
    with torch.inference_mode():prediction=model(x[idx['test']]).sigmoid()>=.5
    actual=y[idx['test']]>=.5;intersection=(prediction&actual).sum().item();union=(prediction|actual).sum().item()
    metrics=dict(pixel_iou=intersection/max(1,union),dice=2*intersection/max(1,prediction.sum().item()+actual.sum().item()),test_frames=len(idx['test']))
    run='SEGMENTATION-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    path=ROOT/'models/checkpoints/parking_unet.pt'
    # Preserve the first failed model separately; never erase its experiment evidence.
    if path.exists():
        backup=ROOT/'models/checkpoints/parking_unet_initial_failed.pt'
        if not backup.exists():backup.write_bytes(path.read_bytes())
    torch.save(dict(state_dict=state,run_id=run,input_size=[192,112]),path)
    report=dict(run_id=run,source_id='SRC-DS-001',architecture='Small U-Net 3→8→16→8→1',seed=43,
        epochs=50,batch_size=4,optimizer='Adam',learning_rate=.003,loss='Train-only weighted BCE + soft Dice',
        positive_weight=float(weight),train_foreground_fraction=train_positive,
        split_policy='Original train/validation dates; new previously unused final semantic-test dates; original classifier test excluded',
        final_test_dates=selected_days,frames_by_split={k:len(v) for k,v in idx.items()},
        metrics=metrics,training_seconds=time.perf_counter()-start,code_sha256=digest(Path(__file__)),checkpoint_sha256=digest(path),
        rejected=rejected,limitations=['Small convenience subset; no universal segmentation reliability',
            'Predicts union of parking-space regions, not individual slot identities or vehicle instances',
            'First failed semantic test became development evidence; final results use distinct unused dates'])
    for name,value in [('run.json',report),('curves.json',curves),('split_frames.json',accepted)]:
        (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    for j,i in enumerate(idx['test']):
        Image.fromarray((prediction[j,0].numpy()*255).astype('uint8')).save(folder/f'pred_{j}.png')
        Image.fromarray((actual[j,0].numpy()*255).astype('uint8')).save(folder/f'true_{j}.png')
    (ROOT/'models/segmentation_model_card.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
