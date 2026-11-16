"""Actual app-engine candidate check against frozen unchanged development fusion."""
import csv
import gc
import json
import sys
import time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.occupancy_expansion import member_name


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def metrics(rows):
    n=len(rows);empty=[r for r in rows if r['state']=='vacant']
    correct_empty=sum(r['label']==0 for r in empty)
    false_occupied=sum(r['state']=='occupied' and r['label']==0 for r in rows)
    uncertain=sum(r['state']=='uncertain' for r in rows)
    return dict(samples=n,vacant_predictions=len(empty),correct_vacant_predictions=correct_empty,
        false_vacant=len(empty)-correct_empty,false_occupied=false_occupied,uncertain=uncertain,
        correct_decisions=n-uncertain-(len(empty)-correct_empty)-false_occupied,
        decision_coverage=(n-uncertain)/n,vacancy_precision=correct_empty/len(empty) if empty else None)


def per_date(rows):
    groups=defaultdict(list)
    for r in rows:groups[(r['camera_id'],r['date'])].append(r)
    return [dict(camera_id=c,date=d,**metrics(g)) for (c,d),g in sorted(groups.items())]


def main():
    state_path=ROOT/'data/automation_state.json';state=read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    training=read('models/occupancy_expansion_candidate.json');assert training['validation_gate_passed']
    checkpoint=ROOT/training['candidate_checkpoint'];assert digest(checkpoint)==training['candidate_checkpoint_sha256']
    reference=read('models/pklot_fresh_fusion_baseline.json')
    dev_path=ROOT/'data/manifests/pklot_fresh_development_v1.json';development=read(dev_path)
    assert digest(dev_path)==reference['development_manifest_sha256']
    final_path=ROOT/'data/manifests/pklot_fresh_final_v2.json';assert_holdout_closed(final_path,root=ROOT)
    predictions_path=ROOT/'experiments/results'/training['run_id']/'candidate_validation_predictions.json'
    probabilities={(r['source_member'],r['slot_id']):r for r in read(predictions_path)}
    started=datetime.now(timezone.utc);rid='OCCUPANCY-EXPANDED-FUSION-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    paths=['scripts/evaluate_expanded_occupancy_fusion.py','src/smart_parking/vision.py','src/smart_parking/layout.py']
    hashes={p:digest(ROOT/p) for p in paths}
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=131,
        source_ids=['SRC-DS-001','SRC-MOD-001','SRC-MOD-002','SRC-MOD-003'],source_hashes=hashes,
        training_run=training['run_id'],candidate_checkpoint=training['candidate_checkpoint'],candidate_checkpoint_sha256=digest(checkpoint),
        unchanged_reference_run=reference['run_id'],reference_card_sha256=digest(ROOT/'models/pklot_fresh_fusion_baseline.json'),
        development_manifest_sha256=digest(dev_path),closed_final_manifest_sha256=digest(final_path),
        candidate_predictions_sha256=digest(predictions_path),
        detector_weight_hashes={p:digest(ROOT/p) for p in reference['weight_hashes'] if '/pretrained/' in p},
        hypothesis='Expanded head improves useful vacancy decisions in the actual app pipeline without worsening wrong-vacant, wrong-occupied or review burden on the same development frames.',
        detectors=['fasterrcnn','maskrcnn'],resolution=640,thresholds=[.5,.25,.75],
        preset_gates=['No overall or per-date false-vacant regression versus the same unchanged detector',
            'No overall or per-date false-occupied regression',
            'Retain at least all baseline correct vacant decisions overall and per date',
            'Uncertain total at most16; per-date at most unchanged+2',
            'Correct decisions at least unchanged overall; all detector gates must pass'],
        limits=dict(wall_seconds=900,frames_per_detector=12,torch_threads=4),
        limitations=['Development only; supplied correct geometry,2known cameras/3new dates',
            'This isolates a candidate classifier loaded into the real engine; main app default remains original',
            'No new final/live score or detector mAP/instance-mask metric','One paired comparison, not one run per frame'])
    dump(folder/'protocol.json',protocol)
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'),deadline_seconds=900)]
    dump(state_path,state);timer=time.perf_counter()
    try:
        import torch
        from PIL import Image
        from smart_parking.layout import read_pklot_xml
        from smart_parking.vision import VisionEngine
        torch.manual_seed(131);torch.set_num_threads(4)
        bundle=torch.load(checkpoint,map_location='cpu',weights_only=True)
        summaries={}
        for detector in protocol['detectors']:
            engine=VisionEngine(detector=detector,resolution=640)
            # Explicit experiment-local replacement. The product constructor and
            # production checkpoint are unchanged; result provenance is updated.
            engine.classifier.load_state_dict(bundle['state_dict']);engine.classifier.eval()
            engine.classifier_sha256=digest(checkpoint);engine.classifier_run_id=training['run_id']
            rows=[];max_delta=0.
            for frame_no,frame in enumerate(development['frames'],1):
                if (folder/'CANCEL').exists() or time.perf_counter()-timer>900:
                    raise InterruptedError('Candidate fusion cancellation/deadline')
                assert digest(ROOT/frame['image'])==frame['image_sha256']
                assert digest(ROOT/frame['annotation'])==frame['annotation_sha256']
                with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
                labelled=read_pklot_xml(ROOT/frame['annotation'],image.size)
                geometry={k:v for k,v in labelled.items() if k!='slots'}
                geometry['slots']=[dict(id=s['id'],polygon=s['polygon']) for s in labelled['slots']]
                result,overlay=engine.analyze(image,geometry,confidence=.5,uncertain_low=.25,uncertain_high=.75)
                frame_rows=[]
                for observation in result['slots']:
                    saved=probabilities[(member_name(frame['image']),observation['slot_id'])]
                    delta=abs(saved['probability_occupied']-observation['occupancy_score']);max_delta=max(max_delta,delta)
                    assert delta<1e-5
                    row=dict(frame=frame['image'],camera_id=frame['camera_id'],date=frame['date'],
                        label=saved['label'],image_sha256=frame['image_sha256'],**observation)
                    rows.append(row);frame_rows.append(row)
                dump(folder/detector/f'frame_{frame_no:02d}.json',dict(source_frame=frame,result=result))
                if any(r['state']=='vacant' and r['label']==1 for r in frame_rows):
                    overlay.save(folder/detector/f'false_vacant_frame_{frame_no:02d}.png')
                dump(folder/'progress.json',dict(detector=detector,frames_completed=frame_no,labelled_slots=len(rows)))
                print(json.dumps(dict(detector=detector,frame=frame_no,counts=result['counts'])),flush=True)
            assert len(rows)==720
            original=reference['detectors'][detector]
            current=metrics(rows);dates=per_date(rows)
            orig_dates={(r['camera_id'],r['date']):r for r in original['per_date']}
            comparisons=[(r,orig_dates[(r['camera_id'],r['date'])]) for r in dates]
            checks=dict(no_false_vacant_regression=current['false_vacant']<=original['overall']['false_vacant']
                    and all(a['false_vacant']<=b['false_vacant'] for a,b in comparisons),
                no_false_occupied_regression=current['false_occupied']<=original['overall']['false_occupied']
                    and all(a['false_occupied']<=b['false_occupied'] for a,b in comparisons),
                retain_correct_vacancies=current['correct_vacant_predictions']>=original['overall']['correct_vacant_predictions']
                    and all(a['correct_vacant_predictions']>=b['correct_vacant_predictions'] for a,b in comparisons),
                review_burden_within_limit=current['uncertain']<=16 and all(a['uncertain']<=b['uncertain']+2 for a,b in comparisons),
                correct_decisions_noninferior=current['correct_decisions']>=original['overall']['correct_decisions'])
            summaries[detector]=dict(overall=current,per_date=dates,checks=checks,development_gate_passed=all(checks.values()),
                max_classifier_probability_delta=max_delta,
                remaining_false_vacant=[r for r in rows if r['state']=='vacant' and r['label']==1])
            dump(folder/detector/'development_predictions.json',rows)
            del engine,image,overlay,result;gc.collect()
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        assert all(digest(ROOT/p)==h for p,h in protocol['detector_weight_hashes'].items())
        assert digest(checkpoint)==protocol['candidate_checkpoint_sha256']
        assert digest(final_path)==protocol['closed_final_manifest_sha256'];assert_holdout_closed(final_path,root=ROOT)
        outcome=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-timer,
            detectors=summaries,validation_gate_passed=all(c['development_gate_passed'] for c in summaries.values()),
            production_promoted=False,final_images_or_labels_read=0)
        dump(folder/'run.json',outcome);dump(ROOT/'models/occupancy_expansion_fusion_candidate.json',outcome)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Expanded head actual app fusion development comparison',started_at=started.isoformat(),
            finished_at=outcome['finished_at'],source_ids=';'.join(protocol['source_ids']),split_ids='Same12development photos/720labels;final6closed',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Actual Faster/Mask R-CNN + expanded ResNet18head',
            epochs=0,random_seed=131,hardware='CPU/Torch4threads',execution_environment=sys.version.split()[0],training_duration=outcome['duration_seconds'],
            evaluation_metrics=json.dumps(summaries),logs=folder.relative_to(ROOT).as_posix(),checkpoints=training['candidate_checkpoint'],
            code_revision_basis='e1c6461 plus frozen candidate/fusion sources',implementation_sha256=hashes[paths[0]],
            conclusions='Both-detector development gate='+str(outcome['validation_gate_passed'])+'; no app promotion or final/live score')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,gate=outcome['validation_gate_passed'],detectors=summaries),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False))
        state=read(state_path);raise
    finally:
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
