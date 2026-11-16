"""Prepare bounded source-bound occupancy crops from accepted TRAIN labels."""
import json,sys,time,hashlib,csv
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.parking_labels import parse_space_polygons
from smart_parking.annotation_quality import occupancy_support
from smart_parking.source_crops import select_source_rows,prepare_occupancy_crop
def read(p):return json.loads((ROOT/p).read_text())
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def main():
    started=datetime.now(timezone.utc);rid='SOURCE-CROPS-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    state=read('data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    audit=read('models/open_space_train_audit.json');usage=read('data/manifests/open_space_usage_qualification_v3.json');assert usage['occupancy_crop_preparation_admitted']
    assert all(digest(ROOT/p)==h for p,h in audit['derived_files'].items())
    frames=read(next(p for p in audit['derived_files'] if p.endswith('frames.json')));accepted=[x for x in frames if x['status']=='accepted_syntax'];assert len(accepted)==517
    paths=['scripts/prepare_source_occupancy_crops.py','src/smart_parking/source_crops.py','src/smart_parking/annotation_quality.py','src/smart_parking/parking_labels.py']
    hashes={p:digest(ROOT/p) for p in paths};protected=read('models/open_space_asset_qualification.json')['protected_hashes']
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=128,source_ids=['SRC-DS-018'],parent_audit=audit['run_id'],parent_card_sha256=digest(ROOT/'models/open_space_train_audit.json'),
        source_hashes=hashes,protected_hashes=protected,maximum_per_frame=32,minimum_native_side=12,minimum_known_fraction=.95,crop_size=96,
        crop_background_rgb=[127,127,127],target_mapping={'source0occupied':1,'source1vacant':0},maximum_seconds=300,
        hypothesis='At most32label-blind uniformly selected polygons per accepted TRAIN frame yield source-bound96x96occupancy crops while excluding tiny/ambiguous crops,retaining every exclusion and preserving model target semantics.',
        scope='Occupancy TRAIN crop preparation only;whole source development-exposed;no model training/scoring/final replay;not background segmentation targets')
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text()) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,phase='bounded occupancy crop preparation')];dump('data/automation_state.json',state)
    cache=ROOT/'outputs/source_occupancy_crops'/rid;cache.mkdir(parents=True,exist_ok=False);records=[];rejected=[];chunks=[];timer=time.monotonic();selected=0
    try:
        for n,frame in enumerate(accepted,1):
            if (folder/'CANCEL').exists() or time.monotonic()-timer>300:raise InterruptedError('Crop preparation cancelled/timed out')
            image_path=ROOT/audit['original_copies']/frame['image'];label_path=ROOT/audit['original_copies']/frame['annotation']
            assert digest(image_path)==frame['source_image_sha256'] and digest(label_path)==frame['source_label_sha256']
            with Image.open(image_path) as source:image=source.convert('RGB')
            labels=parse_space_polygons(label_path.read_text());support,_=occupancy_support(labels,image.size)
            values=[];frame_rows=[]
            for row in select_source_rows(labels,32):
                selected+=1;crop,quality=prepare_occupancy_crop(image,row,support)
                identity=dict(source_id='SRC-DS-018',role='train',camera_id='whole-publisher-collection',image=frame['image'],source_line=row['source_line'],
                    source_class_id=row['class_id'],label=1-row['class_id'],image_sha256=frame['source_image_sha256'],annotation_sha256=frame['source_label_sha256'],
                    source_line_text_sha256=hashlib.sha256(row['source_text'].encode()).hexdigest(),normalized_polygon=row['normalized_polygon'],quality=quality)
                if crop is None:rejected.append(identity);continue
                array=np.asarray(crop,dtype=np.uint8);identity.update(crop_index=len(values),crop_rgb_sha256=hashlib.sha256(array.tobytes()).hexdigest())
                values.append(array);frame_rows.append(identity)
            path=cache/f'frame_{n:03d}.npz';array=np.stack(values) if values else np.empty((0,96,96,3),dtype=np.uint8);np.savez_compressed(path,crops=array)
            for row in frame_rows:row['crop_file']=path.relative_to(ROOT).as_posix()
            records.extend(frame_rows);chunks.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path),rows=len(frame_rows)))
            dump(folder/'progress.json',dict(frames=n,total=517,accepted_crops=len(records),rejected_crops=len(rejected),elapsed_seconds=time.monotonic()-timer))
        assert selected==len(records)+len(rejected) and len(chunks)==517
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**protected}.items())
        manifest=ROOT/'data/processed/source_occupancy_crops'/rid/'manifest.json';dump(manifest,dict(protocol=protocol,records=records,rejected=rejected,chunks=chunks))
        summary=dict(frames=517,selected_polygons=selected,accepted_crops=len(records),excluded_crops=len(rejected),classes=dict(Counter(str(r['label']) for r in records)),
            exclusions=dict(Counter(r['quality']['reason'] for r in rejected)),cache_bytes=sum((ROOT/x['path']).stat().st_size for x in chunks),
            cache_files=517,target_mapping_verified=True,source_validation_or_test_read=False,model_training_or_scoring=False)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,summary=summary,
            manifest=manifest.relative_to(ROOT).as_posix(),manifest_sha256=digest(manifest),crop_gate_passed=len(records)>0)
        dump(folder/'run.json',report);dump('models/source_occupancy_crop_preparation.json',report)
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Bounded source TRAIN occupancy crop preparation;no model score',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids='SRC-DS-018',
            split_ids='Accepted publisherTRAIN only;whole source development-exposed',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Unknown-aware polygon crop96x96',random_seed=128,
            hardware='CPU',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(summary),logs=folder.relative_to(ROOT).as_posix(),
            code_revision_basis='8ae82a3 plus sealed source snapshots',implementation_sha256=hashes[paths[0]],conclusions='Crops prepared with exclusions/target inversion;no model training or independent accuracy')
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read('data/automation_state.json');state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,summary=summary),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False,crop_chunks_preserved=True));state=read('data/automation_state.json');raise
    finally:state['active_validation_jobs']=[];dump('data/automation_state.json',state)
if __name__=='__main__':main()
