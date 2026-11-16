"""Reserve whole publisher TEST before any annotation semantic decoding."""
import argparse,csv,json,struct,sys,time,urllib.request,zlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
from smart_parking.zip_metadata import validate_range
from smart_parking.acpds_admission import development_only,validate_development
RAW=ROOT/'data/raw/acpds_official/17da2c8b33055be8019483260f0efbcbdfda0478'
MANIFEST=ROOT/'data/manifests/acpds_source_roles_v1.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    now=datetime.now(timezone.utc);rid='ACPDS-DEVELOPMENT-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    assert not MANIFEST.exists()
    inv=read(RAW/'directory_inventory.json')
    dump(MANIFEST,dict(schema_version=1,source_id='SRC-DS-021',created_at=now.isoformat(),canonical_collection='https://github.com/martin-marek/parking-space-occupancy',revision=inv['revision'],archive_url=inv['archive_url'],archive_total_bytes=inv['total_bytes'],metadata_sha256=digest(RAW/'directory_inventory.json'),
        rights='Author explicitly shares dataset,code,models under MIT in arXiv:2107.12207 abstract;retain Copyright(c)2021 Martin Marek and MIT notice',
        partition_roles=dict(train='training_development',valid='validation_development',test='reserved_final'),
        group_rule='Whole author TEST partition and all its parking lots/views/aliases/annotations/derived representations remain closed. All archive images not explicitly admitted by TRAIN/VALID filenames default to closed;never infer fresh groups from renamed frames.',
        separation_evidence='Author abstract states parking lots across train/validation/test are unique;independent location/date verification unavailable',
        final_semantics_opened=False,final_pixels_opened=False,final_evaluation_started=False,
        future_gate='Implement and test durable canonical collection/whole TEST claim and frozen evaluation gates before TEST semantic/pixel access;failure consumes. Reservation is not a claim or evaluation.',
        limitations='Unique viewpoints,not fixed CCTV trajectories;capture dates and pretraining overlap unknown;no future occupancy/region accuracy inferred. No TEST JSON deserialization.'))
    code=['scripts/qualify_acpds_development.py','src/smart_parking/acpds_admission.py','tests/test_acpds_admission.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=151,source_ids=['SRC-DS-021'],hypothesis='Author-disjoint-lot partitions can admit development labels while reserving the entire TEST before semantic access.',
        prior_exposure='Author abstract/README/licence/loader and archive names/sizes inspected;no archive image or annotation semantic access before reservation.',
        gates=['Pinned author rights evidence and exact source identity','Exact bounded HTTP206/ETag and ZIP local/central size/CRC agreement','Only TRAIN/VALID deserialized;TEST semantics/pixels closed','Aligned explicit finite nondegenerate ROI/binary label arrays;no missing or cross-partition duplicate names','Protected hashes unchanged'],
        input_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in RAW.iterdir() if p.is_file()},role_manifest_sha256=digest(MANIFEST),implementation_hashes={p:digest(ROOT/p) for p in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],maximum_seconds=180,model_calls=0)
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in code});print(str(out/'protocol.json'))

def acquire_annotation(inv):
    e=next(x for x in inv['entries'] if x['name']=='annotations.json');total=inv['total_bytes'];url=inv['archive_url'];etag=read(RAW/'head.json')['etag'];events=[]
    def span(start,end,name):
        started=datetime.now(timezone.utc).isoformat();path=RAW/name
        assert end-start+1<=131072
        if path.exists():
            records=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
            cached=[r for r in records if r.get('local_path')==path.relative_to(ROOT).as_posix()]
            assert len(cached)==1
            r=cached[0];assert (r['sha256'],r['start'],r['end'],r['total'],r['etag'])==(digest(path),start,end,total,etag)
            events.append(r);return path.read_bytes()
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SmartParkingPBL/0.2','Range':f'bytes={start}-{end}','If-Match':etag}),timeout=30) as r:
            b=r.read(end-start+2);validate_range(r.status,r.headers.get('Content-Range'),start,end,total,b)
            if r.headers.get('ETag')!=etag:raise ValueError('Remote archive changed')
        path.write_bytes(b);events.append(receipt('SRC-DS-021',path,url,'Exact ZIP annotation range;compressed/TEST content remains opaque until scoped development reader',request_started_at=started,start=start,end=end,total=total,etag=etag))
        return b
    h=span(e['header_offset'],e['header_offset']+29,'annotations_header.bin');sig,version,flags,method,mt,md,crc,compressed,expanded,nlen,xlen=struct.unpack('<4s5H3I2H',h)
    if sig!=b'PK\x03\x04' or flags not in (0,8) or method!=8 or e['size']>2_000_000:raise ValueError('Unsupported annotation ZIP header')
    if flags==0 and (compressed,expanded,crc)!=(e['compressed_size'],e['size'],e['crc32']):raise ValueError('Local and central annotation sizes differ')
    if flags==8 and (crc!=0 or compressed!=0 or expanded not in (0,e['size'])):raise ValueError('Invalid streamed ZIP placeholders')
    compressed,expanded,crc=e['compressed_size'],e['size'],e['crc32']
    name=span(e['header_offset']+30,e['header_offset']+29+nlen+xlen,'annotations_name.bin')
    if name[:nlen]!=b'annotations.json':raise ValueError('Unexpected annotation member')
    begin=e['header_offset']+30+nlen+xlen;chunks=[]
    for j,start in enumerate(range(begin,begin+compressed,131072)):chunks.append(span(start,min(start+131071,begin+compressed-1),f'annotations_compressed_{j}.bin'))
    if flags==8:
        descriptor=span(begin+compressed,begin+compressed+15,'annotations_descriptor.bin')
        if struct.unpack('<4s3I',descriptor)!=(b'PK\x07\x08',crc,compressed,expanded):raise ValueError('ZIP data descriptor differs from central CRC/sizes')
    d=zlib.decompressobj(-15);body=d.decompress(b''.join(chunks),expanded+1)
    if len(body)!=expanded or not d.eof or d.unused_data or d.unconsumed_tail or zlib.crc32(body)!=crc:raise ValueError('Annotation CRC/expansion mismatch')
    path=RAW/'annotations_mixed_OPAQUE.json'
    if path.exists():assert path.read_bytes()==body
    else:
        path.write_bytes(body);receipt('SRC-DS-021',path,url,'CRC-verified mixed annotation body;TEST branch retained opaque;development-only structural reader')
    dump(RAW/'annotation_ranges.json',events);return body

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);start=datetime.now(timezone.utc);timer=time.perf_counter()
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not (out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    assert digest(MANIFEST)==p['role_manifest_sha256']
    implementations=p['implementation_hashes']
    amendment=out/'protocol_amendment_02.json'
    if not amendment.exists():amendment=out/'protocol_amendment.json'
    if amendment.exists():
        assert digest(amendment)==read(out/'amendment_binding.json')['sha256']
        a=read(amendment);assert a['original_protocol_sha256']==digest(path) and a.get('final_semantics_opened_at_amendment',a.get('semantic_labels_opened_at_amendment'))==0
        implementations=a['implementation_hashes']
    for f,h in {**p['input_hashes'],**implementations,**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    inv=read(RAW/'directory_inventory.json');body=acquire_annotation(inv);parts=development_only(body)
    summary=validate_development(parts,{e['name'] for e in inv['entries']})
    admitted={'images/'+name for d in parts.values() for name in d['file_names']};images={e['name'] for e in inv['entries'] if e['name'].lower().endswith('.jpg')}
    (out/'development_annotations.json').write_text(json.dumps(parts)+'\n',encoding='utf-8')
    closed=sorted(images-admitted);dump(out/'closed_image_names.json',dict(default_closed_images=closed,names_only=True,test_semantics_opened=False))
    for f,h in p['protected_hashes'].items():assert digest(ROOT/f)==h,f
    r=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-timer,seed=p['seed'],source_ids=p['source_ids'],protocol_sha256=digest(path),role_manifest_sha256=digest(MANIFEST),metadata_gate_passed=True,development=summary,archive_image_names=len(images),default_closed_image_names=len(closed),
        annotation_body_sha256=digest(RAW/'annotations_mixed_OPAQUE.json'),development_annotations=(out/'development_annotations.json').relative_to(ROOT).as_posix(),development_annotations_sha256=digest(out/'development_annotations.json'),
        protocol_amendment_sha256=digest(amendment) if amendment.exists() else None,all_range_receipts=read(RAW/'annotation_ranges.json'),whole_archive_acquired=False,whole_archive_integrity_verified=False,annotation_crc_verified=True,image_pixels_decoded=0,final_json_deserialized=False,final_semantic_validity_checked=False,final_evaluation=False,model_calls=0,production_promoted=False,
        limitations='Dataset qualification only. TEST structure scanned for top-level boundaries but values not deserialized/validated. Default-closed image names are archive complement,not a decoded TEST list. Author disjoint-lot claim not independent geolocation verification. No image geometry/dimension check yet;no model or CCTV reliability score.')
    dump(out/'run.json',r);dump(ROOT/'models/acpds_development_qualification.json',r);dump(ROOT/'reports/acpds_development_latest.json',r)
    registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
    with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
    row=dict(experiment_id=p['run_id'],run_type='Real author-source development annotation qualification;TEST closed',started_at=r['started_at'],finished_at=r['finished_at'],source_ids='SRC-DS-021',split_ids='Author TRAIN/VALID development;whole TEST reserved',configuration=path.relative_to(ROOT).as_posix(),architecture='CRC-bound scoped annotation adapter',random_seed=151,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(r),logs=out.relative_to(ROOT).as_posix(),checkpoints='No model',code_revision_basis='d1b4173 plus sealed qualification implementation',implementation_sha256=digest(__file__),conclusions='Development-only annotation integrity;no pixels/model/final score')
    with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
    statepath=ROOT/'data/automation_state.json';s=read(statepath);assert p['run_id'] not in s['completed_run_ids'];s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['acpds_development_qualification']=r;dump(statepath,s)
    print(json.dumps({k:r[k] for k in ['run_id','duration_seconds','metadata_gate_passed','development','archive_image_names','default_closed_image_names','final_json_deserialized']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
