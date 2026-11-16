"""One predeclared setup-only gate experiment on saved development detections."""
import csv, json, sys, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.flow import GateCounter
from smart_parking.sequence_setup import setup_gate
from smart_parking.sequence_reference import box_iou, reference_crossings, match_reference_events
from smart_parking.provenance import digest


def dump(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    state_path = ROOT/'data/automation_state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_validation_jobs'] or state['active_training_jobs']:
        raise RuntimeError('Another recorded job active')
    started = datetime.now(timezone.utc)
    run_id = 'DAVIS-SETUP-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT/'experiments/results'/run_id
    folder.mkdir(parents=True, exist_ok=False)
    cache = ROOT/'experiments/results/DAVIS-FOREGROUND-20261025T113304928428Z/frame_records.json'
    manifest = ROOT/'data/manifests/davis_car_sequences_v2.json'
    paths = ['scripts/replay_davis_setup.py', 'src/smart_parking/sequence_setup.py',
             'src/smart_parking/sequence_reference.py', 'src/smart_parking/flow.py']
    hashes = {p: digest(ROOT/p) for p in paths}
    protocol = dict(run_id=run_id, started_at=started.isoformat(), seed=112,
        source_ids=['SRC-DS-012', 'SRC-MOD-001'], code_revision_basis='a27bc9b plus exact sealed sources',
        hypothesis='A single gate placed ahead of setup-only foreground motion yields a positive annotated image-line crossing with the unchanged conservative tracker.',
        setup_rule='Use ONLY labelled object1 boxes at frames0..4. Vertical x=median setup centre + sign(last-first x)*max(24, half median box width), clipped to24..width-25. y24..height-25. Below2px initial motion: unavailable. No gate search or alternate retry.',
        scored_frames=[5, 79], sequence='car-turn', split='Reused development sequence; no fresh final claim',
        detector='Cached Faster R-CNN ResNet50FPNv2 detections, no inference or training',
        detector_sha256='dd69338a24b8d7381807e247652bdc356325bcbaf1cd3e092e00e0a1a58706bf',
        cache_path=cache.relative_to(ROOT).as_posix(), cache_sha256=digest(cache),
        source_manifest_sha256=digest(manifest), source_hashes=hashes,
        prespecified_gate=dict(min_reference_events=1, min_event_recall=.8, min_box_recall=.9,
                              min_track_coverage=.9, min_dominant_track_fraction=.8),
        limitations=['Label-assisted setup, not automatic entrance discovery',
                     'Single repeatedly observed foreground car; masks are partial traffic labels',
                     'Image-plane line; camera motion can cause crossings; no physical fps/time claim',
                     'Original midpoint result already seen; this is another development test',
                     'No car-roundabout pixels or annotation values opened'])
    dump(folder/'protocol.json', protocol)
    dump(folder/'implementation_sources.json', {p: dict(sha256=h, source=(ROOT/p).read_text(encoding='utf-8')) for p, h in hashes.items()})
    state['active_validation_jobs'] = [dict(run_id=run_id, cancel_file=str(folder/'CANCEL'))]
    dump(state_path, state)
    clock = time.perf_counter()
    try:
        frames = json.loads(cache.read_text(encoding='utf-8'))
        assert [r['frame_index'] for r in frames] == list(range(80))
        members = [r for r in json.loads(manifest.read_text(encoding='utf-8'))['frames'] if r['sequence']=='car-turn']
        setup_rows = [dict(frame_index=r['frame_index'], objects=r['reference_objects']) for r in frames[:5]]
        config, setup = setup_gate(setup_rows, members[0]['image_size'])
        dump(folder/'setup.json', dict(config=config, setup=setup))  # frozen before replay
        tracker = GateCounter(**config)
        references, predicted, matches, track_ids, recalls, journal = [], [], {}, [], [], []
        for row in frames:
            if (folder/'CANCEL').exists():
                raise InterruptedError('Cancellation requested')
            frame = row['frame_index']
            tracking = tracker.update(row['result']['detections'], frame, image_size=members[0]['image_size'])
            references.append(dict(frame_index=frame, objects=row['reference_objects']))
            predicted.extend(tracking['events'])
            ident = None
            visible = bool(row['reference_objects'])
            detected = False
            if visible:
                box = row['reference_objects'][0]['box']
                detected = any(box_iou(d['box'], box)>=.5 for d in row['result']['detections'])
                ranked = sorted([(box_iou(t['box'], box), t['track_id']) for t in tracking['tracks']], reverse=True)
                if ranked and ranked[0][0]>=.5:
                    ident = ranked[0][1]
                    matches[(frame, ident)] = 1
                if frame>=5:
                    recalls.append(detected)
                    track_ids.append(ident)
            journal.append(dict(frame_index=frame, matched_track_id=ident, visible=visible, detected=detected,
                                tracking=tracking))
        ref_events = [e for e in reference_crossings(references, config) if e['frame_index']>=5]
        pred_events = [e for e in predicted if e['frame_index']>=5]
        event_metrics = match_reference_events(ref_events, pred_events, matches)
        ids = [i for i in track_ids if i is not None]
        counts = Counter(ids)
        metrics = dict(scored_visible_car_frames=len(recalls), annotated_car_box_recall=sum(recalls)/len(recalls),
                       matched_track_coverage=len(ids)/len(recalls), dominant_track_fraction=max(counts.values())/len(recalls),
                       **event_metrics)
        g = protocol['prespecified_gate']
        gate_checks = dict(positive_reference=metrics['reference_events']>=g['min_reference_events'],
            crossing_recovery=metrics['annotated_event_recall'] is not None and metrics['annotated_event_recall']>=g['min_event_recall'],
            detection_coverage=metrics['annotated_car_box_recall']>=g['min_box_recall'],
            track_coverage=metrics['matched_track_coverage']>=g['min_track_coverage'],
            dominant_identity=metrics['dominant_track_fraction']>=g['min_dominant_track_fraction'])
        result = dict(protocol, finished_at=datetime.now(timezone.utc).isoformat(), duration_seconds=time.perf_counter()-clock,
            gate_config=config, setup=setup, setup_sha256=digest(folder/'setup.json'), metrics=metrics,
            reference_events=ref_events, predicted_events=pred_events, gate_checks=gate_checks,
            counting_final_qualified=all(gate_checks.values()), final_sequence_evaluated=False,
            model_training_performed=False, detector_inference_performed=False, production_weights_changed=False)
        assert digest(cache)==protocol['cache_sha256'] and all(digest(ROOT/p)==h for p,h in hashes.items())
        dump(folder/'replay.json', journal)
        dump(folder/'run.json', result)
        with (folder/'observations.csv').open('w', encoding='utf-8', newline='') as stream:
            writer=csv.DictWriter(stream, fieldnames=['frame_index','matched_track_id','visible','detected','entries','exits'])
            writer.writeheader()
            for r in journal:
                writer.writerow({k:r[k] for k in ['frame_index','matched_track_id','visible','detected']} | r['tracking']['counts'])
        registry_path=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry_path.open(encoding='utf-8-sig', newline='') as stream:
            fields=csv.DictReader(stream).fieldnames
        registry=dict(experiment_id=run_id, run_type='Predeclared setup-only development replay', started_at=protocol['started_at'],
            finished_at=result['finished_at'], source_ids='SRC-DS-012;SRC-MOD-001', split_ids='car-turn development only',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(), architecture=protocol['detector'],
            model_version=protocol['detector_sha256'], epochs=0, batch_size=1, random_seed=112,
            hardware='CPU; cached detections; no model loaded', execution_environment=sys.version.split()[0],
            training_duration=result['duration_seconds'], evaluation_metrics=json.dumps(metrics), logs=folder.relative_to(ROOT).as_posix(),
            checkpoints='No new weights', code_revision_basis=protocol['code_revision_basis'],
            implementation_sha256=hashes[paths[0]], conclusions='Counting qualification '+str(result['counting_final_qualified'])+'; partial-label image-plane development scope only; final closed')
        with registry_path.open('a',encoding='utf-8',newline='') as stream:
            csv.DictWriter(stream, fieldnames=fields).writerow({k:registry.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'))
        state['completed_run_ids'].append(run_id)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']))
        state['last_completed_run']=run_id
        print(json.dumps(dict(run_id=run_id, metrics=metrics, gate_checks=gate_checks),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error), completed_run_counted=False))
        state=json.loads(state_path.read_text(encoding='utf-8'))
        raise
    finally:
        state['active_validation_jobs']=[]
        dump(state_path,state)


if __name__=='__main__':
    main()
