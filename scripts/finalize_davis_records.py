"""Verify the explicit source correction and save the actual continuation/live state."""
import csv,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.source_catalog import require_source_identity
from smart_parking.live import parse_feed
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T110727Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();tests=(E/'unit_tests_verified.txt').read_text(encoding='utf-8-sig');assert 'Ran 142 tests' in tests and tests.rstrip().endswith('OK')
    source=require_source_identity(ROOT/'data/source_manifest.csv','SRC-DS-012','DAVIS2017 car-turn and car-roundabout original JPEG frames / publisher foreground masks','https://davischallenge.org/davis2017/code.html')
    with (ROOT/'data/source_manifest.csv').open(encoding='utf-8-sig',newline='') as f:sources=list(csv.DictReader(f))
    assert len(sources)==len({r['source_id'] for r in sources})==45 and next(r for r in sources if r['source_id']=='SRC-DS-011')['resource']=='TRANCOS'
    correction=read('data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json')
    original=read('data/manifests/davis_car_sequences_v1.json');current=read('data/manifests/davis_car_sequences_v2.json')
    assert original['frames']==current['frames'] and current['source_id']=='SRC-DS-012'
    old_reserved=read('data/manifests/davis_car_roundabout_final_v1.json');reserved=read('data/manifests/davis_car_roundabout_final_v2.json');assert old_reserved['frames']==reserved['frames'] and len(reserved['frames'])==75
    assert digest(ROOT/'data/manifests/davis_car_sequences_v1.json')==correction['original_v1_manifest_sha256'] and digest(ROOT/'data/manifests/davis_car_sequences_v2.json')==correction['corrected_v2_manifest_sha256']
    assert digest(ROOT/'data/manifests/davis_car_roundabout_final_v2.json')==correction['corrected_v2_reservation_sha256']
    for frame in current['frames']:
        assert digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['annotation'])==frame['annotation_sha256']
    lines=(ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines();by_hash={hashlib.sha256(line.encode()).hexdigest():json.loads(line) for line in lines}
    corrections=[r for r in by_hash.values() if r.get('record_type')=='source_id_correction' and r['source_id']=='SRC-DS-012']
    assert len(corrections)==len({r['corrects_receipt_sha256'] for r in corrections})==321
    for row in corrections:
        previous=by_hash[row['corrects_receipt_sha256']];assert previous['source_id']=='SRC-DS-011' and previous['local_path']==row['local_path'] and previous['sha256']==row['sha256'] and previous['accessed_at']==row['accessed_at']
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==29
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    v=next(i for i in reversed(state['completed_run_ids']) if i.startswith('DAVIS-FOREGROUND-'));frozen=read('experiments/results/'+v+'/run.json');card=read('models/davis_foreground_development.json');assert card['metrics']==frozen['metrics']
    snapshots=read('experiments/results/'+v+'/implementation_sources.json')
    for path,h in frozen['source_hashes'].items():
        assert hashlib.sha256(snapshots[path]['source'].encode()).hexdigest()==h
        if digest(ROOT/path)!=h:
            expected=snapshots[path]['source'].replace('SRC-DS-011','SRC-DS-012').replace('davis_car_sequences_v1.json','davis_car_sequences_v2.json')
            assert (ROOT/path).read_text(encoding='utf-8')==expected
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as f:registry=list(csv.DictReader(f))
    assert all(sum(r['experiment_id']==ident for r in registry)==1 for ident in state['completed_run_ids'])
    live=read('data/processed/singapore_prospective/summary.json');latest=[r for r in by_hash.values() if r['source_id']=='SRC-LIVE-001'][-1];payload=read(latest['local_path']);observations=parse_feed(payload)
    assert digest(ROOT/latest['local_path'])==latest['sha256'] and len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in observations})==len(observations)
    prior=read(E.relative_to(ROOT)/'live_checkpoint.json')['receipt'];gap=(datetime.fromisoformat(latest['accessed_at'])-datetime.fromisoformat(prior['accessed_at'])).total_seconds()/60
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'continuation_live_checkpoint.json',dict(summary=live,receipt=latest,collection_gap_minutes=gap,gap_cause='Not established; no intervening collections or scores claimed',accepted_rows=len(observations),raw_records=raw_count,invalid_capacity_excluded=raw_count-len(observations),duplicates=0,interpretation='No new scores at13:48;1291previous pending targets expired honestly.15684matched-only MAE unchanged, not zero error for missing targets.'))
    state['last_updated_at']=now;state['trigger_handling_note']='One productive continuation for pending11:07 through13:45triggers; no model runs or collections claimed at intervening trigger times. Source/receipt metadata correction and actual13:48feed checkpoint retained.'
    state['davis_sequences'].update(source_id='SRC-DS-012',source_manifest='data/manifests/davis_car_sequences_v2.json',final_manifest='data/manifests/davis_car_roundabout_final_v2.json',source_id_correction='data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json')
    state['davis_sequences'].update(crossing_accuracy_evaluable=False,counting_final_qualified=False,qualification_note='Coverage diagnostic only; zero reference crossings leaves counting unqualified')
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;14scored cohorts; not neural/camera accuracy',coverage=live['forecast_coverage'])
    state['next_actions'][-1]='Next official collection: match frozen13:48 forecasts only to later fresh same-capacity targets. At13:48:15684scored/6138expired/1312pending. Observed159.82min collection gap; no missing targets invented. Counter29; separate100-run live checkpoint100.'
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in observations}),observations=len(observations),raw_lot_records=raw_count,raw_path=latest['local_path'],provider_timestamp=latest['provider_timestamp'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    write(E.relative_to(ROOT)/'provenance_repair_checks.json',dict(tests_passed=142,source_count=45,correct_davis_source_id='SRC-DS-012',trancos_id011_unchanged=True,append_only_correction_records=321,no_duplicate_correction_records=True,all310original_member_hashes_match=True,roles_and_metrics_unchanged=True,frozen_source_snapshots_and_protocols_preserved=True,canonical_manifest_version=2,final_sequence_pixels_unopened=True,completed_runs=29,active_jobs=[]))
    note=f'''Continuation integrity check:142software tests pass. Canonical source catalog now
has45unique IDs. A collision was found: early DAVIS records used SRC-DS-011,
already assigned to TRANCOS. DAVIS is now SRC-DS-012. Original receipts, raw
acquisition manifest, frozen protocols/results/source snapshots and v1 role records
remain intact.321append-only correction receipts preserve original URLs/times/SHA;
v2manifests correct metadata only, identical155frame roles/310member hashes. The
crosswalk is data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json. Catalog
guards now reject a reused identity before acquisition. Windows UTF8 read repairs
were also required; the repair is documented, no model metrics changed.

Successful development result:one car detected75/75scored frames; tracked74/75,
dominant identity53/75;0reference crossings. Event recall remains NOT EVALUABLE;
no positive counting-accuracy claim or exhaustive traffic precision. First reporting
failure is preserved and excluded from29completed trials. New final sequence still
unopened; no active jobs. See docs/LABELLED_SEQUENCE_GUIDE.md for real data paths.

Actual fresh official collection13:48UTC followed a{gap:.2f}minute observed gap;
no intervening collections/runs are invented. Snapshot22adds1312future forecasts
but0scores:1291old pending forecasts expired without targets. Totals15684scored,
MAE4.330528,6138expired/1312pending,71.87%resolved matching, not accuracy.
Counter29; separate100-run checkpoint100. Continued work is the predeclared
setup-only gate replay on saved development detections, then a tested whole-sequence
claim/protocol before any reserved pixel decoding; no extra detector run needed.'''
    heading='## 25 October 2026 / source-ID repair and actual continuation checkpoint'
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        p=ROOT/name;text=p.read_text(encoding='utf-8')
        if heading not in text:p.write_text(text.rstrip()+'\n\n'+heading+'\n\n'+note+'\n',encoding='utf-8')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=p.read_text(encoding='utf-8').replace('Twenty-one authorized public snapshots acquired','Twenty-two authorized public snapshots acquired').replace('139 tests pass; network-disabled-process image check passes','142 tests pass; network-disabled-process image check passes');text+='\n\nSource/provenance continuation:142tests,45sources,29completed trials. DAVIS is SRC-DS-012; explicit correction preserves original evidence. Single-car development recall75/75frames; tracking fragmentation and zero reference crossings leave counting accuracy unmeasured. Reserved75frame sequence unopened. Actual13:48live snapshot22;15684matched persistence outcomes/MAE4.330528,6138expired/1312pending after collection gap.\n';p.write_text(text,encoding='utf-8')
    print(json.dumps(dict(tests=142,sources=45,completed_trials=29,original_members_verified=310,correction_receipts=321,live_gap_minutes=gap,final_sequence_unopened=True),indent=2))
