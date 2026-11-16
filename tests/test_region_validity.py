import math
import unittest
import numpy as np
import torch
from smart_parking.region_validity import masked_bay_loss,valid_mask_metrics
from smart_parking.region_fpn import segmentation_loss


class RegionValidityTests(unittest.TestCase):
    def test_all_valid_loss_and_gradient_match_legacy_training_objective(self):
        generator=torch.Generator().manual_seed(175)
        for dtype in (torch.float32,torch.float64):
            for shape in ((1,1,3,5),(4,1,7,9)):
                for weight in (0.25,1.,4.):
                    for target_kind in ('empty','full','mixed'):
                        with self.subTest(dtype=dtype,shape=shape,weight=weight,target=target_kind):
                            logits=(torch.randn(shape,generator=generator,dtype=dtype)*12).requires_grad_()
                            target=(torch.rand(shape,generator=generator)>0.6).to(dtype)
                            if target_kind=='empty':target.zero_()
                            if target_kind=='full':target.fill_(1)
                            reference=logits.detach().clone().requires_grad_()
                            legacy=segmentation_loss(reference,target,torch.tensor(weight,dtype=dtype))
                            masked=masked_bay_loss(logits,target,torch.ones_like(target,dtype=torch.bool),weight)
                            legacy.backward();masked.backward()
                            tolerance=2e-6 if dtype==torch.float32 else 1e-12
                            torch.testing.assert_close(masked,legacy,rtol=tolerance,atol=tolerance)
                            torch.testing.assert_close(logits.grad,reference.grad,rtol=tolerance,atol=tolerance)

    def test_padding_logits_do_not_affect_loss_or_valid_gradient(self):
        valid=torch.tensor([[[[True,True],[False,False]]]])
        target=torch.tensor([[[[1.,0.],[0.,0.]]]])
        a=torch.tensor([[[[.2,-.3],[0.,0.]]]],requires_grad=True)
        b=torch.tensor([[[[.2,-.3],[float('nan'),float('inf')]]]],requires_grad=True)
        first=masked_bay_loss(a,target,valid,2.);second=masked_bay_loss(b,target,valid,2.)
        self.assertTrue(torch.equal(first,second));first.backward();second.backward()
        self.assertTrue(torch.equal(a.grad[valid],b.grad[valid]));self.assertTrue(torch.equal(b.grad[~valid],torch.zeros(2)))

    def test_single_supervised_pixel_has_known_loss_and_rejects_empty_support(self):
        logits=torch.zeros(1,1,2,2);target=torch.zeros_like(logits);target[0,0,0,0]=1
        valid=torch.zeros_like(logits,dtype=torch.bool);valid[0,0,0,0]=True
        self.assertAlmostEqual(float(masked_bay_loss(logits,target,valid)),math.log(2)+.2,places=6)
        with self.assertRaises(ValueError):masked_bay_loss(logits,target,torch.zeros_like(valid))
        with self.assertRaises(ValueError):masked_bay_loss(logits[:0],target[:0],valid[:0])
        bad=target.clone();bad[0,0,1,1]=1
        with self.assertRaises(ValueError):masked_bay_loss(logits,bad,valid)

    def test_metric_ignores_padding_predictions_without_creating_extra_samples(self):
        valid=np.array([[[True,False],[False,False]]]);truth=valid.copy()
        all_prediction=np.ones_like(valid);only_true=truth.copy()
        a=valid_mask_metrics(all_prediction,truth,valid);b=valid_mask_metrics(only_true,truth,valid)
        self.assertEqual(a,b);self.assertEqual(a['images'],1);self.assertEqual(a['mean_image_iou'],1.)
        self.assertEqual(a['per_image'][0]['valid_pixels'],1)
        with self.assertRaises(ValueError):valid_mask_metrics(only_true,truth,np.zeros_like(valid))

    def test_all_valid_reproduces_direct_iou_and_dice(self):
        actual=np.array([[[True,True],[False,False]]]);pred=np.array([[[True,False],[True,False]]]);valid=np.ones_like(actual)
        m=valid_mask_metrics(pred,actual,valid)
        self.assertAlmostEqual(m['mean_image_iou'],1/3);self.assertEqual(m['mean_image_dice'],.5)
