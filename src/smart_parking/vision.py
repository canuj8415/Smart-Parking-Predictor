"""Offline Faster R-CNN/ResNet detection and genuine Mask R-CNN instance masks."""
import copy,json
import time
from datetime import datetime,timezone
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import torch
from torchvision.transforms import functional as TF
from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2,maskrcnn_resnet50_fpn
from torchvision.models import resnet18
from .provenance import ROOT,digest
from .layout import validate_layout,slot_mask,crop_slot
from .analysis_identity import image_identity,layout_identity
from .occupancy_patches import assign_occupancy_patches

VEHICLES={3:'car',4:'motorcycle',6:'bus',8:'truck'}
COLORS={'occupied':'#ef6470','vacant':'#39c999','uncertain':'#f7c65d'}

class VisionEngine:
    def __init__(self,detector='fasterrcnn',resolution=640):
        torch.set_num_threads(4)
        if detector not in {'fasterrcnn','maskrcnn'}:raise ValueError('Unknown detector')
        self.kind=detector;self.resolution=resolution
        name='fasterrcnn_resnet50_fpn_v2' if detector=='fasterrcnn' else 'maskrcnn_resnet50_fpn'
        path=ROOT/f'models/pretrained/{name}.pth'
        if not path.exists():raise FileNotFoundError('Missing detection weights; run scripts/acquire_vision_assets.py online once.')
        builder=fasterrcnn_resnet50_fpn_v2 if detector=='fasterrcnn' else maskrcnn_resnet50_fpn
        self.model=builder(weights=None,weights_backbone=None,min_size=resolution,max_size=resolution,
                           box_detections_per_img=150)
        self.model.load_state_dict(torch.load(path,map_location='cpu',weights_only=True));self.model.eval()
        self.model_name=name;self.weight_sha256=digest(path);self.classifier=None;self.classifier_sha256=None;self.classifier_run_id=None
        classifier=ROOT/'models/checkpoints/occupancy_resnet18.pt'
        if classifier.exists():
            bundle=torch.load(classifier,map_location='cpu',weights_only=True)
            self.classifier=resnet18(weights=None);self.classifier.fc=torch.nn.Linear(512,2)
            self.classifier.load_state_dict(bundle['state_dict']);self.classifier.eval()
            self.classifier_sha256=digest(classifier);self.classifier_run_id=bundle.get('run_id')

    @torch.inference_mode()
    def analyze(self,image,layout=None,confidence=.5,uncertain_low=.25,uncertain_high=.75):
        if not 0<confidence<1 or not 0<=uncertain_low<uncertain_high<=1:raise ValueError('Invalid thresholds')
        image=image.convert('RGB')
        if image.width*image.height>25_000_000:raise ValueError('Image too large; resize below 25 megapixels')
        if layout is not None:
            layout=copy.deepcopy(layout);validate_layout(layout,image.size)
        input_identity=image_identity(image);geometry_identity=layout_identity(layout)
        start=time.perf_counter();prediction=self.model([TF.to_tensor(image)])[0]
        detections=[];masks=[]
        for i,(box,label,score) in enumerate(zip(prediction['boxes'],prediction['labels'],prediction['scores'])):
            label=int(label);score=float(score)
            if label not in VEHICLES or score<confidence:continue
            mask=(prediction['masks'][i,0].cpu().numpy()>=.5) if 'masks' in prediction else None
            detections.append(dict(id=len(detections),label=VEHICLES[label],score=score,box=box.tolist(),
                                   has_instance_mask=mask is not None))
            masks.append(mask)
        probabilities=None
        if layout is not None and self.classifier:
            batch=torch.stack([normalize_crop(crop_slot(image,s)) for s in layout['slots']])
            probabilities=torch.softmax(self.classifier(batch),dim=1)[:,1].tolist()
        observations=assign_occupancy(image.size,layout,detections,masks,probabilities,uncertain_low,uncertain_high) if layout is not None else []
        counts={s:sum(o['state']==s for o in observations) for s in COLORS} if layout is not None else None
        if counts is not None:counts['total']=len(observations)
        result=dict(model=self.model_name,weight_sha256=self.weight_sha256,pretrained=True,
            input_image=input_identity,layout_identity=geometry_identity,
            classifier_checkpoint_sha256=getattr(self,'classifier_sha256',None),classifier_run_id=getattr(self,'classifier_run_id',None),
            detections=detections,slots=observations,counts=counts,occupancy_evaluated=layout is not None,
            classifier='PKLot-trained ResNet18 head' if self.classifier else 'unavailable; no vacancy inferred from missing detection',
            confidence_threshold=confidence,uncertain_thresholds=[uncertain_low,uncertain_high],
            latency_seconds=time.perf_counter()-start,recorded_at=datetime.now(timezone.utc).isoformat(),
            limitations=['Raw scores are not calibrated confidence','Slot geometry must match the actual camera',
                         'Configured polygons are not learned semantic segmentation','No layout means only detections, no occupancy counts'])
        overlay=render_overlay(image,layout,result,masks)
        return result,overlay

def normalize_crop(image):
    return TF.normalize(TF.to_tensor(image),[.485,.456,.406],[.229,.224,.225])

def _assign_occupancy_dense_reference(size,layout,detections,masks,probabilities=None,low=.25,high=.75):
    """One vehicle supports at most one slot; disagreements remain uncertain."""
    slot_arrays=[np.asarray(slot_mask(slot,size))>0 for slot in layout['slots']]
    candidates=[]
    for d,instance in zip(detections,masks):
        if instance is None:
            bitmap=Image.new('L',size,0);ImageDraw.Draw(bitmap).rectangle(d['box'],fill=255);instance=np.asarray(bitmap)>0
        for i,slot in enumerate(slot_arrays):
            overlap=float(np.logical_and(slot,instance).sum()/max(1,slot.sum()))
            if overlap>=.12:candidates.append((overlap*d['score'],i,d['id'],overlap))
    assigned={};used=set()
    for _,i,d,overlap in sorted(candidates,reverse=True):
        if i not in assigned and d not in used:assigned[i]=(d,overlap);used.add(d)
    observations=[]
    for i,slot in enumerate(layout['slots']):
        p=probabilities[i] if probabilities is not None else None
        matched=i in assigned
        if p is None:state='occupied' if matched else 'uncertain'
        elif p>=high:state='occupied'
        elif p<=low and not matched:state='vacant'
        else:state='uncertain'
        observations.append(dict(slot_id=slot['id'],state=state,occupancy_score=p,
            vehicle_id=assigned[i][0] if matched else None,slot_overlap=assigned[i][1] if matched else 0))
    return observations

def assign_occupancy(size,layout,detections,masks,probabilities=None,low=.25,high=.75):
    """Qualified bounded-memory assignment;legacy reference retained for replay."""
    return assign_occupancy_patches(size,layout,detections,masks,probabilities,low,high)

def render_overlay(image,layout,result,masks=None):
    canvas=image.convert('RGBA');layer=Image.new('RGBA',image.size);draw=ImageDraw.Draw(layer)
    if masks:
        for mask in masks:
            if mask is not None:
                color=Image.new('RGBA',image.size,(85,161,255,70));layer.alpha_composite(Image.composite(color,Image.new('RGBA',image.size),Image.fromarray((mask*255).astype('uint8'))))
    if layout:
        draw=ImageDraw.Draw(layer)
        for slot,observation in zip(layout['slots'],result['slots']):
            color=COLORS[observation['state']];points=[tuple(p) for p in slot['polygon']]
            rgb=tuple(int(color[i:i+2],16) for i in (1,3,5))
            draw.polygon(points,fill=(*rgb,45),outline=(*rgb,255),width=3)
            draw.text(points[0],slot['id'],fill='white',stroke_width=2,stroke_fill='black')
    canvas=Image.alpha_composite(canvas,layer).convert('RGB');draw=ImageDraw.Draw(canvas)
    for d in result['detections']:
        draw.rectangle(d['box'],outline='#66b5ff',width=2)
        draw.text((d['box'][0],max(0,d['box'][1]-14)),f"{d['label']} {d['score']:.2f}",fill='white',stroke_width=2,stroke_fill='black')
    return canvas
