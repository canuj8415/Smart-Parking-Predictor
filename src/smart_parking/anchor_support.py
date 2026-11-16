"""Research-only box-bottom support; it never infers vacancy from no support.

Bottom-center of a 2D detector box is only a geometric proxy. It is not a
calibrated ground-contact point, especially with oblique views or occlusion.
"""
import math
from collections import defaultdict
from .occupancy_patches import prepare_slot_patches


def assign_bottom_center(size,layout,detections):
    patches=prepare_slot_patches(size,layout)
    identities=[d['id'] for d in detections]
    if any(type(i)!=int or i<0 for i in identities) or len(set(identities))!=len(identities):
        raise ValueError('Unique nonnegative integer detection IDs required')
    candidates=[]
    for d in detections:
        box=d['box'];score=d['score']
        if len(box)!=4 or any(not math.isfinite(x) for x in box) or box[2]<box[0] or box[3]<box[1] or not math.isfinite(score) or not 0<=score<=1:
            raise ValueError('Finite ordered box and bounded score required')
        anchor=((box[0]+box[2])/2,box[3]);x,y=map(math.floor,anchor)
        # Do not clip an out-of-image anchor onto an edge bay.
        if not(0<=x<size[0] and 0<=y<size[1]):continue
        for i,(bounds,mask,_) in enumerate(patches):
            left,top,right,bottom=bounds
            if left<=x<right and top<=y<bottom and mask[y-top,x-left]:
                candidates.append((score,i,d['id'],anchor))
    assigned={};used=set()
    for _,i,identity,anchor in sorted(candidates,reverse=True):
        if i not in assigned and identity not in used:
            assigned[i]=(identity,list(anchor));used.add(identity)
    return [dict(slot_id=slot['id'],vehicle_id=assigned[i][0] if i in assigned else None,
                 anchor_xy=assigned[i][1] if i in assigned else None,
                 support_rule='box_bottom_center_floor_original_raster') for i,slot in enumerate(layout['slots'])]


def support_diagnostics(rows):
    rows=list(rows);seen=set();groups=defaultdict(list)
    for row in rows:
        key=(row['image'],row['slot_id'])
        if key in seen or row['label'] not in (0,1):raise ValueError('Unique image/slot and binary truth required')
        seen.add(key);groups[row['image']].append(row)
    def summary(values):
        counts={}
        for method in ['reference','anchor']:
            counts[method]=dict(occupied_supported=sum(r['label']==1 and r[method+'_id'] is not None for r in values),
                                vacant_supported=sum(r['label']==0 and r[method+'_id'] is not None for r in values),
                                total_supported=sum(r[method+'_id'] is not None for r in values))
        eligible=[r for r in values if r['label']==1 and r['reference_id'] is not None]
        retained=sum(r['anchor_id'] is not None for r in eligible)
        return dict(samples=len(values),occupied=sum(r['label'] for r in values),vacant=sum(1-r['label'] for r in values),
                    **counts,reference_occupied_support_retention=dict(eligible=len(eligible),retained=retained,fraction=retained/len(eligible) if eligible else None),
                    newly_supported_vacant=sum(r['label']==0 and r['reference_id'] is None and r['anchor_id'] is not None for r in values),
                    newly_supported_occupied=sum(r['label']==1 and r['reference_id'] is None and r['anchor_id'] is not None for r in values))
    result=summary(rows);result['per_image']=[dict(image=name,**summary(values)) for name,values in sorted(groups.items())]
    return result


def support_gates(metrics,gates):
    retention=metrics['reference_occupied_support_retention']['fraction']
    images=[r['reference_occupied_support_retention']['fraction'] for r in metrics['per_image'] if r['reference_occupied_support_retention']['eligible']]
    return dict(labelled_cohort_sufficient=min(metrics['occupied'],metrics['vacant'])>=gates['minimum_each_truth_count'],
                false_support_reduced=metrics['reference']['vacant_supported']>0 and metrics['anchor']['vacant_supported']<=gates['false_support_fraction_of_reference_max']*metrics['reference']['vacant_supported'],
                occupied_support_retained=retention is not None and retention>=gates['occupied_support_retention_min'],
                every_image_occupied_support_retained=bool(images) and min(images)>=gates['image_occupied_support_retention_min'])
