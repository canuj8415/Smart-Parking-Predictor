"""Synthetic causal feature/preprocessing fixtures;no actual forecast scores."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.singapore_ridge import feature_vector,fit_residual_ridge,predict_available
class SingaporeRidgeTests(unittest.TestCase):
    def row(self):return dict(capacity=100,origin_available=50,previous_available=40,previous_gap_minutes=30,issued_at='2026-01-01T01:00:00+00:00',origin_available_at='2026-01-01T01:00:00+00:00',previous_available_at='2026-01-01T00:30:00+00:00',target_available=60,actual_target_lead_minutes=30)
    def test_features_do_not_read_target_values_or_realized_horizon(self):
        row=self.row();self.assertEqual(feature_vector(row),feature_vector(dict(row,target_available=0,actual_target_lead_minutes=45)))
    def test_future_features_and_bad_gap_rejected(self):
        for change in [dict(previous_available_at='2026-01-01T01:00:01+00:00'),dict(previous_gap_minutes=90),dict(origin_available=101)]:
            with self.assertRaises(ValueError):feature_vector(dict(self.row(),**change))
    def test_training_statistics_and_roundtrip_predictions_are_fixed(self):
        rows=[dict(self.row(),origin_available=i,target_available=i+10) for i in [40,50,60]];model=fit_residual_ridge(rows)
        self.assertEqual(model['mean'][0],.5);before=list(model['mean']);pred=predict_available(model,[dict(self.row(),origin_available=99,target_available=0)])
        self.assertEqual(model['mean'],before);self.assertTrue(0<=pred[0]<=100)
    def test_empty_training_or_nonpositive_regularization_rejected(self):
        with self.assertRaises(ValueError):fit_residual_ridge([])
        with self.assertRaises(ValueError):fit_residual_ridge([self.row()],0)
if __name__=='__main__':unittest.main()
