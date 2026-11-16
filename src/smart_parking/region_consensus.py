"""Known-camera composition of unanimous training geometry and frozen CNN masks."""
import numpy as np


def binary_masks(value):
    masks=np.asarray(value)
    if masks.ndim<2 or not np.isin(masks,[0,1]).all():raise ValueError('Expected finite binary masks')
    return masks.astype(bool)


def fit_consensus(masks,rows,min_dates=3):
    masks=binary_masks(masks)
    if len(masks)!=len(rows) or not rows:raise ValueError('Training masks and metadata must match')
    priors={}
    for camera in sorted({r['camera_id'] for r in rows}):
        ids=[i for i,r in enumerate(rows) if r['camera_id']==camera]
        days=sorted({rows[i]['date'] for i in ids})
        if len(days)<min_dates:raise ValueError('Insufficient training dates for camera prior')
        subset=masks[ids];positive=subset.all(axis=0);negative=(~subset).all(axis=0)
        priors[camera]=dict(positive=positive,negative=negative,majority=subset.mean(axis=0)>=.5,
            training_frames=len(ids),training_dates=days)
    return priors


def compose_mask(neural_mask,camera_id,priors,policy='unanimous_pixels'):
    neural=binary_masks(neural_mask)
    if camera_id not in priors:raise ValueError('No fitted geometry prior for this camera')
    prior=priors[camera_id]
    if neural.shape!=prior['positive'].shape:raise ValueError('Neural mask and geometry prior dimensions differ')
    if policy not in {'unanimous_pixels','stable_camera_only'}:raise ValueError('Unknown geometry routing policy')
    if policy=='stable_camera_only' and np.any(~(prior['positive']|prior['negative'])):
        return neural.copy()
    # Stable pixels contain no evidence of automatic image segmentation here.
    return np.where(prior['positive'],True,np.where(prior['negative'],False,neural))


def prior_summary(priors):
    return {c:dict(training_frames=p['training_frames'],training_dates=p['training_dates'],pixels=int(p['positive'].size),
        locked_foreground_pixels=int(p['positive'].sum()),locked_background_pixels=int(p['negative'].sum()),
        cnn_controlled_fraction=float((~(p['positive']|p['negative'])).mean())) for c,p in priors.items()}
