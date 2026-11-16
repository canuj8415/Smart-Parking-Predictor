import unittest
from pathlib import Path
from smart_parking.positive_instances import box_iou,match_positives,result_reference


def item(box,label='car'):return dict(box=box,label=label)


class PositiveInstanceTests(unittest.TestCase):
    def test_relative_and_absolute_result_paths_are_equivalent(self):
        relative=Path('experiments/results/example/run.json');root=Path.cwd()
        self.assertEqual(result_reference(relative,root),result_reference(root/relative,root))
        self.assertEqual(result_reference(relative,root),relative.as_posix())

    def test_result_reference_rejects_outside_root(self):
        root=Path.cwd()
        with self.assertRaises(ValueError):result_reference(root.parent/'outside.json',root)

    def test_maximum_cardinality_avoids_greedy_loss(self):
        truth=[item([0,0,10,10]),item([0,0,6,10])]
        pred=[item([0,0,8,10]),item([3,0,10,10])]
        result=match_positives(truth,pred,.5)
        self.assertEqual(result['matched_positives'],2)

    def test_one_prediction_never_supports_two_truth_objects(self):
        result=match_positives([item([0,0,10,10])]*2,[item([0,0,10,10])])
        self.assertEqual(result['matched_positives'],1)

    def test_wrong_class_and_unmatched_predictions_are_not_precision(self):
        result=match_positives([item([0,0,10,10])],[item([0,0,10,10],'truck')])
        self.assertEqual(result['matched_positives'],0)
        self.assertEqual(result['unmatched_predictions'],1)
        self.assertFalse(result['exhaustive_precision_evaluable'])

    def test_empty_targets_have_no_invented_recall(self):
        self.assertIsNone(match_positives([],[])['provided_positive_recall'])

    def test_invalid_geometry_and_threshold_fail(self):
        for a in ([0,0,0,1],[0,0,float('nan'),1]):
            with self.assertRaises(ValueError):box_iou(a,[0,0,1,1])
        with self.assertRaises(ValueError):match_positives([],[],0)
