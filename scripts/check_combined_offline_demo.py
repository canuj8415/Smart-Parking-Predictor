"""Check actual package/environment bindings and preserve scoped negative controls."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T221738Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
    state=read('data/automation_state.json');run=read('experiments/results/'+state['last_completed_run']+'/run.json')
    assert run['run_id'].startswith('COMBINED-DEMO-') and run['combined_demo_gate_passed'] and not run['cancelled']
    package=ROOT/run['package'];python=package/'.venv/Scripts/python.exe';E.mkdir(parents=True,exist_ok=True)
    assert all(Path(run[key][field]).resolve()==python.resolve() for key,field in [('offline_environment','python'),('app_validation','runtime_executable'),('notebook_validation','python')])
    expected=dict(occupied=68,vacant=32,uncertain=0,total=100)
    assert len(run['app_validation']['detectors'])==2 and all(d['counts']==expected for d in run['app_validation']['detectors'])
    assert run['notebook_validation']['actual_kernel_executed'] and run['notebook_validation']['all_modules_from_package_venv']
    assert run['app_validation']['normal_python_network_attempts']==0
    for relative in ['outputs/setup/install_audit.json','outputs/notebook_check/controller_audit.json','outputs/notebook_check/kernel_audit.json']:
        assert not read(package/relative)['denied']
    assert all(sha(package/e['path'])==e['sha256'] for e in run['payload'])
    assert all(sha(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes']}.items())
    cfg=package/'.venv/pyvenv.cfg';before=sha(cfg)
    refusal=subprocess.run([str(python),'-I',str(package/'scripts/setup_offline_bundle.py')],cwd=package,capture_output=True,text=True,timeout=30)
    assert refusal.returncode!=0 and 'FileExistsError' in refusal.stderr and sha(cfg)==before
    manifests=[read(package/'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json'),read(package/'dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json')]
    expected_versions={e['name']:e['version'] for m in manifests for e in m['entries']};assert len(expected_versions)==107
    child='''import importlib.metadata as m,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from package_offline_guard import install
save=install(Path.cwd(),Path.cwd()/'outputs/setup/version_check_audit.json')
expected=json.loads(sys.argv[1]);versions={name:m.version(name) for name in expected};assert versions==expected
save();print(json.dumps(dict(expected=107,verified=107,python=sys.executable,prefix=sys.prefix,versions=versions)))
'''
    version=subprocess.run([str(python),'-I','-c',child,json.dumps(expected_versions)],cwd=package,capture_output=True,text=True,timeout=60)
    assert version.returncode==0,version.stderr
    versions=json.loads(version.stdout);assert not read(package/'outputs/setup/version_check_audit.json')['denied']
    # Deliberate negative controls are separate from normal-use audit evidence.
    probe='''import json,socket,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from package_offline_guard import install
save=install(Path.cwd(),Path.cwd()/'outputs/setup/negative_guard_audit.json')
blocked=[]
try:Path(sys.argv[1]).read_text(encoding='utf-8')
except PermissionError:blocked.append('original_workspace_read')
try:socket.getaddrinfo('example.invalid',443)
except PermissionError:blocked.append('external_dns')
save();assert len(blocked)==2;print(json.dumps(dict(expected_blocked=blocked)))
'''
    negative=subprocess.run([str(python),'-I','-c',probe,str(ROOT/'README.md')],cwd=package,capture_output=True,text=True,timeout=30)
    assert negative.returncode==0,negative.stderr
    assert len(read(package/'outputs/setup/negative_guard_audit.json')['denied'])==2
    summary=dict(run_id=run['run_id'],fresh_environment_inside_copy=True,all107_locked_versions_verified=versions,
        expected_training_counts_agree=True,actual_notebook_kernel=True,existing_environment_overwrite_refused=True,
        environment_config_unchanged=True,explicit_guard_negative_controls=json.loads(negative.stdout),
        payload_files=run['payload_files'],payload_bytes=run['payload_bytes'],payload_hashes_unchanged=True,
        original_weights_and_consumed_claims_unchanged=True,normal_audits_have_no_denials=True,
        physical_offline_new_machine_or_manual_acceptance=False)
    (E/'package_checks.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    (E/'overwrite_refusal.txt').write_text(refusal.stdout+refusal.stderr,encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='all107_locked_versions_verified'},indent=2))
if __name__=='__main__':main()
