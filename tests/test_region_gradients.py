import unittest
import numpy as np
from smart_parking.region_gradients import gradient_geometry


class RegionGradientTests(unittest.TestCase):
    def test_opposed_gradients_predict_correct_first_order_quadratic_change(self):
        a=np.array([1.,0.]);b=np.array([-2.,0.]);m=gradient_geometry(a,b)
        self.assertEqual(m['cosine'],-1.);self.assertEqual(m['acpds_to_pklot_norm_ratio'],2.)
        self.assertTrue(m['pklot_first_order_worsens']);self.assertFalse(m['acpds_first_order_worsens'])
        direction=-(a+b)/2;step=1e-6
        # L(x)=g.x+0.5*x.x has gradient g at x=0.
        for vector,key in [(a,'pklot'),(b,'acpds')]:
            actual=float(vector@(step*direction)+.5*(step*direction)@(step*direction))/step
            self.assertAlmostEqual(actual,m[key+'_equal_descent_directional_derivative'],places=6)

    def test_aligned_and_orthogonal_gradients_do_not_conflict(self):
        aligned=gradient_geometry([1,2],[2,4]);self.assertAlmostEqual(aligned['cosine'],1.)
        self.assertFalse(aligned['conflicting']);self.assertLess(aligned['pklot_equal_descent_directional_derivative'],0)
        orthogonal=gradient_geometry([1,0],[0,1]);self.assertEqual(orthogonal['cosine'],0.)
        self.assertEqual(orthogonal['pklot_equal_descent_directional_derivative'],-.5)

    def test_zero_gradient_has_undefined_cosine_not_invented_alignment(self):
        result=gradient_geometry([0,0],[1,0]);self.assertIsNone(result['cosine']);self.assertFalse(result['cosine_defined'])
        self.assertIsNone(result['acpds_to_pklot_norm_ratio']);self.assertFalse(result['pklot_first_order_worsens'])

    def test_invalid_nonfinite_empty_and_mismatched_vectors_rejected(self):
        for a,b in [([],[]),([1],[1,2]),([[1]],[[2]]),([np.nan],[1]),([1],[np.inf]),([1e308],[1e308])]:
            with self.subTest(a=a,b=b),self.assertRaises(ValueError):gradient_geometry(a,b)
