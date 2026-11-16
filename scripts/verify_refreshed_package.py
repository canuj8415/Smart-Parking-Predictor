"""Run inside any newly built selected package; no historical date or PID assumptions."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from smart_parking.package_acceptance import verify_payload,verify_report_contract
from package_offline_guard import install

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    output=ROOT/'outputs/current_acceptance';output.mkdir(parents=True,exist_ok=False);save=install(ROOT,output/'audit.json')
    contract=read(ROOT/'data/manifests/copied_package_acceptance_v1.json');manifest=read(ROOT/'BUNDLE_MANIFEST.json');python=ROOT/'.venv/Scripts/python.exe';assert Path(sys.executable).resolve()==python.resolve()
    count=verify_payload(ROOT,manifest['files'])
    records=[read(ROOT/f) for f in ['OFFLINE_ENVIRONMENT.json','VALIDATION_REPORT.json','NOTEBOOK_VALIDATION.json','EXPORT_TRANSACTION_VALIDATION.json']]
    checks=verify_report_contract(ROOT,*records,contract['expected_counts'])
    assert records[1]['training_demo']['image_sha256']==contract['training_image_sha256']
    assert {d['kind']:d['weight_sha256'] for d in records[1]['detectors']}==contract['detector_weight_hashes']
    assert sha(ROOT/'src/smart_parking/occupancy_patches.py')==contract['occupancy_patch_sha256']
    assert sha(ROOT/'src/smart_parking/vision.py')==contract['vision_sha256']
    import smart_parking.vision as vision
    import smart_parking.occupancy_patches as patches
    assert vision.assign_occupancy.__module__=='smart_parking.vision' and vision.assign_occupancy.__globals__['assign_occupancy_patches'] is patches.assign_occupancy_patches
    expected={e['name']:e['version'] for name in ['offline_app','offline_jupyter'] for e in read(ROOT/f'dependencies/{name}/v1/WHEELHOUSE_MANIFEST.json')['entries']};assert len(expected)==107
    code="import sys,json,importlib.metadata;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts'));from package_offline_guard import install;save=install(Path.cwd(),Path.cwd()/'outputs/current_acceptance/versions_audit.json');print(json.dumps({n:importlib.metadata.version(n) for n in "+repr(expected)+"}));save()"
    child=subprocess.run([str(python),'-I','-c',code],cwd=ROOT,capture_output=True,text=True,timeout=45);assert child.returncode==0,child.stderr;actual=json.loads(child.stdout);assert actual==expected and not read(output/'versions_audit.json')['denied']
    configuration=ROOT/'.venv/pyvenv.cfg';before=sha(configuration);refusal=subprocess.run([str(python),'-I',str(ROOT/'scripts/setup_offline_bundle.py')],cwd=ROOT,capture_output=True,text=True,timeout=30);assert refusal.returncode!=0 and 'FileExistsError' in refusal.stderr and sha(configuration)==before
    (output/'overwrite_refusal.txt').write_text(refusal.stdout+refusal.stderr,encoding='utf-8')
    probe="""import json,socket,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from package_offline_guard import install
save=install(Path.cwd(),Path.cwd()/'outputs/current_acceptance/negative_audit.json')
blocked=[]
try:Path(sys.argv[1]).read_text()
except PermissionError:blocked.append('original_workspace_read')
try:socket.getaddrinfo('offline-validation.invalid',443)
except PermissionError:blocked.append('external_dns')
save();assert len(blocked)==2;print(json.dumps(blocked))
"""
    original=Path(read(ROOT/'BUNDLE_SCOPE.json')['original_project_root'])/'README.md';negative=subprocess.run([str(python),'-I','-c',probe,str(original)],cwd=ROOT,capture_output=True,text=True,timeout=30);assert negative.returncode==0,negative.stderr;assert len(read(output/'negative_audit.json')['denied'])==2
    assert not read(ROOT/'outputs/notebook_check/controller_audit.json')['denied'];save();assert not read(output/'audit.json')['denied'];verify_payload(ROOT,manifest['files'])
    result=dict(status='passed',runtime=str(python),payload_files=count,all107versions=actual,checks=checks,occupancy_patch_import_verified=True,existing_environment_overwrite_refused=True,normal_audit_denials=0,expected_negative_controls=json.loads(negative.stdout),model_calls=0,scientific_accuracy_evaluated=False,physical_offline_newmachine_manual_student_acceptance=False)
    dump(ROOT/'CURRENT_ACCEPTANCE_VALIDATION.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
