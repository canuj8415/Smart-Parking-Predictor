"""Padding-aware bay-union loss/metrics;validity is not annotation certainty."""
import numpy as np
import torch
from torch.nn import functional as F


def masked_bay_loss(logits,target,valid,positive_weight=1.):
    if logits.shape!=target.shape or valid.shape!=target.shape or logits.ndim!=4 or logits.shape[0]<1 or logits.shape[1]!=1 or valid.dtype!=torch.bool:
        raise ValueError('Aligned N,1,H,W logits/target and boolean nonpadding validity required')
    counts=valid.sum((1,2,3))
    if not torch.all(counts>0):raise ValueError('Each image needs real valid pixels')
    if not torch.isfinite(logits[valid]).all() or not torch.isfinite(target[valid]).all():raise ValueError('Nonfinite supervised values')
    if torch.any((target!=0)&(target!=1)) or torch.any(target[~valid]!=0):raise ValueError('Binary target must be zero in padding')
    safe_logits=torch.where(valid,logits,torch.zeros_like(logits))
    safe_target=target.to(logits.dtype)
    weight=torch.as_tensor(positive_weight,dtype=logits.dtype,device=logits.device)
    if weight.numel()!=1 or not torch.isfinite(weight).all() or not torch.all(weight>0):raise ValueError('Positive finite scalar class weight required')
    bce=F.binary_cross_entropy_with_logits(safe_logits,safe_target,pos_weight=weight,reduction='none')
    bce=(bce*valid).sum((1,2,3))/counts
    probability=safe_logits.sigmoid()*valid
    intersection=(probability*safe_target).sum((1,2,3))
    dice=1-(2*intersection+1)/(probability.sum((1,2,3))+safe_target.sum((1,2,3))+1)
    return (bce+dice).mean()


def valid_mask_metrics(predicted,actual,valid):
    if any(x.dtype!=np.bool_ for x in [predicted,actual,valid]) or predicted.shape!=actual.shape or valid.shape!=actual.shape or actual.ndim!=3 or len(actual)==0:
        raise ValueError('Aligned nonempty N,H,W boolean masks required')
    counts=valid.sum((1,2))
    if np.any(counts==0) or np.any(actual&~valid):raise ValueError('Invalid nonpadding support or target in padding')
    pred=predicted&valid;intersection=(pred&actual).sum((1,2));union=(pred|actual).sum((1,2));total=pred.sum((1,2))+actual.sum((1,2))
    iou=np.divide(intersection,union,out=np.ones(len(union)),where=union>0)
    dice=np.divide(2*intersection,total,out=np.ones(len(total)),where=total>0)
    return dict(images=len(actual),mean_image_iou=float(iou.mean()),mean_image_dice=float(dice.mean()),minimum_image_iou=float(iou.min()),
        per_image=[dict(index=i,iou=float(iou[i]),dice=float(dice[i]),valid_pixels=int(counts[i])) for i in range(len(actual))])
