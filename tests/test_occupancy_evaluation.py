"""Synthetic confusion and empty-denominator fixtures, not model accuracy."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.occupancy_evaluation import occupancy_metrics

class OccupancyEvaluationTests(unittest.TestCase):
    def test_false_vacancy_and_uncertainty_have_distinct_denominators(self):
        r=occupancy_metrics([0,1,1,0],[.1,.2,.8,.5])
        self.assertEqual(r['hard_confusion'],[[1,1],[1,1]])
        self.assertEqual(r['selective_confusion'],[[1,0,1],[1,1,0]])
        self.assertEqual(r['selective']['false_vacant'],1)
        self.assertEqual(r['selective']['vacancy_precision'],.5)
        self.assertEqual(r['selective']['coverage'],.75)
        self.assertEqual(r['selective']['fraction_of_occupied_called_vacant'],.5)
    def test_no_decisions_or_no_vacancies_does_not_mean_perfect_accuracy(self):
        r=occupancy_metrics([0,1],[.4,.6]);self.assertIsNone(r['selective']['accuracy_on_covered']);self.assertIsNone(r['selective']['vacancy_precision'])
        self.assertEqual(r['selective']['coverage'],0)
        r=occupancy_metrics([],[]);self.assertIsNone(r['hard']['accuracy_on_covered']);self.assertIsNone(r['probability_calibration_ece'])
    def test_exact_boundaries_match_existing_runtime(self):
        r=occupancy_metrics([0,1],[.25,.75]);self.assertEqual(r['selective_confusion'],[[1,0,0],[0,1,0]])
    def test_perfect_probabilities_and_upper_bin(self):
        r=occupancy_metrics([0,1],[0.,1.]);self.assertEqual(r['brier_score'],0);self.assertEqual(r['probability_calibration_ece'],0)
        self.assertEqual(r['calibration_bins'][-1]['count'],1)
    def test_invalid_data_rejected(self):
        for labels,scores in [([1],[]),([2],[.1]),([1],[float('nan')]),([0],[1.1])]:
            with self.assertRaises(ValueError):occupancy_metrics(labels,scores)
        with self.assertRaises(ValueError):occupancy_metrics([0],[.5],low=.8,high=.7)

if __name__=='__main__':unittest.main()
