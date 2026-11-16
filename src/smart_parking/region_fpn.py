"""Research-only image encoder/decoder and explicitly conditional mask baseline."""
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torchvision.models import resnet18


class FrozenRegionEncoder(nn.Module):
    def __init__(self, state_dict):
        super().__init__()
        self.backbone = resnet18(weights=None)
        self.backbone.load_state_dict(state_dict, strict=True)
        self.backbone.requires_grad_(False)
        self.train(False)

    def train(self, mode=True):
        super().train(False)  # Frozen running statistics as well as parameters.
        return self

    @torch.no_grad()
    def forward(self, rgb):
        b = self.backbone
        x = b.maxpool(b.relu(b.bn1(b.conv1(rgb))))
        a = b.layer1(x)
        c = b.layer2(a)
        d = b.layer3(c)
        e = b.layer4(d)
        return a, c, d, e


class RegionPyramidDecoder(nn.Module):
    def __init__(self, width=32):
        super().__init__()
        self.lateral = nn.ModuleList(nn.Conv2d(c, width, 1) for c in [64, 128, 256, 512])
        self.head = nn.Sequential(nn.Conv2d(width, width, 3, padding=1), nn.ReLU(),
                                  nn.Conv2d(width, 1, 1))

    def forward(self, features, output_size=(144, 256)):
        if len(features) != 4:
            raise ValueError('Four encoder scales are required')
        x = self.lateral[3](features[3])
        for i in [2, 1, 0]:
            x = F.relu(self.lateral[i](features[i]) +
                       F.interpolate(x, size=features[i].shape[-2:], mode='bilinear', align_corners=False))
        return F.interpolate(self.head(x), size=output_size, mode='bilinear', align_corners=False)


def segmentation_loss(logits, target, positive_weight):
    probability = logits.sigmoid()
    intersection = (probability * target).sum((1, 2, 3))
    dice = 1 - ((2 * intersection + 1) /
                (probability.sum((1, 2, 3)) + target.sum((1, 2, 3)) + 1)).mean()
    return F.binary_cross_entropy_with_logits(logits, target, pos_weight=positive_weight) + dice


def train_camera_templates(masks, records):
    """Camera IDs explicitly condition this comparator; never enter the decoder."""
    if masks.dtype != np.bool_ or len(masks) != len(records):
        raise ValueError('Boolean mask/record alignment required')
    cameras = sorted({r['camera_id'] for r in records if r['role'] == 'train'})
    return {c: masks[[i for i, r in enumerate(records)
                     if r['role'] == 'train' and r['camera_id'] == c]].mean(axis=0) >= .5
            for c in cameras}


def mask_metrics(predicted, actual, cameras):
    if predicted.dtype != np.bool_ or actual.dtype != np.bool_:
        raise ValueError('Threshold explicitly before scoring')
    if predicted.shape != actual.shape or predicted.ndim != 3 or len(cameras) != len(actual) or not cameras:
        raise ValueError('Aligned nonempty N,H,W masks and camera IDs required')
    intersection = (predicted & actual).sum((1, 2))
    union = (predicted | actual).sum((1, 2))
    count = predicted.sum((1, 2)) + actual.sum((1, 2))
    iou = np.divide(intersection, union, out=np.ones(len(union)), where=union > 0)
    dice = np.divide(2 * intersection, count, out=np.ones(len(count)), where=count > 0)
    by_camera = {c: dict(images=cameras.count(c), mean_iou=float(iou[np.array(cameras) == c].mean()),
                         mean_dice=float(dice[np.array(cameras) == c].mean())) for c in sorted(set(cameras))}
    return dict(images=len(cameras), macro_camera_iou=float(np.mean([r['mean_iou'] for r in by_camera.values()])),
                macro_camera_dice=float(np.mean([r['mean_dice'] for r in by_camera.values()])),
                mean_image_iou=float(iou.mean()), minimum_image_iou=float(iou.min()), by_camera=by_camera,
                per_image=[dict(index=i, camera_id=c, iou=float(iou[i]), dice=float(dice[i]))
                           for i, c in enumerate(cameras)])
