import unittest
import numpy as np
from smart_parking.uvg import instance_pixels, supported_instance_mask


class MaskChannelTests(unittest.TestCase):
    def test_explicit_bgr_conversion_prevents_identity_swap(self):
        image=np.array([[[255,255,155],[155,255,255]]],dtype=np.uint8)
        self.assertEqual(instance_pixels(image,[155,255,255]).tolist(),[[True,False]])

    def test_transparent_matching_bytes_are_not_instance_support(self):
        image=np.array([[[255,255,155,0],[255,255,155,255]]],dtype=np.uint8)
        self.assertEqual(instance_pixels(image,[155,255,255]).tolist(),[[False,True]])

    def test_unknown_channels_dtypes_and_colors_fail(self):
        for image,color in [(np.zeros((2,2),dtype=np.uint8),[1,2,3]),
                            (np.zeros((2,2,3)),[1,2,3]),
                            (np.zeros((2,2,3),dtype=np.uint8),[1,2,256])]:
            with self.assertRaises(ValueError): instance_pixels(image,color)

    def test_absent_raster_is_unknown_not_empty_truth(self):
        mask,status=supported_instance_mask(np.zeros((2,2,4),dtype=np.uint8),[1,2,3])
        self.assertIsNone(mask)
        self.assertEqual(status,'unknown_no_raster_support')

    def test_present_raster_retains_only_matching_instance(self):
        image=np.array([[[3,2,1,255],[1,2,3,255]]],dtype=np.uint8)
        mask,status=supported_instance_mask(image,[1,2,3])
        self.assertEqual(mask.tolist(),[[True,False]])
        self.assertEqual(status,'provided_instance_pixels')
