import unittest
import numpy as np
from PIL import Image
from smart_parking.region_letterbox import letterbox_plan,letterbox_arrays,check_admitted_frames


class RegionLetterboxTests(unittest.TestCase):
    def test_full_native_target_stays_inside_centered_valid_region(self):
        rgb=Image.new('RGB',(4,2),(255,0,0));mask=Image.new('L',(4,2),255)
        a,m,v,p=letterbox_arrays(rgb,mask,(8,8))
        self.assertEqual(p['resized_size'],[8,4]);self.assertEqual(p['offset'],[0,2])
        self.assertTrue(np.array_equal(m,v));self.assertEqual(int(v.sum()),32)
        self.assertTrue(np.all(a[~v]==np.array([124,116,104])))
        self.assertEqual(a.dtype,np.uint8);self.assertEqual(m.dtype,np.bool_)

    def test_tall_image_corner_and_nearest_mask_have_known_mapping(self):
        rgb=Image.new('RGB',(2,4));rgb.putpixel((0,0),(255,0,0));mask=Image.new('L',(2,4));mask.putpixel((0,0),255)
        a,m,v,p=letterbox_arrays(rgb,mask,(8,8))
        expected=np.zeros((8,8),dtype=bool);expected[0:2,2:4]=True
        self.assertTrue(np.array_equal(m,expected));self.assertEqual(p['offset'],[2,0])
        self.assertEqual(tuple(a[0,2]),(255,0,0));self.assertFalse(np.any(m&~v))

    def test_identity_transform_and_invalid_inputs(self):
        rgb=Image.new('RGB',(3,2),(10,20,30));mask=Image.new('L',(3,2));mask.putpixel((2,1),255)
        a,m,v,p=letterbox_arrays(rgb,mask,(3,2))
        self.assertTrue(np.array_equal(a,np.asarray(rgb)));self.assertTrue(np.array_equal(m,np.asarray(mask)>0));self.assertTrue(v.all())
        with self.assertRaises(ValueError):letterbox_plan((0,10))
        with self.assertRaises(ValueError):letterbox_arrays(rgb,Image.new('L',(2,2)))
        with self.assertRaises(ValueError):letterbox_arrays(rgb,Image.new('L',(3,2),128))

    def test_admission_rejects_closed_role_duplicate_and_cross_role_alias(self):
        allowed={'train':['a.JPG'],'valid':['b.JPG']}
        rows=[dict(name='a.JPG',role='train',source_id='SRC-DS-021'),dict(name='b.JPG',role='validation',source_id='SRC-DS-021')]
        self.assertTrue(check_admitted_frames(rows,allowed))
        for bad in [[rows[0],dict(rows[1],role='test')],[rows[0],rows[0]],
                    [rows[0],dict(rows[1],name='UNADMITTED.JPG')],
                    [rows[0],dict(rows[1],name='../b.JPG')]]:
            with self.assertRaises(ValueError):check_admitted_frames(bad,allowed)
        with self.assertRaises(ValueError):check_admitted_frames(rows,{'train':['a.JPG'],'valid':['A.jpg']})
