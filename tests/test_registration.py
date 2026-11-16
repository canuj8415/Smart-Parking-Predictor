"""Synthetic geometry checks are software evidence, not parking accuracy."""
import sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.registration import check_transform,describe,estimate,development_rows

class RegistrationTests(unittest.TestCase):
    def test_reflection_singular_and_off_frame_transforms_rejected(self):
        for matrix in [np.zeros((3,3)),np.array([[-1,0,767],[0,1,0],[0,0,1]]),np.array([[1,0,700],[0,1,0],[0,0,1]])]:
            self.assertFalse(check_transform(matrix,(768,448))['accepted'])
        self.assertTrue(check_transform(np.array([[1,0,20],[0,1,10],[0,0,1]]),(768,448))['accepted'])
    def test_blank_images_do_not_invent_a_transform(self):
        features=describe(Image.new('RGB',(768,448)))
        matrix,result=estimate(features,features)
        self.assertIsNone(matrix);self.assertFalse(result['accepted'])
    def test_final_or_unknown_rows_are_excluded_before_loading(self):
        rows=[dict(split=s,image='must-not-open') for s in ['train','validation','test','unknown']]
        self.assertEqual([r['split'] for r in development_rows(rows)],['train','validation'])
    def test_known_texture_translation_recovers_source_to_target_direction(self):
        import cv2
        texture=np.random.default_rng(123).integers(0,256,(448,768),dtype=np.uint8)
        expected=np.array([[1.,0,12],[0,1,7],[0,0,1]])
        shifted=cv2.warpPerspective(texture,expected,(768,448))
        matrix,result=estimate(describe(Image.fromarray(texture)),describe(Image.fromarray(shifted)))
        self.assertTrue(result['accepted'],result)
        corners=np.float32([[150,100],[600,100],[600,350],[150,350]]).reshape(-1,1,2)
        recovered=cv2.perspectiveTransform(corners,matrix)
        truth=cv2.perspectiveTransform(corners,expected)
        self.assertLess(float(np.max(np.abs(recovered-truth))),1.)

if __name__=='__main__':unittest.main()
