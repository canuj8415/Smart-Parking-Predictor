"""Genuine ResNet transfer-head and parking-region segmentation training."""
import csv
import json
import random
import time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader,TensorDataset
from torchvision.models import resnet18
from torchvision.transforms import functional as TF
from .provenance import ROOT,digest
from .layout import read_pklot_xml,crop_slot,union_mask
from .vision import normalize_crop

class ParkingUNet(nn.Module):
    def __init__(self):
        super().__init__()
        def block(a,b):return nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.ReLU(),nn.Conv2d(b,b,3,padding=1),nn.ReLU())
        self.enc=block(3,8);self.mid=block(8,16);self.dec=block(24,8);self.out=nn.Conv2d(8,1,1)
    def forward(self,x):
        skip=self.enc(x);mid=self.mid(nn.functional.max_pool2d(skip,2))
        up=nn.functional.interpolate(mid,size=skip.shape[-2:],mode='bilinear',align_corners=False)
        return self.out(self.dec(torch.cat([skip,up],1)))

def prepare_pklot():
    acquisition=json.loads((ROOT/'data/raw/pklot_subset/acquisition.json').read_text())
    frames=[];rejected=[];hashes=set()
    # Fixed, pre-declared development cap: at most 60 frames, distributed across dates.
    by_day={}
    for pair in acquisition['pairs']:
        try:datetime.strptime(pair['date'],'%Y-%m-%d')
        except ValueError:
            rejected.append(dict(**pair,reason='Invalid source calendar-date folder; not repaired or used in chronological grouping'))
            continue
        by_day.setdefault(pair['date'],[]).append(pair)
    chosen=[]
    ordered_days=sorted(by_day)
    if len(ordered_days)>20:
        ordered_days=[ordered_days[i] for i in np.linspace(0,len(ordered_days)-1,20,dtype=int)]
    for day in ordered_days:
        candidates=sorted(by_day[day],key=lambda p:p['image'])
        positions=np.linspace(0,len(candidates)-1,min(3,len(candidates)),dtype=int)
        chosen.extend(candidates[i] for i in positions)
    for pair in chosen:
        try:
            image=Image.open(ROOT/pair['image']).convert('RGB');layout=read_pklot_xml(ROOT/pair['annotation'],image.size)
            image_hash=digest(ROOT/pair['image'])
            if image_hash in hashes:raise ValueError('Exact duplicate frame')
            hashes.add(image_hash)
            frames.append(dict(**pair,camera_id=layout['camera_id'],image_sha256=image_hash,layout=layout))
        except (ValueError,OSError,KeyError) as error:rejected.append(dict(**pair,reason=str(error)))
    dates=sorted({f['date'] for f in frames});n=len(dates)
    if n<3:raise ValueError('At least three capture dates required for leakage-safe image splits')
    ntrain=max(1,int(n*.7));nval=max(1,int(n*.15))
    if ntrain+nval>=n:ntrain=n-2;nval=1
    split={day:'train' if i<ntrain else 'validation' if i<ntrain+nval else 'test' for i,day in enumerate(dates)}
    crops=[];folder=ROOT/'data/processed/pklot_crops';folder.mkdir(parents=True,exist_ok=True)
    layouts=ROOT/'configs/layouts';layouts.mkdir(parents=True,exist_ok=True)
    for index,frame in enumerate(frames):
        frame['split']=split[frame['date']];image=Image.open(ROOT/frame['image']).convert('RGB')
        name=f"{frame['camera_id']}_{Path(frame['image']).stem}"
        # Product layouts contain geometry only, never occupancy labels.
        geometry={**frame['layout'],'slots':[dict(id=s['id'],polygon=s['polygon']) for s in frame['layout']['slots']]}
        (layouts/(name+'.json')).write_text(json.dumps(geometry,indent=2),encoding='utf-8')
        frame['layout_path']=(layouts/(name+'.json')).relative_to(ROOT).as_posix()
        for slot in frame['layout']['slots']:
            if slot['ground_truth_occupied'] is None:continue
            path=folder/(name+'_'+slot['id']+'.png');crop_slot(image,slot).save(path)
            crops.append(dict(path=path.relative_to(ROOT).as_posix(),label=slot['ground_truth_occupied'],
                split=frame['split'],source_frame=frame['image'],date=frame['date'],camera_id=frame['camera_id'],slot_id=slot['id']))
    manifests=ROOT/'data/manifests';manifests.mkdir(parents=True,exist_ok=True)
    for name,rows in [('pklot_crops.csv',crops),('pklot_frames.csv',[{k:v for k,v in f.items() if k!='layout'} for f in frames])]:
        with (manifests/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary=dict(source_id='SRC-DS-001',frames=len(frames),capture_dates=len(dates),crops=len(crops),
        frames_by_split=dict(Counter(f['split'] for f in frames)),crops_by_split=dict(Counter(c['split'] for c in crops)),
        labels_by_split={s:dict(Counter(c['label'] for c in crops if c['split']==s)) for s in ['train','validation','test']},
        split_dates=split,rejected_frames=rejected,acquisition_policy=acquisition['policy'],
        annotation_type='Original parking-slot polygons and occupied/vacant labels; not vehicle boxes or masks',
        available_paired_frames=len(acquisition['pairs']),training_subset_policy='At most 20 dates, evenly spaced over available dates; at most three evenly spaced frames/date; fixed before model evaluation',
        limitations=['Convenience prefix subset only; not full PKLot benchmark','Grouped by capture date, not unseen-camera evaluation',
                     'Adjacent/overlapping slot crops from the same source frame remain within its split'])
    (manifests/'pklot_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return frames,crops,summary

def binary_metrics(target,pred):
    target=np.asarray(target);pred=np.asarray(pred);tp=int(((target==1)&(pred==1)).sum());tn=int(((target==0)&(pred==0)).sum())
    fp=int(((target==0)&(pred==1)).sum());fn=int(((target==1)&(pred==0)).sum())
    return dict(accuracy=float((tp+tn)/len(target)),precision=tp/max(1,tp+fp),recall=tp/max(1,tp+fn),
                f1=2*tp/max(1,2*tp+fp+fn),confusion_matrix=[[tn,fp],[fn,tp]],samples=len(target))

def train_vision(head_epochs=30,seg_epochs=12):
    torch.set_num_threads(4);torch.manual_seed(42);random.seed(42);np.random.seed(42)
    frames,crops,summary=prepare_pklot()
    print(json.dumps(summary,indent=2),flush=True)
    run='VISION-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    backbone=resnet18(weights=None);backbone.load_state_dict(torch.load(ROOT/'models/pretrained/resnet18_imagenet.pth',map_location='cpu',weights_only=True))
    backbone.fc=nn.Identity();backbone.eval();features=[];start=time.perf_counter()
    for offset in range(0,len(crops),64):
        batch=torch.stack([normalize_crop(Image.open(ROOT/c['path']).convert('RGB')) for c in crops[offset:offset+64]])
        with torch.inference_mode():features.append(backbone(batch).clone())
        if offset%512==0:print('ResNet feature extraction',offset,'/',len(crops),flush=True)
    features=torch.cat(features);labels=torch.tensor([c['label'] for c in crops]);indices={s:torch.tensor([i for i,c in enumerate(crops) if c['split']==s]) for s in ('train','validation','test')}
    if any(len(indices[s])==0 for s in indices):raise ValueError('Empty image split')
    head=nn.Linear(512,2);optimizer=torch.optim.Adam(head.parameters(),lr=.003,weight_decay=.001)
    train_indices=indices['train'];counts=torch.bincount(labels[train_indices],minlength=2)
    if (counts==0).any():raise ValueError('Training split lacks one occupancy class')
    loss_fn=nn.CrossEntropyLoss(weight=(counts.sum()/(2*counts)).float());curves=[];best=float('inf');best_head=None
    for epoch in range(head_epochs):
        order=train_indices[torch.randperm(len(train_indices))];total=0
        for idx in order.split(128):
            optimizer.zero_grad();loss=loss_fn(head(features[idx]),labels[idx]);loss.backward();optimizer.step();total+=loss.item()*len(idx)
        with torch.inference_mode():validation=loss_fn(head(features[indices['validation']]),labels[indices['validation']]).item()
        curves.append(dict(epoch=epoch+1,train_loss=total/len(order),validation_loss=validation))
        if validation<best:best=validation;best_head={k:v.detach().clone() for k,v in head.state_dict().items()}
    head.load_state_dict(best_head)
    with torch.inference_mode():pred=head(features[indices['test']]).argmax(1).numpy()
    classifier_metrics=binary_metrics(labels[indices['test']].numpy(),pred)
    backbone.fc=head;checkpoint=ROOT/'models/checkpoints/occupancy_resnet18.pt';checkpoint.parent.mkdir(parents=True,exist_ok=True)
    torch.save(dict(state_dict=backbone.state_dict(),run_id=run,classes=['vacant','occupied'],
        training='ImageNet ResNet18 frozen feature extractor; project-trained linear head',crop_size=96,seed=42),checkpoint)
    predictions=[dict(**crops[int(i)],predicted_label=int(p)) for i,p in zip(indices['test'],pred)]
    print('CLASSIFIER',classifier_metrics,flush=True)
    # Train a distinct semantic parking-region model using union of original slot polygons.
    image_tensors=torch.stack([TF.to_tensor(Image.open(ROOT/f['image']).convert('RGB').resize((192,112))) for f in frames])
    mask_tensors=torch.stack([TF.to_tensor(union_mask(f['layout'],(192,112))) for f in frames])
    fi={s:torch.tensor([i for i,f in enumerate(frames) if f['split']==s]) for s in indices}
    segmenter=ParkingUNet();opt=torch.optim.Adam(segmenter.parameters(),lr=.003);seg_curves=[];best=float('inf');best_seg=None
    for epoch in range(seg_epochs):
        segmenter.train();order=fi['train'][torch.randperm(len(fi['train']))];total=0
        for idx in order.split(4):
            opt.zero_grad();logits=segmenter(image_tensors[idx]);loss=nn.functional.binary_cross_entropy_with_logits(logits,mask_tensors[idx])
            loss.backward();opt.step();total+=loss.item()*len(idx)
        segmenter.eval()
        with torch.inference_mode():validation=nn.functional.binary_cross_entropy_with_logits(segmenter(image_tensors[fi['validation']]),mask_tensors[fi['validation']]).item()
        seg_curves.append(dict(epoch=epoch+1,train_bce=total/len(order),validation_bce=validation))
        if validation<best:best=validation;best_seg={k:v.detach().clone() for k,v in segmenter.state_dict().items()}
        print('Segmentation epoch',epoch+1,'val',round(validation,4),flush=True)
    segmenter.load_state_dict(best_seg);segmenter.eval()
    with torch.inference_mode():predmask=segmenter(image_tensors[fi['test']]).sigmoid()>=.5
    actual=mask_tensors[fi['test']]>=.5;intersection=(predmask&actual).sum().item();union=(predmask|actual).sum().item()
    seg_metrics=dict(pixel_iou=intersection/max(1,union),dice=2*intersection/max(1,predmask.sum().item()+actual.sum().item()),test_frames=len(fi['test']))
    seg_path=ROOT/'models/checkpoints/parking_unet.pt';torch.save(dict(state_dict=best_seg,run_id=run,input_size=[192,112]),seg_path)
    for local,index in enumerate(fi['test']):
        Image.fromarray((predmask[local,0].numpy()*255).astype('uint8')).save(folder/f'semantic_pred_{int(index)}.png')
        union_mask(frames[int(index)]['layout'],(192,112)).save(folder/f'semantic_true_{int(index)}.png')
    report=dict(run_id=run,source_id='SRC-DS-001',dataset=summary,seed=42,head_epochs=head_epochs,
        segmentation_epochs=seg_epochs,optimizer='Adam',head_learning_rate=.003,segmentation_learning_rate=.003,
        classifier_training='Frozen ImageNet ResNet18 features; linear head trained on original PKLot labels',
        classifier_metrics=classifier_metrics,semantic_metrics=seg_metrics,
        checkpoint_sha256=digest(checkpoint),segmentation_checkpoint_sha256=digest(seg_path),
        code_sha256=digest(Path(__file__)),manifest_sha256=digest(ROOT/'data/manifests/pklot_crops.csv'),
        training_seconds=time.perf_counter()-start,device='cpu',torch_version=torch.__version__,
        limitations=['Small convenience subset; scores not full PKLot benchmark',
                     'Configured slots and learned semantic masks are distinct','No vehicle-box/instance-mask ground truth acquired; no mAP claimed',
                     'Masks predict union of annotated parking regions, not individual slot IDs','Raw classifier scores uncalibrated'])
    for name,value in [('run.json',report),('classifier_curves.json',curves),('segmentation_curves.json',seg_curves),('classifier_test_predictions.json',predictions)]:
        (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    (ROOT/'models/vision_model_card.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
