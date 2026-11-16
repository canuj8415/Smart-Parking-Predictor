"""Required milestone feed/app validation; never replay older target snapshots.

Acquires one official snapshot using existing immutable receipts/history. Scores
only the existing rolling persistence plan; frozen learned final scoring is separate.
"""
import argparse,csv,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    s=read(ROOT/'data/automation_state.json');milestone=s['next_live_checkpoint_at_run'];assert s['completed_recorded_runs_since_schedule']>=milestone and not s['active_training_jobs'] and not s['active_validation_jobs']
    now=datetime.now(timezone.utc);rid=f'LIVE-MILESTONE-{milestone}-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    code=['scripts/checkpoint_live_milestone.py','src/smart_parking/live.py','src/smart_parking/prospective.py','src/smart_parking/app.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=166,milestone=milestone,counter_before=s['completed_recorded_runs_since_schedule'],source_ids=['SRC-LIVE-001'],
        hypothesis='The required completed-run milestone remains compatible with a fresh official feed and the actual hidden native live-table/filter/status callback.',
        gates=['One new receipted official acquisition at least60seconds after previous poll','Timestamp aware,feed age between-60and180seconds at acquisition','All accepted count bounds and canonical identities valid;raw rejects/duplicates disclosed','Exact per-checkpoint normalized CSV round-trip','Actual hidden app table/counts/filter/provider/status agree with acquired real rows','Source/protected hashes unchanged;no learned final callback or camera accuracy claim'],
        source_hashes={f:digest(ROOT/f) for f in code},protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T040910Z/checks.json')['frozen_hashes_unchanged'],
        maximum_seconds=180,maximum_app_seconds=90,polling_minimum_seconds=60,licence='Singapore Open Data Licence1.0',scope='Fresh aggregate availability and software integration only. No neural inference/CCTV ground truth,old target replay,learned matching or final scoring. A mocked backend return delivers the actual freshly acquired rows to native app callback without a second poll.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json')

def app_worker(path):
    from unittest.mock import patch
    from smart_parking.app import ParkingApp
    out=Path(path).parent;a=read(out/'acquisition.json');assert digest(out/'rows.json')==a['rows_sha256'];rows=read(out/'rows.json');metadata=a['metadata'];app=ParkingApp();app.withdraw();errors=[];clock=time.perf_counter()
    try:
        with patch('smart_parking.live.get_live',return_value=(rows,metadata)) as backend,patch('smart_parking.app.messagebox.showerror',side_effect=lambda title,message:errors.append(str(message))):
            app.refresh_live(True)
            while app.busy and time.perf_counter()-clock<60:app.update();time.sleep(.01)
            assert not app.busy and not errors,errors;assert backend.call_count==1 and backend.call_args.kwargs==dict(refresh=True)
            children=app.live_table.get_children();assert len(children)==len(rows)
            displayed=[app.live_table.item(key,'values') for key in children]
            expected=[[str(r[k]) for k in ['car_park_id','lot_type','capacity','occupied','available','observed_at']] for r in rows]
            assert [[str(cell) for cell in v] for v in displayed]==expected
            query=rows[0]['car_park_id'];app.query.set(query);app.filter_live();filtered=app.live_table.get_children();assert len(filtered)==sum(query.upper() in r['car_park_id'].upper() for r in rows)
            text=app.live_info.get();assert rows[0]['feed_timestamp'] in text and metadata['path'] in text
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(rows[0]['feed_timestamp'])).total_seconds();state='STALE snapshot' if age>180 else 'Live snapshot';assert text.startswith(state)
            dump(out/'app.json',dict(status='passed',actual_hidden_Tk=True,table_rows=len(children),filtered_rows=len(filtered),query=query,provider_timestamp_displayed=True,storage_path_displayed=True,age_status=state,backend_delivered_acquired_real_rows=True,backend_calls=1,new_network_polls=0,model_calls=0,duration_seconds=time.perf_counter()-clock,visible_manual_acceptance=False))
    finally:app.destroy()

def run(path):
    from smart_parking.live import get_live,latest_snapshot,URL,_count,_observation_key
    from smart_parking.prospective import record_snapshot
    from smart_parking.singapore_issuance import issue_forecasts
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not(out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    for f,h in {**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    sp=ROOT/'data/automation_state.json';s=read(sp);assert s['next_live_checkpoint_at_run']==p['milestone'] and s['completed_recorded_runs_since_schedule']>=p['milestone'];assert not s['active_training_jobs'] and not s['active_validation_jobs']
    prior=latest_snapshot();assert datetime.now(timezone.utc).timestamp()-prior.stat().st_mtime>=60,'Poll not due;resume later without changing protocol'
    s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),maximum_seconds=180)];dump(sp,s);start=datetime.now(timezone.utc).isoformat();clock=time.perf_counter();details={};failure=None;completed=True
    try:
        if (out/'CANCEL').exists():raise InterruptedError('Cancelled before acquisition')
        rows,metadata=get_live(refresh=True);assert not metadata['cached'];rawpath=Path(metadata['path']);assert rawpath!=prior
        payload=read(rawpath);at=datetime.now(timezone.utc);provider=datetime.fromisoformat(metadata['provider_timestamp']);assert provider.tzinfo is not None;age=(at-provider).total_seconds();assert -60<=age<=180,('Provider freshness failure',age)
        receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];receipt=next(v for v in reversed(receipts) if v['source_id']=='SRC-LIVE-001' and (ROOT/v['local_path']).resolve()==rawpath.resolve());assert receipt['sha256']==digest(rawpath) and receipt['source_url']==URL
        raw_lots=0;valid_raw=0;identities=set()
        for item in payload['items']:
            for park in item['carpark_data']:
                for info in park['carpark_info']:
                    raw_lots+=1;capacity=_count(info['total_lots']);available=_count(info['lots_available'])
                    if capacity<=0 or not 0<=available<=capacity:continue
                    valid_raw+=1;identities.add(_observation_key(park['carpark_number'],info['lot_type'],park.get('update_datetime',item['timestamp'])))
        keys=[_observation_key(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows];assert len(keys)==len(set(keys))==len(identities);assert all(0<=r['available']<=r['capacity'] and r['occupied']==r['capacity']-r['available'] for r in rows)
        csvpath=out/'normalized_snapshot.csv'
        with csvpath.open('x',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        with csvpath.open(encoding='utf-8',newline='') as stream:assert list(csv.DictReader(stream))==[{k:str(v) for k,v in row.items()} for row in rows]
        dump(out/'rows.json',rows);dump(out/'acquisition.json',dict(metadata=metadata,receipt=receipt,raw_sha256=digest(rawpath),rows_sha256=digest(out/'rows.json'),normalized_csv_sha256=digest(csvpath)))
        details=dict(url=URL,receipt=receipt,metadata=metadata,raw_sha256=digest(rawpath),normalized_csv=csvpath.relative_to(ROOT).as_posix(),normalized_csv_sha256=digest(csvpath),accepted_rows=len(rows),car_parks=len({r['car_park_id'] for r in rows}),raw_lot_records=raw_lots,invalid_bounds_excluded=raw_lots-valid_raw,exact_raw_duplicates_deduplicated=valid_raw-len(identities),accepted_duplicate_rows=0,feed_age_seconds_at_acquisition=age,bounds_valid=True,csv_roundtrip=True)
        baseline=record_snapshot(rows,metadata);issuance=issue_forecasts(ROOT/'data/manifests/singapore_trend_issuance_v1.json')
        if (out/'CANCEL').exists():raise InterruptedError('Cancelled after acquisition;raw/receipts preserved')
        child=subprocess.run([sys.executable,__file__,'--app',str(path)],cwd=ROOT,capture_output=True,text=True,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);(out/'app_stdout.txt').write_text(child.stdout,encoding='utf-8');(out/'app_stderr.txt').write_text(child.stderr,encoding='utf-8');assert child.returncode==0,child.stderr
        app=read(out/'app.json');assert app['status']=='passed'
        details.update(app=app,rolling_persistence=baseline,frozen_future_issuance=issuance,individual_park_freshness_not_guaranteed=True)
        for f,h in {**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    except (InterruptedError,KeyboardInterrupt) as error:completed=False;failure=repr(error);dump(out/'interrupted.json',dict(failure=failure,completed_run_counted=False));raise
    except Exception as error:failure=repr(error)
    finally:
        s=read(sp);s['active_validation_jobs']=[];dump(sp,s)
    if completed:
        r=dict(run_id=p['run_id'],milestone=p['milestone'],started_at=start,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=166,protocol_sha256=digest(path),checkpoint_gate_passed=failure is None,failure=failure,details=details,learned_accuracy_evaluated=False,learned_MAE=None,learned_persistence_comparison=None,camera_accuracy_evaluable=False,reason='Aggregate availability has no camera ground truth;learned prospective study remains reserved until its separate once-only closure/scorer',scope=p['scope'])
        dump(out/'run.json',r);dump(ROOT/f'models/live_checkpoint_{p["milestone"]}.json',r)
        reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Required100-run official live/schema/native-app checkpoint',started_at=start,finished_at=r['finished_at'],source_ids='SRC-LIVE-001',split_ids='One newly acquired official snapshot;no labelled camera/final-model evaluation',configuration=path.relative_to(ROOT).as_posix(),architecture='Existing live acquisition/parser/history plus real hidden Tk callback/filter',random_seed=166,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(dict(checkpoint_gate_passed=r['checkpoint_gate_passed'],failure=failure,accepted_rows=details.get('accepted_rows'),camera_accuracy='not_evaluable',learned_performance='not_evaluated')),logs=out.relative_to(ROOT).as_posix(),checkpoints='No model calls/training/weights changes',code_revision_basis='404d3ba plus sealed milestone checker',implementation_sha256=digest(__file__),conclusions='Source/software checkpoint only;no camera or learned accuracy;gate='+str(r['checkpoint_gate_passed']))
        with reg.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(sp);assert p['run_id'] not in s['completed_run_ids'];s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['last_live_milestone_attempt']=r
        if r['checkpoint_gate_passed']:s['last_scheduled_live_checkpoint']=dict(milestone=p['milestone'],run_id=p['run_id'],report=(out/'run.json').relative_to(ROOT).as_posix(),passed=True);s['next_live_checkpoint_at_run']=p['milestone']+s['live_checkpoint_interval_runs']
        dump(sp,s);print(json.dumps(dict(run_id=p['run_id'],counter=s['completed_recorded_runs_since_schedule'],milestone=p['milestone'],gate_passed=r['checkpoint_gate_passed'],failure=failure,accepted_rows=details.get('accepted_rows'))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');parser.add_argument('--app');a=parser.parse_args();app_worker(a.app) if a.app else run(a.run) if a.run else prepare()
