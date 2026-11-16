"""Synthetic geometry masks check leakage boundaries and explicit neural contribution."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.region_consensus import fit_consensus,compose_mask,prior_summary

class ConsensusTests(unittest.TestCase):
    def fixture(self):
        masks=np.array([[[1,0,0]],[[1,0,1]],[[1,0,1]]],dtype=bool)
        rows=[dict(camera_id='SYNTHETIC',date=f'2020-01-0{i}') for i in range(1,4)]
        return fit_consensus(masks,rows)
    def test_stable_pixels_use_geometry_variable_pixels_use_network(self):
        priors=self.fixture()
        self.assertEqual(compose_mask([[0,1,0]],'SYNTHETIC',priors).tolist(),[[True,False,False]])
        self.assertEqual(compose_mask([[0,1,1]],'SYNTHETIC',priors).tolist(),[[True,False,True]])
        self.assertAlmostEqual(prior_summary(priors)['SYNTHETIC']['cnn_controlled_fraction'],1/3)
    def test_constant_training_geometry_does_not_claim_neural_contribution(self):
        p=fit_consensus(np.ones((3,2,2)),[dict(camera_id='A',date=str(i)) for i in range(3)])
        self.assertEqual(prior_summary(p)['A']['cnn_controlled_fraction'],0)
        self.assertTrue(compose_mask(np.zeros((2,2)),'A',p).all())
    def test_unknown_view_dimensions_and_nonbinary_inputs_fail(self):
        p=self.fixture()
        for mask,camera in [([[0,0,0]],'OTHER'),([[0]],'SYNTHETIC'),([[.5,0,0]],'SYNTHETIC')]:
            with self.assertRaises(ValueError):compose_mask(mask,camera,p)
    def test_dates_and_matching_training_membership_are_required(self):
        for masks,rows in [(np.zeros((3,2,2)),[dict(camera_id='A',date='one')]*3),(np.zeros((2,2,2)),[dict(camera_id='A',date=str(i)) for i in range(3)])]:
            with self.assertRaises(ValueError):fit_consensus(masks,rows)
    def test_any_training_variation_routes_whole_view_to_neural_mask(self):
        priors=self.fixture();neural=np.array([[0,1,0]],dtype=bool)
        np.testing.assert_array_equal(compose_mask(neural,'SYNTHETIC',priors,'stable_camera_only'),neural)
        self.assertEqual(compose_mask(neural,'SYNTHETIC',priors).tolist(),[[True,False,False]])
        with self.assertRaisesRegex(ValueError,'routing'):compose_mask(neural,'SYNTHETIC',priors,'unknown')
