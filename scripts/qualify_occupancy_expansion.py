"""Materialize a bounded training expansion without reading any final images."""
import csv
import hashlib
import json
import sys
import tarfile
import time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.occupancy_expansion import member_name,select_frames


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    state_path=ROOT/'data/automation_state.json';state=read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    started=datetime.now(timezone.utc);rid='OCCUPANCY-EXPANSION-DATA-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    plan=read('data/manifests/pklot_fresh_group_plan_v1.json')
    with (ROOT/plan['inventory_manifest']).open(encoding='utf-8',newline='') as stream:
        inventory=list(csv.DictReader(stream))
    assert digest(ROOT/plan['inventory_manifest'])==plan['inventory_manifest_sha256']
    with (ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8-sig',newline='') as stream:
        original=list(csv.DictReader(stream))
    claims=[read(p) for p in (ROOT/'data/holdout_claims').glob('*.claim.json')]
    selection=select_frames(inventory,original,read('data/manifests/region_broader_development_v1.json'),
        read('data/manifests/pklot_fresh_development_v1.json'),plan,claims,per_group=4)
    frames=selection['frames']
    assert Counter(f['role'] for f in frames)==dict(train=170,validation=45)
    assert len(selection['training_global_dates'])==32
    final=ROOT/'data/manifests/pklot_fresh_final_v2.json';assert_holdout_closed(final,root=ROOT)
    paths=['scripts/qualify_occupancy_expansion.py','src/smart_parking/occupancy_expansion.py','src/smart_parking/layout.py']
    inputs=['data/manifests/pklot_frames.csv','data/manifests/region_broader_development_v1.json',
        'data/manifests/pklot_fresh_development_v1.json','data/manifests/pklot_fresh_group_plan_v1.json',
        'data/manifests/pklot_fresh_final_v2.json']
    hashes={p:digest(ROOT/p) for p in paths};input_hashes={p:digest(ROOT/p) for p in inputs}
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=129,source_ids=['SRC-DS-001'],source_hashes=hashes,
        input_hashes=input_hashes,inventory_sha256=plan['inventory_manifest_sha256'],archive_sha256=plan['archive_sha256'],
        hypothesis='Previously designated training dates can supply third-camera occupancy examples while all development/final date roles remain isolated.',
        selection=selection,limits=dict(frames=215,member_bytes_max=10*1024**2,wall_seconds=360),
        gates=['Canonical inventory/source binding and all protected global dates excluded',
            '170train and45validation frames selected solely by prior roles/metadata',
            'No encoded-byte duplicate across training/development/final dates',
            'Original labels only; unknown labels excluded and counted, never vacant',
            'No final JPEG decode/XML parse; original model files unchanged'],
        limitations=['Known cameras only; training/date roles inherited from earlier experiments',
            'Multiple photos/slots are correlated; not215independent scenes',
            'Encoded duplicates audited, not perceptual/near duplicates',
            'This is data qualification, no model training or accuracy'])
    dump(folder/'protocol.json',protocol)
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    weights=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    state['active_validation_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'),deadline_seconds=360)]
    dump(state_path,state);timer=time.perf_counter()
    try:
        archive=ROOT/plan['archive'];assert digest(archive)==protocol['archive_sha256']
        wanted={}
        for f in frames:
            for kind in ['image','annotation']:wanted[f[kind+'_archive_member']]=(f,kind)
        copied=set()
        with tarfile.open(archive,mode='r|gz') as source:
            for member in source:
                if (folder/'CANCEL').exists() or time.perf_counter()-timer>360:
                    raise InterruptedError('Expansion qualification cancellation/deadline')
                if member.name not in wanted:continue
                assert member.isfile() and member_name(member.name)==member.name
                f,kind=wanted[member.name]
                raw=source.extractfile(member).read(10*1024**2+1)
                assert len(raw)==member.size==f['expected_'+kind+'_bytes'] and len(raw)<=10*1024**2
                destination=(ROOT/f[kind]).resolve()
                assert destination.is_relative_to((ROOT/'data/raw/pklot_occupancy_expansion_v1').resolve())
                checksum=hashlib.sha256(raw).hexdigest();destination.parent.mkdir(parents=True,exist_ok=True)
                copied_at=datetime.now(timezone.utc).isoformat()
                if destination.exists():assert digest(destination)==checksum
                else:
                    with destination.open('xb') as stream:stream.write(raw)
                f[kind+'_sha256']=checksum
                receipt('SRC-DS-001',destination,'https://www.inf.ufpr.br/lesoliveira/download/PKLot.tar.gz',
                    'Training/development-only local archive member copy; no network acquisition',
                    acquisition_kind='local_archive_member_copy',archive_member=member.name,
                    parent_archive=plan['archive'],parent_archive_sha256=protocol['archive_sha256'],
                    qualification_run=rid,role=f['role'],copy_event_start=copied_at,
                    copy_event_finished=datetime.now(timezone.utc).isoformat())
                copied.add(member.name)
                if len(copied)%40==0:
                    dump(folder/'progress.json',dict(phase='copying_selected_source_bytes',members_copied=len(copied)))
                if len(copied)==len(wanted):break
        assert copied==set(wanted)
        meta={r['image_member']:r for r in inventory}
        prohibited=set(selection['protected_global_dates'])|set(selection['validation_global_dates'])
        known=defaultdict(set)
        for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines():
            record=json.loads(line)
            if record['source_id']!='SRC-DS-001' or not record['local_path'].lower().endswith('.jpg'):continue
            try:identity=member_name(record.get('archive_member') or record['local_path'])
            except ValueError:continue
            if identity in meta:known[record['sha256']].add(meta[identity]['capture_date'])
        encoded=defaultdict(set)
        for f in frames:
            if f['role']=='train':
                assert not known[f['image_sha256']]&prohibited,'Training hash aliases a development/final date'
            encoded[f['image_sha256']].add(f['date'])
        assert all(len(days)==1 for days in encoded.values()),'Selected cross-date byte duplicate'
        from PIL import Image
        from smart_parking.layout import read_pklot_xml
        coverage=[]
        for n,f in enumerate(frames,1):
            if (folder/'CANCEL').exists() or time.perf_counter()-timer>360:
                raise InterruptedError('Expansion annotation cancellation/deadline')
            with Image.open(ROOT/f['image']) as source:
                source.load();size=source.size
            layout=read_pklot_xml(ROOT/f['annotation'],size)
            assert layout['camera_id']==f['camera_id']
            labels=[s['ground_truth_occupied'] for s in layout['slots']]
            f.update(image_size=list(size),slots=len(labels),explicit_labels=sum(v is not None for v in labels),
                unknown_labels=sum(v is None for v in labels),vacant_labels=sum(v==0 for v in labels),occupied_labels=sum(v==1 for v in labels))
            coverage.append({k:f[k] for k in ['camera_id','date','role','explicit_labels','unknown_labels','vacant_labels','occupied_labels']})
            if n%20==0:dump(folder/'progress.json',dict(phase='auditing_training_development_labels',frames_checked=n))
        grouped=defaultdict(Counter)
        for f in frames:
            g=grouped[(f['role'],f['camera_id'])];g['frames']+=1
            for k in ['slots','explicit_labels','unknown_labels','vacant_labels','occupied_labels']:g[k]+=f[k]
        counts=[dict(role=role,camera_id=camera,**values) for (role,camera),values in sorted(grouped.items())]
        assert all(sum(f['explicit_labels'] for f in frames if f['role']==role)>0 for role in ['train','validation'])
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        assert all(digest(ROOT/p)==h for p,h in input_hashes.items())
        assert all(digest(ROOT/p)==h for p,h in weights.items())
        assert_holdout_closed(final,root=ROOT)
        manifest=ROOT/'data/manifests/occupancy_expansion_v1.json';assert not manifest.exists()
        dump(manifest,dict(schema_version=1,source_id='SRC-DS-001',qualification_run=rid,
            **selection,label_coverage=counts,protected_final_pixels_or_labels_read=0,
            unknown_label_policy='Exclude unknowns from loss and accuracy; preserve/count them in all inventories',
            byte_duplicate_scope='No cross-date selected byte aliases and no training-byte alias of receipt-known protected/development date; no perceptual audit'))
        outcome=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-timer,
            data_qualification_gate_passed=True,manifest=manifest.relative_to(ROOT).as_posix(),manifest_sha256=digest(manifest),
            summary=dict(train_frames=170,validation_frames=45,train_dates=32,validation_dates=len(selection['validation_global_dates']),
                member_files_copied=len(copied),network_bytes=0,label_coverage=counts,final_pixels_or_labels_read=0,
                original_model_files_unchanged=True,model_training_or_scoring=False))
        dump(folder/'run.json',outcome);dump(ROOT/'models/occupancy_expansion_data_card.json',outcome)
        dump(folder/'label_coverage.json',coverage)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Training expansion source/split/label qualification',started_at=started.isoformat(),
            finished_at=outcome['finished_at'],source_ids='SRC-DS-001',split_ids='occupancy_expansion_v1; final6closed',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Source byte and grouped label audit; no model use',
            epochs=0,random_seed=129,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=outcome['duration_seconds'],
            evaluation_metrics=json.dumps(outcome['summary']),logs=folder.relative_to(ROOT).as_posix(),checkpoints='Original weights unchanged',
            code_revision_basis='e1c6461 plus frozen expansion qualification sources',implementation_sha256=hashes[paths[0]],
            conclusions='Training/development roles kept; unknown labels explicit; no final use or accuracy')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,summary=outcome['summary']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False))
        state=read(state_path);raise
    finally:
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
