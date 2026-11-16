"""A small fake detector verifies result semantics, not trained model accuracy."""
import sys,unittest
from pathlib import Path
import torch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.vision import VisionEngine

class DetectionOnlyTests(unittest.TestCase):
    def test_occupancy_is_unknown_without_a_camera_layout(self):
        engine=VisionEngine.__new__(VisionEngine)
        engine.model=lambda images:[dict(boxes=torch.empty((0,4)),labels=torch.empty(0,dtype=torch.int64),scores=torch.empty(0))]
        engine.model_name='software-fixture';engine.weight_sha256='not-a-model-weight';engine.classifier=None
        result,overlay=engine.analyze(Image.new('RGB',(8,8)))
        self.assertIsNone(result['counts']);self.assertFalse(result['occupancy_evaluated']);self.assertEqual(result['slots'],[])
        self.assertEqual(overlay.size,(8,8))
if __name__=='__main__':unittest.main()
