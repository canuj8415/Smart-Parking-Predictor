"""Evaluate existing unmodified detector/classifier fusion on labelled slots."""
import csv,json,os,sys,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.vision import VisionEngine
from smart_parking.layout import read_pklot_xml
from smart_parking.occupancy_decisions import decision_metrics
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.provenance import digest
CLASSIFIER_RUN='OCCUPANCY-BROADER-20261025T084307397022Z'

def evaluate():
    started=datetime.now(timezone.utc);clock=time.perf_counter();run='OCCUPANCY-FUSION-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state.get('active_training_jobs') or state.get('active_validation_jobs'):raise ValueError('Another recorded experiment is active')
    manifest=ROOT/'data/manifests/region_broader_development_v1.json';reservation=json.loads(manifest.read_text());validation=[r for r in reservation['frames'] if r['split']=='validation'];assert len(validation)==24
    classifier_folder=ROOT/'experiments/results'/CLASSIFIER_RUN;reference=json.loads((classifier_folder/'run.json').read_text())
    if digest(manifest)!=reference['source_manifest_sha256']:raise ValueError('Development manifest changed')
    shared=ROOT/reservation['shared_final_manifest'];assert_holdout_closed(shared)
    frozen=json.loads((classifier_folder/'crop_predictions.json').read_text());lookup={(r['source_frame'],r['slot_id']):r for r in frozen}
    sources=['scripts/evaluate_broader_fusion.py','src/smart_parking/occupancy_decisions.py','src/smart_parking/vision.py','src/smart_parking/layout.py','src/smart_parking/analysis_identity.py']
    protocol=dict(run_id=run,started_at=started.isoformat(),source_ids=['SRC-DS-001','SRC-MOD-001','SRC-MOD-003'],seed='Deterministic existing inference; no randomized fitting',
        hypothesis='The existing detector-to-slot matching vetoes some classifier-only vacant decisions when a vehicle overlaps a slot, reducing false vacancy at a coverage cost',
        scope='Broader known-camera development labels only; prior classifier diagnostics informed this comparison. No independent final-test or detector-mAP claim.',
        source_manifest_sha256=digest(manifest),classifier_reference=CLASSIFIER_RUN,classifier_reference_sha256=digest(classifier_folder/'run.json'),
        checkpoint_sha256=digest(ROOT/'models/checkpoints/occupancy_resnet18.pt'),detector_sha256=digest(ROOT/'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth'),
        detector='Existing Faster R-CNN ResNet50FPNv2',resolution=640,detector_confidence=.5,uncertainty_thresholds=[.25,.75],
        algorithm='Unmodified VisionEngine and assign_occupancy. Geometry-only layout passed to engine; source occupancy answers retained separately for scoring.',
        diagnostic_gate=reference['diagnostic_gate'],
        missing_label_policy='Score only the same948labelled slots; retain396unknown labels without inventing answers or full-camera accuracy',
        code_sha256={p:digest(ROOT/p) for p in sources},shared_final_sha256=digest(shared),
        limitations=['Existing method on a reused development cohort, no tuning/fitting','Known-camera layouts provided; no discovery/alignment accuracy metric','Source occupancy labels have not had independent human verification','No vehicle box/instance mask labels, so detection accuracy is not evaluable'])
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    (folder/'implementation_sources.json').write_text(json.dumps({p:dict(sha256=digest(ROOT/p),source=(ROOT/p).read_text(encoding='utf-8')) for p in sources},indent=2),encoding='utf-8')
    state['active_validation_jobs']=[dict(run_id=run,pid=os.getpid(),kind='bounded existing fused-pipeline development validation')];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    try:
        engine=VisionEngine('fasterrcnn',resolution=640);records=[];frames=[];unknown=0;max_score_delta=0.
        for i,row in enumerate(validation):
            checks=json.loads((classifier_folder/'source_frame_checks.json').read_text());check=next(c for c in checks if c['image']==row['image'])
            assert digest(ROOT/row['image'])==check['image_sha256'];assert digest(ROOT/row['annotation'])==check['annotation_sha256']
            with Image.open(ROOT/row['image']) as image:
                image=image.convert('RGB');truth=read_pklot_xml(ROOT/row['annotation'],image.size)
                geometry=dict(schema_version=1,camera_id=truth['camera_id'],image_size=list(image.size),slots=[dict(id=s['id'],polygon=s['polygon']) for s in truth['slots']])
                if any('ground_truth_occupied' in s for s in geometry['slots']):raise ValueError('Answer label leaked to engine')
                result,overlay=engine.analyze(image,geometry,confidence=.5,uncertain_low=.25,uncertain_high=.75)
            (folder/f'frame_{i:02}.json').write_text(json.dumps(result,indent=2),encoding='utf-8');overlay.convert('RGB').save(folder/f'frame_{i:02}.jpg',quality=88)
            by_slot={s['slot_id']:s for s in result['slots']}
            for slot in truth['slots']:
                label=slot['ground_truth_occupied']
                if label is None:unknown+=1;continue
                prior=lookup[(row['image'],slot['id'])];pred=by_slot[slot['id']];delta=abs(prior['occupied_score']-pred['occupancy_score']);max_score_delta=max(max_score_delta,delta)
                if delta>1e-5:raise ValueError('Classifier probability changed materially')
                records.append(dict(source_frame=row['image'],annotation=row['annotation'],date=row['date'],camera_id=row['camera_id'],slot_id=slot['id'],label=label,
                    classifier_state=prior['selective_state'],fused_state=pred['state'],occupied_score=pred['occupancy_score'],vehicle_id=pred['vehicle_id'],slot_overlap=pred['slot_overlap']))
            frames.append(dict(source_frame=row['image'],detections=len(result['detections']),labelled_slots=check['labelled_slots'],all_slot_counts=result['counts'],input_identity=result['input_image'],geometry_identity=result['layout_identity']))
            print(f'{run}: frame{i+1}/24, detections{len(result["detections"])}',flush=True)
        assert len(records)==reference['metrics']['samples'];assert unknown==reference['missing_labels']
        def score(rows,key):return decision_metrics([r['label'] for r in rows],[r[key] for r in rows])
        baseline=score(records,'classifier_state');fused=score(records,'fused_state');per_camera={c:dict(classifier=score([r for r in records if r['camera_id']==c],'classifier_state'),fused=score([r for r in records if r['camera_id']==c],'fused_state')) for c in sorted({r['camera_id'] for r in records})}
        assert baseline['confusion']==reference['metrics']['selective_confusion']
        risk=fused['false_vacancy_fraction_of_vacant_predictions']
        passed=fused['predicted_vacant']>=20 and risk is not None and risk<=.01 and fused['coverage']>=.8 and all(v['fused']['false_vacancy_fraction_of_vacant_predictions']<=.02 for v in per_camera.values() if v['fused']['predicted_vacant']>=20)
        assert digest(ROOT/'models/checkpoints/occupancy_resnet18.pt')==protocol['checkpoint_sha256'];assert digest(ROOT/'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth')==protocol['detector_sha256'];assert digest(shared)==protocol['shared_final_sha256'];assert_holdout_closed(shared)
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,frames=24,labelled_slots=len(records),unlabelled_slots=unknown,
            classifier_only=baseline,fused=fused,per_camera=per_camera,diagnostic_gate_passed=passed,max_classifier_score_difference=max_score_delta,
            camera_ground_truth_complete=False,model_training_performed=False,production_algorithm_changed=False,final_images_decoded=0,final_annotations_decoded=0)
        for name,value in [('run.json',report),('predictions.json',records),('source_frames.json',frames),('changed_decisions.json',[r for r in records if r['classifier_state']!=r['fused_state']])]:
            (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
        with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
        (folder/'source_attribution.json').write_bytes((classifier_folder/'source_attribution.json').read_bytes())
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,classifier_only=baseline,fused=fused,diagnostic_gate_passed=passed,duration_seconds=report['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        (folder/'failure.json').write_text(json.dumps(dict(error=str(error),completed_run_counted=False),indent=2),encoding='utf-8');state=json.loads(state_path.read_text());raise
    finally:state['active_validation_jobs']=[];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')

if __name__=='__main__':
    lock=ROOT/'.cache/broader_fusion.lock';lock.parent.mkdir(exist_ok=True);fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:evaluate()
    finally:lock.unlink(missing_ok=True)
