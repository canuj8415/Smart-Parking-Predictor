"""Controlled last-block adaptation and unchanged RGB normalization."""
import torch
from torch import nn


def configure_last_block(model):
    model.eval()
    for name,p in model.named_parameters():p.requires_grad_(name.startswith(('layer4.','fc.')))
    for module in model.modules():
        if isinstance(module,nn.modules.batchnorm._BatchNorm):
            module.eval()
            for p in module.parameters():p.requires_grad_(False)
    names=[name for name,p in model.named_parameters() if p.requires_grad]
    if not names or not any(n.startswith('layer4.') for n in names) or not any(n.startswith('fc.') for n in names):raise ValueError('Expected ResNet last block and classifier')
    return names


def normalize_rgb_batch(values):
    if values.dtype!=torch.uint8 or values.ndim!=4 or values.shape[-1]!=3:raise ValueError('Expected NHWC uint8 RGB batch')
    x=values.permute(0,3,1,2).contiguous().to(torch.float32).div(255)
    mean=x.new_tensor([.485,.456,.406]).view(1,3,1,1);std=x.new_tensor([.229,.224,.225]).view(1,3,1,1)
    return x.sub_(mean).div_(std)
