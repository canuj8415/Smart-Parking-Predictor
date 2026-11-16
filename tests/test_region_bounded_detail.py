import unittest
import torch
from smart_parking.region_detail import RegionDetailDecoder
from smart_parking.region_bounded_detail import BoundedRegionDetailDecoder,bounded_rgb_delta


class BoundedDetailTests(unittest.TestCase):
    def test_large_synthetic_residuals_obey_bound_and_strong_coarse_sign(self):
        # Generated numeric fixtures,not real-world segmentation evidence.
        generator=torch.Generator().manual_seed(172)
        coarse=torch.randn(8192,generator=generator)*20
        raw=torch.randn(8192,generator=generator)*100
        delta=bounded_rgb_delta(coarse,raw)
        self.assertTrue(torch.isfinite(delta).all())
        self.assertLessEqual(float(delta.abs().max()),.500001)
        strong=coarse.abs()>.5
        self.assertTrue(torch.equal((coarse+delta)[strong]>0,coarse[strong]>0))
        self.assertTrue(torch.equal(bounded_rgb_delta(coarse,torch.zeros_like(raw)),torch.zeros_like(raw)))
        with self.assertRaises(ValueError):bounded_rgb_delta(coarse,raw,float('nan'))

    def test_gate_is_detached_but_raw_gradient_is_finite(self):
        coarse=torch.tensor([-2.,0.,2.],requires_grad=True);raw=torch.tensor([-.2,0.,.2],requires_grad=True)
        bounded_rgb_delta(coarse,raw).sum().backward()
        self.assertIsNone(coarse.grad)
        self.assertTrue(torch.isfinite(raw.grad).all())
        self.assertTrue((raw.grad>0).all())

    def test_model_has_same_parameters_rng_and_zero_start_as_unbounded_model(self):
        torch.set_num_threads(2);torch.manual_seed(169)
        plain=RegionDetailDecoder(8);state=torch.random.get_rng_state().clone()
        torch.manual_seed(169);bounded=BoundedRegionDetailDecoder(8)
        self.assertTrue(torch.equal(state,torch.random.get_rng_state()))
        self.assertTrue(all(torch.equal(v,plain.state_dict()[k]) for k,v in bounded.state_dict().items()))
        features=[torch.rand(2,c,h,w) for c,h,w in [(64,9,13),(128,5,7),(256,3,4),(512,2,2)]]
        rgb=torch.rand(2,3,35,51)
        self.assertTrue(torch.equal(plain(features,rgb),bounded(features,rgb)))
        bounded.residual[-1].bias.data.fill_(1000)
        coarse=bounded.coarse(features,(35,51));pred=bounded(features,rgb)
        self.assertLessEqual(float((pred-coarse).abs().max().detach()),.500001)
