"""Fail closed before decoding when a new study's inputs/audit are invalid."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('region_trainer_settings',ROOT/'scripts/train_region_transfer.py')
trainer=importlib.util.module_from_spec(spec);spec.loader.exec_module(trainer)

class RegionTrainingSettingsTests(unittest.TestCase):
    def test_epoch_budget_and_development_path_rejected_before_decoding(self):
        with patch.object(trainer,'load',side_effect=AssertionError('Must not decode')):
            for value in [0,81]:
                with self.assertRaisesRegex(ValueError,'epoch budget'):trainer.study(max_epochs=value)
            with self.assertRaisesRegex(ValueError,'project manifests'):trainer.study(development_manifest='../outside.json')

    def test_failed_or_changed_broader_data_audit_blocks_training(self):
        parent=ROOT/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root=Path(temporary);manifests=root/'data/manifests';manifests.mkdir(parents=True)
            manifest=manifests/'region_broader_development_v1.json';manifest.write_text(json.dumps(dict(run_id='fixture')),encoding='utf-8')
            folder=root/'experiments/results/fixture';folder.mkdir(parents=True)
            with patch.object(trainer,'ROOT',root),patch.object(trainer,'load',side_effect=AssertionError('Must not decode')):
                for passed in [False,True]:
                    (folder/'run.json').write_text(json.dumps(dict(data_gate_passed=passed,development_manifest_sha256='changed')),encoding='utf-8')
                    with self.assertRaisesRegex(ValueError,'audit missing or changed'):
                        trainer.study(development_manifest='data/manifests/region_broader_development_v1.json')

if __name__=='__main__':unittest.main()
