import unittest
import torch
from smart_parking.region_fpn import RegionPyramidDecoder,segmentation_loss
from smart_parking.region_detail import RegionDetailDecoder,reference_sampler_orders,sampler_order_digest


class RegionDetailTests(unittest.TestCase):
    def test_zero_residual_identity_coarse_weights_and_sampler_rng(self):
        torch.set_num_threads(2);torch.manual_seed(169)
        coarse=RegionPyramidDecoder(8);state=torch.random.get_rng_state().clone()
        torch.manual_seed(169);detail=RegionDetailDecoder(8)
        self.assertTrue(torch.equal(torch.random.get_rng_state(),state))
        self.assertTrue(all(torch.equal(v,coarse.state_dict()[k]) for k,v in detail.coarse.state_dict().items()))
        features=[torch.rand(2,c,h,w) for c,h,w in [(64,9,13),(128,5,7),(256,3,4),(512,2,2)]]
        rgb=torch.rand(2,3,35,51)
        self.assertTrue(torch.equal(coarse(features,(35,51)),detail(features,rgb)))
        with self.assertRaises(ValueError):detail(features,rgb[:,:1])

    def test_residual_and_rgb_branch_receive_finite_learning_signal(self):
        torch.set_num_threads(2);torch.manual_seed(171)
        model=RegionDetailDecoder(8);opt=torch.optim.SGD(model.parameters(),lr=.01)
        features=[torch.rand(2,c,h,w) for c,h,w in [(64,9,13),(128,5,7),(256,3,4),(512,2,2)]]
        rgb=torch.rand(2,3,35,51);target=(torch.rand(2,1,35,51)>.6).float()
        for _ in range(2):
            opt.zero_grad();loss=segmentation_loss(model(features,rgb),target,torch.tensor(2.));loss.backward();opt.step()
        self.assertGreater(float(model.residual[-1].weight.grad.abs().sum()),0)
        self.assertGreater(float(model.rgb[0].weight.grad.abs().sum()),0)
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_reference_orders_match_actual_stream_without_changing_global_state(self):
        torch.manual_seed(169);indices=torch.tensor([3,5,8,12,19]);state=torch.random.get_rng_state().clone()
        orders,end=reference_sampler_orders(indices,state,4)
        self.assertTrue(torch.equal(torch.random.get_rng_state(),state))
        actual=[indices[torch.randperm(len(indices))] for _ in range(4)]
        self.assertEqual([sampler_order_digest(x) for x in actual],[sampler_order_digest(x) for x in orders])
        self.assertTrue(torch.equal(torch.random.get_rng_state(),end))
        self.assertTrue(all(sorted(x.tolist())==indices.tolist() for x in orders))
