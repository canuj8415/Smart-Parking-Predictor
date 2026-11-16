"""Conservative same-class crop-mask duplicates; conflicts remain review-only."""
import math
import numpy as np


def box_containment(a,b):
    for box in (a,b):
        if len(box)!=4 or any(not math.isfinite(v) for v in box) or box[0]>=box[2] or box[1]>=box[3]:raise ValueError('Invalid box')
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    return intersection/min((a[2]-a[0])*(a[3]-a[1]),(b[2]-b[0])*(b[3]-b[1]))


def deduplicate(predictions,masks,reference_count,min_mask_pixels=16,mask_containment=.85,box_threshold=.8):
    masks=np.asarray(masks)
    if masks.dtype!=bool or masks.ndim!=3 or masks.shape[0]!=len(predictions):raise ValueError('Predictions require same-shaped boolean masks')
    if type(reference_count) is not int or not 0<=reference_count<=len(predictions):raise ValueError('Invalid reference prefix')
    if min_mask_pixels<1 or not 0<mask_containment<=1 or not 0<box_threshold<=1:raise ValueError('Invalid duplicate controls')
    for p in predictions:
        if not isinstance(p['label'],str) or not p['label']:raise ValueError('Missing class')
        box_containment(p['box'],p['box'])
    areas=masks.sum(axis=(1,2));kept=list(range(reference_count));suppressed=[];reviews=[]
    for i in range(reference_count,len(predictions)):
        candidates=[]
        for j in kept:
            if predictions[i]['label']!=predictions[j]['label']:continue
            containment=box_containment(predictions[i]['box'],predictions[j]['box'])
            small=min(int(areas[i]),int(areas[j]))
            if containment<box_threshold or not small:continue
            overlap=float(np.count_nonzero(masks[i]&masks[j])/small)
            if overlap<mask_containment:continue
            if small<min_mask_pixels:
                reviews.append(dict(indices=[j,i],reason='tiny_mask_identity_uncertain',box_containment=containment,mask_containment=overlap))
            else:candidates.append((j,containment,overlap))
        if candidates:
            j,box_overlap,mask_overlap=sorted(candidates,key=lambda item:(item[0]>=reference_count,-item[2],-item[1],item[0]))[0]
            suppressed.append(dict(removed_index=i,retained_index=j,label=predictions[i]['label'],box_containment=box_overlap,mask_containment=mask_overlap,min_mask_pixels=min(int(areas[i]),int(areas[j]))))
        else:kept.append(i)
    for offset,i in enumerate(kept):
        if not areas[i]:reviews.append(dict(indices=[i],reason='empty_predicted_mask_support'))
        for j in kept[offset+1:]:
            if predictions[i]['label']==predictions[j]['label']:continue
            containment=box_containment(predictions[i]['box'],predictions[j]['box']);small=min(int(areas[i]),int(areas[j]))
            if containment<box_threshold or small<min_mask_pixels:continue
            overlap=float(np.count_nonzero(masks[i]&masks[j])/small)
            if overlap>=mask_containment:reviews.append(dict(indices=[i,j],reason='overlapping_road_class_conflict',labels=[predictions[i]['label'],predictions[j]['label']],box_containment=containment,mask_containment=overlap))
    return dict(kept_indices=kept,suppressed=suppressed,reviews=reviews,reference_prefix_preserved=kept[:reference_count]==list(range(reference_count)),
                classes_remapped=False,scope='Prediction-only same-class duplicate heuristic;review flags are not occupancy states or verified false-positive labels')
