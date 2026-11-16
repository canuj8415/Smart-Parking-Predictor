import unittest
from PIL import Image
from smart_parking.layout import crop_slot
from smart_parking.local_crops import crop_slot_local
from smart_parking.exact_crops import crop_slot_exact

class ExactCropTests(unittest.TestCase):
    def test_observed_native_training_geometry_keeps_reference_raster(self):
        # Publisher TRAIN geometry,synthetic constant-colour raster;not accuracy.
        image=Image.new('RGB',(4000,3000),(20,100,200));slot=dict(polygon=[[1558.01339925,1232.1501463333332],[1328.07089925,1080.200813],[1508.0258992499998,808.2914796666668],[1715.9738992500002,910.2574796666667]])
        reference=crop_slot(image,slot).tobytes();self.assertNotEqual(crop_slot_local(image,slot).tobytes(),reference);self.assertEqual(crop_slot_exact(image,slot).tobytes(),reference)
    def test_boundaries_and_multiple_sizes_are_exact(self):
        image=Image.new('RGB',(81,63),(21,87,166))
        for polygon in [[[0,0],[80,0],[80,62],[0,62]],[[.2,.3],[78.8,1.7],[64.34,60.19],[2.22,50.89]]]:
            for size in [1,47,96,128]:self.assertEqual(crop_slot_exact(image,dict(polygon=polygon),size).tobytes(),crop_slot(image,dict(polygon=polygon),size).tobytes())
    def test_mode_bounds_and_nonfinite_inputs_refused(self):
        p=dict(polygon=[[0,0],[3,0],[3,3]])
        with self.assertRaises(ValueError):crop_slot_exact(Image.new('L',(10,10)),p)
        with self.assertRaises(ValueError):crop_slot_exact(Image.new('RGB',(10,10)),dict(polygon=[[0,0],[10,0],[3,3]]))
        with self.assertRaises(ValueError):crop_slot_exact(Image.new('RGB',(10,10)),dict(polygon=[[0,0],[float('nan'),0],[3,3]]))
