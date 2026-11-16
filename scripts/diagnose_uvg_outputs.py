"""Prespecified, bounded audit of final COCO outputs before product filtering."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
from PIL import Image
import torch
from torchvision.transforms import functional as TF
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_V2_Weights,MaskRCNN_ResNet50_FPN_Weights

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.vision import VisionEngine,VEHICLES
from smart_parking.uvg import require_development
from smart_parking.detection_diagnosis import diagnose


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def prepare():
    now=datetime.now(timezone.utc);run_id='UVG-OUTPUT-AUDIT-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/results'/run_id;out.mkdir(parents=True,exist_ok=False)
    ref=ROOT/'experiments/results/UVG-DETECTORS-20261026T131820602234Z';baseline=read(ref/'run.json')
    frames=[121,300,541];inputs=[ref/'run.json']
    for f in frames:inputs.extend([ref/f'input_{f:04d}.png',ref/f'truth_{f:04d}.json',ref/f'fasterrcnn_{f:04d}.json',ref/f'maskrcnn_{f:04d}.json'])
    paths=['scripts/diagnose_uvg_outputs.py','src/smart_parking/detection_diagnosis.py','tests/test_detection_diagnosis.py','src/smart_parking/positive_instances.py','src/smart_parking/vision.py']
    protocol=dict(run_id=run_id,prepared_at=now.isoformat(),seed=139,source_ids=['SRC-DS-019','SRC-DOC-021'],
        hypothesis='Preserved final COCO detections before product road-class/0.5 filtering reproduce the archived operating outputs and provide traceable class/score/localization signatures for supplied-positive misses, including frame300truck25.',
        frames=frames,input_size=[960,540],internal_max_side=960,confidence=.5,box_iou=.5,
        reference_run=baseline['run_id'],reference_folder=ref.relative_to(ROOT).as_posix(),
        input_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},
        implementation_hashes={p:digest(ROOT/p) for p in paths},weight_hashes=baseline['weight_hashes'],protected_hashes=baseline['protected_hashes'],
        reservation=baseline['reservation'],reservation_sha256=baseline['reservation_sha256'],
        question_selection='Fixed three already development-exposed frames;known large-truck miss plus temporal/context variation;not a fresh accuracy cohort',
        captured_outputs='Final post-NMS COCO outputs at the unchanged model head defaults, before app class/0.5 filters;not raw RPN/logits or all proposals',
        diagnostic_priority=['matched','one-to-one competition','same-class below operating score','other class at operating point','same-class localization gap','other class below operating score','unresolved after postprocessing'],
        gates=['Reconstructed product detections reproduce archived identities/order/boxes within0.001px/scores within0.00001',
               'Every supplied target has one signature and traceable output indices;eligible and smaller targets kept separate',
               'Frozen methods,weights,reference artifacts unchanged;no final source or learned target reads'],
        maximum_seconds=300,maximum_model_calls=6,model_training=False,production_promotion=False,
        boundary='Diagnostic evidence only;no threshold/class remap or new held-out/exhaustive precision/parking-occupancy accuracy claim')
    dump(out/'protocol.json',protocol);dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in paths})
    dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json'),sealed_before_model_calls=True));print(str(out/'protocol.json'))


def run(path):
    path=Path(path).resolve();out=path.parent;config=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve())
    assert digest(path)==read(out/'protocol_binding.json')['sha256']
    assert not (out/'progress.json').exists() and not (out/'run.json').exists(),'No silent replay of an existing diagnostic attempt'
    for p,h in {**config['input_hashes'],**config['implementation_hashes'],**config['weight_hashes'],**config['protected_hashes']}.items():assert digest(ROOT/p)==h,p
    require_development(ROOT/config['reservation'],config['reservation_sha256'],'https://ultravideo.fi/UVG-VCM/HighwayView/HighwayView.mp4')
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    state['active_validation_jobs']=[dict(run_id=config['run_id'],pid=os.getpid(),phase='Prespecified development output signature audit')];dump(state_path,state)
    timer=time.monotonic();start=datetime.now(timezone.utc);torch.manual_seed(139);np.random.seed(139)
    ref=ROOT/config['reference_folder'];rows=[];calls=0;head_settings={}
    try:
        for kind in ['fasterrcnn','maskrcnn']:
            engine=VisionEngine(kind,resolution=config['internal_max_side'])
            categories=(FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT if kind=='fasterrcnn' else MaskRCNN_ResNet50_FPN_Weights.DEFAULT).meta['categories']
            head=engine.model.roi_heads
            head_settings[kind]=dict(score_thresh=head.score_thresh,nms_thresh=head.nms_thresh,detections_per_img=head.detections_per_img,
                                     min_size=engine.model.transform.min_size,max_size=engine.model.transform.max_size,categories=categories)
            for f in config['frames']:
                if time.monotonic()-timer>300 or (out/'CANCEL').exists():raise InterruptedError('Bounded diagnostic cancelled/timed out')
                image=Image.open(ref/f'input_{f:04d}.png').convert('RGB');t=time.perf_counter()
                with torch.inference_mode():prediction=engine.model([TF.to_tensor(image)])[0]
                elapsed=time.perf_counter()-t;calls+=1;assert calls<=6
                outputs=[dict(output_index=i,class_id=int(label),label=categories[int(label)],score=float(score),box=box.tolist())
                         for i,(box,label,score) in enumerate(zip(prediction['boxes'],prediction['labels'],prediction['scores']))]
                reconstructed=[dict(label=VEHICLES[o['class_id']],box=o['box'],score=o['score']) for o in outputs if o['class_id'] in VEHICLES and o['score']>=.5]
                previous=read(ref/f'{kind}_{f:04d}.json')['predictions']
                reproduced=len(previous)==len(reconstructed) and all(p['label']==q['label'] and abs(p['score']-q['score'])<=.00001 and max(abs(a-b) for a,b in zip(p['box'],q['box']))<=.001 for p,q in zip(previous,reconstructed))
                targets=read(ref/f'truth_{f:04d}.json')['objects'];result=diagnose(targets,outputs)
                row=dict(model=kind,frame=f,head_output_count=len(outputs),product_output_count=len(reconstructed),operating_outputs_reproduced=reproduced,
                         latency_seconds=elapsed,outputs=outputs,diagnosis=result)
                rows.append(row);dump(out/f'{kind}_{f:04d}.json',row)
                dump(out/'progress.json',dict(model=kind,frame=f,model_calls=calls,maximum_calls=6,cancellable=True))
                print(json.dumps(dict(model=kind,frame=f,reproduced=reproduced,outputs=len(outputs))),flush=True);del prediction
            del engine
        summary={}
        for kind in ['fasterrcnn','maskrcnn']:
            all_rows=[o for r in rows if r['model']==kind for o in r['diagnosis']['rows']]
            eligible=[o for o in all_rows if o['eligible']]
            summary[kind]=dict(all_supplied=len(all_rows),eligible=len(eligible),eligible_signatures=dict(Counter(o['category'] for o in eligible)),
                               smaller_signatures=dict(Counter(o['category'] for o in all_rows if not o['eligible'])))
        selected=[dict(model=r['model'],**o) for r in rows if r['frame']==300 for o in r['diagnosis']['rows'] if o['track_id']==25]
        checks=dict(archived_operating_outputs_reproduced=all(r['operating_outputs_reproduced'] for r in rows),
            six_bounded_calls=calls==6,all_targets_have_signature=all(len(r['diagnosis']['rows'])==r['diagnosis']['operating_match']['provided_positives'] for r in rows),
            protected_hashes_unchanged=all(digest(ROOT/p)==h for p,h in {**config['protected_hashes'],**config['weight_hashes'],**config['input_hashes']}.items()),
            final_source_unopened=True,learned_forecast_targets_not_read=True)
        report=dict(config,started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,
                    head_settings=head_settings,summary=summary,selected_truck_evidence=selected,checks=checks,all_diagnostic_gates_passed=all(checks.values()),
                    scope='Postprocessed-output signatures on three reused development frames;not causal proof,new model accuracy,threshold selection or final acceptance')
        dump(out/'run.json',report);dump(ROOT/'reports/uvg_output_audit_latest.json',dict(run_id=config['run_id'],report=(out/'run.json').relative_to(ROOT).as_posix(),summary=summary,selected_truck_evidence=selected,checks=checks,all_diagnostic_gates_passed=report['all_diagnostic_gates_passed']))
    except BaseException as error:
        dump(out/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:
        state=read(state_path);state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--run');args=parser.parse_args()
    if args.prepare:prepare()
    elif args.run:run(args.run)
    else:parser.error('Choose --prepare or --run with a sealed protocol')
