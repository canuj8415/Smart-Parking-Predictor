import unittest
from smart_parking.detection_diagnosis import diagnose


def target():return dict(label='truck',box=[0,0,10,10],track_id=25,eligible=True)
def pred(label='truck',score=.8,box=None):return dict(label=label,score=score,box=box or [0,0,10,10])


class DiagnosisTests(unittest.TestCase):
    def category(self,outputs):return diagnose([target()],outputs)['rows'][0]['category']

    def test_matched_road_vehicle(self):self.assertEqual(self.category([pred()]),'matched_at_operating_point')

    def test_low_score_is_evidence_not_new_match(self):
        result=diagnose([target()],[pred(score=.4)])
        self.assertEqual(result['rows'][0]['category'],'same_class_below_operating_threshold')
        self.assertEqual(result['operating_match']['matched_positives'],0)

    def test_outside_product_and_other_road_classes_are_distinct(self):
        self.assertEqual(self.category([pred('train')]),'outside_product_class_at_operating_point')
        self.assertEqual(self.category([pred('bus')]),'road_class_disagreement')

    def test_localization_and_unresolved_do_not_invent_rpn_failure(self):
        self.assertEqual(self.category([pred(box=[6,0,16,10])]),'same_class_localization_gap')
        self.assertEqual(self.category([]),'unresolved_after_postprocessing')
        self.assertFalse(diagnose([target()],[])['exhaustive_precision_evaluable'])

    def test_competing_truth_never_double_counts_one_prediction(self):
        result=diagnose([target(),target()],[pred()])
        self.assertEqual(result['operating_match']['matched_positives'],1)
        self.assertIn('one_to_one_competition',[r['category'] for r in result['rows']])

    def test_other_low_score_class_signature(self):
        self.assertEqual(self.category([pred('train',.2)]),'other_class_below_operating_threshold')

    def test_nonfinite_scores_and_invalid_thresholds_fail(self):
        with self.assertRaises(ValueError):diagnose([target()],[pred(score=float('nan'))])
        with self.assertRaises(ValueError):diagnose([target()],[],confidence=1)
