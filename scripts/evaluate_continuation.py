"""One frozen, paired development experiment; no neural inference or final data."""
import csv,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.flow import GateCounter
from smart_parking.flow_continuation import ContinuationGateCounter
from smart_parking.sequence_evaluation import evaluate_cached_sequence
from smart_parking.provenance import digest


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_validation_jobs'] or state['active_training_jobs']:raise RuntimeError('Another recorded job active')
    started=datetime.now(timezone.utc);run_id='FLOW-CONTINUATION-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run_id;folder.mkdir(parents=True,exist_ok=False)
    prior=ROOT/'experiments/results/DAVIS-SETUP-20261025T141839144041Z'
    previous=json.loads((prior/'run.json').read_text(encoding='utf-8'))
    cache=ROOT/previous['cache_path'];config=previous['gate_config']
    paths=['scripts/evaluate_continuation.py','src/smart_parking/sequence_evaluation.py',
           'src/smart_parking/flow_continuation.py','src/smart_parking/flow.py','src/smart_parking/sequence_reference.py']
    hashes={p:digest(ROOT/p) for p in paths}
    assert hashes['src/smart_parking/flow.py']=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    protocol=dict(run_id=run_id,started_at=started.isoformat(),seed=113,source_ids=['SRC-DS-012','SRC-MOD-001'],
        hypothesis='Weak-confidence boxes can preserve unambiguous existing identity while erasing crossing memory, repairing frame26fragmentation without extra crossings or weak births.',
        code_revision_basis='f284514 plus exact sealed sources',source_hashes=hashes,
        cache_path=cache.relative_to(ROOT).as_posix(),cache_sha256=digest(cache),
        source_manifest_sha256=previous['source_manifest_sha256'],setup_sha256=previous['setup_sha256'],
        baseline_run=previous['run_id'],baseline_run_sha256=digest(prior/'run.json'),
        gate_config=config,continuation_confidence=.5,
        policy='High births>=0.7; continuation>=0.5only for existing mutually nearest unambiguous tracks, no competition with high association; class-agnostic dedup. Weak observation resets crossing memory before and after update. Actual missing observation/long gap still drops identity. No modified scores.',
        prespecified_gate=previous['prespecified_gate'],extra_gate='No additional unmatched predicted events vs frozen baseline; no weak new identity or weak-triggered count in synthetic regression tests',
        sequence='car-turn',split='Reused labelled development frames0..79; setup0..4, scored5..79',
        detector_sha256=previous['detector_sha256'],detector_inference_performed=False,model_training_performed=False,
        limitations=['One repeated labelled car; partial foreground masks; no exhaustive precision/mAP',
                     'Gate x694 fixed from earlier five-frame setup; no line change',
                     'Camera movement and unknown fps: image-plane crossings only, not parking entrance/time/speed accuracy',
                     'Hypothesis informed by reused development error; reserved car-roundabout unopened'])
    dump(folder/'protocol.json',protocol)
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run_id,cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    clock=time.perf_counter()
    try:
        records=json.loads(cache.read_text(encoding='utf-8'));assert [r['frame_index'] for r in records]==list(range(80))
        baseline,base_journal=evaluate_cached_sequence(records,config['image_size'],config,GateCounter,cancel_file=folder/'CANCEL')
        assert baseline['metrics']==previous['metrics'],'Paired baseline must reproduce the prior scoring exactly'
        candidate,journal=evaluate_cached_sequence(records,config['image_size'],dict(config,continuation_confidence=.5),ContinuationGateCounter,cancel_file=folder/'CANCEL')
        m=candidate['metrics'];g=protocol['prespecified_gate']
        gates=dict(positive_reference=m['reference_events']>=g['min_reference_events'],
            crossing_recovery=m['annotated_event_recall'] is not None and m['annotated_event_recall']>=g['min_event_recall'],
            detection_coverage=m['annotated_car_box_recall']>=g['min_box_recall'],
            track_coverage=m['matched_track_coverage']>=g['min_track_coverage'],
            dominant_identity=m['dominant_track_fraction']>=g['min_dominant_track_fraction'],
            no_additional_unmatched_events=m['unmatched_predicted_events']<=baseline['metrics']['unmatched_predicted_events'])
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            metrics=m,baseline=baseline,reference_events=candidate['reference_events'],predicted_events=candidate['predicted_events'],
            weak_continuations=candidate['weak_continuations'],gate_checks=gates,counting_final_qualified=all(gates.values()),
            final_sequence_evaluated=False,production_promoted=False,production_weights_changed=False)
        assert all(digest(ROOT/p)==h for p,h in hashes.items()) and digest(cache)==protocol['cache_sha256']
        dump(folder/'replay.json',journal);dump(folder/'run.json',report)
        with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['frame_index','baseline_track_id','candidate_track_id','weak_observations','entries','exits']);writer.writeheader()
            for b,r in zip(base_journal,journal):
                writer.writerow(dict(frame_index=r['frame_index'],baseline_track_id=b['matched_track_id'],candidate_track_id=r['matched_track_id'],weak_observations=r['tracking']['weak_observations_this_frame'],**r['tracking']['counts']))
        path=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with path.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run_id,run_type='Paired cached weak-confidence identity-only continuation development',started_at=protocol['started_at'],
            finished_at=report['finished_at'],source_ids='SRC-DS-012;SRC-MOD-001',split_ids=protocol['split'],configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Frozen detector cache + conservative identity-only continuation',model_version=protocol['detector_sha256'],epochs=0,batch_size=1,random_seed=113,
            hardware='CPU; no model inference',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(m),logs=folder.relative_to(ROOT).as_posix(),
            checkpoints='No new weights',code_revision_basis=protocol['code_revision_basis'],implementation_sha256=hashes[paths[0]],
            conclusions='Development qualification='+str(report['counting_final_qualified'])+'; partial-foreground reused-development evidence; no final evaluation/promotion')
        with path.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run_id)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run_id
        print(json.dumps(dict(run_id=run_id,metrics=m,gate_checks=gates,weak_continuations=candidate['weak_continuations']),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False));state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
