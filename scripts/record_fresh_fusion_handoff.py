"""Save measured fusion evidence, source inventory and a resumable handoff."""
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.provenance import digest
from smart_parking.live import URL, get_live, parse_feed, _observation_key

E=ROOT/'experiments/evidence/HEARTBEAT-20261026T004741Z'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def write(path,value):
    path=ROOT/path
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def append(path,title,text):
    path=ROOT/path
    old=path.read_text(encoding='utf-8')
    assert title not in old
    path.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')


def main():
    assert not (E/'handoff_checks.json').exists(), 'Handoff already saved'
    state=read('data/automation_state.json')
    study=read('models/pklot_fresh_fusion_baseline.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==48
    assert state['last_completed_run']==study['run_id']
    assert state['scheduled_wakeups_completed']==32
    assert not state['active_validation_jobs'] and not state['active_training_jobs']
    targeted=read(E/'targeted_checks.json')
    assert targeted['tests_run']==14 and targeted['success'] and targeted['failures']==targeted['errors']==0
    with (ROOT/'data/source_manifest.csv').open(encoding='utf-8-sig',newline='') as stream:
        assert len(list(csv.DictReader(stream)))==57
    assert study['final_images_or_labels_read']==0 and not study['production_promoted']
    assert all(digest(ROOT/p)==h for p,h in study['source_hashes'].items())
    assert all(digest(ROOT/p)==h for p,h in study['weight_hashes'].items())
    original=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in original.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    final=ROOT/'data/manifests/pklot_fresh_final_v2.json'
    assert digest(final)==study['closed_final_manifest_sha256']
    assert_holdout_closed(final,root=ROOT)
    folder=ROOT/'experiments/results'/study['run_id']
    # Cross-check actual app observations independently of the summary writer.
    for detector,card in study['detectors'].items():
        rows=read(folder/detector/'development_predictions.json')
        assert len(rows)==720 and len({(r['frame'],r['slot_id']) for r in rows})==720
        assert sum(r['state']=='vacant' and r['label']==1 for r in rows)==card['overall']['false_vacant']
        assert sum(r['state']=='uncertain' for r in rows)==card['overall']['uncertain']
        for frame_path in (folder/detector).glob('frame_*.json'):
            frame=read(frame_path)['result']
            assert sum(frame['counts'][s] for s in ['occupied','vacant','uncertain'])==frame['counts']['total']
            assigned=[r['vehicle_id'] for r in frame['slots'] if r['vehicle_id'] is not None]
            assert len(assigned)==len(set(assigned)), 'One vehicle assigned to multiple slots'
            assert all(r['state']!='vacant' for r in frame['slots'] if r['vehicle_id'] is not None)
    blocked=[]
    def no_network(event,args):
        if event in {'socket.connect','socket.getaddrinfo'}:
            blocked.append(event)
            raise RuntimeError('Saved-snapshot check must stay offline')
    sys.addaudithook(no_network)
    rows,metadata=get_live(refresh=False)
    raw_path=Path(metadata['path'])
    raw=read(raw_path)
    assert rows==parse_feed(raw) and metadata['cached'] and not blocked
    live=read('data/processed/singapore_prospective/summary.json')
    assert raw_path==Path(live['snapshot_path'])
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(receipts) if r['local_path']==raw_path.relative_to(ROOT).as_posix())
    assert receipt['source_url']==URL and receipt['sha256']==digest(raw_path)
    with (ROOT/'data/processed/singapore_live_observations.csv').open(encoding='utf-8',newline='') as stream:
        history=list(csv.DictReader(stream))
    keys=[_observation_key(r['car_park_id'],r['lot_type'],r['observed_at']) for r in history]
    assert len(keys)==len(set(keys))
    raw_lots=sum(len(p['carpark_info']) for item in raw['items'] for p in item['carpark_data'])
    provider=datetime.fromisoformat(metadata['provider_timestamp'])
    checked=datetime.fromisoformat(live['checked_at'])
    age=(checked-provider.astimezone(timezone.utc)).total_seconds()
    assert -30<=age<=180 and all(0<=r['available']<=r['capacity'] and r['capacity']>0 for r in rows)
    live_evidence=dict(**live,raw_sha256=digest(raw_path),raw_bytes=raw_path.stat().st_size,
        snapshot_count=len(list(raw_path.parent.glob('*.json'))),valid_rows=len(rows),raw_lot_records=raw_lots,
        omitted_invalid_or_duplicate_lot_records=raw_lots-len(rows),car_parks=len({r['car_park_id'] for r in rows}),
        provider_timestamp=metadata['provider_timestamp'],feed_age_at_collection_seconds=age,
        history_rows=len(history),history_duplicates=0,cached_app_route_passed=True,cached_route_network_attempts=blocked,
        first_restricted_attempt='DNS resolution failed with socket.gaierror11001; no public bytes acquired',
        recovery='One already-authorized public-network retry succeeded; raw receipt carries actual acquisition time',
        scheduled_100_run_checkpoint=False,next_100_run_checkpoint=100)
    write(E.relative_to(ROOT)/'live_checkpoint.json',live_evidence)
    summary=dict(run_id=study['run_id'],scope='Development only:12photos/720explicit slot labels/3dates/2known cameras',
        crop_baseline=study['baseline'],detectors=study['detectors'],weights_unchanged=True,
        production_promoted=False,final_images_or_labels_read=0,
        final_manifest='data/manifests/pklot_fresh_final_v2.json',
        final_manifest_sha256=digest(final),guide='docs/FRESH_PARKING_DATA_GUIDE.md')
    write('reports/fresh_parking_fusion_latest.json',summary)
    inventory=read('data/dataset_inventory.json')
    inventory['inventoried_at']=datetime.now(timezone.utc).isoformat()
    inventory['fresh_pklot_fusion_baseline']=summary
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-001':
            item['fresh_fusion_development']=summary
        if item['source_id']=='SRC-LIVE-001':
            item.update(car_parks=live_evidence['car_parks'],observations=len(rows),
                provider_timestamp=metadata['provider_timestamp'],raw_path=raw_path.relative_to(ROOT).as_posix(),
                snapshot_count=live_evidence['snapshot_count'],prospective_baseline_scored_outcomes=live['scores_total'],
                prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state.update(scheduled_wakeups_completed=33,last_updated_at=datetime.now(timezone.utc).isoformat(),
        fresh_pklot_fusion_baseline=summary,last_live_baseline_score=dict(outcomes=live['scores_total'],
        mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; no neural/camera accuracy',coverage=live['forecast_coverage']))
    due=(checked+timedelta(minutes=30)).isoformat()
    state['next_actions']=[
        'Review the unchanged fusion results in models/pklot_fresh_fusion_baseline.json. Both models use actual app inference with fixed geometry stripped of labels; differences include abstention, so compare vacancy precision/recall and coverage rather than cherry-picking decided accuracy.',
        'Next qualify a bounded extra TRAINING-only PKLot manifest from existing legitimate archive groups, excluding every consumed/reserved final camera/date and the12fresh DEVELOPMENT frames and their dates. Check byte/source/layout lineage before decoding. Preserve original checkpoint; freeze any candidate-head training/validation gates before training. Fresh final6 remain closed for a qualified paired comparison.',
        'Use the retained development error traces and overlays to understand false empty/false occupied calls. Do not infer vacancy solely from missing detection, tune on final data, or treat uncertain as a corrected occupied answer. No production change has been made.',
        'Fresh final6/3whole camera-date groups unclaimed;171source frames reserved in full. Old image/Birmingham/DAVIS finals consumed. CNR image rights unqualified,144965metadata records only;32079reserved CNR images unopened.191full software regressions retain prior scope; targeted checks saved separately.',
        f'Counter48; next separate100-run live checkpoint100; no active jobs. LatestSingapore{checked.isoformat()}:38snapshots,{live["scores_total"]}matched persistence outcomes,MAE{live["baseline_mae_spaces"]:.6f}spaces. Next sensible source collection after{due}. Missing target windows remain unscored. Existing copied demo is an older snapshot.',
        'Physical/new-machine offline,visible browser/manual,student rehearsal/mastery and official university-document acceptance remain incomplete. Preserve failed studies,source57,all raw bytes/checkpoints and exact evidence.'
    ]
    write('data/automation_state.json',state)
    table=['| Method | Empty answers | Wrong empty | Correct empty | Wrong occupied | Needs review | Decisions /720 | Development gate |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    base=study['baseline']
    table.append(f'| Classifier crop only | {base["vacant_predictions"]} | {base["false_vacant"]} | {base["correct_vacant_predictions"]} | {base["false_occupied"]} | {base["uncertain"]} | {base["decided"]} | Earlier coarse gate |')
    parts=[]
    for detector,card in study['detectors'].items():
        m=card['overall']
        table.append(f'| {detector} + same classifier | {m["vacant_predictions"]} | {m["false_vacant"]} | {m["correct_vacant_predictions"]} | {m["false_occupied"]} | {m["uncertain"]} | {m["decided"]} | {card["development_gate_passed"]} |')
        parts.append(f'{detector}: {m["false_vacant"]} wrong empty/{m["vacant_predictions"]} empty answers, {m["uncertain"]} uncertain, {m["correct_vacant_predictions"]} correct empty, gate {card["development_gate_passed"]}')
    note='Unchanged actual app fusion measured on the same 12 fixed DEVELOPMENT photos/720 explicit slot labels: '+ '; '.join(parts)+'. Gates were written before inference: fewer than2false-vacants, no per-date false-vacant regression, at most10%uncertainty, retain at least80%of88correct crop-only vacancies. Both existing detector options tested; no training/threshold/weight change or promotion. Faster flags both crop false-vacants as uncertain,not occupied; Mask flags only one. Ten false-occupied answers remain with either option. Mask Feb28vacancy precision is only2/3;Faster Feb28finds only2/6true vacancies despite zero observed wrong empty answers. Aggregate gate pass is not vacancy-safe certification. XML geometry was supplied without answer labels; this is not automatic learned space segmentation. Final6images/labels stay unopened/unclaimed; old finals remain consumed. All three production checkpoints and tracker source hashes unchanged. One completed comparison advances47->48; frames/tests/live collection do not add runs. Latest official Singapore snapshot38 adds1100matched earlier persistence outcomes,31714total,MAE4.623069spaces;1094newforecasts frozen. Restricted DNS failure retained; authorized retry succeeded. Immutable raw JSON, receipt URL/time/SHA, normalized CSV and cached app route validated; history duplicates0. No neural/camera live accuracy. Original full191regressions retain prior scope;14targeted product/holdout tests pass with zero failures/errors. Source catalog57 unchanged. Next: qualified training-only data expansion while final stays closed. Physical/manual/browser/student/official acceptance remains incomplete.'
    title='## 26 October 2026 / unchanged app fusion on fresh development photos'
    for path in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md']:
        append(path,title,note)
    append('docs/DATASET_PROVENANCE.md',title,'Existing SRC-DS-001 original PKLot geometry/labels only on the12development frames; externally pretrained detector SRC-MOD-001/002 plus original classifier derived from SRC-MOD-003. No new image download or label transformation. Final6raw JPEG/XML files not decoded/parsed. Actual Singapore receipt/source and normalized/prospective history remain separate; no camera labels derived from aggregate availability.')
    append('docs/UI_TEST_LOG.md',title,'Actual VisionEngine.analyze backend paths for both detector options measured; offline get_live(refresh=False) route validated against new saved source bytes with network denied. No new desktop/browser/manual UI interaction in this wakeup.')
    guide=ROOT/'docs/FRESH_PARKING_DATA_GUIDE.md'
    text=guide.read_text(encoding='utf-8')
    text=text.replace('The next check is whether the app\'s\nexisting vehicle detector plus space-classifier fusion catches those errors.',
        'The combined check below now measures whether the app\'s\nexisting vehicle detector plus space-classifier fusion catches those errors.')
    text=text.replace('Original checkpoints,the47recorded trials','Original checkpoints,the48recorded trials')
    extra='\n\n## The combined app check\n\nImagine a parking attendant who first looks at each space, then asks a second attendant to look for cars. When the two disagree, the app says “needs review.” That is different from knowing the space is occupied. These results use the same photos and unchanged settings.\n\n'+'\n'.join(table)+'\n\nThe data contain108truly empty and612occupied spaces. “Decisions” excludes review answers; compare how many useful empty spaces remain as well as wrong empty answers. The same2crop-only false-empty examples are traced below.\n\n| Source photo / slot37 | Faster R-CNN fusion | Vehicle matched | Mask R-CNN fusion | Vehicle matched |\n|---|---|---|---|---|\n'
    traces={d:{r['frame']:r for r in c['crop_false_vacant_trace']} for d,c in study['detectors'].items()}
    for frame in sorted(traces['fasterrcnn']):
        a=traces['fasterrcnn'][frame];b=traces['maskrcnn'][frame]
        extra+=f'| {Path(frame).name} | {a["state"]} | {a["vehicle_id"] is not None} | {b["state"]} | {b["vehicle_id"] is not None} |\n'
    extra+='\nPer-date details, probabilities, matched-car overlaps and frozen gates: `models/pklot_fresh_fusion_baseline.json`. Exact per-frame app outputs and two error-photo overlays per detector: `experiments/results/'+study['run_id']+'/`. Latest pointer: `reports/fresh_parking_fusion_latest.json`. Source data locations in the earlier table remain valid.\n\nNo new model was trained here. This is an honest check of what the current app already does on known cameras/new dates. The6reserved final photos remain untouched. Neither this development result nor the Singapore feed establishes live camera accuracy or universal reliability.\n'
    extra+='\nThere are still useful empty spaces being missed: on28February, Faster correctly says “empty” for only2of6empty spaces. Mask has one wrong empty answer among its3empty answers that day. Both models also wrongly call10empty spaces occupied overall. These limits remain even though both pass the prespecified development gate. A correct “empty” count on a small development sample cannot guarantee the next driver will find an empty space.\n'
    assert '## The combined app check' not in text
    guide.write_text(text.rstrip()+extra,encoding='utf-8')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in {'OCC-01','CLS-03'}:
            row['actual_evidence']+='; models/pklot_fresh_fusion_baseline.json; reports/fresh_parking_fusion_latest.json'
            row['test_result']+='; fresh DEVELOPMENT actual unchanged fusion: '+'; '.join(parts)
            row['open_problems']=row['open_problems'].replace('unchanged full-fusion evaluation next','unchanged full-fusion development measured; final/live accuracy remains unmeasured')
            row['open_problems']+='; supplied geometry, correlated development photos, abstentions separate from correct occupancy; no production promotion'
    with req.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    write(E.relative_to(ROOT)/'handoff_checks.json',dict(run_id=study['run_id'],completed_trials=48,
        wakeups_completed=33,source_records=57,production_weights_and_tracker_unchanged=True,
        final_pixels_or_labels_read=0,final_group_guard_passed=True,app_observation_invariants_passed=True,
        live_history_duplicates=0,cached_live_route_network_attempts=blocked,no_active_jobs=True,
        targeted_tests_passed=14,full_191_test_suite_rerun_this_wakeup=False,
        next_live_100_run_milestone=100,new_training=False,production_promoted=False))
    print(json.dumps(dict(completed_trials=48,results=parts,live_scores=live['scores_total'],final_closed=True),indent=2))


if __name__=='__main__':
    main()
