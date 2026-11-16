"""One sealed native-detail tile candidate against cached full-frame evidence."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import time
import cv2
import numpy as np
from PIL import Image,ImageDraw
import torch
from torchvision.transforms import functional as TF

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.vision import VisionEngine,VEHICLES
from smart_parking.uvg import require_development
from smart_parking.positive_instances import match_positives
from smart_parking.tiled_detection import tile_plan,map_box,mask_to_view,touches_inner_edge,select_additions


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def prepare():
    now=datetime.now(timezone.utc);run_id='UVG-TILES-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/results'/run_id;out.mkdir(parents=True,exist_ok=False)
    ref=ROOT/'experiments/results/UVG-DETECTORS-20261026T131820602234Z';baseline=read(ref/'run.json')
    paths=['scripts/evaluate_uvg_tiles.py','src/smart_parking/tiled_detection.py','tests/test_tiled_detection.py','src/smart_parking/positive_instances.py','src/smart_parking/vision.py']
    files=[p for p in ref.iterdir() if p.name=='run.json' or p.name.startswith(('input_','truth_','fasterrcnn_','maskrcnn_'))]
    protocol=dict(run_id=run_id,prepared_at=now.isoformat(),seed=141,source_ids=['SRC-DS-019','SRC-DOC-021'],
        hypothesis='Four fixed overlapping crops from native4K frames recover small supplied objects lost during whole-frame resizing, while preserving full-frame outputs and mask quality under fixed road-class/score rules.',
        reference_folder=ref.relative_to(ROOT).as_posix(),reference_report_sha256=digest(ref/'run.json'),
        frames=baseline['frames'],source_size=[3840,2160],view_size=[960,540],tile_extents=tile_plan((3840,2160)),tile_resize='Pillow bicubic to960x540',
        internal_max_side=960,confidence=.5,mask_probability=.5,box_iou=.5,duplicate_iou=.5,interior_edge_exclusion_pixels=2,
        merge='Keep all full-frame predictions in original order;sort crop proposals by descending score/tile/index;reject artificial-edge boxes;append only proposals without same-classIoU>=0.5 against kept outputs',
        mask_mapping='Nearest resize from960x540tile output to declared tile extent on common960x540grid;no learned or label-based geometry',
        source_to_product_classes=baseline['source_to_product_class_names'],eligibility='Same153>=4x4input-pixel car/truck targets;all194also reported;unknown mask support excluded;train outside product scope',
        gates=dict(minimum_eligible_recall=.75,minimum_zero_inclusive_mask_iou=.5,maximum_mask_recall_gap=.05,
                   minimum_recall_gain_each=.05,minimum_mask_iou_gain=.05,maximum_paired_reference_mask_iou_loss=.02,minimum_reference_mask_match_retention=.95,
                   maximum_extra_unassigned_per_frame=2,maximum_estimated_forward_time_ratio=6),
        unassigned_boundary='Unassigned predictions are not verified false positives;growth cap is an output-volume constraint,not a precision/safety gate',
        maximum_model_calls=88,maximum_seconds=900,estimated_runtime='Cached full-frame reference cost plus actual four-crop model calls;not deployment FPS',
        reservation=baseline['reservation'],reservation_sha256=baseline['reservation_sha256'],
        video='data/raw/uvg_vcm_official/HighwayView/HighwayView.mp4',video_sha256=baseline['input_hashes']['HighwayView.mp4'],
        reference_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in files if p.is_file()},
        implementation_hashes={p:digest(ROOT/p) for p in paths},weight_hashes=baseline['weight_hashes'],protected_hashes=baseline['protected_hashes'],
        new_training=False,final_evaluation=False,exhaustive_precision_evaluable=False,parking_occupancy_evaluable=False,production_promoted=False)
    dump(out/'protocol.json',protocol);dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in paths});dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json'),sealed_before_crop_inference=True));print(str(out/'protocol.json'))


def run(path):
    path=Path(path).resolve();out=path.parent;config=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256']
    assert not (out/'progress.json').exists() and not (out/'run.json').exists(),'Preserve existing attempt;no silent replay'
    for p,h in {**config['reference_hashes'],**config['implementation_hashes'],**config['weight_hashes'],**config['protected_hashes']}.items():assert digest(ROOT/p)==h,p
    require_development(ROOT/config['reservation'],config['reservation_sha256'],'https://ultravideo.fi/UVG-VCM/HighwayView/HighwayView.mp4')
    assert digest(ROOT/config['video'])==config['video_sha256']
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    state['active_validation_jobs']=[dict(run_id=config['run_id'],pid=os.getpid(),phase='Bounded native-detail crop comparison;no training')];dump(state_path,state)
    started=datetime.now(timezone.utc);timer=time.monotonic();torch.manual_seed(141);np.random.seed(141);calls=0
    ref=ROOT/config['reference_folder'];baseline=read(ref/'run.json');results={};comparisons={}
    def bounded():
        if calls>88 or time.monotonic()-timer>900 or (out/'CANCEL').exists():raise InterruptedError('Native-detail trial cancelled/time/call bound reached')
    try:
        for kind in ['fasterrcnn','maskrcnn']:
            engine=VisionEngine(kind,resolution=960);frame_rows=[];cap=cv2.VideoCapture(str(ROOT/config['video']));assert cap.isOpened()
            try:
                for f in config['frames']:
                    bounded();cap.set(cv2.CAP_PROP_POS_FRAMES,f-1);ok,raw=cap.read();assert ok and abs(cap.get(cv2.CAP_PROP_POS_FRAMES)-f)<.01
                    native=Image.fromarray(cv2.cvtColor(raw,cv2.COLOR_BGR2RGB));assert native.size==(3840,2160)
                    common=native.resize((960,540),Image.Resampling.BICUBIC)
                    assert np.array_equal(np.asarray(common),np.asarray(Image.open(ref/f'input_{f:04d}.png').convert('RGB'))),'Native frame differs from reference'
                    targets=read(ref/f'truth_{f:04d}.json')['objects'];original=read(ref/f'{kind}_{f:04d}.json')
                    predictions=[dict(p,origin='full_frame') for p in original['predictions']];proposals=[];crop_log=[];edge_rejected=0;seconds=0
                    for tile_index,extent in enumerate(config['tile_extents']):
                        bounded();image=native.crop(tuple(extent)).resize((960,540),Image.Resampling.BICUBIC);t=time.perf_counter()
                        with torch.inference_mode():output=engine.model([TF.to_tensor(image)])[0]
                        elapsed=time.perf_counter()-t;seconds+=elapsed;calls+=1;assert calls<=88;objects=[]
                        for i,(box,label,score) in enumerate(zip(output['boxes'],output['labels'],output['scores'])):
                            label=int(label);score=float(score)
                            if label not in VEHICLES or score<.5:continue
                            local=box.tolist();edge=touches_inner_edge(local,extent,(3840,2160),(960,540),2)
                            entry=dict(label=VEHICLES[label],score=score,tile_box=local,box=map_box(local,extent,(3840,2160),(960,540)),tile_index=tile_index,proposal_index=i,artificial_edge_rejected=bool(edge))
                            objects.append(entry)
                            if edge:edge_rejected+=1;continue
                            mask=(output['masks'][i,0].numpy()>=.5) if 'masks' in output else None
                            proposals.append(dict(entry,mask=mask))
                        crop_log.append(dict(tile_index=tile_index,extent=extent,outputs=objects,model_seconds=elapsed));del output
                    selected,duplicates=select_additions(predictions,proposals,.5)
                    masks=[]
                    if kind=='maskrcnn':
                        packed=np.load(ref/f'maskrcnn_{f:04d}_masks.npz',allow_pickle=False)
                        masks=list(np.unpackbits(packed['packed'],axis=-1,count=960).astype(bool))
                    for i in selected:
                        prop=proposals[i];predictions.append({k:v for k,v in prop.items() if k!='mask'})
                        if kind=='maskrcnn':masks.append(mask_to_view(prop['mask'],config['tile_extents'][prop['tile_index']],(3840,2160),(960,540)))
                    assert predictions[:len(original['predictions'])]==[dict(p,origin='full_frame') for p in original['predictions']]
                    all_match=match_positives(targets,predictions,.5);eligible=[i for i,tgt in enumerate(targets) if tgt['eligible']]
                    eligible_match=match_positives([targets[i] for i in eligible],predictions,.5);mask_rows=[]
                    if kind=='maskrcnn':
                        archive=np.load(ref/f'truth_masks_{f:04d}.npz',allow_pickle=False);truth_masks=np.unpackbits(archive['packed'],axis=-1,count=960).astype(bool)
                        assignments={eligible[m['truth_index']]:m['prediction_index'] for m in eligible_match['matches']}
                        for i in eligible:
                            if not archive['known'][i]:continue
                            j=assignments.get(i);value=0.0 if j is None else float((truth_masks[i]&masks[j]).sum()/max(1,(truth_masks[i]|masks[j]).sum()))
                            mask_rows.append(dict(track_id=targets[i]['track_id'],matched=j is not None,iou=value))
                        np.savez_compressed(out/f'maskrcnn_{f:04d}_masks.npz',packed=np.packbits(np.stack(masks),axis=-1) if masks else np.zeros((0,540,120),dtype=np.uint8),shape=[len(masks),540,960])
                    row=dict(frame=f,predictions=predictions,crop_outputs=crop_log,full_frame_predictions_preserved=True,accepted_crop_predictions=len(selected),duplicate_crop_predictions=len(duplicates),artificial_edge_rejections=edge_rejected,
                             crop_model_seconds=seconds,all_provided=all_match,eligible_provided=eligible_match,supported_eligible_masks=mask_rows)
                    frame_rows.append(row);dump(out/f'{kind}_{f:04d}.json',row)
                    if f in [1,300,600]:
                        image=common.copy();draw=ImageDraw.Draw(image)
                        for obj in predictions:draw.rectangle(obj['box'],outline='cyan' if obj.get('origin')=='full_frame' else 'orange',width=2)
                        draw.rectangle((0,0,960,23),fill='black');draw.text((6,5),f'{kind} DEV frame{f}:cyan reference;orange native-crop additions',fill='white');image.save(out/f'{kind}_{f:04d}.png')
                    dump(out/'progress.json',dict(model=kind,frame=f,completed_crop_calls=calls,maximum_calls=88,cancellable=True));print(json.dumps(dict(model=kind,frame=f,matched=eligible_match['matched_positives'],eligible=eligible_match['provided_positives'],added=len(selected),calls=calls)),flush=True)
            finally:cap.release()
            def aggregate(key):
                n=sum(r[key]['provided_positives'] for r in frame_rows);m=sum(r[key]['matched_positives'] for r in frame_rows)
                return dict(provided_positives=n,matched_positives=m,recall=m/n,unassigned_predictions=sum(r[key]['unmatched_predictions'] for r in frame_rows))
            values=[m for r in frame_rows for m in r['supported_eligible_masks']];prior=baseline['results'][kind]
            results[kind]=dict(all_provided=aggregate('all_provided'),eligible_provided=aggregate('eligible_provided'),supported_masks=len(values),mask_zero_inclusive_mean_iou=None if not values else sum(m['iou'] for m in values)/len(values),
                matched_mask_mean_iou=None if not values or not any(m['matched'] for m in values) else sum(m['iou'] for m in values if m['matched'])/sum(m['matched'] for m in values),crop_model_seconds=sum(r['crop_model_seconds'] for r in frame_rows),
                estimated_total_model_seconds=prior['model_forward_total_seconds']+sum(r['crop_model_seconds'] for r in frame_rows),accepted_crop_predictions=sum(r['accepted_crop_predictions'] for r in frame_rows),edge_rejections=sum(r['artificial_edge_rejections'] for r in frame_rows))
            before_classes={};after_classes={};prior_unassigned=0;frame_losses=[]
            for row in frame_rows:
                f=row['frame'];targets=[t for t in read(ref/f'truth_{f:04d}.json')['objects'] if t['eligible']];old=read(ref/f'{kind}_{f:04d}.json')['eligible_provided'];new=row['eligible_provided']
                prior_unassigned+=old['unmatched_predictions'];frame_losses.append(old['provided_positive_recall']-new['provided_positive_recall'])
                for match in old['matches']:
                    label=targets[match['truth_index']]['label'];before_classes[label]=before_classes.get(label,0)+1
                for match in new['matches']:
                    label=targets[match['truth_index']]['label'];after_classes[label]=after_classes.get(label,0)+1
            comparisons[kind]=dict(recall_gain=results[kind]['eligible_provided']['recall']-prior['eligible_provided']['recall'],maximum_per_frame_loss=max(frame_losses),class_matches_before=before_classes,class_matches_after=after_classes,
                no_class_match_loss=all(after_classes.get(c,0)>=n for c,n in before_classes.items()),extra_unassigned=results[kind]['eligible_provided']['unassigned_predictions']-prior_unassigned,
                estimated_forward_time_ratio=results[kind]['estimated_total_model_seconds']/prior['model_forward_total_seconds'])
            if kind=='maskrcnn':
                pairs=[]
                for row in frame_rows:
                    previous=read(ref/f"maskrcnn_{row['frame']:04d}.json")['supported_eligible_masks']
                    current={m['track_id']:m for m in row['supported_eligible_masks']}
                    pairs.extend((m,current[m['track_id']]) for m in previous if m['matched'])
                comparisons[kind].update(paired_reference_mask_count=len(pairs),paired_reference_mask_iou_before=sum(a['iou'] for a,b in pairs)/len(pairs),
                    paired_reference_mask_iou_after=sum(b['iou'] for a,b in pairs)/len(pairs),reference_mask_match_retention=sum(b['matched'] for a,b in pairs)/len(pairs))
            del engine
        mask=results['maskrcnn'];old_mask=baseline['results']['maskrcnn'];fr=results['fasterrcnn']['eligible_provided']['recall'];mr=mask['eligible_provided']['recall']
        checks=dict(faster_absolute_recall=fr>=.75,mask_absolute_recall=mr>=.75,mask_absolute_overlap=mask['mask_zero_inclusive_mean_iou']>=.5,mask_recall_gap=mr>=fr-.05,
            both_relative_recall_gain=all(v['recall_gain']>=.05 for v in comparisons.values()),mask_relative_overlap_gain=mask['mask_zero_inclusive_mean_iou']>=old_mask['mask_zero_inclusive_mean_iou']+.05,
            paired_mask_nonregression=comparisons['maskrcnn']['paired_reference_mask_iou_after']>=comparisons['maskrcnn']['paired_reference_mask_iou_before']-.02,
            reference_mask_match_retention=comparisons['maskrcnn']['reference_mask_match_retention']>=.95,per_class_nonregression=all(v['no_class_match_loss'] for v in comparisons.values()),
            per_frame_nonregression=all(v['maximum_per_frame_loss']<=0 for v in comparisons.values()),unassigned_volume_bound=all(v['extra_unassigned']<=22 for v in comparisons.values()),
            runtime_bound=all(v['estimated_forward_time_ratio']<=6 for v in comparisons.values()),full_frame_outputs_preserved=True,crop_calls_bounded=calls==88,
            protected_hashes_unchanged=all(digest(ROOT/p)==h for p,h in {**config['protected_hashes'],**config['weight_hashes'],**config['reference_hashes']}.items()),final_source_unopened=True)
        report=dict(config,started_at=started.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,crop_model_calls=calls,results=results,comparisons=comparisons,checks=checks,all_gates_passed=all(checks.values()),
                    scope='Provided-positive development augmentation on sameoneclip;unassignedpredictionsnotverifiedFP;noexhaustiveprecision,occupancy,independentfinalaccuracyordeploymentFPS')
        dump(out/'run.json',report);dump(ROOT/'reports/uvg_tiles_latest.json',dict(run_id=config['run_id'],report=(out/'run.json').relative_to(ROOT).as_posix(),results=results,comparisons=comparisons,checks=checks,all_gates_passed=report['all_gates_passed']))
    except BaseException as error:
        dump(out/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:
        state=read(state_path);state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--run');args=parser.parse_args()
    if args.prepare:prepare()
    elif args.run:run(args.run)
    else:parser.error('Choose --prepare or --run with a sealed protocol')
