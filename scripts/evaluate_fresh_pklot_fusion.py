"""Measure unchanged app fusion on fixed DEVELOPMENT data, leaving final closed."""
import csv
import gc
import json
import math
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.provenance import digest


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def metrics(rows):
    n = len(rows)
    empty = [r for r in rows if r['state'] == 'vacant']
    occupied = [r for r in rows if r['state'] == 'occupied']
    uncertain = sum(r['state'] == 'uncertain' for r in rows)
    correct_empty = sum(r['label'] == 0 for r in empty)
    correct_occupied = sum(r['label'] == 1 for r in occupied)
    decided = n - uncertain
    true_vacant = sum(r['label'] == 0 for r in rows)
    return dict(samples=n, vacant_labels=true_vacant, occupied_labels=n-true_vacant,
        vacant_predictions=len(empty), correct_vacant_predictions=correct_empty,
        false_vacant=len(empty)-correct_empty,
        vacancy_precision=correct_empty/len(empty) if empty else None,
        vacancy_recall=correct_empty/true_vacant if true_vacant else None,
        occupied_predictions=len(occupied), false_occupied=len(occupied)-correct_occupied,
        uncertain=uncertain, uncertain_fraction=uncertain/n,
        decided=decided, decision_coverage=decided/n,
        correct_decisions=correct_empty+correct_occupied,
        decided_accuracy=(correct_empty+correct_occupied)/decided if decided else None,
        correct_decisions_fraction_of_all=(correct_empty+correct_occupied)/n)


def by_date(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['camera_id'], row['date'])].append(row)
    return [dict(camera_id=c, date=d, **metrics(group)) for (c,d),group in sorted(grouped.items())]


def main():
    state_path = ROOT / 'data/automation_state.json'
    state = read(state_path)
    assert not state['active_validation_jobs'] and not state['active_training_jobs']
    started = datetime.now(timezone.utc)
    rid = 'PKLOT-FRESH-FUSION-' + started.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'experiments/results' / rid
    folder.mkdir(parents=True, exist_ok=False)
    dev_path = ROOT / 'data/manifests/pklot_fresh_development_v1.json'
    final_path = ROOT / 'data/manifests/pklot_fresh_final_v2.json'
    assert_holdout_closed(final_path, root=ROOT)
    development = read(dev_path)
    assert len(development['frames']) == 12
    assert all(f['role'] == 'development' for f in development['frames'])
    baseline_card = read('models/pklot_fresh_classifier_baseline.json')
    baseline_path = ROOT / 'experiments/results' / baseline_card['run_id'] / 'development_predictions.json'
    baseline = read(baseline_path)
    assert len(baseline) == 720
    index = {(r['frame'], r['slot_id']): r for r in baseline}
    assert len(index) == 720
    baseline_states = [dict(r, state=('vacant' if r['probability_occupied'] <= .25 else
        'occupied' if r['probability_occupied'] >= .75 else 'uncertain')) for r in baseline]
    # Existing app uses inclusive end points; verify the earlier strict-band
    # baseline has no boundary cases before comparing the two.
    assert all(r['probability_occupied'] not in (.25, .75) for r in baseline)
    base_metrics = metrics(baseline_states)
    base_dates = by_date(baseline_states)
    paths = ['scripts/evaluate_fresh_pklot_fusion.py', 'src/smart_parking/vision.py',
        'src/smart_parking/layout.py', 'src/smart_parking/analysis_identity.py']
    hashes = {p: digest(ROOT/p) for p in paths}
    weight_paths = ['models/checkpoints/occupancy_resnet18.pt',
        'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth',
        'models/pretrained/maskrcnn_resnet50_fpn.pth']
    weights = {p: digest(ROOT/p) for p in weight_paths}
    protocol = dict(run_id=rid, started_at=started.isoformat(), seed=128,
        source_ids=['SRC-DS-001','SRC-MOD-001','SRC-MOD-002','SRC-MOD-003'],
        source_hashes=hashes, weight_hashes=weights,
        development_manifest_sha256=digest(dev_path), closed_final_manifest_sha256=digest(final_path),
        baseline_run=baseline_card['run_id'], baseline_predictions_sha256=digest(baseline_path),
        hypothesis='Unchanged app detector/ResNet fusion can flag the two crop-only false-vacant development answers without excessive abstention or loss of useful vacancy decisions.',
        detector_order=['fasterrcnn','maskrcnn'], resolution=640,
        thresholds=dict(detection=.5, uncertain_low=.25, uncertain_high=.75),
        preset_gates=dict(false_vacant_max_exclusive=base_metrics['false_vacant'],
            no_date_false_vacant_regression=True, uncertain_fraction_max=.10,
            retain_correct_crop_vacancies_fraction_min=.80),
        baseline=base_metrics, baseline_per_date=base_dates,
        limits=dict(wall_seconds=600, torch_threads=4, images_per_detector=12),
        limitations=['Development only; two known cameras, three new dates, correlated slots/times',
            'Original XML geometry supplied, stripped of occupancy labels before inference; not automatic space segmentation',
            'No weights/settings changed, no promotion, no final-image/label read',
            'Abstention is reported separately; a flagged false vacancy is not a corrected occupied answer',
            'No exhaustive vehicle boxes/masks ground truth, so no detector mAP or mask accuracy'])
    dump(folder/'protocol.json', protocol)
    dump(folder/'implementation_sources.json', {p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs'] = [dict(run_id=rid,cancel_file=str(folder/'CANCEL'),deadline_seconds=600)]
    dump(state_path,state)
    timer = time.perf_counter()
    try:
        import torch
        from PIL import Image
        from smart_parking.layout import read_pklot_xml
        from smart_parking.vision import VisionEngine
        torch.manual_seed(128)
        summaries = {}
        for detector in protocol['detector_order']:
            engine = VisionEngine(detector=detector, resolution=640)
            rows = []
            max_probability_delta = 0.0
            for frame_no,frame in enumerate(development['frames'],1):
                if (folder/'CANCEL').exists() or time.perf_counter()-timer > 600:
                    raise InterruptedError('Fusion cancellation/deadline')
                assert digest(ROOT/frame['image']) == frame['image_sha256']
                assert digest(ROOT/frame['annotation']) == frame['annotation_sha256']
                with Image.open(ROOT/frame['image']) as source:
                    image = source.convert('RGB')
                labelled = read_pklot_xml(ROOT/frame['annotation'],image.size)
                geometry = {k:v for k,v in labelled.items() if k!='slots'}
                geometry['slots'] = [dict(id=s['id'],polygon=s['polygon']) for s in labelled['slots']]
                assert not any('ground_truth_occupied' in s for s in geometry['slots'])
                result,overlay = engine.analyze(image,geometry,confidence=.5,uncertain_low=.25,uncertain_high=.75)
                truth = {s['id']:s['ground_truth_occupied'] for s in labelled['slots']}
                frame_rows = []
                for observation in result['slots']:
                    original = index[(frame['image'],observation['slot_id'])]
                    assert truth[observation['slot_id']] == original['label']
                    delta = abs(observation['occupancy_score']-original['probability_occupied'])
                    max_probability_delta = max(max_probability_delta,delta)
                    assert delta < 1e-5, 'Unexpected classifier probability drift'
                    row = dict(frame=frame['image'],image_sha256=frame['image_sha256'],camera_id=frame['camera_id'],
                        date=frame['date'],label=original['label'],crop_probability_occupied=original['probability_occupied'],
                        **observation)
                    rows.append(row)
                    frame_rows.append(row)
                dump(folder/detector/f'frame_{frame_no:02d}.json',dict(source_frame=frame,result=result))
                if any(r['label']==1 and r['crop_probability_occupied']<.25 for r in frame_rows):
                    overlay.save(folder/detector/f'crop_error_frame_{frame_no:02d}.png')
                dump(folder/'progress.json',dict(detector=detector,frames_completed=frame_no,
                    labelled_samples=len(rows),elapsed_seconds=time.perf_counter()-timer))
                print(json.dumps(dict(detector=detector,frame=frame_no,counts=result['counts'])),flush=True)
            assert len(rows)==720
            overall = metrics(rows)
            dates = by_date(rows)
            base_by_date = {(g['camera_id'],g['date']):g for g in base_dates}
            checks = dict(fewer_false_vacant=overall['false_vacant']<base_metrics['false_vacant'],
                no_date_false_vacant_regression=all(g['false_vacant']<=base_by_date[(g['camera_id'],g['date'])]['false_vacant'] for g in dates),
                uncertainty_within_limit=overall['uncertain_fraction']<=.10,
                retains_correct_vacancies=overall['correct_vacant_predictions']>=math.ceil(.80*base_metrics['correct_vacant_predictions']))
            trace = [r for r in rows if r['label']==1 and r['crop_probability_occupied']<.25]
            summaries[detector] = dict(overall=overall,per_date=dates,checks=checks,
                development_gate_passed=all(checks.values()),crop_false_vacant_trace=trace,
                max_classifier_probability_delta=max_probability_delta)
            dump(folder/detector/'development_predictions.json',rows)
            del engine,rows,image,overlay,result
            gc.collect()
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        assert all(digest(ROOT/p)==h for p,h in weights.items())
        assert digest(dev_path)==protocol['development_manifest_sha256']
        assert digest(final_path)==protocol['closed_final_manifest_sha256']
        assert digest(baseline_path)==protocol['baseline_predictions_sha256']
        assert_holdout_closed(final_path,root=ROOT)
        outcome = dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),
            duration_seconds=time.perf_counter()-timer,detectors=summaries,
            weights_and_settings_unchanged=True,production_promoted=False,
            final_images_or_labels_read=0,model_training_performed=False)
        dump(folder/'run.json',outcome)
        dump(ROOT/'models/pklot_fresh_fusion_baseline.json',outcome)
        registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:
            fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Unchanged actual app fusion fresh-development comparison',
            started_at=protocol['started_at'],finished_at=outcome['finished_at'],source_ids=';'.join(protocol['source_ids']),
            split_ids='Same12development images/720labels as frozen crop baseline; final6closed',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Existing Faster/Mask R-CNN ResNet50 + original ResNet18 occupancy fusion',
            epochs=0,batch_size='100 or40 slots per frame',random_seed=128,hardware='CPU/Torch4threads',
            execution_environment=sys.version.split()[0],training_duration=outcome['duration_seconds'],
            evaluation_metrics=json.dumps(summaries),logs=folder.relative_to(ROOT).as_posix(),
            checkpoints='All original weights unchanged',code_revision_basis='8dcbcff plus frozen evaluator source',
            implementation_sha256=hashes[paths[0]],conclusions='Development diagnostic only; unchanged app measured, no promotion or final/live accuracy')
        with registry.open('a',encoding='utf-8',newline='') as stream:
            csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path)
        assert rid not in state['completed_run_ids']
        state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']))
        state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,detectors=summaries),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False))
        state=read(state_path)
        raise
    finally:
        state['active_validation_jobs']=[]
        dump(state_path,state)


if __name__=='__main__':
    main()
