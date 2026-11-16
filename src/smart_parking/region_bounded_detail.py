"""Bound a score-gated RGB contribution;this is not calibrated uncertainty."""
import math
import torch
from .region_detail import RegionDetailDecoder


def bounded_rgb_delta(coarse,raw,max_delta=.5):
    if not math.isfinite(max_delta) or max_delta<=0:
        raise ValueError('A finite positive residual bound is required')
    if coarse.shape!=raw.shape or not coarse.is_floating_point() or not raw.is_floating_point():
        raise ValueError('Aligned floating-point coarse and raw residual tensors required')
    score=coarse.detach().sigmoid()
    gate=4*score*(1-score)
    return max_delta*raw.tanh()*gate


class BoundedRegionDetailDecoder(RegionDetailDecoder):
    def __init__(self,width=32,detail_width=8,detail_seed=170,max_detail_logit=.5):
        if not math.isfinite(max_detail_logit) or max_detail_logit<=0:
            raise ValueError('Invalid detail bound')
        super().__init__(width,detail_width,detail_seed)
        self.max_detail_logit=float(max_detail_logit)

    def forward(self,features,normalized_rgb):
        if normalized_rgb.ndim!=4 or normalized_rgb.shape[1]!=3 or normalized_rgb.shape[0]!=features[0].shape[0]:
            raise ValueError('Aligned N,3,H,W normalized RGB is required')
        coarse=self.coarse(features,output_size=normalized_rgb.shape[-2:])
        raw=self.residual(torch.cat([coarse,self.rgb(normalized_rgb)],dim=1))
        return coarse+bounded_rgb_delta(coarse,raw,self.max_detail_logit)
