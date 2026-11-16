"""Record the dated continuation study and one-use final evidence exactly once."""
import csv,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
from smart_parking.sequence_holdouts import assert_sequence_closed
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T144531Z'
D='FLOW-CONTINUATION-20261025T145043485311Z'
F='FLOW-SEQUENCE-FINAL-20261025T145525078714Z'
FAILED='FLOW-CONTINUATION-20261025T144953942757Z'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    path=ROOT/p;old=path.read_text(encoding='utf-8')
    if title not in old:path.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text.strip()+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('Dated evidence already recorded; use a new continuation')
    now=datetime.now(timezone.utc).isoformat();dev=read('experiments/results/'+D+'/run.json');final=read('experiments/results/'+F+'/run.json')
    state=read('data/automation_state.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==32
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert dev['counting_final_qualified'] and not dev['final_sequence_evaluated']
    assert final['reserved_sequence_consumed']
    for run in [dev,final]:
        for p,h in run['source_hashes'].items():assert digest(ROOT/p)==h
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig')
    assert 'Ran 159 tests' in tests and tests.rstrip().endswith('OK')
    # The numeric final outcome is not rerun: read only its existing claim/report.
    claims=list((ROOT/'data/sequence_holdout_claims').glob('*.claim.json'));assert len(claims)==1
    claim=json.loads(claims[0].read_text(encoding='utf-8'));assert claim['run_id']==F
    assert read(claims[0].with_suffix('.outcome.json').relative_to(ROOT))['status']=='completed; whole sequences consumed'
    manifest=ROOT/'data/manifests/davis_car_roundabout_final_v2.json'
    parent=ROOT/'data/manifests/davis_car_sequences_v2.json'
    assert digest(manifest)=='95a329918a282a482d60408b3c834e4bb7df2a573f4396b198eeb92928b9d240'
    try:assert_sequence_closed(manifest,parent,'https://data.vision.ee.ethz.ch/csergi/share/davis/DAVIS-2017-trainval-480p.zip')
    except ValueError as error:assert 'already started' in str(error);rejection=str(error)
    else:raise AssertionError('Consumed final must be blocked')
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in production.items())
    assert digest(ROOT/'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth')==final['detector_sha256']
    write('models/flow_continuation_development.json',dict(dev,scope='Reused one-car development; not production promotion',final_run=F))
    write('models/davis_sequence_final.json',dict(final,scope='One selected foreground car, first5label-assisted setup/remaining70scored; image-plane crossing only',
        semantic_review='experiments/evidence/HEARTBEAT-20261025T144531Z/semantic_review.json',
        consumed_claim=claims[0].relative_to(ROOT).as_posix(),changed_method_reuse_allowed=False))
    path=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;registry=list(reader)
    if not any(r['experiment_id']==FAILED for r in registry):
        failed=read('experiments/results/'+FAILED+'/protocol.json')
        row=dict(experiment_id=FAILED,run_type='Interrupted scorer adapter attempt; NOT counted as completed experiment',started_at=failed['started_at'],source_ids='SRC-DS-012;SRC-MOD-001',
            split_ids='car-turn development only',configuration='experiments/results/'+FAILED+'/protocol.json',architecture='Cached weak-confidence continuation',epochs=0,
            evaluation_metrics='No valid completed metrics saved',logs='experiments/results/'+FAILED,code_revision_basis=failed['code_revision_basis'],
            implementation_sha256=failed['source_hashes']['scripts/evaluate_continuation.py'],
            conclusions='Scorer passed continuation_confidence to reference GateCounter; TypeError. Frozen failed sources/protocol/error preserved; separated reference geometry config, integration fixture added; unchanged hypothesis/thresholds rerun on development only. No final pixels used for this repair.')
        registry.append({k:row.get(k,'') for k in fields})
        with path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(registry)
    assert all(sum(r['experiment_id']==i for r in registry)==1 for i in state['completed_run_ids'])
    live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(s) for s in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001')
    assert receipt['local_path']=='data/raw/singapore_live/20261025T144748436937Z.json'
    payload=read(receipt['local_path']);rows=parse_feed(payload)
    assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    assert len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})==len(rows)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        feed_age_seconds=(datetime.fromisoformat(receipt['accessed_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds(),
        interpretation='1124earlier frozen persistence forecasts matched to later observations; no neural or camera accuracy'))
    state['last_updated_at']=now;state['scheduled_wakeups_completed']+=1
    state['davis_sequences'].update(continuation_development_run=D,continuation_development_metrics=dev['metrics'],continuation_development_qualified=True,counting_final_qualified=final['final_gate_passed'],
        qualification_note='Development gates pass, but final lacks positive reference crossings: final acceptance fails; no deployment claim',
        final_run=F,final_metrics=final['metrics'],final_gate_passed=final['final_gate_passed'],final_sequence_consumed=True,final_pixels_unopened=False,
        final_claim=claims[0].relative_to(ROOT).as_posix(),changed_method_final_reuse_allowed=False)
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; no neural/camera accuracy',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'DAVIS car-roundabout whole sequence now CONSUMED by '+F+'. Do not tune or evaluate changed methods on any frame from this sequence; original reservation stays unchanged. Preserve failed attempts, selected sources, raw data, weights and claim/outcome.',
        'Final detector/identity coverage70/70matches baseline, but ZERO reference crossings leaves event recovery unavailable; overall final gate FAILS. One unmatched prediction is unassessable with partial labels. Do not move the line or rerun this consumed sequence. Seek fresh legitimate labelled sequence/groups with a predeclared meaningful positive-crossing protocol; retain candidate as development-only, no runtime promotion.',
        'Complete application integration/exports only within verified scope, native visible/dialog checks, fresh physically offline rehearsal, final report/presentation and student explanations. Keep all old camera/date and Birmingham holdouts consumed; no universal accuracy/completion claim.',
        'Next official live collection around next30minwake;14:47snapshot24:18021matched persistence outcomes,MAE4.424949,6237expired/1398pending. Source/capacity/time checks apply. Counter32; separate100-run checkpoint100.'
    ]
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-DS-012':row.update(status='development_and_one_use_final_evaluated_whole_final_sequence_consumed',
            continuation_development_run=D,development_validation_passed=True,counting_final_qualified=final['final_gate_passed'],final_run=F,final_gate_passed=final['final_gate_passed'],
            reserved_pixels_decoded=True,final_pixels_unopened=False,final_sequence_consumed=True,consumed_claim=claims[0].relative_to(ROOT).as_posix())
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    path=ROOT/'data/source_manifest.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==len({r['source_id'] for r in sources})==45
    for row in sources:
        if row['source_id']=='SRC-DS-012':
            row['used_by']+='; '+D+'; '+F
            row['status']='acquired / development and frozen final evaluated; entire car-roundabout sequence consumed'
            row['open_issues']='Only selected foreground labels, label-assisted setup and image-plane crossings; unknown fps/moving camera; not exhaustive traffic precision/parking entrance accuracy. Full final sequence consumed; changed methods need fresh groups; no production promotion.'
    with path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    write(E.relative_to(ROOT)/'checks.json',dict(tests_passed=159,randomized_synthetic_weak_rule_cases=500,completed_trials=32,
        development_qualified=True,development_metrics=dev['metrics'],final_metrics=final['metrics'],final_gate_passed=final['final_gate_passed'],
        full_sequence_consumed=True,consumed_guard_rejection=rejection,final_reservation_sha256=digest(manifest),source_count=45,
        production_flow_source_unchanged=digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9',
        production_weights_unchanged=True,failed_development_attempt_preserved_not_counted=True,active_jobs=[]))
    dm,fm=dev['metrics'],final['metrics']
    note=f'''A separate experimental identity-only continuation preserves actual low detector
scores and only reuses unambiguous existing identities; weak boxes cannot create
tracks and erase crossing memory before/after update. Real missing observations
or long gaps still drop identity. Original GateCounter source/config/output policy
is unchanged. On reused car-turn development, fixed x694line:tracking coverage
74/75->75/75, dominant identity53/75->75/75;1/1reference crossing recovered,
no extra unmatched event. Fixed development gates pass. No threshold/line sweep.

First development scorer attempt failed because candidate metadata was passed to
reference geometry. Failure/protocol/source snapshots preserved, not counted.
Separated reference config and added integration fixture, then reran unchanged
candidate on development only.159software tests pass, including500randomized
synthetic weak-only rule cases; synthetic checks are not camera accuracy.

Frozen final {F} consumed the entire75frame car-roundabout
sequence with an exclusive fsynced source/sequence claim BEFORE pixel decoding.
First5labelled setup frames use the unchanged gate rule;70remaining frames scored.
No project training or final tuning. Actual final metrics:
{json.dumps(fm,ensure_ascii=True)}
Final gate passed:{final['final_gate_passed']}. Baseline metrics are in the same
report. This is one selected foreground car, partial traffic labels, image-plane
crossings and unknown fps, not exhaustive traffic precision, occupancy/parking
entrance accuracy or broad deployment evidence. Foreground semantic vehicle
review performed after claim/freeze, no parameter adjustment. Entire sequence is
now consumed, including all setup frames; no changed-method reuse. Original role
manifest unchanged. No production promotion/weights change.32completed trials,
no active jobs; separate100-run live checkpoint100. Next:scoped runtime acceptance,
offline/native UI and student/report materials; fresh groups for model changes.

Actual14:47UTC authorized Singapore snapshot24matched1124later persistence
outcomes:18021total,MAE4.424949spaces;6237expired missing targets,1398pending.
Resolved matching74.29%, not accuracy. Immutable JSON/URL/time/SHA and normalized
CSV retained. No neural/camera accuracy or zero-error substitute for missing targets.'''
    title='## 25 October 2026 / identity-only continuation and whole-sequence final'
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        append(p,title,note)
    append('docs/PROJECT_CONSTRAINTS.md',title,'DAVIS car-roundabout entire75frame source/sequence is now CONSUMED, including setup frames. Do not tune/re-evaluate changed methods on it. Original role manifest remains immutable; claim/outcome enforces consumption. Candidate differs from production tracker, no promotion. Partial foreground/image-plane/label-assisted setup scope; no physical fps/parking accuracy or universal claims. Preserve all failed experiments and selected snapshots; use fresh source/sequence groups for changed methods.')
    path=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=path.read_text(encoding='utf-8')
    text=text.replace('150 tests pass; network-disabled-process','159 tests pass; network-disabled-process').replace('Twenty-three authorized public snapshots acquired','Twenty-four authorized public snapshots acquired')
    text=text.replace('Fifteen prospective persistence cohorts scored','Sixteen prospective persistence cohorts scored').replace('16,897 matched later outcomes, MAE4.387','18,021 matched later outcomes, MAE4.425')
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| Vehicle flow |'):lines[i]=f'| Vehicle flow | Separate continuation candidate; one-use final evaluated | Development identity75/75and1/1crossing; final gates:{final["final_gate_passed"]}, actual metrics models/davis_sequence_final.json. Partial labels/setup scope, whole final sequence consumed; original app tracker unchanged; native acceptance pending |'
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['VID-01','FLOW-01']:
            row['actual_evidence']+='; models/flow_continuation_development.json; models/davis_sequence_final.json; data/sequence_holdout_claims'
            row['test_result']=f'159software tests; development dominant identity53/75->75/75; frozen final gates:{final["final_gate_passed"]}, '+json.dumps(fm)
            row['open_problems']='Small partial-foreground/label-assisted setup/image-plane scope, unknown fps/camera motion; whole final sequence consumed; no exhaustive precision/parking accuracy or production promotion'
            row['next_action']='Scoped runtime/exports/native/offline acceptance and archived student explanation; changed methods need genuinely fresh whole sequences'
    with path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    print(json.dumps(dict(completed_trials=32,tests=159,development_qualified=True,final_gate_passed=final['final_gate_passed'],final_metrics=fm),indent=2))


if __name__=='__main__':main()
