"""Synthetic-fixture software tests for label reconstruction (no real data)."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from smart_parking.mask_reconstruction import area_downsample, bilinear_upsample, reconstruct


class MaskReconstructionTests(unittest.TestCase):
    def test_area_is_block_mean(self):
        m = np.zeros((1, 8, 8), bool); m[0, :4, :2] = True
        np.testing.assert_array_equal(area_downsample(m, 4), [[[.5, 0], [0, 0]]])

    def test_bilinear_matches_align_corners_false_reference(self):
        # torch.nn.functional.interpolate([[0,1]], size=8, bilinear, align_corners=False) row values
        out = bilinear_upsample(np.array([[[0., 1.]]]), (1, 8))[0, 0]
        np.testing.assert_allclose(out, [0, 0, .125, .375, .625, .875, 1, 1])

    def test_constant_and_block_aligned_masks_roundtrip(self):
        for value in (False, True):
            m = np.full((2, 16, 16), value)
            np.testing.assert_array_equal(reconstruct(m), m)

    def test_thin_structure_is_lost(self):
        m = np.zeros((1, 16, 16), bool); m[0, :, 7] = True  # 1px line is below half a 4px cell
        self.assertFalse(reconstruct(m).any())

    def test_rejects_non_divisible_or_non_boolean(self):
        with self.assertRaises(ValueError): reconstruct(np.zeros((1, 10, 16), bool))
        with self.assertRaises(ValueError): reconstruct(np.zeros((1, 16, 16), float))


if __name__ == '__main__':
    unittest.main()
