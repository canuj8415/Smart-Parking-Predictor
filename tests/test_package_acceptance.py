import copy,hashlib,tempfile,unittest
from pathlib import Path
from smart_parking.package_acceptance import verify_payload,verify_report_contract


class PackageAcceptanceTests(unittest.TestCase):
    def test_payload_changes_and_duplicate_aliases_are_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);file=root/'a.bin';file.write_bytes(b'original')
            row=dict(path='a.bin',sha256=hashlib.sha256(b'original').hexdigest())
            self.assertEqual(verify_payload(root,[row]),1)
            with self.assertRaises(ValueError):verify_payload(root,[row,dict(row,path='./a.bin')])
            file.write_bytes(b'changed')
            with self.assertRaises(ValueError):verify_payload(root,[row])

    def test_payload_traversal_and_absolute_paths_are_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            for value in ['../outside.bin',str(Path(folder).resolve()/'a.bin')]:
                with self.assertRaises(ValueError):verify_payload(folder,[dict(path=value,sha256='0'*64)])

    def records(self,root):
        python=str(root/'.venv/Scripts/python.exe');counts=dict(occupied=2,vacant=1,uncertain=1,total=4)
        env=dict(status='passed',python=python,packages=107,no_index_hash_locked_install=True,network_audit=dict(denied=[]),dependency_check='No broken requirements found.')
        app=dict(status='passed',runtime_executable=python,source_module_root=str(root),detectors=[dict(kind=k,counts=counts.copy()) for k in ['fasterrcnn','maskrcnn']],normal_python_network_attempts=0,forecast_method_exports=[dict(method_label=k) for k in ['Original LSTM','Group-relative residual LSTM']])
        app.update({k:True for k in ['forecast_plot_export_invalidated_on_selection_change','semantic_preview_separate_from_analysis','convolution_arithmetic_passed','progress_export_passed','svd_app_rank_switching_passed','strict_live_fixture_checks_passed','original_workspace_fallback_blocked','all_bundle_hashes_unchanged']})
        notebook=dict(status='passed',python=python,actual_kernel_executed=True,all_modules_from_package_venv=True,inline_png_outputs=1,kernel_audit=dict(denied=[]),origins=dict(test=str(root/'.venv/Lib/site-packages/test.py')))
        transactions=dict(status='passed',python=python,synthetic_transaction_tests=13,normal_forbidden_attempts=0,negative_network_probe_blocked=True)
        return [env,app,notebook,transactions],{k:counts.copy() for k in ['fasterrcnn','maskrcnn']}

    def test_metadata_contract_detects_count_regression_and_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();records,counts=self.records(root)
            self.assertTrue(verify_report_contract(root,*records,counts)['both_detector_counts_preserved'])
            altered=copy.deepcopy(records);altered[1]['detectors'][0]['counts']['vacant']=0
            with self.assertRaises(ValueError):verify_report_contract(root,*altered,counts)
            altered=copy.deepcopy(records);altered[2]['origins']['test']=str(root.parent/'foreign.py')
            with self.assertRaises(ValueError):verify_report_contract(root,*altered,counts)

    def test_empty_output_and_denials_do_not_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();records,counts=self.records(root)
            for change in ['kernel','denial','duplicate_detector']:
                altered=copy.deepcopy(records)
                if change=='kernel':altered[2]['actual_kernel_executed']=False
                elif change=='denial':altered[0]['network_audit']['denied']=['unexpected']
                else:altered[1]['detectors'][1]['kind']='fasterrcnn'
                with self.assertRaises(ValueError):verify_report_contract(root,*altered,counts)
