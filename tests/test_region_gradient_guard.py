import unittest
import numpy as np
from smart_parking.region_gradient_guard import guard_auxiliary_gradient


class RegionGradientGuardTests(unittest.TestCase):
    def test_opposed_direction_is_projected_and_capped_in_known_plane(self):
        reference=np.array([1.,0.]);aux=np.array([-2.,2.]);before=aux.copy()
        guarded=guard_auxiliary_gradient(reference,aux)
        np.testing.assert_allclose(guarded,[0.,1.],atol=1e-12)
        np.testing.assert_array_equal(aux,before)
        self.assertEqual(float(reference@(-.5*(reference+guarded))),-.5)

    def test_small_aligned_direction_is_preserved_and_zero_reference_is_explicit(self):
        np.testing.assert_array_equal(guard_auxiliary_gradient([1,0],[.2,0]),[.2,0])
        np.testing.assert_array_equal(guard_auxiliary_gradient([0,0],[100,-200]),[0,0])

    def test_seeded_random_vectors_satisfy_projection_and_norm_properties(self):
        rng=np.random.default_rng(179)
        for _ in range(512):
            reference=rng.normal(size=17)*10**rng.uniform(-3,3)
            auxiliary=rng.normal(size=17)*10**rng.uniform(-3,3)
            guarded=guard_auxiliary_gradient(reference,auxiliary)
            scale=float(reference@reference)
            self.assertGreaterEqual(float(reference@guarded),-1e-10*scale)
            self.assertLessEqual(float(np.linalg.norm(guarded)),np.linalg.norm(reference)*(1+1e-12))
            self.assertLessEqual(float(reference@(-.5*(reference+guarded))),-0.5*scale+1e-10*scale)

    def test_invalid_vectors_fail_without_creating_a_direction(self):
        for a,b in [([],[]),([1],[1,2]),([[1]],[[2]]),([np.nan],[1]),([1],[np.inf]),([1e308],[1])]:
            with self.subTest(a=a,b=b),self.assertRaises(ValueError):guard_auxiliary_gradient(a,b)
