"""Partially adaptable ResNet18 region encoder (layer3/layer4 trainable, BatchNorm frozen).

Same outputs as FrozenRegionEncoder at initialisation. Stem/layer1/layer2 run without
gradients; BatchNorm layers stay in eval mode with frozen affine parameters and running
statistics, so only convolution weights in layer3/layer4 change.
"""
import torch
from torch import nn
from torchvision.models import resnet18

TRAINABLE_BLOCKS = ('layer3', 'layer4')


class AdaptableRegionEncoder(nn.Module):
    def __init__(self, state_dict, trainable=TRAINABLE_BLOCKS):
        super().__init__()
        if not set(trainable) <= {'layer3', 'layer4'}:
            raise ValueError('Only layer3/layer4 may be adapted')
        self.backbone = resnet18(weights=None)
        self.backbone.load_state_dict(state_dict, strict=True)
        self.trainable = tuple(trainable)
        for name, parameter in self.backbone.named_parameters():
            block = name.split('.')[0]
            is_bn = isinstance(self.backbone.get_submodule(name.rsplit('.', 1)[0]), nn.BatchNorm2d)
            parameter.requires_grad_(block in self.trainable and not is_bn)
        self.train(False)

    def train(self, mode=True):
        super().train(mode)
        for module in self.modules():
            if isinstance(module, nn.BatchNorm2d):
                module.train(False)  # frozen running statistics in every mode
        return self

    def trainable_parameters(self):
        return [p for p in self.parameters() if p.requires_grad]

    def forward(self, rgb):
        b = self.backbone
        with torch.no_grad():
            x = b.maxpool(b.relu(b.bn1(b.conv1(rgb))))
            a = b.layer1(x)
            c = b.layer2(a)
        d = b.layer3(c)
        e = b.layer4(d)
        return a, c, d, e
