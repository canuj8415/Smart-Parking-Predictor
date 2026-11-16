"""Resumable routine TRAIN acquisition;no extra experiment count per image."""
import io,json,os,sys,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
from smart_parking.zip_members import image_member_span,validate_member_range,decode_jpeg_member
from smart_parking.layout import validate_layout
from PIL import Image
RAW=ROOT/'data/raw/acpds_official/17da2c8b33055be8019483260f0efbcbdfda0478';DEV=ROOT/'experiments/results/ACPDS-DEVELOPMENT-20261026T224240258641Z/development_annotations.json';ROLES=ROOT/'data/manifests/acpds_source_roles_v1.json'
OUT=ROOT/'data/processed/acpds_development_v1';PLAN=ROOT/'data/manifests/acpds_training_acquisition_v1.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def verified_cached(path,records,role):
    matching=[r for r in records if r.get('source_id')=='SRC-DS-021' and r.get('local_path')==path.relative_to(ROOT).as_posix()]
    if len(matching)!=1 or matching[0]['sha256']!=digest(path) or matching[0].get('role')!=role:raise ValueError('Existing file lacks one correct role/hash receipt')
    return matching[0]

def main():
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'development_images.json').exists():raise FileExistsError('Completed acquisition is immutable;use its manifest')
    dev=read(DEV);inv=read(RAW/'directory_inventory.json');head=read(RAW/'head.json');code=['scripts/acquire_acpds_training.py','src/smart_parking/zip_members.py','src/smart_parking/layout.py'];inputs=[DEV,ROLES,RAW/'directory_inventory.json',RAW/'head.json']
    if not PLAN.exists():dump(PLAN,dict(prepared_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-021',purpose='Routine remaining TRAIN acquisition plus receipted reuse of38development images;no per-image experiment count',selected=[dict(role=k,name=n) for k,d in dev.items() for n in d['file_names']],maximum_invocation_seconds=600,maximum_member_bytes=8_000_000,source_hashes={p:digest(ROOT/p) for p in code},input_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes']))
    plan=read(PLAN)
    for p,h in {**plan['source_hashes'],**plan['input_hashes'],**plan['protected_hashes']}.items():assert digest(ROOT/p)==h,p
    statepath=ROOT/'data/automation_state.json';s['active_validation_jobs']=[dict(kind='Routine ACPDS TRAIN acquisition',pid=os.getpid(),cancel_file=(OUT/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/acquire_acpds_training.py')];dump(statepath,s)
    records=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];allowed={'images/'+n for d in dev.values() for n in d['file_names']};frames=[];start=time.perf_counter();network_bytes=0;reused=0
    try:
        for chosen in plan['selected']:
            if (OUT/'CANCEL').exists() or time.perf_counter()-start>600:raise InterruptedError('Bounded acquisition stopped;receipts permit resume')
            role,name=chosen['role'],chosen['name'];assert role in ('train','valid') and name in dev[role]['file_names'];entry,begin,end=image_member_span('images/'+name,allowed,inv)
            member=RAW/'member_ranges'/(name+'.bin');imagepath=RAW/'images'/name
            if member.exists():
                r=verified_cached(member,records,role);assert (r['start'],r['end'],r['total'],r['etag'])==(begin,end,inv['total_bytes'],head['etag']);body=member.read_bytes();reused+=1
            else:
                # All VALID images were already acquired;never expand validation content here.
                assert role=='train';requested=datetime.now(timezone.utc).isoformat()
                with urllib.request.urlopen(urllib.request.Request(inv['archive_url'],headers={'User-Agent':'SmartParkingPBL/0.2','Range':f'bytes={begin}-{end}','If-Match':head['etag']}),timeout=30) as r:
                    body=r.read(end-begin+2);validate_member_range(r.status,r.headers.get('Content-Range'),begin,end,inv['total_bytes'],body,r.headers.get('ETag'),head['etag'])
                member.write_bytes(body);network_bytes+=len(body);records.append(receipt('SRC-DS-021',member,inv['archive_url'],'Exact admitted TRAIN JPEG member;routine data preparation',request_started_at=requested,status=206,start=begin,end=end,total=inv['total_bytes'],etag=head['etag'],role=role))
            decoded=decode_jpeg_member(body,entry)
            if imagepath.exists():verified_cached(imagepath,records,role);assert imagepath.read_bytes()==decoded
            else:
                imagepath.write_bytes(decoded);records.append(receipt('SRC-DS-021',imagepath,inv['archive_url'],'CRC-verified admitted TRAIN JPEG;original preserved',member='images/'+name,role=role,derived_from=member.relative_to(ROOT).as_posix(),derived_from_sha256=digest(member)))
            with Image.open(io.BytesIO(decoded)) as source:
                assert source.format=='JPEG' and source.size==(4000,3000) and source.getexif().get(274,1)==1
                source.load()
            index=dev[role]['file_names'].index(name);polygons=dev[role]['rois_list'][index];labels=dev[role]['occupancy_list'][index]
            layout=dict(schema_version=1,camera_id='ACPDS-unique-view-'+name,image_size=[4000,3000],origin='Author supplied normalized ground-space polygons',slots=[dict(id=str(i),polygon=[[float(x)*3999,float(y)*2999] for x,y in polygon],ground_truth_occupied=int(y)) for i,(polygon,y) in enumerate(zip(polygons,labels))]);validate_layout(layout,(4000,3000));lp=OUT/'layouts'/(name+'.json')
            if lp.exists():assert read(lp)==layout
            else:dump(lp,layout)
            frames.append(dict(role='validation' if role=='valid' else 'train',source_id='SRC-DS-021',name=name,image=imagepath.relative_to(ROOT).as_posix(),image_sha256=digest(imagepath),layout=lp.relative_to(ROOT).as_posix(),layout_sha256=digest(lp),slots=len(labels)))
            dump(OUT/'progress.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),images_verified=len(frames),images_total=266,network_bytes_this_invocation=network_bytes,reused_members=reused,elapsed_seconds=time.perf_counter()-start,completed=False,final_members_accessed=0))
            if len(frames)%40==0:print('Qualified development images',len(frames),'/266',flush=True)
        assert len(frames)==266 and sum(f['slots'] for f in frames if f['role']=='train')==7842 and sum(f['slots'] for f in frames if f['role']=='validation')==1904
        for p,h in {**plan['source_hashes'],**plan['input_hashes'],**plan['protected_hashes']}.items():assert digest(ROOT/p)==h,p
        result=dict(completed_at=datetime.now(timezone.utc).isoformat(),plan_sha256=digest(PLAN),role_manifest_sha256=digest(ROLES),frames=frames,training_images=231,validation_images=35,training_spaces=7842,validation_spaces=1904,final_members_accessed=0,network_bytes_this_invocation=network_bytes,duration_seconds_this_invocation=time.perf_counter()-start,completed_experiment_count_added=0)
        dump(OUT/'development_images.json',result);dump(ROOT/'reports/acpds_training_data_latest.json',dict(manifest=(OUT/'development_images.json').relative_to(ROOT).as_posix(),manifest_sha256=digest(OUT/'development_images.json'),**{k:v for k,v in result.items() if k!='frames'}));print(json.dumps({k:v for k,v in result.items() if k!='frames'}))
    except BaseException as e:dump(OUT/'interrupted.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),error=type(e).__name__,detail=str(e),verified=len(frames),resume_command='scripts/acquire_acpds_training.py',completed_experiment_count_added=0));raise
    finally:s=read(statepath);s['active_validation_jobs']=[];dump(statepath,s)

if __name__=='__main__':main()
