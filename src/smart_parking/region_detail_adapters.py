"""Batch-only RGB adapters for a matched coarse/detail research experiment."""
import torch
from torch import nn
from .region_fpn import RegionPyramidDecoder
from .region_detail import RegionDetailDecoder


def split_inputs(inputs):
    if not isinstance(inputs,tuple) or len(inputs)!=5:raise ValueError('Four feature scales plus uint8 RGB required')
    features=inputs[:4];rgb=inputs[4]
    if rgb.ndim!=4 or rgb.shape[1]!=3 or rgb.dtype!=torch.uint8:raise ValueError('RGB must be N,3,H,W uint8;normalize once inside the adapter')
    if any(f.ndim!=4 or f.shape[0]!=rgb.shape[0] for f in features):raise ValueError('Aligned feature/RGB batches required')
    return features,rgb


class CoarseRGBAdapter(nn.Module):
    def __init__(self,width=32):
        super().__init__();self.coarse=RegionPyramidDecoder(width)

    def forward(self,inputs):
        features,rgb=split_inputs(inputs)
        return self.coarse(features,output_size=rgb.shape[-2:])


class DetailRGBAdapter(nn.Module):
    def __init__(self,width=32,detail_width=8,detail_seed=183,mean=(.485,.456,.406),std=(.229,.224,.225)):
        super().__init__();self.decoder=RegionDetailDecoder(width,detail_width,detail_seed)
        self.register_buffer('mean',torch.tensor(mean,dtype=torch.float32)[None,:,None,None])
        self.register_buffer('std',torch.tensor(std,dtype=torch.float32)[None,:,None,None])

    @property
    def coarse(self):return self.decoder.coarse

    def normalize_rgb(self,rgb):
        if rgb.ndim!=4 or rgb.shape[1]!=3 or rgb.dtype!=torch.uint8:raise ValueError('Normalize only N,3,H,W uint8 RGB')
        return (rgb.to(torch.float32)/255-self.mean)/self.std

    def forward(self,inputs):
        features,rgb=split_inputs(inputs)
        return self.decoder(features,self.normalize_rgb(rgb))


def build_adapter_pair(warm_state,width=32,detail_width=8,detail_seed=183,mean=(.485,.456,.406),std=(.229,.224,.225)):
    # Construction must not consume the caller's sampler/random stream.
    with torch.random.fork_rng(devices=[]):
        control=CoarseRGBAdapter(width)
        detail=DetailRGBAdapter(width,detail_width,detail_seed,mean,std)
        control.coarse.load_state_dict(warm_state,strict=True);detail.coarse.load_state_dict(warm_state,strict=True)
    return {'control':control,'detail':detail}
