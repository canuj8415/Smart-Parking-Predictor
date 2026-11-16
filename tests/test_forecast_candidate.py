import sys,unittest
from pathlib import Path
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecast_experiment import ResidualOccupancyLSTM,TrendGuardedOccupancyLSTM
from smart_parking.forecasting import build_windows
class CandidateTests(unittest.TestCase):
    def test_zero_initialized_candidate_exactly_matches_persistence(self):
        model=ResidualOccupancyLSTM();x=torch.rand(4,6,3)
        torch.testing.assert_close(model(x),x[:,-1,0],rtol=0,atol=0)
    def test_output_is_bounded_even_with_extreme_correction(self):
        model=ResidualOccupancyLSTM();model.output.bias.data.fill_(100)
        x=torch.zeros(2,6,3);x[:,-1,0]=torch.tensor([.99,.01])
        y=model(x);self.assertTrue(torch.all((y>=0)&(y<=1)))
    def test_validation_experiment_excludes_final_test_windows(self):
        windows=build_windows(splits=('train','validation'))
        self.assertEqual(set(windows),{'train','validation'})
        self.assertGreater(len(windows['train']),0);self.assertGreater(len(windows['validation']),0)
    def test_trend_guard_rejects_opposite_direction_and_flat_history(self):
        model=TrendGuardedOccupancyLSTM();model.output.bias.data.fill_(10)
        x=torch.full((3,6,3),.5);x[:,-3,0]=torch.tensor([.4,.6,.5])
        prediction=model(x)
        self.assertLessEqual(prediction[0].item(),.600001)
        torch.testing.assert_close(prediction[1:],x[1:,-1,0],rtol=0,atol=0)
    def test_trend_guard_can_learn_from_zero_initialization(self):
        model=TrendGuardedOccupancyLSTM();x=torch.full((1,6,3),.5);x[:,-3,0]=.4
        loss=(model(x)-.55).square().sum();loss.backward()
        self.assertGreater(model.output.bias.grad.abs().sum().item(),0)
if __name__=='__main__':unittest.main()
