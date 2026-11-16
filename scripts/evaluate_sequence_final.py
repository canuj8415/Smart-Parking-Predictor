"""One-use frozen partial-foreground final exam; no retuning or retry on failure."""
import csv,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.vision import VisionEngine
from smart_parking.flow import GateCounter
from smart_parking.flow_continuation import ContinuationGateCounter
from smart_parking.labelled_sequence import infer_labelled_frame
from smart_parking.sequence_setup import setup_gate
from smart_parking.sequence_evaluation import evaluate_cached_sequence
from smart_parking.sequence_holdouts import evaluate_sequence_once,assert_sequence_closed


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    torch.set_num_threads(4);torch.manual_seed(114)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_validation_jobs'] or state['active_training_jobs']:raise RuntimeError('Another recorded job active')
    manifest=ROOT/'data/manifests/davis_car_roundabout_final_v2.json'
    parent=ROOT/'data/manifests/davis_car_sequences_v2.json'
    collection='https://data.vision.ee.ethz.ch/csergi/share/davis/DAVIS-2017-trainval-480p.zip'
    assert_sequence_closed(manifest,parent,collection)  # Metadata only; no pixels.
    development=ROOT/'experiments/results/FLOW-CONTINUATION-20261025T145043485311Z/run.json'
    selected=json.loads(development.read_text(encoding='utf-8'))
    if not selected['counting_final_qualified']:raise ValueError('Development qualification failed')
    # Require the completed meaningful regression gate before consuming final data.
    tests=ROOT/'experiments/evidence/HEARTBEAT-20261025T144531Z/unit_tests_final.txt'
    text=tests.read_text(encoding='utf-8-sig')
    if 'Ran 159 tests' not in text or not text.rstrip().endswith('OK'):raise ValueError('Required final-loader regression checks have not passed')
    for p,h in selected['source_hashes'].items():
        if digest(ROOT/p)!=h:raise ValueError('Selected development implementation changed')
    engine=VisionEngine('fasterrcnn')
    if engine.weight_sha256!=selected['detector_sha256']:raise ValueError('Detector weights changed')
    started=datetime.now(timezone.utc);run_id='FLOW-SEQUENCE-FINAL-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run_id;folder.mkdir(parents=True,exist_ok=False)
    paths=['scripts/evaluate_sequence_final.py','src/smart_parking/labelled_sequence.py','src/smart_parking/sequence_holdouts.py',
        'src/smart_parking/sequence_setup.py','src/smart_parking/sequence_evaluation.py','src/smart_parking/sequence_reference.py',
        'src/smart_parking/flow.py','src/smart_parking/flow_continuation.py','src/smart_parking/vision.py']
    hashes={p:digest(ROOT/p) for p in paths}
    protocol=dict(run_id=run_id,started_at=started.isoformat(),seed=114,source_ids=['SRC-DS-012','SRC-MOD-001'],
        code_revision_basis='f284514 plus sealed selected development/final sources',source_hashes=hashes,
        hypothesis='Frozen identity-only weak continuation retains the selected foreground object and recovers its rule-specific image-line crossings on a reserved independent sequence.',
        selection_run=selected['run_id'],selection_run_sha256=digest(development),
        final_manifest_sha256=digest(manifest),parent_manifest_sha256=digest(parent),
        sequence='car-roundabout',expected_frames=75,setup_frames=list(range(5)),scored_frames=[5,74],
        setup_rule='Unchanged setup_gate: publisher object1 bbox on frames0..4, median x plus initial-motion sign times max(24,half median width), clipped24..width-25; full-height gate with24pixel margins. Below2px motion or missing setup object: unavailable, no alternate gate.',
        detector='Frozen Faster R-CNN ResNet50FPNv2 confidence0.5; high-confidence births0.7; continuation-only0.5',
        detector_sha256=selected['detector_sha256'],prespecified_gate=selected['prespecified_gate'],
        extra_gate='No more unmatched predicted events than predeclared unchanged default tracker; this is not exhaustive false-positive precision',
        comparator='Frozen default GateCounter, identical detections/reference/setup rule',
        measurements='Same IoU>=0.5 selected-object frame recall, matched/dominant identity coverage, reference crossing recovery within2frames, no exhaustive precision',
        limitations=['One publisher-selected foreground object; object1 semantic vehicle check reported separately from numeric scoring',
            'First5frames are label-assisted setup, not scored; all75frames consumed on first callback, including failure',
            'Unknown source fps and camera motion; no physical-time/speed/parking entrance accuracy',
            'A small one-sequence exam, no universal accuracy, exhaustive traffic mAP or occupancy claims',
            'Any missing positive reference leaves event recall unavailable; do not replace the gate or repeat changed methods',
            'No project training on DAVIS; upstream pretrained-data overlap unaudited'])
    dump(folder/'protocol.json',protocol)
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    selection=dict(counting_final_qualified=True,metrics=selected['metrics'],collection_identity=collection,
        protocol_sha256=digest(folder/'protocol.json'),source_hashes=hashes,
        checkpoint_hashes={'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth':selected['detector_sha256']})
    dump(folder/'selection.json',selection)
    state['active_validation_jobs']=[dict(run_id=run_id,cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    clock=time.perf_counter()
    def evaluate(rows):
        if len(rows)!=75 or {r['sequence'] for r in rows}!={'car-roundabout'}:raise ValueError('Unexpected final membership')
        records=[];config=None
        with (folder/'frame_records.partial.jsonl').open('x',encoding='utf-8',newline='\n') as journal:
            for row in rows:
                if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested; final remains consumed')
                record=infer_labelled_frame(row,ROOT,engine);records.append(record)
                journal.write(json.dumps(record)+'\n');journal.flush();os.fsync(journal.fileno())
                if row['frame_index']==4:
                    config,setup=setup_gate([dict(frame_index=r['frame_index'],objects=r['reference_objects']) for r in records],rows[0]['image_size'])
                    dump(folder/'setup.json',dict(config=config,setup=setup))
                dump(folder/'progress.json',dict(processed_frames=len(records),last_frame_index=row['frame_index'],final_sequence_consumed=True))
                if row['frame_index']%15==0:print(f'{run_id}: processed {len(records)}/75',flush=True)
        if config is None:raise ValueError('Setup unavailable')
        base,_=evaluate_cached_sequence(records,rows[0]['image_size'],config,GateCounter,cancel_file=folder/'CANCEL')
        candidate,replay=evaluate_cached_sequence(records,rows[0]['image_size'],dict(config,continuation_confidence=.5),ContinuationGateCounter,cancel_file=folder/'CANCEL')
        m=candidate['metrics'];g=protocol['prespecified_gate']
        gates=dict(positive_reference=m['reference_events']>=g['min_reference_events'],
            crossing_recovery=m['annotated_event_recall'] is not None and m['annotated_event_recall']>=g['min_event_recall'],
            detection_coverage=m['annotated_car_box_recall'] is not None and m['annotated_car_box_recall']>=g['min_box_recall'],
            track_coverage=m['matched_track_coverage'] is not None and m['matched_track_coverage']>=g['min_track_coverage'],
            dominant_identity=m['dominant_track_fraction'] is not None and m['dominant_track_fraction']>=g['min_dominant_track_fraction'],
            no_additional_unmatched_events=m['unmatched_predicted_events']<=base['metrics']['unmatched_predicted_events'])
        result=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            gate_config=config,setup=setup,metrics=m,baseline=base,reference_events=candidate['reference_events'],
            predicted_events=candidate['predicted_events'],weak_continuations=candidate['weak_continuations'],
            final_gate_checks=gates,final_gate_passed=all(gates.values()),reserved_sequence_consumed=True,
            model_training_performed=False,production_promoted=False,production_weights_changed=False)
        if not all(digest(ROOT/p)==h for p,h in hashes.items()):raise ValueError('Frozen final source changed during evaluation')
        dump(folder/'frame_records.json',records);dump(folder/'replay.json',replay);dump(folder/'run.json',result)
        with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['frame_index','visible','detected','matched_track_id','weak_observations','entries','exits']);writer.writeheader()
            for r in replay:writer.writerow({k:r[k] for k in ['frame_index','visible','detected','matched_track_id']} | dict(weak_observations=r['tracking']['weak_observations_this_frame']) | r['tracking']['counts'])
        return result
    try:
        result=evaluate_sequence_once(manifest,parent,folder/'selection.json',folder/'protocol.json',run_id,evaluate,
            collection_identity=collection,expected_manifest_sha256=protocol['final_manifest_sha256'],expected_selection_sha256=digest(folder/'selection.json'))
        path=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with path.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run_id,run_type='One-use guarded reserved whole-sequence final evaluation',started_at=protocol['started_at'],finished_at=result['finished_at'],
            source_ids='SRC-DS-012;SRC-MOD-001',split_ids='car-roundabout75whole-sequence final; first5setup/70scored; now consumed',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Frozen Faster R-CNN ResNet50 + identity-only continuation',model_version=selected['detector_sha256'],epochs=0,batch_size=1,random_seed=114,
            hardware='CPU; Torch4/BLAS1/OMP2/MKL2',execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(result['metrics']),
            logs=folder.relative_to(ROOT).as_posix(),checkpoints='No new weights',code_revision_basis=protocol['code_revision_basis'],implementation_sha256=hashes[paths[0]],
            conclusions='Final gate='+str(result['final_gate_passed'])+'; source/whole sequence consumed; no changed-method reuse; partial foreground/image-plane scope only')
        with path.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run_id);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run_id
        print(json.dumps(dict(run_id=run_id,metrics=result['metrics'],gate_checks=result['final_gate_checks']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False,final_may_be_consumed=True));state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:
        claims=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data/sequence_holdout_claims').glob('*.claim.json')]
        if any(c['run_id']==run_id for c in claims):state['davis_sequences'].update(final_pixels_unopened=False,final_sequence_consumed=True,final_run=run_id)
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
