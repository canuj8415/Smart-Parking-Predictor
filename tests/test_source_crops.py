"""Synthetic crop/target/weight boundaries;no real model-accuracy evidence."""
import sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.source_crops import select_source_rows,prepare_occupancy_crop,balanced_source_weights

class SourceCropTests(unittest.TestCase):
    def row(self,label=0):return dict(source_line=1,class_id=label,normalized_polygon=[[.1,.1],[.8,.1],[.8,.8],[.1,.8]])
    def test_source_indices_are_explicitly_inverted_for_occupied_target(self):
        image=Image.new('RGB',(100,100),'white')
        for source in [0,1]:
            crop,info=prepare_occupancy_crop(image,self.row(source),np.full((100,100),1-source,dtype=np.uint8))
            self.assertTrue(info['accepted']);self.assertEqual(info['model_label'],1-source);self.assertEqual(crop.size,(96,96))
    def test_unknown_support_is_never_invented_and_small_crops_rejected(self):
        image=Image.new('RGB',(100,100),'white')
        crop,info=prepare_occupancy_crop(image,self.row(),np.full((100,100),255,dtype=np.uint8))
        self.assertIsNone(crop);self.assertEqual(info['known_fraction'],0)
        tiny=self.row();tiny['normalized_polygon']=[[.1,.1],[.11,.1],[.11,.11],[.1,.11]]
        self.assertIsNone(prepare_occupancy_crop(image,tiny,np.ones((100,100),dtype=np.uint8))[0])
    def test_label_blind_cap_order_and_no_replacement(self):
        rows=[dict(source_line=i) for i in range(100)]
        self.assertEqual([x['source_line'] for x in select_source_rows(rows,4)],[0,33,66,99])
        self.assertEqual(select_source_rows(rows,4),select_source_rows(rows[::-1],4))
        with self.assertRaises(ValueError):select_source_rows([rows[0],rows[0]])
    def test_small_unknown_patch_is_gray_instead_of_false_occupancy_content(self):
        support=np.ones((100,100),dtype=np.uint8);support[40:45,40:45]=255
        crop,info=prepare_occupancy_crop(Image.new('RGB',(100,100),'white'),self.row(),support)
        self.assertTrue(info['accepted']);self.assertLess(info['known_fraction'],1)
        self.assertLess(np.asarray(crop).min(),255)
        with self.assertRaises(ValueError):prepare_occupancy_crop(Image.new('RGB',(100,100)),self.row(),support,size=0)
    def test_configured_source_mass_and_mean_weight_are_preserved(self):
        rows=[dict(source_id='SRC-DS-001',camera_id=c,label=l) for c in ['a','b','c'] for l in [0,1] for _ in range(2)]
        rows += [dict(source_id='SRC-DS-018',camera_id='collection',label=l) for l in [0,1] for _ in range(9)]
        weights=balanced_source_weights(rows)
        self.assertAlmostEqual(sum(weights)/len(rows),1)
        self.assertAlmostEqual(sum(w for r,w in zip(rows,weights) if r['source_id']=='SRC-DS-001')/sum(weights),.75)
        with self.assertRaises(ValueError):balanced_source_weights(rows[:12])

if __name__=='__main__':unittest.main()
