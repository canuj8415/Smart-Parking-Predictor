"""Seal broader development dates, validate originals and replay a frozen model.

Only selected training/development images and XML are decoded. Protected image
bytes may be hashed for duplicate screening; final annotations remain unopened.
"""
import csv,json,os,sys,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from torchvision.models import resnet18
from torchvision.transforms import functional as TF
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.region_data import select_broader_development,CAMERAS
from smart_parking.region_transfer import FrozenRegionEncoder,RegionDecoder
from smart_parking.region_evaluation import project_logits
from smart_parking.layout import read_pklot_xml,union_mask
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.provenance import digest

def metric(prediction,truth):
    p=np.asarray(prediction,dtype=bool);y=np.asarray(truth,dtype=bool);intersection=int((p&y).sum());union=int((p|y).sum())
    return dict(pixel_iou=intersection/union if union else 1.,dice=2*intersection/(int(p.sum())+int(y.sum())) if int(p.sum())+int(y.sum()) else 1.)

def main():
    lock=ROOT/'.cache/broader_region_audit.lock';lock.parent.mkdir(exist_ok=True)
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:audit()
    finally:lock.unlink(missing_ok=True)

def audit():
    torch.set_num_threads(4);started=datetime.now(timezone.utc);clock=time.perf_counter()
    run='REGION-DATA-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state.get('active_training_jobs') or state.get('active_validation_jobs'):raise ValueError('Another experiment is active')
    manifest=ROOT/'data/manifests/region_broader_development_v1.json'
    if manifest.exists():raise FileExistsError('Broader dates already reserved; do not silently select/reuse them')
    shared=ROOT/'data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json'
    finals=assert_holdout_closed(shared);boundaries={r['camera_id']:r['date'] for r in finals}
    known_path=ROOT/'data/manifests/segmentation_known_camera_v1.json';known=json.loads(known_path.read_text())
    original_path=ROOT/'data/manifests/pklot_frames.csv'
    with original_path.open(newline='',encoding='utf-8') as stream:original=list(csv.DictReader(stream))
    excluded=set(known['excluded_previously_used_dates'])|{r['date'] for r in original+known['frames']+finals}
    excluded.update(json.loads((ROOT/'models/segmentation_model_card.json').read_text())['final_test_dates'])
    acquisition=ROOT/'data/raw/pklot_subset/acquisition.json';pairs=json.loads(acquisition.read_text())['pairs']
    selected=select_broader_development(pairs,excluded,boundaries)
    rows=selected['frames'];train=[r for r in rows if r['split']=='train'];validation=[r for r in rows if r['split']=='validation']
    frozen_folder=ROOT/'experiments/results/REGION-TRANSFER-20261024T214740232123Z';frozen=json.loads((frozen_folder/'run.json').read_text())
    checkpoint=frozen_folder/'candidate.pt';assert digest(checkpoint)==frozen['checkpoint_sha256']
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-DS-001',pretrained_source_id='SRC-MOD-003',seed='Deterministic metadata selection; no randomized training',
        hypothesis='Broader unused dates and daytime samples expose within-camera variation missed by six repeatedly used development frames',
        scope='Known-camera broader development only, not a new final test; no new weights trained or promoted',
        selection='8uniformly spaced unused dates/camera with>=4indexed pairs; first6train/last2validation; up to8train/4validation chronological samples/date',
        excluded_dates=sorted(excluded),dates=selected['dates'],final_boundaries=boundaries,shared_final_manifest=str(shared.relative_to(ROOT)),shared_final_manifest_sha256=digest(shared),
        source_index_sha256=digest(acquisition),original_manifest_sha256=digest(original_path),known_manifest_sha256=digest(known_path),
        frames_by_split=dict(Counter(r['split'] for r in rows)),frozen_candidate=frozen['run_id'],frozen_checkpoint_sha256=digest(checkpoint),
        evaluation_grid=[192,112],input_size=[384,224],threshold=.5,
        gates='Data: valid dimensions/XML/polygons/camera, nonempty masks, global date/path/hash separation, no protected duplicate. Frozen replay is descriptive; no new selection/promotion gate.',
        limitations=['Same three known cameras, convenience subset','Only2newvalidationdates/camera; no unseen-camera claim','Exact hash checks do not establish perceptual uniqueness','Slot union masks do not provide vehicle masks or individual slot predictions'])
    source_paths=['scripts/audit_broader_regions.py','src/smart_parking/region_data.py','src/smart_parking/region_transfer.py','src/smart_parking/region_evaluation.py','src/smart_parking/layout.py']
    protocol['code_sha256']={p:digest(ROOT/p) for p in source_paths}
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    (folder/'implementation_sources.json').write_text(json.dumps({p:dict(sha256=digest(ROOT/p),source=(ROOT/p).read_text(encoding='utf-8')) for p in source_paths},indent=2),encoding='utf-8')
    # Exclusive manifest reservation precedes ANY selected image/XML decoding.
    reservation=dict(run_id=run,created_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-001',policy=protocol['selection'],
        excluded_dates=sorted(excluded),dates=selected['dates'],shared_final_manifest=protocol['shared_final_manifest'],shared_final_manifest_sha256=digest(shared),frames=rows)
    with manifest.open('x',encoding='utf-8') as stream:json.dump(reservation,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    state['active_validation_jobs']=[dict(run_id=run,pid=os.getpid(),kind='bounded selected-development data audit and frozen-model replay')]
    state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    try:
        selected_hashes={r['image']:digest(ROOT/r['image']) for r in rows}
        if len(set(selected_hashes.values()))!=len(rows):raise ValueError('Selected source bytes duplicate')
        hashes_by_split={split:{selected_hashes[r['image']] for r in rows if r['split']==split} for split in ['train','validation']}
        assert not hashes_by_split['train']&hashes_by_split['validation']
        protected_hashes=set();protected_count=0
        for pair in pairs:
            if pair['date'] in excluded:
                protected_hashes.add(digest(ROOT/pair['image']));protected_count+=1
        if set(selected_hashes.values())&protected_hashes:raise ValueError('Selected bytes duplicate a protected/previously used date')
        decoded=[];mask_lookup={};slot_counts=Counter();weather=Counter();geometries=defaultdict(set)
        rgb=[]
        for row in rows:
            with Image.open(ROOT/row['image']) as image:
                image.load();layout=read_pklot_xml(ROOT/row['annotation'],image.size)
                if layout['camera_id']!=row['camera_id']:raise ValueError('XML camera does not match manifest')
                mask=np.asarray(union_mask(layout,(192,112)))>0
                if not mask.any() or mask.all():raise ValueError('Degenerate parking-region mask')
                if row['split']=='validation':rgb.append(TF.to_tensor(image.convert('RGB').resize((384,224),Image.Resampling.BILINEAR)))
                dimensions=list(image.size)
            mask_lookup[row['image']]=mask;slot_counts[row['split']]+=len(layout['slots']);weather[(row['split'],Path(row['image']).parts[5])]+=1
            signature=tuple((s['id'],tuple(tuple(p) for p in s['polygon'])) for s in layout['slots']);geometries[row['camera_id']].add(signature)
            decoded.append(dict(**row,image_sha256=selected_hashes[row['image']],annotation_sha256=digest(ROOT/row['annotation']),image_size=dimensions,slots=len(layout['slots']),mask_foreground_fraction=float(mask.mean())))
        backbone=resnet18(weights=None);backbone.load_state_dict(torch.load(ROOT/'models/pretrained/resnet18_imagenet.pth',map_location='cpu',weights_only=True));encoder=FrozenRegionEncoder(backbone)
        decoder=RegionDecoder();decoder.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['decoder_state_dict']);decoder.eval()
        mean=torch.tensor([.485,.456,.406])[None,:,None,None];std=torch.tensor([.229,.224,.225])[None,:,None,None]
        prediction=[]
        with torch.inference_mode():
            for batch in torch.stack(rgb).split(4):prediction.extend((project_logits(decoder(batch,encoder((batch-mean)/std))).sigmoid()>=.5).numpy()[:,0])
        prediction=np.stack(prediction);truth=np.stack([mask_lookup[r['image']] for r in validation])
        majority={c:np.stack([mask_lookup[r['image']] for r in train if r['camera_id']==c]).mean(0)>=.5 for c in sorted(CAMERAS.values())}
        geometry=np.stack([majority[r['camera_id']] for r in validation])
        results={}
        for name,indices in [('overall',list(range(len(validation))))]+[(c,[i for i,r in enumerate(validation) if r['camera_id']==c]) for c in sorted(CAMERAS.values())]:
            results[name]=dict(frames=len(indices),frozen_candidate=metric(prediction[indices],truth[indices]),train_geometry=metric(geometry[indices],truth[indices]))
        for i in range(len(validation)):
            for label,array in [('candidate',prediction),('truth',truth),('geometry',geometry)]:Image.fromarray((array[i]*255).astype('uint8')).save(folder/f'validation_{label}_{i:02}.png')
        (folder/'validated_frames.json').write_text(json.dumps(decoded,indent=2),encoding='utf-8')
        (folder/'metadata_rejections.json').write_text(json.dumps(selected['rejected_metadata'],indent=2),encoding='utf-8')
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            development_manifest=str(manifest.relative_to(ROOT)),development_manifest_sha256=digest(manifest),selected_source_hashes=selected_hashes,
            decoded_training_frames=len(train),decoded_validation_frames=len(validation),decoded_final_images=0,decoded_final_annotations=0,
            protected_image_bytes_hashed_only=protected_count,duplicate_selected_or_protected_hashes=0,slot_annotations_by_split=dict(slot_counts),
            weather_counts={f'{a}/{b}':n for (a,b),n in weather.items()},geometry_variants_by_camera={c:len(v) for c,v in geometries.items()},
            data_gate_passed=True,frozen_replay=results,model_training_performed=False,production_changed=False)
        (folder/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        assert digest(shared)==protocol['shared_final_manifest_sha256'];assert_holdout_closed(shared)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run
        print(json.dumps({k:report[k] for k in ['run_id','duration_seconds','frames_by_split','geometry_variants_by_camera','frozen_replay','decoded_final_images']},indent=2),flush=True)
    except BaseException as error:
        (folder/'failure.json').write_text(json.dumps(dict(error=str(error),manifest_kept_sealed=True,completed_run_counted=False),indent=2),encoding='utf-8');state=json.loads(state_path.read_text());raise
    finally:
        state['active_validation_jobs']=[];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')

if __name__=='__main__':main()
