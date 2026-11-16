"""Synthetic block maps verify projection direction and grid dimensions."""
import sys,unittest
from pathlib import Path
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.region_evaluation import project_logits
from smart_parking.region_transfer import RegionDecoder

class RegionEvaluationTests(unittest.TestCase):
    def test_double_resolution_block_map_projects_to_original_rectangular_grid(self):
        original=torch.tensor([[[[2.,-2.,1.],[-1.,3.,-3.]]]])
        native=original.repeat_interleave(2,2).repeat_interleave(2,3)
        actual=project_logits(native,(3,2))
        self.assertTrue(torch.equal(actual,original));self.assertEqual(actual.shape,(1,1,2,3))
    def test_decoder_supports_larger_input_without_changing_parameter_shapes(self):
        torch.set_num_threads(2);decoder=RegionDecoder();before={k:tuple(v.shape) for k,v in decoder.state_dict().items()}
        rgb=torch.zeros(1,3,224,384)
        features=(torch.zeros(1,64,56,96),torch.zeros(1,128,28,48),torch.zeros(1,256,14,24))
        with torch.no_grad():output=decoder(rgb,features)
        self.assertEqual(output.shape,(1,1,224,384));self.assertEqual(before,{k:tuple(v.shape) for k,v in decoder.state_dict().items()})

if __name__=='__main__':unittest.main()
