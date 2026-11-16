"""Independent identity/version and scoped negative controls after the build."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T025043Z'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def main():
    state=read('data/automation_state.json');run=read('experiments/results/'+state['last_completed_run']+'/run.json')
    assert run['run_id'].startswith('COMBINED-DEMO-20261026') and run['combined_demo_gate_passed'] and not run['cancelled']
    package=ROOT/run['package'];python=package/'.venv/Scripts/python.exe'
    assert all(Path(run[key][field]).resolve()==python.resolve() for key,field in [('offline_environment','python'),('app_validation','runtime_executable'),('notebook_validation','python')])
    expected_counts=dict(occupied=68,vacant=32,uncertain=0,total=100)
    assert len(run['app_validation']['detectors'])==2 and all(d['counts']==expected_counts for d in run['app_validation']['detectors'])
    methods=run['app_validation']['forecast_method_exports']
    assert [m['method_label'] for m in methods]==['Original LSTM','Group-relative residual LSTM']
    assert run['app_validation']['forecast_plot_export_invalidated_on_selection_change']
    assert run['notebook_validation']['actual_kernel_executed'] and run['notebook_validation']['all_modules_from_package_venv']
    assert run['app_validation']['normal_python_network_attempts']==0
    assert all(sha(package/e['path'])==e['sha256'] for e in run['payload'])
    assert all(sha(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes']}.items())
    pre=read(E/'preflight.json');old=ROOT/pre['old_pointer']['path'];old_manifest=read(old/'BUNDLE_MANIFEST.json')
    assert all(sha(ROOT/p)==h for p,h in pre['old_files'].items())
    assert all(sha(old/e['path'])==e['sha256'] for e in old_manifest['files'])
    manifests=[read(package/'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json'),read(package/'dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json')]
    expected={e['name']:e['version'] for m in manifests for e in m['entries']};assert len(expected)==107
    code='import importlib.metadata,json;expected='+repr(expected)+';print(json.dumps({n:importlib.metadata.version(n) for n in expected}))'
    versions=subprocess.run([str(python),'-I','-c',code],cwd=package,capture_output=True,text=True,timeout=60)
    assert versions.returncode==0,versions.stderr
    actual=json.loads(versions.stdout);assert actual==expected
    configuration=package/'.venv/pyvenv.cfg';before=sha(configuration)
    refusal=subprocess.run([str(python),'-I',str(package/'scripts/setup_offline_bundle.py')],cwd=package,capture_output=True,text=True,timeout=30)
    assert refusal.returncode!=0 and 'FileExistsError' in refusal.stderr and sha(configuration)==before
    audit=package/'outputs/post_validation';audit.mkdir(parents=True,exist_ok=True)
    for kind in ['fallback','network']:
        action=(repr(str(ROOT/'README.md'))+',"rb"' if kind=='fallback' else None)
        body='open('+action+').read()' if action else '__import__("socket").getaddrinfo("example.invalid",80)'
        code=('import sys;sys.path.insert(0,'+repr(str(package/'scripts'))+');from package_offline_guard import install;'
            'save=install('+repr(str(package))+','+repr(str(audit/(kind+'.json')))+');'+body)
        result=subprocess.run([str(python),'-I','-c',code],cwd=package,capture_output=True,text=True,timeout=30)
        assert result.returncode!=0 and 'PermissionError' in result.stderr
        record=read(audit/(kind+'.json'));assert len(record['denied'])==1
    for relative in ['outputs/setup/install_audit.json','outputs/notebook_check/controller_audit.json','outputs/notebook_check/kernel_audit.json']:
        assert not read(package/relative)['denied']
    outcome=dict(run_id=run['run_id'],package=run['package'],payload_files=run['payload_files'],payload_bytes=run['payload_bytes'],
        exact_installed_versions=actual,expected_installed_packages_verified=107,new_package_environment_verified=True,
        original_package_payload_and_ready_files_unchanged=True,original_package_files_verified=len(old_manifest['files']),
        overwrite_existing_environment_refused=True,original_workspace_fallback_negative_probe_blocked=True,
        network_negative_probe_blocked=True,normal_app_python_network_attempts=0,installer_and_jupyter_audit_denials=0,
        forecast_methods_verified=[m['method_label'] for m in methods],genuine_jupyter_kernel_verified=True,
        copied_live_snapshot=run['cached_live_snapshot'],copied_live_provider_timestamp=run['cached_live_provider_timestamp'],
        selected_notebooks=run['selected_notebooks'],excluded_notebooks=run['excluded_notebooks'],
        scope='Actual copied-folder checks using existing base Python/Windows/Tk;no physical/new-machine/visible/manual/student or model-accuracy claim')
    dump(E/'independent_checks.json',outcome)
    print(json.dumps({k:v for k,v in outcome.items() if k!='exact_installed_versions'},indent=2))


if __name__=='__main__':main()
