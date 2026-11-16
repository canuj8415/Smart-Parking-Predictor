import unittest
from smart_parking.vacancy_retention import vacancy_retention
def row(i,p,label=0):return dict(source_id='A',camera_id='C',date='2026-01-01',frame='f',slot_id=str(i),label=label,probability_occupied=p)
class VacancyRetentionTests(unittest.TestCase):
    def test_equal_total_correct_counts_do_not_hide_identity_loss(self):
        b=[row(1,.1),row(2,.8)];c=[row(1,.8),row(2,.1)];r=vacancy_retention(b,c)
        self.assertFalse(r['gate_passed']);self.assertEqual(r['dates'][0]['fraction'],0)
    def test_identical_cohort_targets_required(self):
        for c in [[row(2,.1)],[row(1,.1,1)],[row(1,.1),row(1,.2)]]:
            with self.assertRaises(ValueError):vacancy_retention([row(1,.1)],c)
    def test_no_baseline_vacancy_is_not_perfect_evidence(self):
        r=vacancy_retention([row(1,.9,1)],[row(1,.9,1)]);self.assertIsNone(r['dates'][0]['fraction']);self.assertTrue(r['gate_passed'])
    def test_threshold_boundary_and_reordering(self):
        b=[row(1,.25),row(2,.2)];c=[row(2,.25),row(1,.25)];self.assertTrue(vacancy_retention(b,c)['gate_passed'])
    def test_nonfinite_and_invalid_settings_rejected(self):
        with self.assertRaises(ValueError):vacancy_retention([row(1,.1)],[row(1,float('nan'))])
        with self.assertRaises(ValueError):vacancy_retention([row(1,.1)],[row(1,.1)],minimum=2)
