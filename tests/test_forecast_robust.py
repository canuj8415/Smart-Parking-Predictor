"""Synthetic objective/split checks; no forecast-accuracy result is implied."""
import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from smart_parking.forecast_robust import blocked_folds,fit_risk_scales,group_relative_loss,occupied_space_predictions
from smart_parking.forecasting import build_windows

class RobustForecastTests(unittest.TestCase):
    def rows(self):
        return [dict(origin=f'2020-01-{d:02d}T12:00:00',target_time=f'2020-01-{d:02d}T12:30:00',
            input_source_rows=[2*d],target_source_row=2*d+1,car_park_id='A',y=.5,baseline=.4,capacity=100) for d in range(1,11)]
    def test_expanding_folds_only_contain_earlier_disjoint_fit_dates(self):
        folds=blocked_folds(self.rows());self.assertEqual([(len(a),len(b)) for a,b in folds],[(4,2),(6,2),(8,2)])
        for a,b in folds:self.assertLess(max(r['target_time'] for r in a),min(r['origin'] for r in b))
    def test_source_overlap_or_insufficient_dates_is_rejected(self):
        rows=self.rows();rows[4]['target_source_row']=rows[0]['target_source_row']
        with self.assertRaisesRegex(ValueError,'overlap'):blocked_folds(rows)
        with self.assertRaisesRegex(ValueError,'ten'):blocked_folds(self.rows()[:9])
    def test_risk_scale_fitting_is_independent_of_future_targets(self):
        rows=self.rows();scales=fit_risk_scales(rows[:4]);rows[-1]['y']=1000
        self.assertEqual(scales,fit_risk_scales(rows[:4]));self.assertAlmostEqual(scales['per_park']['A'],10)
        rows[0]['baseline']=rows[0]['y'];self.assertEqual(fit_risk_scales(rows[:1])['per_park']['A'],1)
    def test_group_weighting_is_not_domination_by_window_count(self):
        rows=[dict(car_park_id=p,capacity=100) for p in ['A','A','B']]
        pred=torch.tensor([.1,.1,.3],requires_grad=True);actual=torch.zeros(3)
        loss=group_relative_loss(pred,actual,rows,dict(per_park={'A':10,'B':10},unknown_park=20))
        self.assertAlmostEqual(loss.item(),2.5);loss.backward();self.assertGreater(pred.grad[2],pred.grad[0])
        # Unknown parks retain a train-derived fallback; no tuning-label normalization.
        loss=group_relative_loss(torch.tensor([.2]),torch.zeros(1),[dict(car_park_id='new',capacity=100)],dict(per_park={'A':10},unknown_park=20))
        self.assertAlmostEqual(loss.item(),1)
    def test_empty_or_mismatched_inputs_fail(self):
        with self.assertRaises(ValueError):fit_risk_scales([])
        with self.assertRaises(ValueError):group_relative_loss(torch.zeros(1),torch.zeros(1),[],{})

    def test_zero_residual_is_exact_original_count_and_output_is_bounded(self):
        rows=[dict(baseline=7/29,capacity=29),dict(baseline=.99,capacity=100)]
        x=torch.zeros(2,6,3);x[:,-1,0]=torch.tensor([7/29,.99])
        self.assertEqual(occupied_space_predictions(rows,x[:,-1,0],x),[7.,99.])
        self.assertEqual(occupied_space_predictions(rows,torch.ones(2)*3,x),[29.,100.])

    def test_reserved_final_dates_block_legacy_read_before_manifest_is_opened(self):
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            base=Path(tmp);folder=base/'data/manifests';folder.mkdir(parents=True)
            (folder/'forecast_fresh_dates_v1.json').write_text('{}')
            # No source file exists: failure must be the reservation, not a data read.
            for splits in [('test',),('train','validation','test')]:
                with self.assertRaisesRegex(ValueError,'reserved'):build_windows(base,splits=splits)

if __name__=='__main__':unittest.main()
