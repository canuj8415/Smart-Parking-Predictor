"""Copy fixed member bytes,audit development labels;keep final pixels/labels closed."""
import csv,hashlib,json,sys,tarfile,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_validation_jobs'] and not state['active_training_jobs']
    started=datetime.now(timezone.utc);rid='PKLOT-MEMBERS-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    plan_path=ROOT/'data/manifests/pklot_fresh_group_plan_v1.json';plan=read(plan_path);archive=ROOT/plan['archive']
    with (ROOT/plan['inventory_manifest']).open(encoding='utf-8',newline='') as stream:inventory=list(csv.DictReader(stream))
    assert digest(ROOT/plan['inventory_manifest'])==plan['inventory_manifest_sha256']
    frames=[]
    for group in plan['development_groups']:
        choices=sorted([r for r in inventory if r['camera_id']==group['camera_id'] and r['capture_date']==group['date']],key=lambda r:r['image_member'])
        for index in sorted({int(i*(len(choices)-1)/3) for i in range(4)}):
            row=choices[index];frames.append(dict(camera_id=row['camera_id'],date=row['capture_date'],image='data/raw/pklot_fresh_v1/'+row['image_member'],annotation='data/raw/pklot_fresh_v1/'+row['annotation_member'],image_archive_member=row['image_member'],annotation_archive_member=row['annotation_member'],role='development'))
    frames+=plan['frames'];assert len(frames)==18 and sum(f['role']=='development' for f in frames)==12
    known=defaultdict(set)
    for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        if row['source_id']=='SRC-DS-001' and row['local_path'].lower().endswith('.jpg'):
            member=row.get('archive_member') or row['local_path'].removeprefix('data/raw/pklot_subset/')
            known[row['sha256']].add(member.casefold())
    paths=['scripts/qualify_fresh_pklot_members.py','src/smart_parking/layout.py','src/smart_parking/holdouts.py'];hashes={p:digest(ROOT/p) for p in paths}
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=126,source_ids=['SRC-DS-001'],source_hashes=hashes,group_plan_sha256=digest(plan_path),
        hypothesis='Fixed metadata-selected development/final members can be materialized with source lineage and byte-duplicate checks;development annotations have auditable support while final pixels/labels remain closed.',
        selection='4uniform lexical positions per development date;preselected first/last2perfinaldate unchanged',frames=frames,
        gates=['Original archive/plan bindings match','Exact selected JPEG/XML bytes copied unchanged','No cross-identity byte duplicates against existing original-source receipts or selected frames',
            'Development JPEG/geometry/explicit-label support audited','Final JPEG not opened by PIL;final XML not parsed','Existing final group guard reports new groups closed'],
        limitations=['Only byte duplicates;perceptual duplication not ruled out','Known cameras/new dates;18frames total,not full benchmark','Development labels may be missing;unknown is not vacant','No model training/scoring'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        assert digest(archive)==plan['archive_sha256'];wanted={}
        for f in frames:
            for kind in ['image','annotation']:wanted[f[kind+'_archive_member']]=(f,kind)
        copied=set();deadline=time.monotonic()+240
        with tarfile.open(archive,mode='r|gz') as source:
            for member in source:
                if (folder/'CANCEL').exists() or time.monotonic()>deadline:raise InterruptedError('Bounded extraction cancelled/timed out')
                if member.name not in wanted:continue
                f,kind=wanted[member.name];target=(ROOT/f[kind]).resolve();assert target.is_relative_to((ROOT/'data/raw/pklot_fresh_v1').resolve())
                raw=source.extractfile(member).read(10*1024**2+1);assert len(raw)==member.size and len(raw)<=10*1024**2
                checksum=hashlib.sha256(raw).hexdigest();target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():assert digest(target)==checksum
                else:
                    with target.open('xb') as output:output.write(raw)
                f[kind+'_sha256']=checksum;copied.add(member.name)
                if len(copied)==len(wanted):break
        assert copied==set(wanted)
        selected_hashes=defaultdict(set);duplicates=[]
        for f in frames:
            identity=f['image_archive_member'].casefold();checksum=f['image_sha256'];others=known[checksum]-{identity}
            if others:duplicates.append(dict(member=identity,prior_other_members=sorted(others)))
            selected_hashes[checksum].add(identity)
        assert not duplicates and all(len(ids)==1 for ids in selected_hashes.values())
        from PIL import Image
        from smart_parking.layout import read_pklot_xml
        development=[]
        for f in frames:
            if f['role']!='development':continue
            with Image.open(ROOT/f['image']) as image:image.load();size=image.size
            layout=read_pklot_xml(ROOT/f['annotation'],size);assert layout['camera_id']==f['camera_id']
            labels=[s['ground_truth_occupied'] for s in layout['slots']]
            development.append(dict(**f,image_size=size,slots=len(labels),explicit_labels=sum(v is not None for v in labels),unknown_labels=sum(v is None for v in labels)))
        final=[{**f} for f in frames if f['role']!='development']
        manifest=ROOT/'data/manifests/pklot_fresh_final_v2.json';assert not manifest.exists()
        reservation=dict(schema_version=2,source_id='SRC-DS-001',parent_group_plan_sha256=digest(plan_path),frames=final,
            selection='Metadata-only preselected6frames;whole3camera/date groups reserved. Raw bytes copied/hashed;final JPEG pixels and XML labels unopened.',
            pixel_duplicate_audit='Not performed;byte-duplicate audit only',model_evaluation_started=False)
        dump(manifest,reservation);assert_holdout_closed(manifest,root=ROOT)
        dev_path=ROOT/'data/manifests/pklot_fresh_development_v1.json';assert not dev_path.exists();dump(dev_path,dict(frames=development,selection=protocol['selection'],source_group_plan_sha256=digest(plan_path)))
        summary=dict(development_frames=12,development_dates=3,development_slots=sum(f['slots'] for f in development),explicit_development_labels=sum(f['explicit_labels'] for f in development),unknown_development_labels=sum(f['unknown_labels'] for f in development),
            final_frames=6,final_camera_date_groups=3,final_pixels_decoded=0,final_xml_parsed=0,member_files_copied=len(copied),byte_duplicate_collisions=0,
            final_manifest=manifest.relative_to(ROOT).as_posix(),final_manifest_sha256=digest(manifest),development_manifest=dev_path.relative_to(ROOT).as_posix(),development_manifest_sha256=digest(dev_path),
            model_training_or_scoring=False,perceptual_duplicate_audit_performed=False)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,member_qualification_gate_passed=True,summary=summary)
        assert all(digest(ROOT/p)==h for p,h in hashes.items());dump(folder/'run.json',report);dump(ROOT/'models/pklot_fresh_member_qualification.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Fresh licensed selected-member provenance/development-label qualification',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids='SRC-DS-001',split_ids='pklot_fresh_group_plan_v1;final6stillclosed',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Byte-copy/duplicate audit and development annotation support;no model use',epochs=0,batch_size=0,random_seed=126,hardware='CPU;gzip archive plus12development JPEGs',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(summary),logs=folder.relative_to(ROOT).as_posix(),checkpoints='Original model weights unchanged',code_revision_basis='fde889c plus sealed source/CNRrecovery',implementation_sha256=hashes[paths[0]],conclusions='Member/development qualification passed;final pixels/labels unopened;no accuracy claim')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,summary=summary),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));state=read(state_path);raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)
if __name__=='__main__':main()
