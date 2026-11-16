"""One fixed prediction-only duplicate candidate on archived real development."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.mask_duplicates import deduplicate
from smart_parking.positive_instances import match_positives
from smart_parking.uvg import require_development


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def prepare():
    now=datetime.now(timezone.utc);run_id='UVG-MASK-DEDUP-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/results'/run_id;out.mkdir(parents=True,exist_ok=False)
    native=ROOT/'experiments/results/UVG-TILES-20261026T141429817814Z';prior=read(native/'run.json');ref=ROOT/prior['reference_folder']
    inputs=[native/'run.json']
    for f in prior['frames']:inputs.extend([native/f'maskrcnn_{f:04d}.json',native/f'maskrcnn_{f:04d}_masks.npz',ref/f'maskrcnn_{f:04d}.json',ref/f'truth_{f:04d}.json',ref/f'truth_masks_{f:04d}.npz'])
    inputs.append(ref/'input_0300.png')
    paths=['scripts/validate_uvg_mask_duplicates.py','src/smart_parking/mask_duplicates.py','tests/test_mask_duplicates.py','src/smart_parking/positive_instances.py']
    protocol=dict(run_id=run_id,prepared_at=now.isoformat(),seed=142,source_ids=['SRC-DS-019','SRC-DOC-021'],data_kind='archived_real_development_prediction_only_candidate',
        hypothesis='Same-class crop masks strongly contained within retained masks can be suppressed while preserving supplied-positive matches and mask quality;different-class overlaps must remain review-only.',
        frames=prior['frames'],native_folder=native.relative_to(ROOT).as_posix(),reference_folder=ref.relative_to(ROOT).as_posix(),
        minimum_mask_pixels=16,mask_containment=.85,box_containment=.8,box_match_iou=.5,
        policy='Never remove/reorder full-frame prefix;only suppress same-class crop additions;prefer reference representative;retain tiny masks and different-class overlaps with review evidence;never remap classes',
        gates=dict(minimum_suppressed_crop_predictions=10,minimum_eligible_matches=113,minimum_all_provided_matches=113,
                   maximum_zero_inclusive_iou_loss=.005,maximum_paired_matched_mask_iou_loss=.005,reference_prefix_preserved=True,no_per_frame_or_class_match_loss=True),
        paired_mask_cohort='Same113previouslymatchednative-candidate targets;notdifferentmatched-onlycohorts',
        input_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},implementation_hashes={p:digest(ROOT/p) for p in paths},
        protected_hashes=prior['protected_hashes'],weight_hashes=prior['weight_hashes'],reservation=prior['reservation'],reservation_sha256=prior['reservation_sha256'],
        maximum_seconds=180,model_calls=0,production_promoted=False,final_evaluation=False,
        boundary='Component duplicate-control validation only. Overall77th-trial Maskrecall/gap/volumefailurespersist;unassignednotverifiedFP,nooccupancy/finalaccuracy.')
    dump(out/'protocol.json',protocol);dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in paths});dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json'),sealed_before_real_candidate_application=True));print(str(out/'protocol.json'))


def run(path):
    path=Path(path).resolve();out=path.parent;config=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256']
    assert not (out/'progress.json').exists() and not (out/'run.json').exists(),'Preserve existing attempt'
    for p,h in {**config['input_hashes'],**config['implementation_hashes'],**config['protected_hashes'],**config['weight_hashes']}.items():assert digest(ROOT/p)==h,p
    require_development(ROOT/config['reservation'],config['reservation_sha256'],'https://ultravideo.fi/UVG-VCM/HighwayView/HighwayView.mp4')
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    state['active_validation_jobs']=[dict(run_id=config['run_id'],pid=os.getpid(),phase='Archived real mask duplicate candidate;no model calls')];dump(state_path,state)
    start=datetime.now(timezone.utc);timer=time.monotonic();native=ROOT/config['native_folder'];ref=ROOT/config['reference_folder'];rows=[];pairs=[];before_classes={};after_classes={}
    try:
        for f in config['frames']:
            if time.monotonic()-timer>180 or (out/'CANCEL').exists():raise InterruptedError('Bounded saved-mask candidate stopped')
            old=read(native/f'maskrcnn_{f:04d}.json');full=read(ref/f'maskrcnn_{f:04d}.json');targets=read(ref/f'truth_{f:04d}.json')['objects'];eligible=[i for i,t in enumerate(targets) if t['eligible']]
            packed=np.load(native/f'maskrcnn_{f:04d}_masks.npz',allow_pickle=False);masks=np.unpackbits(packed['packed'],axis=-1,count=960).astype(bool)
            selection=deduplicate(old['predictions'],masks,len(full['predictions']),16,.85,.8);indices=selection['kept_indices'];predictions=[old['predictions'][i] for i in indices];filtered=masks[indices]
            assert predictions[:len(full['predictions'])]==old['predictions'][:len(full['predictions'])]
            all_match=match_positives(targets,predictions,.5);match=match_positives([targets[i] for i in eligible],predictions,.5)
            gt=np.load(ref/f'truth_masks_{f:04d}.npz',allow_pickle=False);truth=np.unpackbits(gt['packed'],axis=-1,count=960).astype(bool)
            assignment={eligible[m['truth_index']]:m['prediction_index'] for m in match['matches']};mask_rows=[]
            for i in eligible:
                if not gt['known'][i]:continue
                j=assignment.get(i);iou=0.0 if j is None else float((truth[i]&filtered[j]).sum()/max(1,(truth[i]|filtered[j]).sum()))
                mask_rows.append(dict(track_id=targets[i]['track_id'],matched=j is not None,iou=iou))
            current={m['track_id']:m for m in mask_rows};pairs.extend((m,current[m['track_id']]) for m in old['supported_eligible_masks'] if m['matched'])
            for m in old['eligible_provided']['matches']:
                label=targets[eligible[m['truth_index']]]['label'];before_classes[label]=before_classes.get(label,0)+1
            for m in match['matches']:
                label=targets[eligible[m['truth_index']]]['label'];after_classes[label]=after_classes.get(label,0)+1
            row=dict(frame=f,predictions=predictions,source_prediction_indices=indices,duplicate_control=selection,eligible_provided=match,all_provided=all_match,supported_eligible_masks=mask_rows,
                     eligible_match_loss=old['eligible_provided']['matched_positives']-match['matched_positives'],all_match_loss=old['all_provided']['matched_positives']-all_match['matched_positives'])
            rows.append(row);dump(out/f'maskrcnn_{f:04d}.json',row);np.savez_compressed(out/f'maskrcnn_{f:04d}_masks.npz',packed=np.packbits(filtered,axis=-1),shape=list(filtered.shape))
            dump(out/'progress.json',dict(frame=f,completed_frames=len(rows),model_calls=0,cancellable=True))
        prior=read(native/'run.json')['results']['maskrcnn'];values=[m['iou'] for row in rows for m in row['supported_eligible_masks']]
        metrics=dict(eligible_provided=153,eligible_matches=sum(r['eligible_provided']['matched_positives'] for r in rows),all_provided=194,all_matches=sum(r['all_provided']['matched_positives'] for r in rows),
            predictions_before=sum(len(read(native/f"maskrcnn_{f:04d}.json")['predictions']) for f in config['frames']),predictions_after=sum(len(row['predictions']) for row in rows),
            suppressed_crop_predictions=sum(len(row['duplicate_control']['suppressed']) for row in rows),review_pairs=sum(len(row['duplicate_control']['reviews']) for row in rows),
            zero_inclusive_mask_iou=sum(values)/len(values),paired_previous_matches=len(pairs),paired_mask_iou_before=sum(a['iou'] for a,b in pairs)/len(pairs),paired_mask_iou_after=sum(b['iou'] for a,b in pairs)/len(pairs),
            previous_match_retention=sum(b['matched'] for a,b in pairs)/len(pairs),class_matches_before=before_classes,class_matches_after=after_classes,
            eligible_unassigned_after=sum(row['eligible_provided']['unmatched_predictions'] for row in rows),all_unassigned_after=sum(row['all_provided']['unmatched_predictions'] for row in rows))
        checks=dict(at_least10crop_duplicates_removed=metrics['suppressed_crop_predictions']>=10,eligible_match_preservation=metrics['eligible_matches']>=113,all_match_preservation=metrics['all_matches']>=113,
            every_frame_matches_preserved=all(r['eligible_match_loss']<=0 and r['all_match_loss']<=0 for r in rows),every_class_matches_preserved=all(after_classes.get(c,0)>=n for c,n in before_classes.items()),
            mask_overlap_nonregression=metrics['zero_inclusive_mask_iou']>=prior['mask_zero_inclusive_mean_iou']-.005,paired_mask_nonregression=metrics['paired_mask_iou_after']>=metrics['paired_mask_iou_before']-.005,
            reference_prefix_preserved=all(row['duplicate_control']['reference_prefix_preserved'] for row in rows),classes_not_remapped=all(not row['duplicate_control']['classes_remapped'] for row in rows),
            protected_hashes_unchanged=all(digest(ROOT/p)==h for p,h in {**config['input_hashes'],**config['protected_hashes'],**config['weight_hashes']}.items()),no_model_inference=True,final_source_unopened=True)
        report=dict(config,started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,metrics=metrics,checks=checks,component_gates_passed=all(checks.values()),
                    overall_vision_admission_passed=False,scope='Saved real-development duplicate-control candidate;notfreshmodelaccuracy,exhaustiveprecision,occupancyorfinalacceptance')
        dump(out/'run.json',report);dump(ROOT/'reports/uvg_mask_dedup_latest.json',dict(run_id=config['run_id'],report=(out/'run.json').relative_to(ROOT).as_posix(),metrics=metrics,checks=checks,component_gates_passed=report['component_gates_passed'],overall_vision_admission_passed=False));print(json.dumps(dict(run_id=config['run_id'],duration_seconds=report['duration_seconds'],metrics=metrics,checks=checks),indent=2))
    except BaseException as error:dump(out/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:
        state=read(state_path);state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--run');args=parser.parse_args()
    if args.prepare:prepare()
    elif args.run:run(args.run)
    else:parser.error('Choose --prepare or --run with a sealed protocol')
