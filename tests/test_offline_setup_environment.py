import importlib.util,os,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('offline_setup_environment_test',ROOT/'scripts/setup_offline_bundle.py')
setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)


class OfflineSetupEnvironmentTests(unittest.TestCase):
    def test_external_pip_and_python_configuration_cannot_leak_into_child(self):
        base=ROOT/'outputs/test_fixtures';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as directory:
            root=Path(directory).resolve();assert root.is_relative_to(base.resolve())
            original={'PIP_INDEX_URL':'https://synthetic.invalid','pip_extra_index_url':'https://synthetic.invalid/extra','PYTHONPATH':'outside','PYTHONHOME':'outside','PYTHONSTARTUP':'outside','TEMP':'outside','TMP':'outside','PATH':'preserve-system-base-python'}
            env=setup.isolated_environment(root,original)
            self.assertEqual(original['TEMP'],'outside');self.assertNotIn('PYTHONPATH',env);self.assertNotIn('PYTHONHOME',env);self.assertNotIn('PYTHONSTARTUP',env)
            self.assertNotIn('PIP_INDEX_URL',env);self.assertNotIn('pip_extra_index_url',env);self.assertEqual(env['PIP_NO_INDEX'],'1');self.assertEqual(env['PIP_CONFIG_FILE'],os.devnull)
            self.assertEqual(env['PATH'],original['PATH']);self.assertEqual(env['TMP'],env['TEMP']);self.assertTrue(Path(env['TMP']).is_relative_to(root));self.assertTrue(Path(env['TMP']).is_dir())
