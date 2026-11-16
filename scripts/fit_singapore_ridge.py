"""One fixed source-specific learned baseline on sealed PAST data only."""
import csv,json,sys,os,time,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_history import aware_utc
from smart_parking.singapore_holdouts import assert_history_allowed,validate_reservation
from smart_parking.singapore_ridge import fit_residual_ridge,predict_available
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def scores(rows,predictions):
    errors=[abs(float(p)-int(r['target_available'])) for r,p in zip(rows,predictions)];groups=defaultdict(list)
    for row,error in zip(rows,errors):groups[row['issued_at']].append(error)
    return dict(samples=len(rows),mae_spaces=sum(errors)/len(errors),macro_origin_mae_spaces=sum(sum(v)/len(v) for v in groups.values())/len(groups),global_origins=len(groups))
def main():
    start=datetime.now(timezone.utc);rid='SG-RIDGE-'+start.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    state=read('data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    admission=read('models/singapore_history_admission.json');assert admission['summary']['exploratory_history_gate_passed']
    reservation=validate_reservation(read(admission['reservation']));assert digest(ROOT/admission['reservation'])==admission['reservation_sha256']
    if start>=aware_utc(reservation['final_origin_start']):raise ValueError('Model-freeze deadline passed;no late fitting for this final period')
    data_path=next(p for p in admission['derived_files'] if p.endswith('examples.csv'));assert digest(ROOT/data_path)==admission['derived_files'][data_path]
    with (ROOT/data_path).open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    for row in rows:
        assert row['source_id']=='SRC-LIVE-001'
        assert_history_allowed(reservation,row['target_available_at'],row['target_observed_at']);assert_history_allowed(reservation,row['origin_available_at'],row['origin_observed_at'])
        assert aware_utc(row['previous_available_at'])<aware_utc(row['issued_at'])
        if row['role']=='train':assert aware_utc(row['target_available_at'])<=aware_utc(reservation['training_cutoff'])
        else:assert row['role']=='development' and aware_utc(row['issued_at'])>=aware_utc(reservation['training_cutoff'])
    train=[r for r in rows if r['role']=='train'];development=[r for r in rows if r['role']=='development'];assert len(train)==18393 and len(development)==9202
    paths=['scripts/fit_singapore_ridge.py','src/smart_parking/singapore_ridge.py','src/smart_parking/singapore_history.py','src/smart_parking/singapore_holdouts.py']
    hashes={p:digest(ROOT/p) for p in paths};protected=admission['protected_hashes']
    protocol=dict(run_id=rid,started_at=start.isoformat(),seed=131,source_ids=['SRC-LIVE-001'],source_hashes=hashes,protected_hashes=protected,
        hypothesis='One fixed ridge model of normalized availability residuals can beat persistence on same-source chronological development windows using only issue-time features.',
        admission_run=admission['run_id'],dataset=data_path,dataset_sha256=digest(ROOT/data_path),reservation=admission['reservation'],reservation_sha256=admission['reservation_sha256'],
        method='same_source_ridge_residual_v1',ridge_strength=.1,preprocessing='Training-only feature mean/std',
        target='(later available-origin available)/current capacity',features='Current fraction,past30minute fraction change,past gap,SG-hour sine/cosine,logcapacity;no actual future horizon or target features',
        development_gate=dict(raw_mae_relative_improvement_min=.01,macro_origin_mae_noninferior=True,finite_within_capacity=True),
        scope='Exploratory learned LINEAR baseline,not neural;past development only,future final reserved/unread;no camera/Birmingham-transfer claim')
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    lock=ROOT/'outputs/training_locks/singapore_ridge.lock';lock.parent.mkdir(parents=True,exist_ok=True);fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    state['active_training_jobs']=[dict(run_id=rid,pid=os.getpid(),phase='fixed closed-form ridge fit')];dump('data/automation_state.json',state);timer=time.monotonic()
    try:
        model=fit_residual_ridge(train,.1);predictions=predict_available(model,development);baseline=[int(r['origin_available']) for r in development]
        candidate=scores(development,predictions);persistence=scores(development,baseline)
        checks=dict(raw_mae_improves_at_least1percent=candidate['mae_spaces']<=.99*persistence['mae_spaces'],
            macro_origin_noninferior=candidate['macro_origin_mae_spaces']<=persistence['macro_origin_mae_spaces'],
            finite_and_bounded=all(math.isfinite(p) and 0<=p<=int(r['capacity']) for r,p in zip(development,predictions)))
        checkpoint=ROOT/'models/checkpoints/singapore_ridge'/rid/'model.json';dump(checkpoint,dict(model,source_id='SRC-LIVE-001',run_id=rid,reservation_sha256=protocol['reservation_sha256'],training_cutoff=reservation['training_cutoff']))
        reloaded=predict_available(read(checkpoint),development);assert max(abs(a-b) for a,b in zip(reloaded,predictions))<1e-9
        frozen=datetime.now(timezone.utc).isoformat();assert aware_utc(frozen)<aware_utc(reservation['final_origin_start'])
        selection=dict(run_id=rid,source_id='SRC-LIVE-001',method=model['method'],development_gate_passed=all(checks.values()),checkpoint=checkpoint.relative_to(ROOT).as_posix(),checkpoint_sha256=digest(checkpoint),
            reservation_sha256=protocol['reservation_sha256'],frozen_at=frozen,selected_method=model['method'] if all(checks.values()) else 'persistence',
            prospective_forecasts_issued=False,scope='No final performance or future issuance claimed;do not score retrospective forecasts')
        dump('models/singapore_ridge_selection.json',selection)
        with (folder/'observations.csv').open('x',encoding='utf-8',newline='') as stream:
            fields=list(development[0])+['learned_available','learned_absolute_error'];writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
            for row,pred in zip(development,predictions):writer.writerow(dict(row,learned_available=pred,learned_absolute_error=abs(pred-int(row['target_available']))))
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**protected}.items()) and digest(ROOT/data_path)==protocol['dataset_sha256'] and digest(ROOT/protocol['reservation'])==protocol['reservation_sha256']
        report=dict(protocol,finished_at=frozen,duration_seconds=time.monotonic()-timer,training_examples=len(train),development_examples=len(development),
            candidate=candidate,persistence=persistence,checks=checks,development_gate_passed=all(checks.values()),selection=selection,
            checkpoint_roundtrip_verified=True,future_values_read=0,neural_model_trained=False,learned_linear_model_trained=True,
            final_performance_evaluated=False,observations_sha256=digest(folder/'observations.csv'))
        dump(folder/'run.json',report);dump('models/singapore_ridge_development.json',report)
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Fixed learned LINEAR Singapore forecast baseline;chronological development only',started_at=protocol['started_at'],finished_at=frozen,source_ids='SRC-LIVE-001',
            split_ids='Frozen past18393train/9202development;global future final reserved',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Normalized-residual ridge,6causal inputs plusintercept',optimizer='Closed-form solve',random_seed=131,
            hardware='CPU',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(dict(candidate=candidate,persistence=persistence,checks=checks)),logs=folder.relative_to(ROOT).as_posix(),checkpoints=selection['checkpoint'],
            code_revision_basis='74e80c9 plus sealed source snapshots',implementation_sha256=hashes[paths[0]],conclusions='Development gate='+str(report['development_gate_passed'])+';linear not neural;future final unscored/no retroactive issuance')
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read('data/automation_state.json');state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,candidate=candidate,persistence=persistence,checks=checks,selected_method=selection['selected_method']),indent=2))
    except BaseException as error:dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));state=read('data/automation_state.json');raise
    finally:state['active_training_jobs']=[];dump('data/automation_state.json',state);lock.unlink(missing_ok=True)
if __name__=='__main__':main()
