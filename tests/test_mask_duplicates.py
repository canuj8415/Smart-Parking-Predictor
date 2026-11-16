import copy
import random
import unittest
import numpy as np
from smart_parking.mask_duplicates import deduplicate


def obj(label='car',box=None):return dict(label=label,box=box or [0,0,16,16],score=.8)


class MaskDuplicateTests(unittest.TestCase):
    def test_identical_crop_suppressed_but_reference_duplicates_preserved(self):
        masks=np.ones((3,16,16),dtype=bool);result=deduplicate([obj()]*3,masks,2)
        self.assertEqual(result['kept_indices'],[0,1]);self.assertEqual(result['suppressed'][0]['removed_index'],2)

    def test_contained_fragment_uses_mask_support(self):
        masks=np.zeros((2,16,16),dtype=bool);masks[0]=True;masks[1,:4,:4]=True
        result=deduplicate([obj(),obj(box=[0,0,4,4])],masks,1)
        self.assertEqual(result['kept_indices'],[0]);self.assertEqual(result['suppressed'][0]['mask_containment'],1)

    def test_overlapping_boxes_with_distinct_masks_remain_separate(self):
        masks=np.zeros((2,16,16),dtype=bool);masks[0,:,:8]=True;masks[1,:,8:]=True
        self.assertEqual(deduplicate([obj(),obj()],masks,1)['kept_indices'],[0,1])

    def test_different_class_overlap_is_review_only(self):
        result=deduplicate([obj(),obj('bus')],np.ones((2,16,16),dtype=bool),1)
        self.assertEqual(result['kept_indices'],[0,1]);self.assertFalse(result['classes_remapped'])
        self.assertEqual(result['reviews'][0]['reason'],'overlapping_road_class_conflict')

    def test_tiny_masks_not_automatically_merged(self):
        masks=np.zeros((2,16,16),dtype=bool);masks[:,:2,:2]=True
        result=deduplicate([obj(),obj()],masks,1);self.assertEqual(result['kept_indices'],[0,1]);self.assertEqual(result['reviews'][0]['reason'],'tiny_mask_identity_uncertain')

    def test_empty_predicted_mask_remains_review_not_empty_truth(self):
        result=deduplicate([obj()],np.zeros((1,16,16),dtype=bool),1)
        self.assertEqual(result['reviews'][0]['reason'],'empty_predicted_mask_support')

    def test_invalid_shapes_types_or_prefix_fail(self):
        for masks,prefix in [(np.zeros((1,16,16)),1),(np.zeros((2,16,16),dtype=bool),1),(np.zeros((1,16,16),dtype=bool),2)]:
            with self.assertRaises(ValueError):deduplicate([obj()],masks,prefix)

    def test_seeded_distinct_adjacent_masks_are_preserved_without_mutation(self):
        rng=random.Random(142)
        for _ in range(25):
            boundary=rng.randint(5,25);masks=np.zeros((2,32,32),dtype=bool);masks[0,:,:boundary]=True;masks[1,:,boundary:]=True
            before=masks.copy();pred=[obj(box=[0,0,32,32])]*2;source=copy.deepcopy(pred)
            result=deduplicate(pred,masks,1);self.assertEqual(result['kept_indices'],[0,1]);self.assertEqual(pred,source);np.testing.assert_array_equal(masks,before)
