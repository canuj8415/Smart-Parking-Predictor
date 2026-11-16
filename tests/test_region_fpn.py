import unittest
import numpy as np
import torch
from torchvision.models import resnet18
from smart_parking.region_fpn import (FrozenRegionEncoder, RegionPyramidDecoder,
                                      segmentation_loss, train_camera_templates, mask_metrics)


class RegionFPNTests(unittest.TestCase):
    def test_frozen_encoder_keeps_batchnorm_and_no_grad_even_in_train_mode(self):
        torch.set_num_threads(2)
        encoder = FrozenRegionEncoder(resnet18(weights=None).state_dict())
        before = {k: v.clone() for k, v in encoder.state_dict().items()}
        encoder.train(True)
        features = encoder(torch.rand(2, 3, 48, 64, requires_grad=True))
        self.assertFalse(encoder.training)
        self.assertTrue(all(not f.requires_grad for f in features))
        self.assertTrue(all(not p.requires_grad for p in encoder.parameters()))
        self.assertTrue(all(torch.equal(v, before[k]) for k, v in encoder.state_dict().items()))

    def test_odd_scales_decoder_gradient_and_loss(self):
        torch.set_num_threads(2)
        decoder = RegionPyramidDecoder(8)
        features = [torch.rand(2, c, h, w) for c, h, w in
                    [(64, 9, 13), (128, 5, 7), (256, 3, 4), (512, 2, 2)]]
        logits = decoder(features, (35, 51))
        self.assertEqual(tuple(logits.shape), (2, 1, 35, 51))
        loss = segmentation_loss(logits, torch.ones_like(logits), torch.tensor(2.))
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in decoder.parameters()))

    def test_camera_template_cannot_use_development_labels(self):
        records = [dict(role='train', camera_id='a'), dict(role='development', camera_id='a')]
        first = np.array([[[True, False]], [[False, True]]])
        second = first.copy(); second[1] = ~second[1]
        self.assertTrue(np.array_equal(train_camera_templates(first, records)['a'],
                                       train_camera_templates(second, records)['a']))
        self.assertTrue(np.array_equal(train_camera_templates(first, records)['a'], first[0]))

    def test_macro_camera_not_image_weighted_and_empty_agreement(self):
        truth = np.ones((3, 1, 2), dtype=bool)
        pred = truth.copy(); pred[2] = False
        m = mask_metrics(pred, truth, ['a', 'a', 'b'])
        self.assertEqual(m['macro_camera_iou'], .5)
        self.assertAlmostEqual(m['mean_image_iou'], 2 / 3)
        empty = np.zeros((1, 1, 1), dtype=bool)
        self.assertEqual(mask_metrics(empty, empty, ['a'])['minimum_image_iou'], 1.)
        with self.assertRaises(ValueError):
            mask_metrics(pred.astype(float), truth, ['a', 'a', 'b'])
