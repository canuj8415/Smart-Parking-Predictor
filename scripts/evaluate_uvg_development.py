"""Frozen, bounded unchanged-detector positive-instance DEVELOPMENT comparison."""
import argparse
import io
import json
import os
import sys
import time
import zipfile
from datetime import datetime,timezone
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
import torch
from torchvision.transforms import functional as TF

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.uvg import require_development,validate_annotations,supported_instance_mask
from smart_parking.positive_instances import match_positives,result_reference
from smart_parking.vision import VisionEngine,VEHICLES


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def prepare(resolution=640,reference=None):
    now=datetime.now(timezone.utc);run_id='UVG-DETECTORS-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/results'/run_id;out.mkdir(parents=True,exist_ok=False)
    folder=ROOT/'data/raw/uvg_vcm_official/HighwayView'
    paths=['scripts/evaluate_uvg_development.py','src/smart_parking/positive_instances.py','src/smart_parking/uvg.py','src/smart_parking/vision.py','tests/test_positive_instances.py']
    weights=['models/pretrained/fasterrcnn_resnet50_fpn_v2.pth','models/pretrained/maskrcnn_resnet50_fpn.pth']
    protected=read(ROOT/'models/singapore_trend_development.json')['protected_hashes']
    protected.update(read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')['implementation_hashes'])
    protocol=dict(run_id=run_id,prepared_at=now.isoformat(),seed=138,source_ids=['SRC-DS-019','SRC-DOC-021'],
        split='Entire HighwayView development exposed;entire HighwayDrive reserved unopened',
        hypothesis='Unchanged product detectors have >=75% class-aware provided-positive recall on >=4x4 input-pixel car/truck boxes;Mask R-CNN also has >=0.5 zero-inclusive mean IoU on eligible supported masks without >5percentage-point box recall regression versus Faster R-CNN.',
        frames=[1,61,121,181,241,300,361,421,481,541,600],input_size=[960,540],input_resize='Pillow bicubic, unannotated publisher MP4',
        detector_resolution=resolution,confidence=.5,mask_probability=.5,box_iou=.5,
        eligible_minimum_box_side_pixels=4,source_to_product_class_names={'car':'car','truck':'truck'},
        unsupported_classes='Train explicitly outside product VEHICLES and excluded;other product predicted classes are unassigned, not assumed false positives',
        matching='Deterministic maximum-cardinality same-class IoU>=0.5 matching, descending-IoU adjacency;one prediction per truth',
        mask_denominator='Eligible supplied car/truck objects with nonempty PNG support before and after nearest resize;valid supported unmatched targets score0;absent support unknown/excluded',
        gates=dict(minimum_eligible_positive_recall=.75,minimum_mask_zero_inclusive_mean_iou=.5,maximum_mask_box_recall_regression=.05),
        maximum_seconds=900,maximum_frames_per_model=11,
        reservation='data/manifests/uvg_source_roles_v1.json',reservation_sha256='68599fe2e3f8206acf96626f25777af97bafa2351195a0cc76a613f49d35535e',
        implementation_hashes={p:digest(ROOT/p) for p in paths},weight_hashes={p:digest(ROOT/p) for p in weights},
        protected_hashes=protected,input_hashes={p.name:digest(p) for p in folder.iterdir() if p.is_file() and not p.name.endswith('.partial')},
        exhaustive_precision_mAP_evaluable=False,parking_occupancy_evaluable=False,final_evaluation=False,
        pretraining_overlap_audited=False,model_training=False,app_promotion=False)
    if resolution!=640:
        if reference is None:raise ValueError('Resolution candidate requires a completed original reference')
        baseline=Path(reference).resolve();ref=read(baseline)
        assert baseline.is_relative_to((ROOT/'experiments/results').resolve()) and ref['detector_resolution']==640
        for key in ['frames','input_size','input_resize','confidence','mask_probability','box_iou','source_to_product_class_names','eligible_minimum_box_side_pixels','input_hashes']:
            assert ref[key]==protocol[key],key
        protocol['hypothesis']='Preserving native960input detail increases eligible-positive recall by >=5percentage-points in both unchanged detectors and zero-inclusive MaskIoU by >=0.05, without class recall loss or >10percentage-point per-frame recall loss;mean model-forward time <=3xoriginal. Original absolute75percent/0.5gates also retained.'
        protocol['reference_report']=baseline.relative_to(ROOT).as_posix()
        protocol['reference_report_sha256']=digest(baseline)
        references=[*baseline.parent.glob('*rcnn_*.json'),*baseline.parent.glob('truth_*.json'),*baseline.parent.glob('input_*.png')]
        protocol['reference_frame_hashes']={p.relative_to(ROOT).as_posix():digest(p) for p in references}
        protocol['candidate_gates']=dict(minimum_recall_gain=.05,minimum_mask_iou_gain=.05,maximum_per_frame_recall_loss=.10,maximum_forward_time_ratio=3.0,no_per_class_match_loss=True)
    dump(out/'protocol.json',protocol);dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in paths})
    dump(out/'protocol_binding.json',dict(protocol_sha256=digest(out/'protocol.json'),prepared_before_model_inference=True))
    print(str(out/'protocol.json'))


def evaluate(path):
    path=Path(path).resolve()
    config=read(path);out=Path(path).parent
    assert out.resolve().is_relative_to((ROOT/'experiments/results').resolve())
    assert digest(Path(path))==read(out/'protocol_binding.json')['protocol_sha256']
    assert not (out/'run.json').exists() and not (out/'progress.json').exists(),'Preserve existing attempt;no silent replay'
    if config.get('reference_report'):
        assert digest(ROOT/config['reference_report'])==config['reference_report_sha256']
        for p,h in config['reference_frame_hashes'].items():assert digest(ROOT/p)==h
    for p,h in {**config['implementation_hashes'],**config['weight_hashes'],**config['protected_hashes']}.items():assert digest(ROOT/p)==h,p
    assets=ROOT/'data/raw/uvg_vcm_official/HighwayView'
    for name,h in config['input_hashes'].items():
        require_development(ROOT/config['reservation'],config['reservation_sha256'],'https://ultravideo.fi/UVG-VCM/HighwayView/'+name)
        assert digest(assets/name)==h
    state_path=ROOT/'data/automation_state.json';state=read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    start=datetime.now(timezone.utc);timer=time.monotonic();torch.manual_seed(config['seed']);np.random.seed(config['seed'])
    state['active_validation_jobs']=[dict(run_id=config['run_id'],pid=os.getpid(),phase='Bounded real traffic development inference')];dump(state_path,state)
    def bounded():
        if time.monotonic()-timer>config['maximum_seconds'] or (out/'CANCEL').exists():raise InterruptedError('Bounded development inference cancelled/timed out')
    try:
        annotations=read(assets/'HighwayView_annotations.json');validate_annotations(annotations,600)
        frames={};truth={};mask_truth={};preparation=[]
        cap=cv2.VideoCapture(str(assets/'HighwayView.mp4'))
        try:
            with zipfile.ZipFile(assets/'HighwayView_masks.zip') as z:
                for f in config['frames']:
                    bounded();cap.set(cv2.CAP_PROP_POS_FRAMES,f-1);ok,raw=cap.read();assert ok
                    assert abs(cap.get(cv2.CAP_PROP_POS_FRAMES)-f)<.01
                    image=Image.fromarray(cv2.cvtColor(raw,cv2.COLOR_BGR2RGB)).resize(tuple(config['input_size']),Image.Resampling.BICUBIC)
                    frames[f]=image;image.save(out/f'input_{f:04d}.png')
                    with Image.open(io.BytesIO(z.read(f'UVG-VCM/HighwayView/HighwayView_masks/mask_{f:04d}.png'))) as im:array=np.array(im)
                    targets=[];masks=[];excluded_classes=0
                    for obj in annotations[str(f)]:
                        if obj['class_name'] not in config['source_to_product_class_names']:excluded_classes+=1;continue
                        box=[obj[k]*scale for k,scale in zip(['x_min','y_min','x_max','y_max'],[960,540,960,540])]
                        eligible=(box[2]-box[0]>=4 and box[3]-box[1]>=4)
                        full,status=supported_instance_mask(array,obj['mask_color'])
                        scaled=None if full is None else np.array(Image.fromarray(full).resize((960,540),Image.Resampling.NEAREST),dtype=bool)
                        if scaled is not None and not scaled.any():scaled=None;status='unknown_resolution_loss'
                        targets.append(dict(label=obj['class_name'],track_id=obj['track_id'],box=box,eligible=eligible,mask_status=status))
                        masks.append(scaled)
                    truth[f]=targets;mask_truth[f]=masks
                    dump(out/f'truth_{f:04d}.json',dict(objects=targets,excluded_train_observations=excluded_classes))
                    supported=[m if m is not None else np.zeros((540,960),dtype=bool) for m in masks]
                    np.savez_compressed(out/f'truth_masks_{f:04d}.npz',packed=np.packbits(np.stack(supported),axis=-1),shape=[len(supported),540,960],known=[m is not None for m in masks])
                    preparation.append(dict(frame=f,objects=len(targets),eligible=sum(t['eligible'] for t in targets),excluded_train=excluded_classes,unknown_masks=sum(m is None for m in masks)))
        finally:cap.release()
        dump(out/'truth_inventory.json',preparation)
        results={}
        for kind in ['fasterrcnn','maskrcnn']:
            engine=VisionEngine(kind,resolution=config['detector_resolution']);rows=[]
            for f in config['frames']:
                bounded();t=time.perf_counter()
                with torch.inference_mode():prediction=engine.model([TF.to_tensor(frames[f])])[0]
                latency=time.perf_counter()-t;preds=[];pred_masks=[]
                for i,(box,label,score) in enumerate(zip(prediction['boxes'],prediction['labels'],prediction['scores'])):
                    label=int(label);score=float(score)
                    if label not in VEHICLES or score<config['confidence']:continue
                    preds.append(dict(label=VEHICLES[label],box=box.tolist(),score=score))
                    pred_masks.append((prediction['masks'][i,0].numpy()>=config['mask_probability']) if 'masks' in prediction else None)
                all_match=match_positives(truth[f],preds,config['box_iou'])
                eligible_indices=[i for i,tgt in enumerate(truth[f]) if tgt['eligible']]
                eligible_match=match_positives([truth[f][i] for i in eligible_indices],preds,config['box_iou'])
                mask_rows=[]
                if kind=='maskrcnn':
                    assignments={eligible_indices[m['truth_index']]:m['prediction_index'] for m in eligible_match['matches']}
                    for i in eligible_indices:
                        target=mask_truth[f][i]
                        if target is None:continue
                        j=assignments.get(i);iou=0.0
                        if j is not None:
                            candidate=pred_masks[j];iou=float((target&candidate).sum()/max(1,(target|candidate).sum()))
                        mask_rows.append(dict(track_id=truth[f][i]['track_id'],matched=j is not None,iou=iou))
                    packed=np.packbits(np.stack(pred_masks),axis=-1) if pred_masks else np.zeros((0,540,120),dtype=np.uint8)
                    np.savez_compressed(out/f'{kind}_{f:04d}_masks.npz',packed=packed,shape=[len(pred_masks),540,960])
                row=dict(frame=f,predictions=preds,all_provided=all_match,eligible_provided=eligible_match,supported_eligible_masks=mask_rows,latency_seconds=latency)
                rows.append(row);dump(out/f'{kind}_{f:04d}.json',row)
                if f in [1,300,600]:
                    image=frames[f].copy();draw=ImageDraw.Draw(image)
                    for d in preds:draw.rectangle(d['box'],outline='cyan',width=2)
                    draw.rectangle((0,0,960,22),fill='black');draw.text((6,5),f'{kind} DEVELOPMENT frame{f};model boxes;no occupancy truth',fill='white');image.save(out/f'{kind}_{f:04d}.png')
                dump(out/'progress.json',dict(run_id=config['run_id'],model=kind,completed_frames=len(rows),last_frame=f,started_at=start.isoformat(),cancellable=True))
                print(json.dumps(dict(model=kind,frame=f,matched=eligible_match['matched_positives'],eligible=eligible_match['provided_positives'])),flush=True)
                del prediction
            def aggregate(key):
                denominator=sum(r[key]['provided_positives'] for r in rows);matched=sum(r[key]['matched_positives'] for r in rows)
                return dict(provided_positives=denominator,matched_positives=matched,recall=None if not denominator else matched/denominator)
            values=[m for r in rows for m in r['supported_eligible_masks']]
            results[kind]=dict(all_provided=aggregate('all_provided'),eligible_provided=aggregate('eligible_provided'),supported_masks=len(values),
                mask_zero_inclusive_mean_iou=None if not values else sum(m['iou'] for m in values)/len(values),
                matched_mask_mean_iou=None if not any(m['matched'] for m in values) else sum(m['iou'] for m in values if m['matched'])/sum(m['matched'] for m in values),
                model_forward_total_seconds=sum(r['latency_seconds'] for r in rows),weight_sha256=engine.weight_sha256)
            del engine
        fr=results['fasterrcnn']['eligible_provided']['recall'];mr=results['maskrcnn']['eligible_provided']['recall']
        checks=dict(faster_positive_gate=fr>=.75,mask_positive_gate=mr>=.75,mask_overlap_gate=results['maskrcnn']['mask_zero_inclusive_mean_iou']>=.5,
                    mask_box_nonregression=mr>=fr-.05,protected_hashes_unchanged=all(digest(ROOT/p)==h for p,h in config['protected_hashes'].items()),final_source_unopened=True)
        if config.get('reference_report'):
            reference=read(ROOT/config['reference_report']);reference_folder=(ROOT/config['reference_report']).parent
            comparisons={}
            for kind in ['fasterrcnn','maskrcnn']:
                prior=reference['results'][kind];current=results[kind]
                prior_classes={};current_classes={};frame_losses=[]
                for f in config['frames']:
                    targets=read(out/f'truth_{f:04d}.json')['objects'];eligible=[t for t in targets if t['eligible']]
                    assert digest(out/f'truth_{f:04d}.json')==digest(reference_folder/f'truth_{f:04d}.json')
                    assert digest(out/f'input_{f:04d}.png')==digest(reference_folder/f'input_{f:04d}.png')
                    before=read(reference_folder/f'{kind}_{f:04d}.json')['eligible_provided'];after=read(out/f'{kind}_{f:04d}.json')['eligible_provided']
                    frame_losses.append(before['provided_positive_recall']-after['provided_positive_recall'])
                    for match in before['matches']:
                        label=eligible[match['truth_index']]['label'];prior_classes[label]=prior_classes.get(label,0)+1
                    for match in after['matches']:
                        label=eligible[match['truth_index']]['label'];current_classes[label]=current_classes.get(label,0)+1
                comparisons[kind]=dict(recall_gain=current['eligible_provided']['recall']-prior['eligible_provided']['recall'],maximum_per_frame_recall_loss=max(frame_losses),
                    class_matches_before=prior_classes,class_matches_after=current_classes,no_class_match_loss=all(current_classes.get(c,0)>=n for c,n in prior_classes.items()),
                    model_forward_time_ratio=current['model_forward_total_seconds']/prior['model_forward_total_seconds'])
            mask_gain=results['maskrcnn']['mask_zero_inclusive_mean_iou']-reference['results']['maskrcnn']['mask_zero_inclusive_mean_iou']
            checks.update(candidate_positive_gain=all(v['recall_gain']>=.05 for v in comparisons.values()),candidate_mask_gain=mask_gain>=.05,
                candidate_per_frame_nonregression=all(v['maximum_per_frame_recall_loss']<=.10 for v in comparisons.values()),candidate_class_nonregression=all(v['no_class_match_loss'] for v in comparisons.values()),
                candidate_forward_time_gate=all(v['model_forward_time_ratio']<=3 for v in comparisons.values()))
            dump(out/'candidate_comparison.json',dict(comparisons=comparisons,mask_zero_inclusive_iou_gain=mask_gain,checks=checks))
        report=dict(config,started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,
                    results=results,truth_inventory=preparation,checks=checks,all_gates_passed=all(checks.values()),scope='Provided-positive development agreement only;no exhaustive precision/mAP,parking-region/occupancy/final/live-camera claim')
        dump(out/'run.json',report);dump(ROOT/'reports/uvg_detectors_latest.json',dict(run_id=config['run_id'],report=result_reference(out/'run.json',ROOT),results=results,checks=checks,all_gates_passed=report['all_gates_passed']))
    except BaseException as error:
        dump(out/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:
        state=read(state_path);state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--run');parser.add_argument('--resolution',type=int,choices=[640,960],default=640);parser.add_argument('--reference');args=parser.parse_args()
    if args.prepare:prepare(args.resolution,args.reference)
    elif args.run:evaluate(Path(args.run))
    else:parser.error('Choose --prepare or --run with a sealed protocol')
