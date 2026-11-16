"""Freeze the accepted older copy, current module changes and fixed acceptance gates."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.package_acceptance import verify_payload

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    e=ROOT/'experiments/evidence/HEARTBEAT-20261027T043910Z';assert not(e/'preflight.json').exists()
    state=read(ROOT/'data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==99 and not state['active_validation_jobs'] and not state['active_training_jobs']
    pointer=read(ROOT/'reports/demo_package_latest.json');package=(ROOT/pointer['path']).resolve();assert package.is_relative_to(ROOT/'outputs/offline_demo_packages')
    manifest=read(package/'BUNDLE_MANIFEST.json');assert digest(package/'BUNDLE_MANIFEST.json')==pointer['manifest_sha256'];assert verify_payload(package,manifest['files'])==451
    ready=read(package/'READY.json');assert ready['gate_passed'];acceptance=(package/ready.get('report','COMBINED_VALIDATION.json')).resolve();assert acceptance.is_relative_to(package)
    assert digest(acceptance)==ready['report_sha256']==pointer['validation_sha256']
    oldfiles={f.relative_to(ROOT).as_posix():digest(f) for f in [package/name for name in ['READY.json','BUNDLE_MANIFEST.json','BUNDLE_SCOPE.json','COMBINED_VALIDATION.json','VALIDATION_REPORT.json','OFFLINE_ENVIRONMENT.json','NOTEBOOK_VALIDATION.json','EXPORT_TRANSACTION_VALIDATION.json',acceptance.name]]}
    for name in ['demo_package_latest.json','offline_demo_latest.json']:
        source=ROOT/'reports'/name;dump(e/name,read(source));oldfiles[source.relative_to(ROOT).as_posix()]=digest(source)
    assert read(ROOT/'models/occupancy_patch_validation.json')['implementation_gate_passed'] and read(ROOT/'models/assignment_api_validation.json')['integration_gate_passed']
    app=read(package/'VALIDATION_REPORT.json');protected=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T040910Z/checks.json')['frozen_hashes_unchanged']
    for f,h in protected.items():assert digest(ROOT/f)==h,f
    contract=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),previous_run=pointer['run_id'],previous_pointer_sha256=digest(ROOT/'reports/demo_package_latest.json'),expected_counts={d['kind']:d['counts'] for d in app['detectors']},training_image_sha256=app['training_demo']['image_sha256'],detector_weight_hashes={d['kind']:d['weight_sha256'] for d in app['detectors']},vision_sha256=digest(ROOT/'src/smart_parking/vision.py'),occupancy_patch_sha256=digest(ROOT/'src/smart_parking/occupancy_patches.py'),expected_installed_packages=107,expected_transaction_cases=13,scope='Current selected-copy software integration;counts are fixed TRAIN example outputs,not accuracy. Prior copy immutable. No target/final data/model fitting or threshold changes.')
    cp=ROOT/'data/manifests/copied_package_acceptance_v1.json';assert not cp.exists();dump(cp,contract)
    files=['scripts/build_offline_demo.py','scripts/verify_refreshed_package.py','src/smart_parking/package_acceptance.py','tests/test_package_acceptance.py','scripts/prepare_current_copy.py']
    dump(e/'preflight.json',dict(prepared_at=contract['created_at'],counter_before=99,previous_pointer=pointer,previous_files=oldfiles,previous_payload_files=manifest['files'],contract_sha256=digest(cp),source_hashes={f:digest(ROOT/f) for f in files},previous_builder_sha256=digest(e/'build_offline_demo_before_refresh.py'),protected_hashes=protected,old_payload_bytes_verified=True,new_trial_started=False,physical_or_manual_acceptance=False))
    print(json.dumps(dict(counter=99,old_copy_preserved=True,old_payload_files=451,contract_sha256=digest(cp))))

if __name__=='__main__':main()
