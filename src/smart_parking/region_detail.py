"""Research image-only full-resolution residual with an unchanged coarse start."""
import hashlib
import torch
from torch import nn
from .region_fpn import RegionPyramidDecoder


class RegionDetailDecoder(nn.Module):
    def __init__(self, width=32, detail_width=8, detail_seed=170):
        super().__init__()
        self.coarse=RegionPyramidDecoder(width)
        # Extra initialization must not change the existing TRAIN sampler stream.
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(detail_seed)
            self.rgb=nn.Sequential(nn.Conv2d(3,detail_width,3,padding=1),nn.ReLU(),
                                   nn.Conv2d(detail_width,detail_width,3,padding=1),nn.ReLU())
            self.residual=nn.Sequential(nn.Conv2d(detail_width+1,detail_width,3,padding=1),nn.ReLU(),
                                        nn.Conv2d(detail_width,1,1))
            nn.init.zeros_(self.residual[-1].weight)
            nn.init.zeros_(self.residual[-1].bias)

    def forward(self,features,normalized_rgb):
        if normalized_rgb.ndim!=4 or normalized_rgb.shape[1]!=3 or normalized_rgb.shape[0]!=features[0].shape[0]:
            raise ValueError('Aligned N,3,H,W normalized RGB is required')
        coarse=self.coarse(features,output_size=normalized_rgb.shape[-2:])
        return coarse+self.residual(torch.cat([coarse,self.rgb(normalized_rgb)],dim=1))


def sampler_order_digest(order):
    data=order.detach().cpu().to(torch.int64).numpy().astype('<i8').tobytes()
    return hashlib.sha256(data).hexdigest()


def reference_sampler_orders(indices,rng_state,epochs):
    generator=torch.Generator(device='cpu');generator.set_state(rng_state)
    orders=[indices[torch.randperm(len(indices),generator=generator)] for _ in range(epochs)]
    return orders,generator.get_state()
