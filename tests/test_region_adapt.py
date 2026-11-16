"""Synthetic-weight software tests for the adaptable encoder (no real data or pretrained weights)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
try:
    import torch
    from torch import nn
    from torchvision.models import resnet18
    from smart_parking.region_adapt import AdaptableRegionEncoder
    from smart_parking.region_fpn import FrozenRegionEncoder
except ImportError:  # pragma: no cover
    torch = None


@unittest.skipIf(torch is None, 'torch unavailable')
class AdaptableEncoderTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(0)
        self.state = resnet18(weights=None).state_dict()
        self.x = torch.randn(2, 3, 144, 256)

    def test_only_layer3_layer4_convolutions_trainable(self):
        enc = AdaptableRegionEncoder(self.state)
        names = [n for n, p in enc.backbone.named_parameters() if p.requires_grad]
        self.assertTrue(names and all(n.split('.')[0] in ('layer3', 'layer4') for n in names))
        self.assertFalse(any('bn' in n or 'downsample.1' in n for n in names))

    def test_matches_frozen_encoder_at_initialisation(self):
        a = AdaptableRegionEncoder(self.state)(self.x); b = FrozenRegionEncoder(self.state)(self.x)
        for u, v in zip(a, b):
            torch.testing.assert_close(u.detach(), v)

    def test_batchnorm_statistics_frozen_after_update(self):
        enc = AdaptableRegionEncoder(self.state).train(True)
        before = {k: v.clone() for k, v in enc.state_dict().items() if 'running' in k}
        opt = torch.optim.SGD(enc.trainable_parameters(), lr=.1)
        loss = sum(t.mean() for t in enc(self.x)[2:]); loss.backward(); opt.step()
        after = enc.state_dict()
        self.assertTrue(all(torch.equal(before[k], after[k]) for k in before))
        self.assertTrue(all(not m.training for m in enc.modules() if isinstance(m, nn.BatchNorm2d)))
        self.assertFalse(torch.equal(self.state['layer4.1.conv2.weight'], after['backbone.layer4.1.conv2.weight']))
        self.assertTrue(torch.equal(self.state['layer1.0.conv1.weight'], after['backbone.layer1.0.conv1.weight']))

    def test_rejects_other_blocks(self):
        with self.assertRaises(ValueError):
            AdaptableRegionEncoder(self.state, trainable=('layer2',))


if __name__ == '__main__':
    unittest.main()
