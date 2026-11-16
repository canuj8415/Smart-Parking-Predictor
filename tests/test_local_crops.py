import random,unittest
from PIL import Image
from smart_parking.layout import crop_slot
from smart_parking.local_crops import crop_slot_local

class LocalCropTests(unittest.TestCase):
    def image(self,w=73,h=59):
        image=Image.new('RGB',(w,h));image.putdata([((i*31)%256,(i*17)%256,(i*7)%256) for i in range(w*h)]);return image
    def test_fractional_skew_matches_reference(self):
        image=self.image();slot=dict(polygon=[[2.31,1.99],[65.8,5.21],[69.71,50.83],[4.14,55.7]])
        self.assertEqual(crop_slot(image,slot).tobytes(),crop_slot_local(image,slot).tobytes())
    def test_edges_and_output_sizes_match(self):
        image=self.image();slot=dict(polygon=[[0,0],[72,0],[72,58],[0,58]])
        for size in [1,31,96,128]:self.assertEqual(crop_slot(image,slot,size).tobytes(),crop_slot_local(image,slot,size).tobytes())
    def test_seeded_thin_and_fractional_polygons_match(self):
        image=self.image();rng=random.Random(156)
        for i in range(50):
            x=rng.uniform(0,35);y=rng.uniform(0,28);w=rng.uniform(.1,30);h=rng.uniform(.1,24);slot=dict(polygon=[[x,y],[x+w,y+.01],[x+w-.02,y+h],[x,y+h-.01]])
            self.assertEqual(crop_slot(image,slot).tobytes(),crop_slot_local(image,slot).tobytes(),i)
    def test_unknown_mode_or_unbounded_polygons_refused(self):
        slot=dict(polygon=[[0,0],[3,0],[3,3],[0,3]])
        with self.assertRaises(ValueError):crop_slot_local(Image.new('L',(10,10)),slot)
        with self.assertRaises(ValueError):crop_slot_local(self.image(),dict(polygon=[[-1,0],[3,0],[3,3]]))
    def test_nonfinite_geometry_and_bad_size_refused(self):
        with self.assertRaises(ValueError):crop_slot_local(self.image(),dict(polygon=[[0,0],[float('nan'),0],[3,3]]))
        with self.assertRaises(ValueError):crop_slot_local(self.image(),dict(polygon=[[0,0],[3,0],[3,3]]),0)

if __name__=='__main__':unittest.main()
