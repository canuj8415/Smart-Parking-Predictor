"""Generic copied-package integrity contracts, independent of historical run dates."""
import hashlib
from pathlib import Path


def verify_payload(root,entries):
    root=Path(root).resolve();seen=set()
    for entry in entries:
        relative=Path(entry['path']);path=(root/relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root) or path in seen:
            raise ValueError('Payload path escape or duplicate')
        seen.add(path)
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=entry['sha256']:raise ValueError('Payload checksum mismatch: '+entry['path'])
    if not seen:raise ValueError('Empty payload')
    return len(seen)


def verify_report_contract(root,environment,app,notebook,transactions,expected_counts):
    root=Path(root).resolve();python=(root/'.venv/Scripts/python.exe').resolve()
    for record in [environment,app,notebook,transactions]:
        if record['status']!='passed':raise ValueError('Component did not pass')
    for record,key in [(environment,'python'),(app,'runtime_executable'),(notebook,'python'),(transactions,'python')]:
        if Path(record[key]).resolve()!=python:raise ValueError('Runtime outside copied environment')
    if environment['packages']!=107 or environment['no_index_hash_locked_install'] is not True or environment['network_audit']['denied']:
        raise ValueError('Fresh locked offline installation not established')
    if 'No broken requirements found.' not in environment['dependency_check']:raise ValueError('Dependency check missing')
    if Path(app['source_module_root']).resolve()!=root:raise ValueError('Product imported outside copy')
    detectors=app['detectors']
    if len(detectors)!=2 or {d['kind'] for d in detectors}!={'fasterrcnn','maskrcnn'}:raise ValueError('Both distinct detectors required')
    for result in detectors:
        counts=result['counts']
        if set(counts)!={'occupied','vacant','uncertain','total'} or any(type(v)!=int or v<0 for v in counts.values()):raise ValueError('Invalid count fields')
        if counts['total']!=sum(counts[k] for k in ['occupied','vacant','uncertain']) or counts!=expected_counts[result['kind']]:raise ValueError('Training-demo count regression')
    if app['normal_python_network_attempts']!=0:raise ValueError('Normal application attempted Python networking')
    for key in ['forecast_plot_export_invalidated_on_selection_change','semantic_preview_separate_from_analysis','convolution_arithmetic_passed','progress_export_passed','svd_app_rank_switching_passed','strict_live_fixture_checks_passed','original_workspace_fallback_blocked','all_bundle_hashes_unchanged']:
        if app[key] is not True:raise ValueError('Application contract failed: '+key)
    if [r['method_label'] for r in app['forecast_method_exports']]!=['Original LSTM','Group-relative residual LSTM']:raise ValueError('Forecast identity regression')
    if notebook['actual_kernel_executed'] is not True or notebook['all_modules_from_package_venv'] is not True or notebook['inline_png_outputs']<1 or notebook['kernel_audit']['denied']:raise ValueError('Actual copied notebook execution not established')
    if not all(Path(path).resolve().is_relative_to(root/'.venv') for path in notebook['origins'].values()):raise ValueError('Notebook module fallback')
    if transactions['synthetic_transaction_tests']!=13 or transactions['normal_forbidden_attempts']!=0 or transactions['negative_network_probe_blocked'] is not True:raise ValueError('Transaction or negative-control failure')
    return dict(both_detector_counts_preserved=True,actual_package_runtime=True,actual_notebook_kernel=True,transaction_contract=True,normal_network_attempts=0)
