"""Bounded TRAIN/DEV bay-footprint dataset; full opaque-JPEG alias barrier first.

All archive JPEG bytes may be hashed, but only admitted selected TRAIN/DEV images
and XML are decoded. Closed/quarantined labels and pixels are never opened.
"""
import argparse,csv,hashlib,json,os,sys,tarfile,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
from smart_parking.region_dataset_admission import group_key,select_frames,qualify_hashes
from smart_parking.pklot_group_ledger import member_identity

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);temporary=p.with_suffix(p.suffix+'.partial');temporary.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');os.replace(temporary,p)

def prepare():
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];now=datetime.now(timezone.utc);rid='REGION-DATA-V2-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    index=ROOT/'data/splits/pklot-archive-inventory-v1/pairs.csv';ledger=ROOT/'models/pklot_current_role_ledger.json';groups=read(ledger)['current_ledger']['groups']
    with index.open(encoding='utf-8-sig',newline='') as stream:pairs=list(csv.DictReader(stream))
    selected=select_frames(pairs,groups);assert len(selected)<=230 and {f['role'] for f in selected}=={'train','development'}
    code=['scripts/prepare_region_dataset_v2.py','src/smart_parking/region_dataset_admission.py','tests/test_region_dataset_admission.py','src/smart_parking/layout.py','src/smart_parking/pklot_group_ledger.py'];inputs=[index,ledger,*sorted((ROOT/'data/holdout_claims').glob('*.claim.json'))]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=168,source_ids=['SRC-DS-001'],hypothesis='Existing admitted TRAIN/DEV date groups can supply a bounded,source-labelled image-only bay-footprint segmentation study after whole-archive opaque-byte alias qualification.',
        scope='Data qualification only,not model training/accuracy. Existing source cameras/date roles,not unseen final. Target is union of provided bay polygons,not exhaustive whole parking facility or individual slot identities.',
        archive='data/raw/pklot_subset/PKLot.tar.gz',archive_sha256='df182f46184fc29fb7ef3cd293b49cae52599365d9fe9415c4e7e7ea7ded9f79',index=index.relative_to(ROOT).as_posix(),ledger=ledger.relative_to(ROOT).as_posix(),selected=selected,
        roles={group_key(g['camera_id'],g['capture_date']):g['status'] for g in groups},sampling='Seed168 sample4TRAIN/2DEV photos per already admitted date;no replacement after qualification failures',input_size=[256,144],rgb_resize='PIL bilinear',mask_resize='Original source polygon union,nearest-neighbor',
        gates=dict(min_train_images=100,min_development_images=15,min_train_per_camera=20,min_development_per_camera=2,foreground_fraction_min=.005,foreground_fraction_max=.95),
        source_hashes={f:digest(ROOT/f) for f in code},input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T050911Z/checks.json')['frozen_hashes_unchanged'],
        maximum_seconds=900,phases='Opaque JPEG hashes/group-alias barrier,admitted XML acquisition,cancellable per-frame RGB/mask cache',normalization_not_fitted=True,occupancy_labels_used_for_training=False)
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json')

def run(path):
    import numpy as np
    from PIL import Image,ImageDraw
    from smart_parking.layout import read_pklot_xml,union_mask
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256'] and not(out/'run.json').exists()
    for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    assert digest(ROOT/p['archive'])==p['archive_sha256']
    sp=ROOT/'data/automation_state.json';s=read(sp);assert not s['active_training_jobs'] and not s['active_validation_jobs'];s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),maximum_seconds=900,resume_command='scripts/prepare_region_dataset_v2.py --run '+path.relative_to(ROOT).as_posix())];dump(sp,s);started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
    raw=ROOT/'data/raw/pklot_region_v2'/p['run_id'];cache=ROOT/'data/processed/pklot_region_v2'/p['run_id'];assert raw.resolve().is_relative_to(ROOT/'data/raw/pklot_region_v2') and cache.resolve().is_relative_to(ROOT/'data/processed/pklot_region_v2');raw.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    allowed=set();forbidden=[]
    def audit(event,args):
        if event.startswith('socket.'):
            forbidden.append(dict(event=event));raise PermissionError('Dataset qualification is offline')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            target=Path(os.fsdecode(args[0])).resolve()
            if target.suffix.casefold() in {'.jpg','.jpeg','.xml','.png'} and target not in allowed and not target.is_relative_to(out):
                forbidden.append(dict(event=event,path=str(target)));raise PermissionError('Unqualified image/XML file access blocked')
    sys.addaudithook(audit)
    def boundary():
        if (out/'CANCEL').exists() or time.perf_counter()-clock>900:raise InterruptedError('Dataset invocation cancelled/deadline;phase/frame artifacts retained')
    def materialize(member,source,target,role):
        data=source.extractfile(member).read(member.size+1);assert len(data)==member.size
        sha=hashlib.sha256(data).hexdigest()
        if target.exists():assert digest(target)==sha
        else:
            with target.open('xb') as stream:stream.write(data)
        return sha
    try:
        with (ROOT/p['index']).open(encoding='utf-8-sig',newline='') as stream:pairs=list(csv.DictReader(stream))
        indexed={r['image_member'].casefold():r for r in pairs};wanted={r['image_member'].casefold():r for r in p['selected']};hash_complete=out/'hash_phase_complete.json'
        if hash_complete.exists():
            marker=read(hash_complete);assert marker['protocol_sha256']==digest(path) and digest(out/marker['table'])==marker['table_sha256']
            with (out/marker['table']).open(encoding='utf-8',newline='') as stream:hashes=list(csv.DictReader(stream))
        else:
            table=out/('jpeg_hashes_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.csv');hashes=[]
            with table.open('x',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=['member','group_id','sha256','bytes','indexed']);writer.writeheader()
                with tarfile.open(ROOT/p['archive'],mode='r|gz') as archive:
                    for member in archive:
                        boundary()
                        if not member.isfile() or Path(member.name).suffix.casefold()!='.jpg':continue
                        if not 0<member.size<=10*1024**2:raise ValueError('Unexpected JPEG member size')
                        key=member.name.casefold();hasher=hashlib.sha256();source=archive.extractfile(member);data=source.read(member.size+1);assert len(data)==member.size;hasher.update(data)
                        pair=indexed.get(key)
                        if pair:assert int(pair['image_bytes'])==member.size;g=group_key(pair['camera_id'],pair['capture_date'])
                        else:g='unindexed:'+key
                        record=dict(member=member.name,group_id=g,sha256=hasher.hexdigest(),bytes=member.size,indexed=bool(pair));writer.writerow(record);hashes.append(record)
                        if key in wanted:
                            target=raw/f'frame_{wanted[key]["index"]:03}.jpg.pending'
                            if target.exists():assert digest(target)==record['sha256']
                            else:
                                with target.open('xb') as output:output.write(data)
                        if len(hashes)%1000==0:dump(out/'progress.json',dict(phase='opaque_jpeg_hashes',jpeg_members=len(hashes),pixels_decoded=0,XML_parsed=0))
            assert sum(r['member'].casefold() in indexed for r in hashes)==12218
            dump(hash_complete,dict(protocol_sha256=digest(path),table=table.name,table_sha256=digest(table),jpeg_members=len(hashes),pixels_decoded=0,XML_parsed=0))
        qualified=qualify_hashes(hashes,p['selected'],p['roles']);dump(out/'byte_qualification.json',qualified);frames=qualified['accepted'];assert frames
        allowed.update((raw/f'frame_{f["index"]:03}{extension}').resolve() for f in frames for extension in ['.jpg','.xml'])
        xml_marker=out/'xml_acquisition_complete.json'
        if not xml_marker.exists():
            xmlwanted={f['annotation_member'].casefold():f for f in frames};seen=set()
            with tarfile.open(ROOT/p['archive'],mode='r|gz') as archive:
                for member in archive:
                    boundary();key=member.name.casefold()
                    if key not in xmlwanted:continue
                    assert member.isfile() and 0<member.size<=10*1024**2;f=xmlwanted[key];assert int(f['annotation_bytes'])==member.size;target=raw/f'frame_{f["index"]:03}.xml';materialize(member,archive,target,f['role']);seen.add(key)
            assert seen==set(xmlwanted);dump(xml_marker,dict(protocol_sha256=digest(path),files={f'frame_{f["index"]:03}.xml':digest(raw/f'frame_{f["index"]:03}.xml') for f in frames},closed_or_unknown_XML_acquired=0))
        else:
            marker=read(xml_marker);assert marker['protocol_sha256']==digest(path)
            for f,h in marker['files'].items():assert digest(raw/f)==h
        records=[];errors=[];previews={camera for camera in ['pucpr','ufpr04','ufpr05'] if (out/f'qualification_{camera}.png').exists()};url='https://www.inf.ufpr.br/lesoliveira/download/PKLot.tar.gz'
        for f in frames:
            boundary();n=f['index'];journal=out/f'completed_frame_{n:03}.json'
            if journal.exists():
                record=read(journal)
                for key,sha in [('cache','cache_sha256'),('image','image_sha256'),('annotation','annotation_sha256')]:assert digest(ROOT/record[key])==record[sha]
                records.append(record);continue
            pending=raw/f'frame_{n:03}.jpg.pending';image_path=raw/f'frame_{n:03}.jpg';xml=raw/f'frame_{n:03}.xml'
            if not image_path.exists():
                assert pending.resolve().is_relative_to(raw.resolve()) and image_path.resolve().is_relative_to(raw.resolve())
                assert digest(pending)==f['image_sha256'];os.rename(pending,image_path)
            assert digest(image_path)==f['image_sha256']
            try:
                with Image.open(image_path) as source:image=source.convert('RGB');size=image.size;orientation=source.getexif().get(274,1)
                layout=read_pklot_xml(xml,size);mask=union_mask(layout,tuple(p['input_size']));rgb=np.asarray(image.resize(tuple(p['input_size']),Image.Resampling.BILINEAR));target=np.asarray(mask)>0;fraction=float(target.mean())
                assert p['gates']['foreground_fraction_min']<=fraction<=p['gates']['foreground_fraction_max'],'Degenerate provided bay-union target'
                file=cache/f'frame_{n:03}.npz'
                if file.exists():file=cache/('frame_'+str(n)+'_resume_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.npz')
                np.savez_compressed(file,rgb=rgb,mask=target)
                with np.load(file,allow_pickle=False) as saved:assert np.array_equal(saved['rgb'],rgb) and np.array_equal(saved['mask'],target)
                record=dict(index=n,camera_id=f['camera_id'],capture_date=f['capture_date'],role=f['role'],group_id=f['group_id'],image=image_path.relative_to(ROOT).as_posix(),image_sha256=digest(image_path),annotation=xml.relative_to(ROOT).as_posix(),annotation_sha256=digest(xml),image_archive_member=f['image_member'],annotation_archive_member=f['annotation_member'],original_size=list(size),exif_orientation=orientation,resize_size=p['input_size'],slots=len(layout['slots']),foreground_fraction=fraction,cache=file.relative_to(ROOT).as_posix(),cache_sha256=digest(file))
                for source_file,member in [(image_path,f['image_member']),(xml,f['annotation_member'])]:receipt('SRC-DS-001',source_file,url,'Qualified local TRAIN/DEV bay-footprint member;not fresh final',archive_sha256=p['archive_sha256'],archive_member=member,role=f['role'],group_id=f['group_id'],ledger_sha256=p['input_hashes'][p['ledger']])
                dump(journal,record);records.append(record)
                if f['role']=='train' and f['camera_id'] not in previews:
                    small=Image.fromarray(rgb);color=Image.new('RGB',small.size,'#23cfa7');small=Image.blend(small,Image.composite(color,small,Image.fromarray((target*100).astype('uint8'))),.55);png=out/f'qualification_{f["camera_id"]}.png';small.resize((768,432)).save(png);dump(out/f'qualification_{f["camera_id"]}.json',dict(record=record,preview_sha256=digest(png),selection='First admitted TRAIN frame per camera;not a random representative accuracy sample'));previews.add(f['camera_id'])
            except (ValueError,AssertionError,OSError) as error:errors.append(dict(index=n,image_member=f['image_member'],error=str(error)))
            dump(out/'progress.json',dict(phase='selected_RGB_mask_cache',completed=len(records),rejected=len(errors),total=len(frames)))
        counts=Counter(r['role'] for r in records);bycamera={role:dict(Counter(r['camera_id'] for r in records if r['role']==role)) for role in ['train','development']};g=p['gates']
        checks=dict(no_cache_errors=not errors,train_size=counts['train']>=g['min_train_images'],development_size=counts['development']>=g['min_development_images'],all_cameras=all(set(bycamera[role])=={'pucpr','ufpr04','ufpr05'} for role in bycamera),train_camera_min=min(bycamera['train'].values(),default=0)>=g['min_train_per_camera'],development_camera_min=min(bycamera['development'].values(),default=0)>=g['min_development_per_camera'])
        assert not forbidden;normal_forbidden=list(forbidden)
        try:(ROOT/'data/raw/NEVER_OPEN_UNQUALIFIED_IMAGE.jpg').read_bytes()
        except PermissionError:negative_control=True
        else:raise AssertionError('Unqualified image-read guard did not reject probe')
        for f,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        manifest=cache/'manifest.json';dump(manifest,dict(run_id=p['run_id'],protocol_sha256=digest(path),target='Union of source-annotated bay polygons;not exhaustive facility/background class',roles=bycamera,records=records,byte_qualification_sha256=digest(out/'byte_qualification.json'),gates=checks,data_gate_passed=all(checks.values()),new_groups_admitted=False,final_pixels_or_XML_parsed=0,protected_JPEG_use='Opaque SHA256 only;no protected image decode'))
        r=dict(run_id=p['run_id'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.perf_counter()-clock,seed=168,protocol_sha256=digest(path),selected_before_qualification=len(p['selected']),qualified_after_byte_barrier=len(frames),cached_images=len(records),role_counts=dict(counts),by_camera=bycamera,byte_alias_rejections=len(qualified['rejected']),archive_JPEGs_hashed=qualified['jpeg_records'],cross_group_hash_edges=qualified['cross_group_hash_edges'],cache_errors=errors,checks=checks,data_gate_passed=all(checks.values()),manifest=manifest.relative_to(ROOT).as_posix(),manifest_sha256=digest(manifest),neural_model_calls=0,models_trained=0,closed_or_quarantined_image_decodes=0,closed_or_quarantined_XML_parsed=0,new_groups_admitted=0,normal_forbidden_accesses=normal_forbidden,unqualified_image_negative_control_blocked=negative_control,scope=p['scope'])
        dump(out/'run.json',r);dump(ROOT/'models/region_dataset_v2.json',r);dump(ROOT/'reports/region_dataset_v2_latest.json',r);reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='TRAIN/DEV region-data qualification with whole-archive opaque JPEG alias barrier',started_at=started,finished_at=r['finished_at'],source_ids='SRC-DS-001',split_ids='Existing50TRAIN/15DEVgroups only;17consumed+16quarantine excluded',configuration=path.relative_to(ROOT).as_posix(),architecture='Source polygon union masks/RGB256x144/byte-level component qualification',random_seed=168,hardware='CPU/bounded streaming archive and frame caches',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(r),logs=out.relative_to(ROOT).as_posix(),checkpoints='No model changes',code_revision_basis='f17d807 plus sealed region-data admission sources',implementation_sha256=digest(__file__),conclusions='Data gate='+str(r['data_gate_passed'])+';not model/final accuracy')
        with reg.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(sp);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['region_dataset_v2']=r;dump(sp,s);print(json.dumps(r,indent=2))
    except BaseException as error:dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:s=read(sp);s['active_validation_jobs']=[];dump(sp,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
