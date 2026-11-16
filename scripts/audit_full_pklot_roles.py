"""Full validated archive index role audit;no JPEG/XML decoding or network access."""
import argparse,csv,hashlib,json,os,socket,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.pklot_group_ledger import build_ledger

INPUTS=['models/pklot_unused_date_inventory.json','data/splits/pklot-archive-inventory-v1/pairs.csv','data/manifests/pklot_frames.csv','data/manifests/segmentation_known_camera_v1.json','data/manifests/region_broader_development_v1.json','data/manifests/pklot_fresh_development_v1.json','data/manifests/occupancy_expansion_v1.json','data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];now=datetime.now(timezone.utc);rid='PKLOT-ALL-ROLES-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    inventory=read(ROOT/INPUTS[0]);assert digest(ROOT/INPUTS[1])==inventory['summary']['manifest_sha256'];claims=sorted((ROOT/'data/holdout_claims').glob('*.claim.json'));files=[ROOT/p for p in INPUTS]+claims;code=['scripts/audit_full_pklot_roles.py','src/smart_parking/pklot_group_ledger.py','tests/test_pklot_group_ledger.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=167,source_ids=['SRC-DS-001'],hypothesis='A complete12218pair/98group role ledger distinguishes durable final consumption,historical test closure,explicit TRAIN/DEV and earlier conservative metadata exclusions;missing newer claim is never freshness.',
        prior_exposure='Prior archive inventory found6provisionalgroups using conservative date exclusions;later6group audit3DEV/3consumed. This expands role reconciliation to the entire validated index,not a repeated archive/header/pixel scan or automatic admission.',
        index=INPUTS[1],archive='data/raw/pklot_subset/PKLot.tar.gz',expected_archive_sha256=inventory['archive_sha256'],claims=[f.relative_to(ROOT).as_posix() for f in claims],input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in files},source_hashes={f:digest(ROOT/f) for f in code},protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T043910Z/checks.json')['frozen_hashes_unchanged'],
        gates=['Archive compressed bytes/index checksum unchanged','All12218pairs/98canonicalgroups accounted with safe matching member paths','Historical test/durableclaim/known hash-alias closure overrides exposure role','Zero automatic newTRAIN/final admission','No image/XML file opens or network events in normal audit'],maximum_seconds=240,
        limitations=['Historical regex exclusions remain conservative;absence of explicit role does not prove unused data','Only known metadata image hashes detect byte aliases;no exhaustive new pixel/byte comparison across all frames','Supplied bay polygons are not exhaustive whole-parking-area/background ground truth','No new source,camera,model accuracy or final evaluation'])
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json')

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256'] and not(out/'run.json').exists()
    for f,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    sp=ROOT/'data/automation_state.json';s=read(sp);assert not s['active_training_jobs'] and not s['active_validation_jobs'];s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),maximum_seconds=240)];dump(sp,s);clock=time.perf_counter();started=datetime.now(timezone.utc).isoformat();denied=[]
    def audit(event,args):
        if event.startswith('socket.'):
            denied.append(dict(event=event));raise PermissionError('Metadata audit is offline')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)) and Path(os.fsdecode(args[0])).suffix.casefold() in {'.jpg','.jpeg','.png','.xml'}:
            denied.append(dict(event=event,path=os.fsdecode(args[0])));raise PermissionError('Image/XML file access forbidden')
    sys.addaudithook(audit)
    try:
        hasher=hashlib.sha256();size=0
        with (ROOT/p['archive']).open('rb') as stream:
            while chunk:=stream.read(8*1024**2):
                if (out/'CANCEL').exists() or time.perf_counter()-clock>240:raise InterruptedError('Metadata audit boundary')
                hasher.update(chunk);size+=len(chunk)
        assert hasher.hexdigest()==p['expected_archive_sha256']
        with (ROOT/p['index']).open(encoding='utf-8-sig',newline='') as stream:pairs=list(csv.DictReader(stream))
        exposures=[]
        for name in INPUTS[2:]:
            if name.endswith('.csv'):
                with (ROOT/name).open(encoding='utf-8-sig',newline='') as stream:frames=list(csv.DictReader(stream))
            else:frames=read(ROOT/name)['frames']
            exposures.extend(dict(camera_id=f['camera_id'],date=f['date'],role=f.get('split',f.get('role')),source=name,image_sha256=f.get('image_sha256')) for f in frames)
        historical=read(ROOT/INPUTS[0])['exclusion_records'];claims=[read(ROOT/f) for f in p['claims']];result=build_ledger(pairs,exposures,claims,historical)
        assert result['paired_frames']==12218 and result['camera_date_groups']==98 and result['new_final_groups_admitted']==result['new_training_groups_admitted']==0
        assert not denied;normal=list(denied);blocked=[]
        for name,action in [('image_open',lambda:(ROOT/'data/raw/DO_NOT_OPEN.jpg').read_bytes()),('external_socket',lambda:socket.getaddrinfo('role-audit.invalid',443))]:
            try:action()
            except PermissionError:blocked.append(name)
            else:raise AssertionError('Guard negative control failed')
        assert len(blocked)==2
        for f,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        r=dict(run_id=p['run_id'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=167,protocol_sha256=digest(path),**result,compressed_archive_bytes_hashed=size,index_sha256=digest(ROOT/p['index']),image_pixels_decoded=0,xml_labels_parsed=0,neural_model_calls=0,normal_forbidden_accesses=normal,guard_negative_controls=blocked,metadata_gate_passed=True,scope='Entire validated archive index metadata;not new image/label admission or scientific accuracy. Earlier historical exclusions remain in force;unknown roles are quarantined.')
        dump(out/'run.json',r);dump(ROOT/'models/pklot_full_role_ledger.json',r);dump(ROOT/'reports/pklot_full_role_ledger_latest.json',r)
        reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Whole validated archive role/alias metadata integrity audit',started_at=started,finished_at=r['finished_at'],source_ids='SRC-DS-001',split_ids='All12218indexedpairs/98groups;metadataonly,no pixel/semantic-label access',configuration=path.relative_to(ROOT).as_posix(),architecture='Canonical camera/date roles,historical exclusion and known-byte-alias closure',random_seed=167,hardware='CPU/streaming compressed-byte hash',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps({k:v for k,v in r.items() if k not in ['groups','known_cross_group_byte_aliases']}),logs=out.relative_to(ROOT).as_posix(),checkpoints='No weights changed;all prior claims preserved',code_revision_basis='86ceecb plus sealed full role-ledger sources',implementation_sha256=digest(__file__),conclusions='All98groups conservatively accounted;zero automatic newTRAIN/final admission')
        with reg.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(sp);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['pklot_full_role_ledger']=r;dump(sp,s);print(json.dumps({k:v for k,v in r.items() if k not in ['groups','known_cross_group_byte_aliases']},indent=2))
    except BaseException as error:dump(out/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:s=read(sp);s['active_validation_jobs']=[];dump(sp,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
