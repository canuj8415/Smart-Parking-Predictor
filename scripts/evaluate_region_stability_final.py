"""One protected final check of the frozen known-camera stability router."""
import json,sys,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import torch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed,evaluate_final_once
from smart_parking.region_consensus_model import ConsensusRegionModel
from train_region_transfer import masks_at_grid,scores
DEVELOPMENT='REGION-STABILITY-20261025T104606763875Z'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    torch.set_num_threads(4);torch.manual_seed(102)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another job is active')
    tests=(ROOT/'experiments/evidence/HEARTBEAT-20261025T103727Z/unit_tests_final.txt').read_text(encoding='utf-8-sig');assert 'Ran 130 tests' in tests and tests.rstrip().endswith('OK')
    development_folder=ROOT/'experiments/results'/DEVELOPMENT;development=json.loads((development_folder/'run.json').read_text());assert development['validation_gate_passed']
    checkpoint=development_folder/'candidate.pt';assert digest(checkpoint)==development['checkpoint_sha256']
    holdout=ROOT/'data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json';assert_holdout_closed(holdout)
    encoder=ROOT/'models/pretrained/resnet18_imagenet.pth';assert digest(encoder)==development['encoder_weights_sha256']
    model=ConsensusRegionModel(checkpoint,encoder);assert model.bundle['route_policy']=='stable_camera_only'
    started=datetime.now(timezone.utc);run='REGION-STABILITY-FINAL-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    files=['scripts/evaluate_region_stability_final.py','src/smart_parking/region_consensus.py','src/smart_parking/region_consensus_model.py','src/smart_parking/holdouts.py','scripts/train_region_transfer.py','src/smart_parking/region_transfer.py','src/smart_parking/region_evaluation.py','src/smart_parking/layout.py']
    hashes={p:digest(ROOT/p) for p in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),source_ids=['SRC-DS-001','SRC-MOD-003'],seed=102,development_run=DEVELOPMENT,development_result_sha256=digest(development_folder/'run.json'),
        checkpoint_sha256=digest(checkpoint),encoder_weights_sha256=digest(encoder),holdout_manifest_sha256=digest(holdout),route_policy='stable_camera_only',
        hypothesis='An explicit known-camera route based solely on training geometry stability retains regional overlap on the six sealed later-date images without changing neural weights.',
        method=development['method'],quality_gate=development['quality_gate'],added_value_gate=development['added_value_gate'],
        final_selection='Frozen development policy only; no tuning, new fitting, re-selection or automatic production promotion using final outcomes',
        comparators=['Unmodified frozen RGB-only neural mask on same frames','Train-only per-camera majority geometry on same frames'],
        scope='Six known-camera images, two per camera on one later date each. Source camera IDs supplied by sealed metadata; stored priors are not automatic layout discovery. Two stable cameras use geometry only; no neural contribution there.',
        source_hashes=hashes,code_revision_basis='8992727 plus exact sealed development/final source snapshots',
        production_checkpoint_sha256=digest(ROOT/'models/checkpoints/parking_unet.pt'))
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    selection=folder/'frozen_selection.json';dump(selection,dict(validation_gate_passed=True,checkpoint_sha256=digest(checkpoint),protocol_sha256=digest(folder/'protocol.json'),development_result_sha256=digest(development_folder/'run.json')))
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'),warning='Callback failure consumes final camera/date groups')];dump(state_path,state);clock=time.perf_counter()
    try:
        def evaluate(rows):
            if (folder/'CANCEL').exists():raise InterruptedError('Cancelled; final groups consumed')
            images=[]
            for row in rows:
                with Image.open(ROOT/row['image']) as image:images.append(image.convert('RGB'))
            neural,hybrid=model.predict(images,[r['camera_id'] for r in rows]);truth=(masks_at_grid(rows)>=.5).numpy()
            majority=np.stack([model.priors[r['camera_id']]['majority'] for r in rows])
            a=scores(hybrid,truth,rows);b=scores(majority,truth,rows);c=scores(neural,truth,rows)
            quality=a['overall']['pixel_iou']>=.8 and all(v['pixel_iou']>=.65 and v['pixel_iou']>=b['per_camera'][camera]['pixel_iou']-.1 for camera,v in a['per_camera'].items())
            added=a['overall']['pixel_iou']>=b['overall']['pixel_iou']+.005
            for i in range(len(rows)):
                for name,mask in [('hybrid',hybrid),('neural',neural),('majority',majority),('truth',truth)]:Image.fromarray((mask[i,0]*255).astype('uint8')).save(folder/f'final_{name}_{i:02d}.png')
                images[i].resize((384,224),Image.Resampling.BILINEAR).save(folder/f'final_source_{i:02d}.png')
            return dict(hybrid=a,train_majority=b,frozen_neural=c,quality_gate_passed=quality,added_value_gate_passed=added,final_gate_passed=quality and added,
                frames=rows,effective_cnn_controlled_fraction=development['effective_cnn_controlled_fraction'],
                image_sha256={r['image']:digest(ROOT/r['image']) for r in rows},annotation_sha256={r['annotation']:digest(ROOT/r['annotation']) for r in rows})
        final=evaluate_final_once(holdout,selection,checkpoint,run,evaluate,expected_manifest_sha256=protocol['holdout_manifest_sha256'])
        assert all(digest(ROOT/p)==h for p,h in hashes.items()) and digest(checkpoint)==protocol['checkpoint_sha256'] and digest(encoder)==protocol['encoder_weights_sha256']
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,final_evaluation=final,image_final_consumed=True,production_changed=False,neural_training_performed=False)
        dump(folder/'run.json',report)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,final=final['hybrid'],majority=final['train_majority'],neural=final['frozen_neural'],gate=final['final_gate_passed'],duration=report['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False,warning='Check durable claim; do not retry consumed final groups'));state=json.loads(state_path.read_text());raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)

if __name__=='__main__':main()
