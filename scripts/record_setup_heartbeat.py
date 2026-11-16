"""Save one completed cached development replay, software and live evidence."""
import csv,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
from smart_parking.sequence_holdouts import assert_sequence_closed,evaluate_sequence_once

E=ROOT/'experiments/evidence/HEARTBEAT-20261025T141530Z'
RUN='DAVIS-SETUP-20261025T141839144041Z'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():
        raise RuntimeError('This dated heartbeat is already recorded; preserve its evidence and use a new continuation record')
    now=datetime.now(timezone.utc).isoformat()
    result=read('experiments/results/'+RUN+'/run.json')
    state=read('data/automation_state.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==30
    assert not state['active_validation_jobs'] and not state['active_training_jobs']
    assert not result['counting_final_qualified'] and result['metrics']['reference_events']==result['metrics']['recovered_events']==1
    assert result['gate_checks']['dominant_identity'] is False
    for path,h in result['source_hashes'].items():assert digest(ROOT/path)==h
    test_text=(E/'unit_tests.txt').read_text(encoding='utf-8-sig')
    assert 'Ran 150 tests' in test_text and test_text.rstrip().endswith('OK')
    notebook=read('notebooks/06_labelled_vehicle_flow.ipynb')
    code=[c for c in notebook['cells'] if c['cell_type']=='code']
    assert len(code)==4 and all(c['execution_count'] for c in code)
    assert not any(o['output_type']=='error' for c in code for o in c['outputs'])
    card=dict(result,protocol_sha256=digest(ROOT/'experiments/results'/RUN/'protocol.json'),
        collection_identity='https://data.vision.ee.ethz.ch/csergi/share/davis/DAVIS-2017-trainval-480p.zip',
        checkpoint_hashes={'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth':result['detector_sha256']},
        interpretation='One recovered labelled image-line crossing on reused development; identity gate fails, no final qualification or exhaustive traffic accuracy')
    write('models/davis_setup_development.json',card)
    reserved=ROOT/'data/manifests/davis_car_roundabout_final_v2.json'
    parent=ROOT/'data/manifests/davis_car_sequences_v2.json'
    before=digest(reserved)
    rows=assert_sequence_closed(reserved,parent,card['collection_identity'])
    assert len(rows)==75
    callback_calls=[]
    try:
        evaluate_sequence_once(reserved,parent,ROOT/'models/davis_setup_development.json',
            ROOT/'experiments/results'/RUN/'protocol.json','MUST-NOT-START',lambda rows:callback_calls.append(rows),
            collection_identity=card['collection_identity'],expected_manifest_sha256=before,
            expected_selection_sha256=digest(ROOT/'models/davis_setup_development.json'))
    except ValueError as error:
        assert 'positive-reference counting validation gate' in str(error)
        rejection=str(error)
    else:raise AssertionError('Unqualified selection must not open final assets')
    assert not callback_calls and digest(reserved)==before
    assert not list((ROOT/'data/sequence_holdout_claims').glob('*.claim.json'))
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in production.items())
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001')
    payload=read(receipt['local_path']);observations=parse_feed(payload)
    live=read('data/processed/singapore_prospective/summary.json')
    assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    assert len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in observations})==len(observations)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,
        accepted_observations=len(observations),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(observations),duplicates=0,
        bounds_valid=all(0<=r['available']<=r['capacity'] for r in observations),
        feed_age_seconds=(datetime.fromisoformat(receipt['accessed_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds(),
        interpretation='1213previously frozen persistence forecasts newly matched later observations; not neural or camera accuracy'))
    write(E.relative_to(ROOT)/'checks.json',dict(tests_passed=150,completed_recorded_trials=30,
        positive_development_reference_crossings=1,recovered_development_crossings=1,
        counting_validation_gate_passed=False,failed_gate='dominant identity fraction0.7067<0.8',
        final_reservation_sha256=before,final_reservation_frames=75,final_callback_calls=len(callback_calls),
        final_claim_created=False,final_pixels_unopened=True,qualification_rejection=rejection,
        notebook_code_cells_executed=4,notebook_errors=0,production_weights_unchanged=True,
        study_source_snapshots_match=True,guard_scope='whole canonical collection/sequence, paths and asset hashes; metadata-only preflight',
        guard_source_sha256=digest(ROOT/'src/smart_parking/sequence_holdouts.py')))
    state['last_updated_at']=now
    state['scheduled_wakeups_completed']+=1
    state['trigger_handling_note']='14:15wake completed one setup-only cached replay; notebook display/regression tests and live collection are not additional model experiments.'
    state['davis_sequences'].update(setup_replay_run=RUN,setup_replay_card='models/davis_setup_development.json',
        annotated_crossing_recovery_evaluable=True,annotated_reference_crossings=1,annotated_recovered_crossings=1,
        counting_final_qualified=False,qualification_note='One image-line crossing recovered on reused development; dominant identity53/75<80% gate',
        sequence_guard_implemented_and_tested=True,final_pixels_unopened=True)
    state['labelled_flow_lesson']=dict(path='notebooks/06_labelled_vehicle_flow.ipynb',executed=True,code_cells=4,scope='Cached development evidence; no new inference/final evaluation')
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],
        scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Diagnose car-turn identity break using saved detections; propose a bounded conservative association/continuation change using development only. Preserve no-crossing-through-unobserved-gap rule and all default-seconds behavior. Freeze hypothesis/gates before evaluating changed tracker; do not adjust the line again to chase scores.',
        'Setup-only replay recovered1/1labelled image-line crossings at frame22; detection75/75, tracked74/75, dominantID53/75 fails80% qualification. This is partial-label reused development, not parking-entry/full traffic accuracy.',
        'DAVIS car-roundabout75frames remains unopened/unclaimed. Whole-sequence guard and tests now implemented. Current failed qualification is verified to block final callback before any claim/pixel decoding. Freeze complete selected method/protocol/weights/code, pass positive-reference gates, then use durable source/sequence claim for ONE final evaluation; failure consumes whole sequence.',
        'Keep all previous image camera/date finals and Birmingham final dates consumed. Continue native/visible/fresh-offline acceptance, report updates and student explanations; notebook06now shows cached real crossing and failed identity gate. No production checkpoint changed.',
        f'Continue source-compliant official live collection around next wake; freeze and score only later fresh same-capacity observations. At14:16UTC:{live["scores_total"]}matched, MAE{live["baseline_mae_spaces"]:.6f},6138expired/1276pending. Counter30; separate100-run checkpoint remains100.'
    ]
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in observations}),
            observations=len(observations),raw_lot_records=raw_count,raw_path=receipt['local_path'],
            provider_timestamp=receipt['provider_timestamp'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
            forecast_target_coverage=live['forecast_coverage'])
        if row['source_id']=='SRC-DS-012':row.update(setup_replay_run=RUN,setup_replay_reference_events=1,
            setup_replay_recovered_events=1,counting_final_qualified=False,final_pixels_unopened=True)
    write('data/dataset_inventory.json',inventory)
    p=ROOT/'data/source_manifest.csv'
    with p.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    for row in sources:
        if row['source_id']=='SRC-DS-012':
            row['used_by']+='; '+RUN+'; notebook06'
            row['open_issues']='Foreground labels partial;1/1image-plane crossing recovered, identity gate fails53/75; unknown fps and unaudited pretrained overlap; whole-sequence guard implemented/tested, reserved final unopened and blocked by failed qualification'
    with p.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    note='''One predeclared setup-only replay used cached real DAVIS car-turn detections,
not another neural run. Object1 labelled boxes from frames0..4 set vertical x694
before scoring frames5..79. The reference crossing at frame22 was recovered at
frame22 (1/1). Detection75/75, matched tracking74/75, dominant identity53/75
(70.7%). The prespecified >=80%dominant-identity gate FAILS; qualification false.
No line search, alternative retry, training, reserved pixels or weights changes.
This is reused development, partial foreground labels and image-plane motion,
not exhaustive traffic precision, physical timing or parking-facility entry accuracy.

Whole-sequence guard implemented/tested: canonical collection/sequence identity,
full parent-manifest membership, path/content overlap, sealed method/protocol/
checkpoint hashes, exclusive fsynced claim before callback; callback failure
consumes the sequence. Synthetic tests include interruption, source-ID/path alias,
changed sequence with same assets, subset/path escape, failed/zero-reference gate,
changed weights/protocol and stale lock. Actual75frame final metadata preflight
passes, but the failed development selection is rejected BEFORE callback/claim.
No actual final claim created; final75pixels/mask values remain unopened.

150software tests pass. Notebook06executes4code cells with zero errors and shows
the real frame22overlay, saved metrics, source/data/CSV locations and limitations.
This is an educational cached-result display, not another counted experiment or
student mastery assessment. Counter30; no active jobs; next100-run checkpoint100.
Next work: diagnose cached identity break, freeze one conservative tracking
improvement hypothesis with no crossing inference across missing observations.

Actual14:16UTC official Singapore snapshot23newly matches1213earlier frozen
persistence forecasts;16897total matched, MAE4.386873spaces.6138expired missing
targets,1276pending (1177new+99earlier). Resolved matching73.35%, not accuracy.
Source raw JSON/normalized CSV/URL/time/checksum preserved. No neural/camera
accuracy or invented scores for missing targets.'''
    title='## 25 October 2026 / positive image-line crossing and failed identity qualification'
    for path in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md',
                 'reports/PROGRESS_ADDENDUM_20261025.md']:
        p=ROOT/path;old=p.read_text(encoding='utf-8')
        if title not in old:p.write_text(old.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=p.read_text(encoding='utf-8')
    text=text.replace('Five executed teaching notebooks','Six executed teaching notebooks').replace('142 tests pass; network-disabled-process','150 tests pass; network-disabled-process')
    text=text.replace('Twenty-two authorized public snapshots acquired','Twenty-three authorized public snapshots acquired')
    text=text.replace('Fourteen prospective persistence cohorts scored','Fifteen prospective persistence cohorts scored').replace('15,684 matched later outcomes, MAE4.331','16,897 matched later outcomes, MAE4.387')
    text=text.replace('Both detectors, reset/settings','Both detectors, reset/settings')
    text+='\n\nLatest labelled-flow development:setup-only cached replay counts1/1reference crossing at frame22; identity gate FAILS (53/75dominant). Whole-sequence guard and150software tests pass; final75frames remain unopened/unclaimed. Notebook06cached lesson executed; no new production weights/native UI acceptance.\n'
    p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/PROJECT_CONSTRAINTS.md'
    p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nCurrent counting candidate fails dominant-identity gate; do not run final evaluation. Use sequence_holdouts.evaluate_sequence_once for any eventual frozen qualified final; canonical whole collection/sequence claims survive source-ID/path changes and failed callbacks. Car-roundabout remains unopened/unclaimed; no fabricated capture dates/fps. Positive development1/1crossing is label-assisted setup on a reused sequence and does not establish parking-entrance/exhaustive traffic accuracy.\n',encoding='utf-8')
    p=ROOT/'docs/REQUIREMENTS.csv'
    with p.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['VID-01','FLOW-01']:
            row['actual_evidence']+='; models/davis_setup_development.json; notebook06; src/smart_parking/sequence_holdouts.py'
            row['test_result']='150software tests; setup-only cached development:1/1reference image-line crossing recovered;75/75car detections,74/75tracking,53/75dominant identity; identity gate FAILS'
            row['open_problems']='Partial foreground labels/reused development/operator-like labelled setup; unknown fps/camera motion; no exhaustive traffic precision or parking entrance accuracy. Final guard tested but final75pixels unopened; tracking qualification fails'
            row['next_action']='Diagnose cached identity break and test predeclared conservative association improvement; freeze/pass gates before durable one-time whole-sequence final evaluation'
    with p.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    print(json.dumps(dict(completed_trials=30,tests=150,reference_crossings=1,recovered_crossings=1,
        counting_final_qualified=False,final_pixels_unopened=True,notebook_cells=4),indent=2))


if __name__=='__main__':main()
