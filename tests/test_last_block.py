import unittest
import numpy as np
import torch
from PIL import Image
from torchvision.models import resnet18
from smart_parking.last_block import configure_last_block,normalize_rgb_batch
from smart_parking.vision import normalize_crop

class LastBlockTests(unittest.TestCase):
    def test_batched_normalization_equals_existing_crop_transform(self):
        a=np.random.default_rng(160).integers(0,256,(3,96,96,3),dtype=np.uint8);reference=torch.stack([normalize_crop(Image.fromarray(x)) for x in a]);self.assertTrue(torch.equal(normalize_rgb_batch(torch.from_numpy(a)),reference))
    def test_freeze_contract_and_one_gradient_step(self):
        torch.manual_seed(160);torch.set_num_threads(4);model=resnet18(weights=None);model.fc=torch.nn.Linear(512,2);names=configure_last_block(model)
        self.assertTrue(all(n.startswith(('layer4.','fc.')) for n in names));self.assertFalse(any('.bn' in n or n.startswith('bn') for n in names));before={k:v.clone() for k,v in model.state_dict().items()};optimizer=torch.optim.SGD([p for p in model.parameters() if p.requires_grad],lr=.001)
        loss=torch.nn.functional.cross_entropy(model(torch.rand(2,3,96,96)),torch.tensor([0,1]));loss.backward();optimizer.step()
        self.assertTrue(any(not torch.equal(before[k],v) for k,v in model.state_dict().items() if k in names));self.assertTrue(all(torch.equal(before[k],v) for k,v in model.state_dict().items() if k not in names))
        self.assertTrue(all(not m.training for m in model.modules() if isinstance(m,torch.nn.BatchNorm2d)))
    def test_invalid_rgb_shapes_and_types_refused(self):
        for a in [torch.zeros(1,3,96,96,dtype=torch.uint8),torch.zeros(1,96,96,3)]:
            with self.assertRaises(ValueError):normalize_rgb_batch(a)
    def test_wrong_model_contract_refused(self):
        with self.assertRaises(ValueError):configure_last_block(torch.nn.Linear(3,2))
