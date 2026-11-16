"""Recheck six provisional groups using manifests/claims;never open images/XML."""
import csv,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.group_role_audit import audit_groups


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def main():
    start=datetime.now(timezone.utc);rid='PKLOT-REMAINING-GROUPS-'+start.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    inventory=ROOT/'models/pklot_unused_date_inventory.json';development=ROOT/'data/manifests/pklot_fresh_development_v1.json';claims=sorted((ROOT/'data/holdout_claims').glob('*.claim.json'))
    files=[inventory,development,*claims];code=['scripts/audit_remaining_pklot_groups.py','src/smart_parking/group_role_audit.py','tests/test_group_role_audit.py']
    protocol=dict(run_id=rid,prepared_at=start.isoformat(),seed=150,source_ids=['SRC-DS-001'],hypothesis='Previously six provisional unused groups may now all be development-exposed or consumed;frozen old reservation flags cannot override durable claims.',
        input_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in files},source_hashes={p:digest(ROOT/p) for p in code},
        gates=['All six candidates accounted for by development or durable whole-group claims','No image/XML/archive semantic access','No new final admission or old claim changes'],
        prior_exposure='Earlier candidate inventory and completed experiment statuses already known;this is an updated-role integrity audit,not blind data discovery',maximum_seconds=30)
    dump(out/'protocol.json',protocol);dump(out/'source_snapshots.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in code});timer=time.monotonic()
    statepath=ROOT/'data/automation_state.json';s=read(statepath);assert s['completed_recorded_runs_since_schedule']==86 and not s['active_training_jobs'] and not s['active_validation_jobs']
    result=audit_groups(read(inventory)['summary']['eligible_groups'],read(development)['frames'],[read(p) for p in claims])
    assert result['provisional_candidates']==6 and result['development_exposed']==3 and result['consumed_final']==3 and result['not_accounted_for']==0
    assert all(digest(ROOT/p)==h for p,h in protocol['input_hashes'].items())
    report=dict(run_id=rid,started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,seed=150,protocol_sha256=digest(out/'protocol.json'),
        **result,metadata_gate_passed=True,image_pixels_decoded=0,xml_semantic_labels_parsed=0,archive_bodies_scanned=0,model_calls=0,
        scope='Only the six groups identified by the earlier conservative inventory;not proof that no other dataset/camera/new acquisition exists',
        action='Require genuinely new qualified groups/source before evaluating changed vision methods;do not rename exposed dates as fresh final data')
    dump(out/'run.json',report);dump(ROOT/'models/pklot_remaining_group_audit.json',report);dump(ROOT/'reports/pklot_remaining_groups_latest.json',report)
    registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
    with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
    row=dict(experiment_id=rid,run_type='Metadata-only update of provisional PKLot group roles',started_at=report['started_at'],finished_at=report['finished_at'],source_ids='SRC-DS-001',split_ids='Six earlier provisional camera/date groups;no pixels/semanticlabels',configuration=(out/'protocol.json').relative_to(ROOT).as_posix(),architecture='Conservative date/claim reconciliation',random_seed=150,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(report),logs=out.relative_to(ROOT).as_posix(),checkpoints='No model changes',code_revision_basis='64ab20e plus sealed role-audit sources',implementation_sha256=digest(__file__),conclusions='3development/3consumedfinal;0newqualifiedgroups;no replay/automatic admission')
    with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
    s['completed_run_ids'].append(rid);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=rid;s['pklot_remaining_group_audit']=report;dump(statepath,s)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
