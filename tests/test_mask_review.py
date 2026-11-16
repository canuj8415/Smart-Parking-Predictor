import copy
import unittest
import numpy as np
from smart_parking.mask_review import review_candidates


class MaskReviewTests(unittest.TestCase):
    def test_nested_same_class_masks_are_retained_as_review_candidates(self):
        # Synthetic reproduction of the dangerous containment signature, not real accuracy.
        masks=np.zeros((2,16,16),dtype=bool);masks[0]=True;masks[1,:8,:8]=True
        pred=[dict(label='car',box=[0,0,16,16]),dict(label='car',box=[0,0,8,8])]
        result=review_candidates(pred,masks,1)
        self.assertEqual(result['retained_indices'],[0,1]);self.assertEqual(result['automatic_removals'],0)
        self.assertEqual(result['review_items'][0]['reason'],'possible_same_class_duplicate')

    def test_class_conflict_does_not_relabel_or_delete(self):
        pred=[dict(label='car',box=[0,0,16,16]),dict(label='bus',box=[0,0,16,16])]
        result=review_candidates(pred,np.ones((2,16,16),dtype=bool),1)
        self.assertFalse(result['classes_remapped']);self.assertEqual(result['retained_indices'],[0,1])
        self.assertTrue(all(item['action']=='review_only' for item in result['review_items']))

    def test_prediction_and_mask_bytes_are_not_changed(self):
        pred=[dict(label='car',box=[0,0,16,16],score=.8)]*2;before=copy.deepcopy(pred);masks=np.ones((2,16,16),dtype=bool);content=masks.tobytes()
        review_candidates(pred,masks,1);self.assertEqual(pred,before);self.assertEqual(masks.tobytes(),content)

    def test_empty_review_is_not_an_empty_or_vacant_answer(self):
        result=review_candidates([],np.zeros((0,16,16),dtype=bool),0)
        self.assertEqual(result['retained_indices'],[]);self.assertNotIn('occupancy',result);self.assertEqual(result['automatic_removals'],0)
