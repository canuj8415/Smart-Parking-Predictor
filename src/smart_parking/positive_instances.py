"""Provided-positive development agreement, without assuming background truth."""
import math
from pathlib import Path


def result_reference(path, root):
    """Make relative/absolute local result paths equivalent; reject escapes."""
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def box_iou(a, b):
    for box in (a,b):
        if len(box)!=4 or any(not math.isfinite(x) for x in box) or box[0]>=box[2] or box[1]>=box[3]:
            raise ValueError('Invalid positive-instance box')
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    aa=(a[2]-a[0])*(a[3]-a[1]);bb=(b[2]-b[0])*(b[3]-b[1])
    return intersection/(aa+bb-intersection)


def match_positives(truth, predictions, threshold=.5):
    """Deterministic maximum-cardinality class-aware threshold matching.

    Unmatched predictions are unassigned, not automatically false positives.
    Augmenting paths prevent a shared prediction from double-counting truth.
    """
    if not 0<threshold<=1: raise ValueError('Invalid IoU threshold')
    adjacency=[]
    for target in truth:
        candidates=[]
        for j,pred in enumerate(predictions):
            overlap=box_iou(target['box'],pred['box'])
            if target['label']==pred['label'] and overlap>=threshold:
                candidates.append((overlap,j))
        adjacency.append([j for _,j in sorted(candidates,key=lambda v:(-v[0],v[1]))])
    owners={}
    def augment(i,seen):
        for j in adjacency[i]:
            if j in seen: continue
            seen.add(j)
            if j not in owners or augment(owners[j],seen):
                owners[j]=i;return True
        return False
    for i in range(len(truth)): augment(i,set())
    matched={i:j for j,i in owners.items()}
    return dict(matches=[dict(truth_index=i,prediction_index=j,iou=box_iou(truth[i]['box'],predictions[j]['box']))
                         for i,j in sorted(matched.items())],
                provided_positives=len(truth),matched_positives=len(matched),
                unmatched_predictions=len(predictions)-len(owners),
                provided_positive_recall=None if not truth else len(matched)/len(truth),
                exhaustive_precision_evaluable=False)
