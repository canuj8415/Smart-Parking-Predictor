"""Occupancy assignment with reference-raster slot patches,not dense slot stacks.

The legacy vision.assign_occupancy remains unchanged until qualification. This
module preserves its .12 overlap threshold,sorting,ties and uncertainty rules
for valid engine-shaped inputs. It does not bound detector mask production.
"""
import math
import numpy as np
from PIL import Image,ImageDraw
from .layout import validate_layout,slot_mask


def prepare_slot_patches(size,layout):
    validate_layout(layout,size);patches=[]
    for slot in layout['slots']:
        points=slot['polygon'];box=(max(0,math.floor(min(x for x,y in points))),max(0,math.floor(min(y for x,y in points))),min(size[0],math.ceil(max(x for x,y in points))+1),min(size[1],math.ceil(max(y for x,y in points))+1))
        # Preserve full-canvas rasterization;the translated-mask variant was not
        # pixel equivalent on observed fractional development geometry.
        mask=np.asarray(slot_mask(slot,size).crop(box))>0;mask.flags.writeable=False
        patches.append((box,mask,int(mask.sum())))
    return patches


def assign_occupancy_patches(size,layout,detections,masks,probabilities=None,low=.25,high=.75):
    if not 0<=low<high<=1:raise ValueError('Invalid uncertainty thresholds')
    if len(masks)!=len(detections):raise ValueError('Every detection requires a mask or explicit None')
    if probabilities is not None and (len(probabilities)!=len(layout['slots']) or any(not math.isfinite(p) or not 0<=p<=1 for p in probabilities)):raise ValueError('Invalid classifier probabilities')
    ids=[d['id'] for d in detections]
    if any(type(i)!=int or i<0 for i in ids) or len(set(ids))!=len(ids):raise ValueError('Unique nonnegative detection IDs required')
    for d,instance in zip(detections,masks):
        b=d['box']
        if len(b)!=4 or any(not math.isfinite(v) for v in b) or b[2]<b[0] or b[3]<b[1] or not math.isfinite(d['score']) or not 0<=d['score']<=1:raise ValueError('Invalid detection box/score')
        if instance is not None and (not isinstance(instance,np.ndarray) or instance.dtype!=np.bool_ or instance.shape!=(size[1],size[0])):raise ValueError('Expected original-sized boolean detector mask')
    patches=prepare_slot_patches(size,layout);candidates=[]
    for d,instance in zip(detections,masks):
        if instance is None:
            bitmap=Image.new('L',size,0);ImageDraw.Draw(bitmap).rectangle(d['box'],fill=255);instance=np.asarray(bitmap)>0
        for i,(box,slot,area) in enumerate(patches):
            left,top,right,bottom=box;overlap=float(np.logical_and(slot,instance[top:bottom,left:right]).sum()/max(1,area))
            if overlap>=.12:candidates.append((overlap*d['score'],i,d['id'],overlap))
    assigned={};used=set()
    for _,i,identity,overlap in sorted(candidates,reverse=True):
        if i not in assigned and identity not in used:assigned[i]=(identity,overlap);used.add(identity)
    observations=[]
    for i,slot in enumerate(layout['slots']):
        p=probabilities[i] if probabilities is not None else None;matched=i in assigned
        if p is None:state='occupied' if matched else 'uncertain'
        elif p>=high:state='occupied'
        elif p<=low and not matched:state='vacant'
        else:state='uncertain'
        observations.append(dict(slot_id=slot['id'],state=state,occupancy_score=p,vehicle_id=assigned[i][0] if matched else None,slot_overlap=assigned[i][1] if matched else 0))
    return observations
