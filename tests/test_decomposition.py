"""Numerical algebra/invalid-input fixtures, not parking accuracy benchmarks."""
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.decomposition import decompose,reconstruct,rank_report


class DecompositionTests(unittest.TestCase):
    def test_full_rank_recovers_a_rectangular_matrix(self):
        array=np.random.default_rng(116).random((7,11));f=decompose(array)
        np.testing.assert_allclose(reconstruct(f,7),array,rtol=0,atol=1e-12)

    def test_rank_one_fixture_and_zero_energy_have_honest_metrics(self):
        a=np.outer(np.linspace(0,1,8),np.linspace(0,1,10));r=rank_report(decompose(a),1)
        self.assertLess(r['mse'],1e-25)
        zero=rank_report(decompose(np.zeros((5,8))),1)
        self.assertIsNone(zero['retained_energy_fraction']);self.assertIsNone(zero['psnr_db'])
        self.assertEqual(zero['mse'],0)

    def test_rank_error_matches_discarded_energy_and_improves(self):
        f=decompose(np.random.default_rng(117).random((9,13)));errors=[]
        for k in range(1,10):
            r=rank_report(f,k);errors.append(r['mse'])
            self.assertAlmostEqual(r['mse']*117,r['discarded_energy'],places=11)
        self.assertTrue(all(a>=b-1e-14 for a,b in zip(errors,errors[1:])))

    def test_factor_storage_counts_every_array_and_can_expand(self):
        f=decompose(np.eye(4));r=rank_report(f,4)
        self.assertEqual(r['factor_float64_bytes'],(4*4+4+4*4)*8)
        self.assertEqual(r['original_float64_bytes'],4*4*8)
        self.assertGreater(r['factor_to_original_float64_ratio'],1)

    def test_bad_shapes_values_and_ranks_fail_before_reconstruction(self):
        for bad in [[],[1,2],np.zeros((3,4,3)),np.zeros((513,513)),[[float('nan')]],[[1.1]],[[-.1]],[[1j]]]:
            with self.subTest(shape=np.shape(bad)):
                with self.assertRaises(ValueError):decompose(bad)
        f=decompose(np.eye(4))
        for bad in [0,5,-1,2.5,True,'2']:
            with self.assertRaises(ValueError):reconstruct(f,bad)


if __name__=='__main__':unittest.main()
