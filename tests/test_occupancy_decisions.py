"""Synthetic categorical decisions check metrics separately from model quality."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.occupancy_decisions import decision_metrics
from smart_parking.occupancy_evaluation import occupancy_metrics

class OccupancyDecisionTests(unittest.TestCase):
    def test_matches_probability_band_counts_without_calibration_claim(self):
        labels=[0,1,1,0];states=['vacant','vacant','occupied','uncertain']
        r=decision_metrics(labels,states);p=occupancy_metrics(labels,[.1,.2,.8,.5])
        self.assertEqual(r['confusion'],p['selective_confusion'])
        for key,value in p['selective'].items():self.assertEqual(r[key],value)
        self.assertNotIn('brier_score',r)
    def test_unknown_or_empty_decisions_do_not_claim_perfection(self):
        self.assertIsNone(decision_metrics([0,1],['uncertain','uncertain'])['accuracy_on_covered'])
        self.assertIsNone(decision_metrics([],[])['vacancy_precision'])
        for y,s in [([0],[]),([2],['vacant']),([0],['missing'])]:
            with self.assertRaises(ValueError):decision_metrics(y,s)

if __name__=='__main__':unittest.main()
