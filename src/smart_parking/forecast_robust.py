"""Training-only blocked selection and a conservative group-relative objective."""
from collections import defaultdict
import numpy as np
import torch


def blocked_folds(rows):
    """Three expanding, whole-date folds; all rows must already be training data."""
    dates=sorted({r['origin'][:10] for r in rows})
    if len(dates)<10:raise ValueError('At least ten training dates are required')
    # Fixed fractions, resolved from training-date membership only.
    boundaries=[int(len(dates)*f) for f in (.4,.6,.8)]+[len(dates)]
    folds=[]
    for left,right in zip(boundaries,boundaries[1:]):
        fit=[r for r in rows if r['origin'][:10] in dates[:left]]
        tune=[r for r in rows if r['origin'][:10] in dates[left:right]]
        if not fit or not tune:raise ValueError('Empty blocked training fold')
        a={i for r in fit for i in r['input_source_rows']+[r['target_source_row']]}
        b={i for r in tune for i in r['input_source_rows']+[r['target_source_row']]}
        if a&b or max(r['target_time'] for r in fit)>=min(r['origin'] for r in tune):
            raise ValueError('Training fold has source overlap or noncausal dates')
        folds.append((fit,tune))
    return folds


def fit_risk_scales(rows):
    """Fit persistence MAE in spaces on this fitting prefix only; floor one space."""
    groups=defaultdict(list)
    for r in rows:groups[r['car_park_id']].append(abs(r['y']-r['baseline'])*r['capacity'])
    if not groups:raise ValueError('Cannot fit risk scales without training rows')
    scales={p:max(1.,float(np.mean(v))) for p,v in groups.items()}
    return dict(per_park=scales,unknown_park=float(np.median(list(scales.values()))),floor_spaces=1.)


def group_relative_loss(predictions,targets,rows,scales):
    if len(rows)!=len(predictions) or len(rows)!=len(targets) or not rows:
        raise ValueError('Nonempty matching predictions, targets and rows required')
    groups=defaultdict(list)
    for i,r in enumerate(rows):groups[r['car_park_id']].append(i)
    losses=[]
    for park,indices in sorted(groups.items()):
        capacity=predictions.new_tensor([rows[i]['capacity'] for i in indices])
        relative=(predictions[indices]-targets[indices]).abs()*capacity/scales['per_park'].get(park,scales['unknown_park'])
        losses.append(relative.mean())
    values=torch.stack(losses)
    return .5*values.mean()+.5*values.max()


def occupied_space_predictions(rows,predictions,inputs):
    """Apply the learned float32 correction to the original observed space count."""
    correction=(predictions-inputs[:,-1,0]).detach().cpu().numpy()
    return [float(np.clip((r['baseline']+float(delta))*r['capacity'],0,r['capacity']))
            for r,delta in zip(rows,correction)]
