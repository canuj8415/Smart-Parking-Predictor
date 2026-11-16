"""Write-failure fixtures protect the prior checkpoint; no model accuracy claims."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.checkpointing import save_checkpoint_atomic

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        folder=Path(__file__).resolve().parents[1]/'.cache/test_tmp';folder.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=folder);self.path=Path(self.temp.name)/'latest.pt'
    def tearDown(self):self.temp.cleanup()
    def test_partial_failed_write_never_replaces_existing_checkpoint(self):
        self.path.write_bytes(b'previous complete checkpoint')
        def fail(payload,stream):stream.write(b'partial');raise RuntimeError('simulated interrupted serialization')
        with patch('smart_parking.checkpointing.torch.save',side_effect=fail):
            with self.assertRaises(RuntimeError):save_checkpoint_atomic({},self.path)
        self.assertEqual(self.path.read_bytes(),b'previous complete checkpoint')
        self.assertEqual(list(self.path.parent.glob('*.tmp-*')),[])
    def test_complete_checkpoint_is_readable_after_atomic_replacement(self):
        self.path.write_bytes(b'old');save_checkpoint_atomic(dict(value=torch.tensor([2.,5.])),self.path)
        actual=torch.load(self.path,map_location='cpu',weights_only=True)
        self.assertTrue(torch.equal(actual['value'],torch.tensor([2.,5.])))
