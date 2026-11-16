"""Frozen labelled-foreground development check in frame-index units, not seconds."""
import csv,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import Image
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.flow import GateCounter
from smart_parking.vision import VisionEngine
from smart_parking.sequence_reference import reference_crossings,match_reference_events,box_iou
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    torch.set_num_threads(4);torch.manual_seed(111)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another recorded job active')
    manifest=ROOT/'data/manifests/davis_car_sequences_v2.json';rows=[r for r in json.loads(manifest.read_text())['frames'] if r['sequence']=='car-turn'];assert len(rows)==80
    width,height=rows[0]['image_size'];config=GateCounter(image_size=[width,height],line=[[width//2,24],[width//2,height-25]],time_unit='frames',max_gap_frames=1).config
    started=datetime.now(timezone.utc);run='DAVIS-FOREGROUND-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    files=['scripts/evaluate_davis_development.py','src/smart_parking/sequence_reference.py','src/smart_parking/flow.py','src/smart_parking/vision.py']
    hashes={p:digest(ROOT/p) for p in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),source_ids=['SRC-DS-012','SRC-MOD-001'],seed=111,
        hypothesis='A frozen detector/tracker can recover the publisher-labelled car and its rule-specific image-plane crossing in a real annotated sequence, without treating unlabelled background as exhaustive negatives.',
        sequence='car-turn',setup_frames=list(range(5)),scored_frames=[5,79],timebase='original frame indices; physical fps unknown; no fabricated seconds',gate_config=config,
        setup='Frame0 visually inspected as car; publisher foreground object1. Gate fixed at image mid-width, y24..height-25, not selected from future annotation trajectory.',
        detector='Existing Faster R-CNN ResNet50FPNv2',detector_sha256='dd69338a24b8d7381807e247652bdc356325bcbaf1cd3e092e00e0a1a58706bf',detector_confidence=.5,
        reference_rule='Publisher object1 mask bbox centre; known object ID, no predicted association. Same finite-line/deadband/two-stable-observation geometry; missing reference resets memory.',
        metrics='Annotated-car box recall IoU>=0.5; matched track coverage/ID switches; annotated crossing recovery within2frames with same type and track/object IoU association. Extra predicted events unassessable, no exhaustive precision/mAP/flow accuracy.',
        diagnostic_gate='Annotated-car recall>=0.90; if any annotated crossing, recover>=0.80. Development diagnostic only; no parameter fitting or final sequence use.',
        source_manifest_sha256=digest(manifest),source_hashes=hashes,code_revision_basis='b0389db plus sealed exact source snapshots',
        limitations=['One selected foreground car; annotations not exhaustive traffic ground truth','Gate is an image-plane line, not a parking entrance; camera motion can create crossings','Unknown fps: no physical speed, seconds or real-time throughput claim','Upstream COCO/DAVIS image overlap not audited; no project training on DAVIS','Reserved car-roundabout sequence pixels/labels remain unopened'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        engine=VisionEngine('fasterrcnn');assert engine.weight_sha256==protocol['detector_sha256'];tracker=GateCounter(**config)
        observations=[];references=[];predicted_events=[];match_map={};recall=[];matched_track=[];frame_records=[]
        for row in rows:
            frame=row['frame_index']
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
            assert digest(ROOT/row['image'])==row['image_sha256'] and digest(ROOT/row['annotation'])==row['annotation_sha256']
            with Image.open(ROOT/row['image']) as image:result,_=engine.analyze(image.convert('RGB'),None,confidence=.5)
            tracking=tracker.update(result['detections'],frame,image_size=row['image_size']);predicted_events.extend(tracking['events'])
            with Image.open(ROOT/row['annotation']) as mask:mask=np.asarray(mask)==1
            ys,xs=np.where(mask);objects=[];best_iou=0.;track_id=None;detected=False
            if len(xs):
                box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];objects=[dict(object_id=1,box=box)]
                detected=any(box_iou(d['box'],box)>=.5 for d in result['detections'])
                ranked=sorted([(box_iou(t['box'],box),t['track_id']) for t in tracking['tracks']],reverse=True)
                if ranked:best_iou,track_id=ranked[0]
                if best_iou>=.5:match_map[(frame,track_id)]=1
                else:track_id=None
                if frame>=5:recall.append(detected);matched_track.append((frame,track_id))
            references.append(dict(frame_index=frame,objects=objects))
            observations.append(dict(frame_index=frame,reference_car_present=bool(objects),reference_car_detected=detected,matched_track_id=track_id,matched_track_iou=best_iou,predicted_entries=tracker.entries,predicted_exits=tracker.exits))
            frame_records.append(dict(frame_index=frame,result=result,tracking=tracking,reference_objects=objects))
            with (folder/'frame_records.partial.jsonl').open('a',encoding='utf-8',newline='\n') as journal:
                journal.write(json.dumps(dict(**frame_records[-1],summary_row=observations[-1]))+'\n');journal.flush()
            if frame%20==0:print(f'{run}: frame {frame}/79',flush=True)
            dump(folder/'progress.json',dict(processed_frames=frame+1,last_frame_index=frame))
        ref_events=[e for e in reference_crossings(references,config) if e['frame_index']>=5];pred_events=[e for e in predicted_events if e['frame_index']>=5]
        event_metrics=match_reference_events(ref_events,pred_events,match_map)
        ids=[tid for _,tid in matched_track if tid is not None];counts={tid:ids.count(tid) for tid in set(ids)}
        switches=sum(a[1] is not None and b[1] is not None and b[0]==a[0]+1 and a[1]!=b[1] for a,b in zip(matched_track,matched_track[1:]))
        car_recall=sum(recall)/len(recall) if recall else None;passed=car_recall is not None and car_recall>=.9 and (event_metrics['annotated_event_recall'] is None or event_metrics['annotated_event_recall']>=.8)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,metrics=dict(scored_visible_car_frames=len(recall),annotated_car_detected_frames=sum(recall),annotated_car_box_recall=car_recall,
            matched_tracking_frames=len(ids),dominant_track_fraction=max(counts.values())/len(recall) if counts else None,matched_consecutive_id_switches=switches,**event_metrics),reference_events=ref_events,predicted_events=pred_events,diagnostic_gate_passed=passed,final_sequence_evaluated=False,model_training_performed=False,production_weights_changed=False)
        assert all(digest(ROOT/p)==h for p,h in hashes.items());dump(folder/'run.json',report);dump(folder/'frame_records.json',frame_records)
        with (folder/'observations.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(observations[0]));w.writeheader();w.writerows(observations)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,metrics=report['metrics'],gate=passed,duration=report['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False));state=json.loads(state_path.read_text());raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)

if __name__=='__main__':main()
