"""Save causal history admission,failed learned baseline,and fresh reservation."""
import csv,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T073847Z'
TITLE='## 26 October 2026 / Singapore causal history and reserved future forecasting period'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,v):
    p=ROOT/p;s=p.read_text(encoding='utf-8');assert TITLE not in s;p.write_text(s.rstrip()+'\n\n'+TITLE+'\n\n'+v+'\n',encoding='utf-8')
def main():
    assert not (E/'handoff.json').exists()
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');audit=read('models/singapore_history_admission.json');run=read('models/singapore_ridge_development.json');reservation=read(audit['reservation'])
    assert state['last_completed_run']==run['run_id'] and state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==64 and state['scheduled_wakeups_completed']==42
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert audit['summary']['exploratory_history_gate_passed'] and not run['development_gate_passed'] and run['selection']['selected_method']=='persistence'
    assert all(digest(ROOT/p)==h for p,h in {**audit['source_hashes'],**audit['protected_hashes'],**audit['derived_files'],**run['source_hashes'],**run['protected_hashes']}.items())
    assert digest(ROOT/audit['reservation'])==audit['reservation_sha256']==run['reservation_sha256']
    assert read(E/'software_tests.json')['returncode']==0 and 'Ran 260 tests' in read(E/'software_tests.json')['stderr']
    claims=ROOT/reservation['claim_registry'];assert not claims.exists() or not list(claims.glob('*.claim.json'))
    pointer=dict(admission_run=audit['run_id'],learned_baseline_run=run['run_id'],history_snapshots=46,train_examples=18393,development_examples=9202,
        train_global_origin_times=18,development_global_origin_times=9,historical_cutoff=audit['historical_cutoff'],training_cutoff=audit['training_cutoff'],
        reservation=audit['reservation'],reservation_sha256=audit['reservation_sha256'],final_origin_start=reservation['final_origin_start'],final_origin_end=reservation['final_origin_end'],final_target_end=reservation['final_target_end'],
        learned_linear_mae=run['candidate']['mae_spaces'],persistence_same_cohort_mae=run['persistence']['mae_spaces'],development_gate_passed=False,selected_method='persistence',
        future_final_consumed=False,future_final_evaluated=False,learned_forecasts_issued=False,neural_model_trained=False,guide='docs/SINGAPORE_FORECAST_STUDY.md')
    dump('reports/singapore_forecast_study_latest.json',pointer)
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    last=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert digest(ROOT/last['local_path'])==last['sha256']
    payload=read(last['local_path']);rows=parse_feed(payload);raw_lots=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in rows) and len(rows)==len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')));next_poll=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json',dict(receipt=last,summary=live,snapshot_count=snapshots,accepted_rows=len(rows),raw_lot_records=raw_lots,invalid_capacity_excluded=raw_lots-len(rows),
        duplicate_rows=0,bounds_valid=True,next_sensible_collection_after=next_poll,separate100_run_checkpoint_due=False,
        post_cutoff_snapshot_excluded_from_learned_history=last['local_path'] not in {x['path'] for x in reservation['history_inputs']},scope='Existing causal persistence only;not learned-final/neural/camera accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['singapore_forecast_study']=pointer
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(raw_path=last['local_path'],provider_timestamp=last['provider_timestamp'],snapshot_count=snapshots,observations=len(rows),
            car_parks=len({r['car_park_id'] for r in rows}),raw_lot_records=raw_lots,prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
            forecast_target_coverage=live['forecast_coverage'],learned_history_study=pointer)
    dump('data/dataset_inventory.json',inventory)
    catalog=ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==58
    for item in sources:
        if item['source_id']=='SRC-LIVE-001':
            item['used_by']+=';receipt-timed historical admission46snapshots/27595causal windows;one fixed learned LINEAR residual baseline rejected on chronological development;future global period reserved'
            item['open_issues']+=';Only18train/9development global origin times;linear7.738vs6.958persistenceMAE on same9202windows,not neural/camera accuracy;future learned forecasts not issued'
    with catalog.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    state.update(last_updated_at=now,scheduled_wakeups_completed=43,singapore_forecast_study=pointer,prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;not learned/neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Singapore admission63and fixed learned LINEAR baseline64completed.46sealed rawsnapshots/111458parsed rows;56136fresh source observations,0conflicting revisions.27595causal windows=18393train(18globalorigins,1355series)+9202development(9origins,1243series). Onlypast values available at actual acquisition receipts used;no source-time/mtime assumption or interpolation. See models/singapore_history_admission.json/reports/singapore_forecast_study_latest.json.',
        'IMMUTABLE FUTURE RESERVATION:data/manifests/singapore_forecast_reservation_v1.json SHA'+audit['reservation_sha256']+'.Historical cutoff2026-10-26T07:46:23.970649+00:00;training cutoff2026-10-25T21:27:05.002849+00:00. Allcarparks final ORIGINS2026-10-26T10:00Z through2026-10-27T10:00Z;targets/deliveryclose2026-10-27T10:51Z. Reserve isunconsumed;no real final claim. Do not overwrite/shift it. Allpost-cutoff observations,including07:55snapshot47,are excluded from THIS study fitting/development. Futureinferencecontext may use alreadyavailable observations with frozen parameters.',
        'Fixed ridge strength.1,6issue-time features/training-only mean-std/normalized residual target failed:MAE7.738379vs6.957618persistence;macro-origin7.732101vs6.953844. Physical bounds/roundtrip pass;both improvement gatesFalse. Selected persistence,no learned forecasts issued/no appintegration/no neuralSG model trained. Compare these methods only on same9202cohort;do not compare with rolling40753baseline outcome MAE(different cohort). Preserve checkpoint/model/preprocessing/failed predictions.',
        'Next one bounded hypothesis may align training objective with RAW SPACE MAE instead of normalized-residual squared loss. Example:train-only weighted-median coefficient of past availability trend with a fixed0..1constraint;one prespecified fit,not a validation grid. Freeze method/gates/data hashes first. Use ONLY sealed historical examples CSV,not mutable livehistory or post-cutoff snapshots. Few global timestamps limit inference. If it cannot beat persistence on both raw/macro-origin development,keep baseline and do not enable a learned final.',
        'Only if a candidate passes DEVELOPMENT and is frozen BEFORE2026-10-26T10:00Z:implement/test actual prospective issuance integration with immutable forecast batches/checkpoint+reservation/source receipt bindings,commit timestamps before20minute target window,dedup IDs,no outcome fields. No retroactive forecasts. Final guard singapore_holdouts.final_once requires verified bound issuance ledger,complete final_target_end,and durable global overlap-aware claim before target callback;failed callbacksconsumeinterval. Final scoring callback/integration is NOT implemented yet. Missing forecast/targets =>not evaluable,not zero/perfection. Existingbaseline collector can continue independently.',
        'Counter64;wakeups43;source58;next separate100-run live checkpoint100;no activejobs/locks.260software tests PASS(11history/holdout fixtures plus4ridge fixtures added to245). Real future labels remain unread;all claims in tests were synthetic underoutputs/test_fixtures. Existing originalcamera models/Birmingham reports/checkpoints/finals unchanged;twooccupancyheadattempts remain rejected. CNRrights unresolved;source018wholecollection development-exposed. Existing Excel comparison and424fileoffline package remain dated.',
        'Latest officialSingapore'+live['checked_at']+':47snapshots,1110new frozen persistence matches,40753total,MAE4.828111spaces;1240new forecasts frozen;missingtargets unscored. Next sensible collection AFTER'+next_poll+'. Respect minimum1minute. No camera accuracy from aggregate counts,no Birmingham-to-Singapore validation claim. Python/Jupyter preserved;physical/manual/browser/student/official university acceptance remains open.'
    ];dump('data/automation_state.json',state)
    note=('Sealed46receipt-hash-bound snapshots before07:46:23UTC for a source-specific forecast study.111,458parsed rows yield56,136fresh observations;4,547observation-age and50,775source-lag records excluded,0exactduplicates/conflicting revisions among fresh candidates. '+
        'Two known observations10-45minutes apart,same carpark/lot/capacity,form only causal features;first received fresh target20-45minutes later is used,no interpolation. Training labels must arrive before GLOBAL training cutoff21:27:05UTC25October. '+
        '18,393training windows across18origins/1,355series and9,202development windows across9origins/1,243series;many lots are not many independent days. Development actual target lead27.30-43.01minutes,not exact30. '+
        'BEFORE fitting,reserved ALLcarparks future origin interval26October10:00UTCto27October10:00UTC,target/deliveryclosure27October10:51UTC. Future values unread/unconsumed;receipt availability,late-freeze,ledger hashes,target-free issuances,global overlap claims and failed-callback consumption covered by synthetic tests. Operational learned issuance/final scoring callback not yet built. '+
        'One fixed non-neural ridge residual learner(strength.1,6causal features,training-only scaling)failed development:rawMAE7.738379vs6.957618persistence,macro-origin7.732101vs6.953844. Checkpoint roundtrip/bounds pass;no learned forecasts enabled,no final/neural/camera score. Model/source/predictions and rejected result retained. '+
        '260software tests pass. Admission62->63,learnedbaseline63->64;wakeups43/source58/next100-run milestone100/no activejobs. '+
        'Currentmain Singapore47snapshots adds1,110previously frozen persistence matches:40,753total,MAE4.828111spaces,1,240newforecasts. Its07:55post-cutoff snapshot is excluded from the sealed model history;missingtargets unscored. Global rollingbaseline cohort differs from9,202development cohort. '+
        'Original vision/occupancy/Birmingham/neural checkpoints and consumed finalclaims unchanged. Next:one MAE-aligned train-only hypothesis or continue collection;no grid/retrospective final. Guide:docs/SINGAPORE_FORECAST_STUDY.md.')
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','docs/DATASET_PROVENANCE.md','docs/THIRD_PARTY_SOURCES.md']:append(p,note)
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;items=list(reader)
    for row in items:
        if row['requirement_id'] in ['DATA-04','DATA-03','QA-02']:
            row['actual_evidence']+='; reports/singapore_forecast_study_latest.json; models/singapore_history_admission.json; models/singapore_ridge_development.json'
            row['test_result']+=';18393source-consistent train/9202development windows;future global period reserved;linear baseline fails7.738vs6.958MAE;260software tests'
            row['open_problems']+=';Only18train/9development globaltimes;no qualified learned future forecast issuance/final score yet'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(items)
    dump(E/'handoff.json',dict(recorded_at=now,completed_trials=64,wakeups=43,source_records=58,next_live_milestone=100,study=pointer,all260software_tests_passed=True,
        future_final_reserved_unread_unconsumed=True,original_models_claims_unchanged=True,no_active_jobs=True,next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(trials=64,wakeups=43,history_snapshots=46,current_snapshots=snapshots,train=18393,development=9202,learned_gate=False),indent=2))
if __name__=='__main__':main()
