"""Seal past receipt-timed history and a fresh GLOBAL future forecasting window."""
import csv,json,sys,time
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
from smart_parking.prospective import SOURCE
from smart_parking.singapore_history import aware_utc,canonical_observation,deduplicate_observations,causal_examples
from smart_parking.singapore_holdouts import validate_reservation,assert_history_allowed
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    started=datetime.now(timezone.utc);rid='SG-HISTORY-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    state=read('data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    chosen=[r for r in receipts if r['source_id']==SOURCE and r['local_path'].startswith('data/raw/singapore_live/') and aware_utc(r['accessed_at'])<=started]
    chosen=sorted(chosen,key=lambda r:aware_utc(r['accessed_at']));assert len({r['local_path'] for r in chosen})==len(chosen) and len(chosen)>=10
    training_cut=aware_utc(chosen[int(.7*len(chosen))]['accessed_at'])
    final_start=started.replace(minute=0,second=0,microsecond=0)+timedelta(hours=3);final_end=final_start+timedelta(hours=24)
    reservation=dict(schema_version=1,source_id=SOURCE,carparks_scope='ALL',created_at=started.isoformat(),historical_cutoff=started.isoformat(),
        training_cutoff=training_cut.isoformat(),final_origin_start=final_start.isoformat(),final_origin_end=final_end.isoformat(),final_target_end=(final_end+timedelta(minutes=51)).isoformat(),
        model_freeze_deadline=final_start.isoformat(),status='RESERVED;not consumed or evaluated',scope='All carparks/lot types globally reserved;later predictor must be frozen before origin window',
        cutoff_basis='Actual acquisition receipts,not filenames/mtime/source timestamps',history_inputs=[dict(path=r['local_path'],sha256=r['sha256'],available_at=r['accessed_at']) for r in chosen],
        claim_registry='data/singapore_forecast_holdout_claims',future_scoring='Once only after final target window closes;preissued bound forecast ledger and passed frozen development gate required',
        not_evaluable_policy='No retrospective predictions if selected model/real issued forecasts absent;missing matching later targets stay unscored')
    validate_reservation(reservation);reservation_path=ROOT/'data/manifests/singapore_forecast_reservation_v1.json';assert not reservation_path.exists(),'Preserve existing reservation'
    dump(reservation_path,reservation)
    paths=['scripts/qualify_singapore_history.py','src/smart_parking/singapore_history.py','src/smart_parking/singapore_holdouts.py','src/smart_parking/live.py','src/smart_parking/prospective.py']
    hashes={p:digest(ROOT/p) for p in paths};protected=read('models/open_space_asset_qualification.json')['protected_hashes']
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=130,source_ids=[SOURCE],source_hashes=hashes,protected_hashes=protected,
        hypothesis='Captured official snapshots support causal two-observation forecasting windows with same-capacity series and chronological global train/development boundaries,while a future global period stays reserved.',
        selected_snapshots=reservation['history_inputs'],reservation=reservation_path.relative_to(ROOT).as_posix(),reservation_sha256=digest(reservation_path),
        historical_cutoff=started.isoformat(),training_cutoff=training_cut.isoformat(),maximum_seconds=180,
        minimums=dict(train_examples=500,development_examples=200,train_global_origin_times=10,development_global_origin_times=6,series_per_role=50),
        gates=['Raw bytes match acquisition receipts','Origin source/feed fresh within3minutes at actual receipt','First exact observation receipt retained;all conflicting revisions quarantined',
            'Nearest previous observation10-45minutes and unchanged capacity','First received later matching target20-45minutes;no imputation',
            'Train target available before global training cutoff;all inputs within frozen past cutoff','All future carparks reserved BEFORE any changed-model fitting/evaluation'],
        limits=['Admission and persistence diagnostic only;no learned forecast trained/scored','Few global timestamps despite many carparks;not thousands of independent days',
            'Historical snapshots already seen in baseline/integration work are DEVELOPMENT,not fresh final data','Actual matched target horizon varies20-45minutes,not exact30minutes','Aggregate counts cannot score camera vision'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,phase='receipt-timed historical admission;future reservation sealed')];dump('data/automation_state.json',state);clock=time.monotonic()
    records=[];rejections=Counter();snapshot_rows=[]
    try:
        for receipt in chosen:
            if (folder/'CANCEL').exists() or time.monotonic()-clock>180:raise InterruptedError('Bounded history audit stopped;reservation retained')
            path=ROOT/receipt['local_path'];assert digest(path)==receipt['sha256']
            rows=parse_feed(read(path));fresh=0
            for row in rows:
                try:
                    normalized=canonical_observation(row,receipt['accessed_at'],receipt['local_path'],receipt['sha256'])
                    assert_history_allowed(reservation,normalized['available_at'],normalized['observed_at'])
                    if aware_utc(normalized['feed_timestamp'])>started:raise ValueError('Source feed exceeds historical cutoff')
                    records.append(normalized);fresh+=1
                except ValueError as error:rejections[str(error)]+=1
            snapshot_rows.append(dict(path=receipt['local_path'],sha256=receipt['sha256'],available_at=receipt['accessed_at'],parsed_rows=len(rows),fresh_rows=fresh))
        observations,conflicts,duplicates=deduplicate_observations(records)
        examples,exclusions=causal_examples(observations,started.isoformat(),training_cut.isoformat())
        derived=ROOT/'data/processed/singapore_history'/rid;derived.mkdir(parents=True,exist_ok=False)
        if examples:
            with (derived/'examples.csv').open('x',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=list(examples[0]));writer.writeheader();writer.writerows(examples)
        dump(derived/'observations.json',observations);dump(derived/'conflicting_observations.json',conflicts)
        roles={}
        for name in ['train','development']:
            rows=[r for r in examples if r['role']==name];origins=sorted({r['issued_at'] for r in rows})
            roles[name]=dict(examples=len(rows),global_origin_times=len(origins),series=len({(r['car_park_id'],r['lot_type']) for r in rows}),
                first_origin=origins[0] if origins else None,last_origin=origins[-1] if origins else None,
                persistence_mae_spaces=sum(r['persistence_absolute_error'] for r in rows)/len(rows) if rows else None,
                actual_target_lead_min=min((r['actual_target_lead_minutes'] for r in rows),default=None),actual_target_lead_max=max((r['actual_target_lead_minutes'] for r in rows),default=None))
        minima=protocol['minimums'];checks=dict(train_examples=roles['train']['examples']>=500,development_examples=roles['development']['examples']>=200,
            train_origin_times=roles['train']['global_origin_times']>=10,development_origin_times=roles['development']['global_origin_times']>=6,
            series_support=all(r['series']>=50 for r in roles.values()))
        summary=dict(raw_snapshots=len(chosen),raw_parsed_rows=sum(x['parsed_rows'] for x in snapshot_rows),fresh_candidate_rows=len(records),
            freshness_rejections=dict(rejections),exact_duplicate_rows_collapsed=duplicates,conflicting_observation_identities=len(conflicts),
            admitted_observations=len(observations),causal_examples=len(examples),roles=roles,excluded_origins=exclusions,
            admission_checks=checks,exploratory_history_gate_passed=all(checks.values()),learned_model_trained_or_scored=False,
            fresh_future_final_reserved=True,future_final_values_read=0,camera_accuracy_evaluated=False)
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**protected}.items()) and digest(reservation_path)==protocol['reservation_sha256']
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-clock,summary=summary,snapshot_audit=snapshot_rows,
            derived_files={p.relative_to(ROOT).as_posix():digest(p) for p in derived.iterdir()},reservation_not_consumed=True)
        dump(folder/'run.json',report);dump('models/singapore_history_admission.json',report)
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Singapore receipt-timed history admission and future reservation;no learned score',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids=SOURCE,
            split_ids='Global chronological train/development;future all-carpark final reserved',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Causal metadata/window builder and durable future-time guard',random_seed=130,hardware='CPU',execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(summary),logs=folder.relative_to(ROOT).as_posix(),code_revision_basis='74e80c9 plus sealed source snapshots',implementation_sha256=hashes[paths[0]],
            conclusions='Exploratory history gate='+str(summary['exploratory_history_gate_passed'])+';future final reserved/unread;no neural/camera accuracy')
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read('data/automation_state.json');state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,summary=summary,reserved=reservation),indent=2))
    except BaseException as error:dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False,reservation_preserved=True));state=read('data/automation_state.json');raise
    finally:state['active_validation_jobs']=[];dump('data/automation_state.json',state)
if __name__=='__main__':main()
