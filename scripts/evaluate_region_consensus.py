"""Fit unanimous geometry on training only, then test fixed known-camera composition."""
import argparse,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.region_consensus import fit_consensus,prior_summary
from smart_parking.region_consensus_model import ConsensusRegionModel
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.checkpointing import save_checkpoint_atomic
from train_region_transfer import masks_at_grid,scores
REFERENCE='REGION-TRANSFER-20261025T004539209450Z'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main(policy='unanimous_pixels'):
    if policy not in {'unanimous_pixels','stable_camera_only'}:raise ValueError('Unknown routing policy')
    torch.set_num_threads(4);torch.manual_seed(101)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another recorded job is active')
    manifest=ROOT/'data/manifests/region_broader_development_v1.json';metadata=json.loads(manifest.read_text())['frames']
    train=[r for r in metadata if r['split']=='train'];val=[r for r in metadata if r['split']=='validation']
    holdout=ROOT/'data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json';final=assert_holdout_closed(holdout)
    assert not {r['image'] for r in final}&{r['image'] for r in train+val}
    reference_path=ROOT/'experiments/results'/REFERENCE;reference=json.loads((reference_path/'run.json').read_text());encoder=ROOT/'models/pretrained/resnet18_imagenet.pth'
    assert digest(reference_path/'candidate.pt')==reference['checkpoint_sha256'] and digest(encoder)==reference['encoder_weights_sha256']
    started=datetime.now(timezone.utc);run=('REGION-STABILITY-' if policy=='stable_camera_only' else 'REGION-CONSENSUS-')+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    files=['scripts/evaluate_region_consensus.py','src/smart_parking/region_consensus.py','src/smart_parking/region_consensus_model.py','scripts/train_region_transfer.py','src/smart_parking/region_transfer.py','src/smart_parking/region_evaluation.py','src/smart_parking/layout.py']
    hashes={p:digest(ROOT/p) for p in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),source_ids=['SRC-DS-001','SRC-MOD-003'],seed=101,
        hypothesis='Use geometry only for cameras with no differing training-mask pixels; route the entire image to the frozen CNN if ANY training geometry varies. This follows a failed unanimity study on reused development; no final data used.' if policy=='stable_camera_only' else 'Lock pixels on which all training masks agree; use the frozen neural mask only on changing training geometry. Preserve stable known views while retaining image dependence where training layouts vary.',
        route_policy=policy,method='Explicit camera ID; '+('any training-mask variation routes the WHOLE view to the frozen CNN, otherwise stored geometry' if policy=='stable_camera_only' else 'unanimity over all training masks locks pixels')+'; >=3training dates; common192x112 evaluation; existing RGB decoder384x224. No new neural fitting, no current-frame polygons as input.',
        quality_gate='OverallIoU>=0.80; each camera>=0.65 and >=train-only majority cameraIoU-0.10',
        added_value_gate='OverallIoU must exceed train-only majority by >=0.005; both gates required before any fresh final evaluation',
        diagnostic_limits='Camera-conditioned geometry composition, not pure-image segmentation, automatic slots or unseen-camera discovery. Stable-camera pixels may be entirely determined by stored training geometry; explicitly report CNN-controlled fraction. Dimensions do not authenticate a view.',
        reference_run=REFERENCE,reference_checkpoint_sha256=reference['checkpoint_sha256'],encoder_weights_sha256=digest(encoder),split_manifest_sha256=digest(manifest),
        image_holdout_manifest_sha256=digest(holdout),source_hashes=hashes,code_revision_basis='8992727 plus exact sealed source snapshots',
        source_hashes_inputs={r['image']:digest(ROOT/r['image']) for r in train+val},source_hashes_annotations={r['annotation']:digest(ROOT/r['annotation']) for r in train+val},
        scope='Reused known-camera development only; sealed final six remain unopened in this controller. No production promotion.')
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        truth_train=(masks_at_grid(train)>=.5).numpy();priors=fit_consensus(truth_train,train)
        source_sizes={camera:[] for camera in priors}
        for row in train:
            with Image.open(ROOT/row['image']) as image:size=list(image.size)
            if size not in source_sizes[row['camera_id']]:source_sizes[row['camera_id']].append(size)
        reference_bundle=torch.load(reference_path/'candidate.pt',map_location='cpu',weights_only=True)
        checkpoint=folder/'candidate.pt';save_checkpoint_atomic(dict(run_id=run,decoder_state_dict=reference_bundle['decoder_state_dict'],input_size=[384,224],evaluation_grid=[192,112],encoder_weights_sha256=digest(encoder),
            priors={c:{k:torch.from_numpy(v) if isinstance(v,np.ndarray) else v for k,v in p.items()} for c,p in priors.items()},source_image_sizes=source_sizes,method=protocol['method'],route_policy=policy),checkpoint)
        dump(folder/'frozen_training_prior.json',dict(checkpoint_sha256=digest(checkpoint),summary=prior_summary(priors),validation_labels_opened=False,at=datetime.now(timezone.utc).isoformat()))
        images=[]
        for row in val:
            with Image.open(ROOT/row['image']) as image:images.append(image.convert('RGB'))
        if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
        model=ConsensusRegionModel(checkpoint,encoder);neural,composed=model.predict(images,[r['camera_id'] for r in val])
        for i,mask in enumerate(neural):
            cached=np.asarray(Image.open(reference_path/f'validation_candidate_{i}.png'))>0
            assert np.array_equal(mask[0],cached),'Frozen decoder replay differs'
        truth=(masks_at_grid(val)>=.5).numpy();majority=np.stack([priors[r['camera_id']]['majority'] for r in val])
        learned=scores(neural,truth,val);hybrid=scores(composed,truth,val);baseline=scores(majority,truth,val)
        quality=hybrid['overall']['pixel_iou']>=.8 and all(v['pixel_iou']>=.65 and v['pixel_iou']>=baseline['per_camera'][c]['pixel_iou']-.1 for c,v in hybrid['per_camera'].items())
        added=hybrid['overall']['pixel_iou']>=baseline['overall']['pixel_iou']+.005
        for i in range(len(val)):
            for name,mask in [('hybrid',composed),('neural',neural),('majority',majority),('truth',truth)]:Image.fromarray((mask[i,0]*255).astype('uint8')).save(folder/f'validation_{name}_{i:02d}.png')
        selection=dict(validation_gate_passed=quality and added,checkpoint_sha256=digest(checkpoint),quality_gate_passed=quality,added_value_gate_passed=added)
        dump(folder/'selection_closed.json',selection)
        assert all(digest(ROOT/p)==h for p,h in hashes.items());assert_holdout_closed(holdout)
        effective={c:(1. if p['cnn_controlled_fraction']>0 else 0.) if policy=='stable_camera_only' else p['cnn_controlled_fraction'] for c,p in prior_summary(priors).items()}
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,checkpoint_sha256=digest(checkpoint),effective_cnn_controlled_fraction=effective,
            validation=hybrid,frozen_neural=learned,train_majority=baseline,training_prior_summary=prior_summary(priors),validation_gate_passed=quality and added,quality_gate_passed=quality,added_value_gate_passed=added,
            model_training_performed=False,final_images_decoded=0,final_annotations_decoded=0,production_changed=False,frozen_neural_replay_exact=True)
        dump(folder/'run.json',report)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,hybrid=hybrid,majority=baseline,prior=prior_summary(priors),gate=quality and added,duration=report['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False));state=json.loads(state_path.read_text());raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--policy',choices=['unanimous_pixels','stable_camera_only'],default='unanimous_pixels');main(parser.parse_args().policy)
