"""Small learned source-specific forecast baseline;not a neural/camera model."""
import math
import numpy as np
from .singapore_history import aware_utc
from .prospective import SINGAPORE

FEATURES=['origin_fraction','past30min_fraction_change','past_gap_over30','hour_sin','hour_cos','log_capacity']


def feature_vector(row):
    cap=int(row['capacity']);current=int(row['origin_available']);previous=int(row['previous_available']);gap=float(row['previous_gap_minutes'])
    if cap<=0 or not 0<=current<=cap or not 0<=previous<=cap or not math.isfinite(gap) or not 10<=gap<=45:raise ValueError('Invalid causal forecast inputs')
    issue=aware_utc(row['issued_at'])
    if aware_utc(row['origin_available_at'])>issue or aware_utc(row['previous_available_at'])>=issue:raise ValueError('Feature was not available at issue')
    hour=issue.astimezone(SINGAPORE).hour+issue.astimezone(SINGAPORE).minute/60+issue.astimezone(SINGAPORE).second/3600
    return [current/cap,30*(current-previous)/(cap*gap),gap/30,math.sin(2*math.pi*hour/24),math.cos(2*math.pi*hour/24),math.log1p(cap)]


def fit_residual_ridge(rows,strength=.1):
    if not rows or not math.isfinite(strength) or strength<=0:raise ValueError('Nonempty training rows and positive regularization required')
    if any(not 0<=int(r['target_available'])<=int(r['capacity']) for r in rows):raise ValueError('Training target outside capacity')
    x=np.asarray([feature_vector(r) for r in rows],dtype=np.float64)
    y=np.asarray([(int(r['target_available'])-int(r['origin_available']))/int(r['capacity']) for r in rows])
    if not np.isfinite(y).all() or np.any(np.abs(y)>1):raise ValueError('Invalid normalized training targets')
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-12]=1
    design=np.column_stack([np.ones(len(x)),(x-mean)/scale]);penalty=np.eye(design.shape[1])*strength;penalty[0,0]=0
    coef=np.linalg.solve(design.T@design/len(x)+penalty,design.T@y/len(x))
    return dict(method='same_source_ridge_residual_v1',features=FEATURES,mean=mean.tolist(),scale=scale.tolist(),coefficients=coef.tolist(),ridge_strength=strength,
        preprocessing='Mean/std fitted on training rows only',nominal_horizon_minutes=30,matched_target_window_minutes=[20,45])


def predict_available(model,rows):
    if model['features']!=FEATURES:raise ValueError('Feature schema mismatch')
    x=np.asarray([feature_vector(r) for r in rows],dtype=np.float64)
    if len(rows)==0:return []
    scale=np.asarray(model['scale']);coef=np.asarray(model['coefficients'])
    if scale.shape!=(6,) or coef.shape!=(7,) or np.asarray(model['mean']).shape!=(6,) or np.any(scale<=0) or not np.isfinite(scale).all() or not np.isfinite(coef).all() or not np.isfinite(model['mean']).all():raise ValueError('Invalid fitted model')
    residual=np.column_stack([np.ones(len(x)),(x-np.asarray(model['mean']))/scale])@coef
    return [float(np.clip(int(r['origin_available'])+int(r['capacity'])*value,0,int(r['capacity']))) for r,value in zip(rows,residual)]
