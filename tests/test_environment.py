"""Dependency discovery must stay light and avoid claiming runtime acceptance."""
import importlib.util
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.environment import environment_report,setup_message


class EnvironmentTests(unittest.TestCase):
    def test_missing_core_components_report_plain_setup_guidance(self):
        with patch('smart_parking.environment.importlib.util.find_spec',return_value=None):
            report=environment_report(Path.cwd())
        self.assertFalse(report['prerequisites_found'])
        self.assertIn('torch',report['missing_required'])
        message=setup_message(report)
        self.assertIn('Missing components: vehicle models',message)
        self.assertNotIn('ModuleNotFoundError',message)
        self.assertFalse(report['packages_installed']);self.assertFalse(report['network_used'])

    def test_discovery_does_not_claim_binary_models_or_gui_test(self):
        with patch('smart_parking.environment.importlib.util.find_spec',return_value=object()):
            report=environment_report(Path.cwd())
        self.assertTrue(report['prerequisites_found'])
        self.assertFalse(report['binary_compatibility_tested']);self.assertFalse(report['model_files_checked'])
        self.assertFalse(report['gui_started']);self.assertTrue(report['discovery_only'])

    def test_importing_launcher_does_not_import_the_heavy_application(self):
        root=Path(__file__).resolve().parents[1];path=root/'run_app.py'
        spec=importlib.util.spec_from_file_location('_parking_launcher_test',path)
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'smart_parking.app':None}):spec.loader.exec_module(module)
        self.assertTrue(callable(module.launch))


if __name__=='__main__':unittest.main()
