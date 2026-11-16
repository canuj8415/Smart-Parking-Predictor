"""One paired real-feed compatibility/adversarial validation, without model training."""
import copy
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.live import parse_feed
from smart_parking.provenance import digest


def dump(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another job is active')
    started=datetime.now(timezone.utc);run_id='LIVE-QUALITY-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run_id;folder.mkdir(parents=True,exist_ok=False)
    files=['scripts/validate_live_quality.py','src/smart_parking/live.py','tests/test_live_quality.py']
    hashes={path:digest(ROOT/path) for path in files}
    previous=subprocess.check_output(['git','show','7ebfc40:src/smart_parking/live.py'],cwd=ROOT).decode()
    raw_paths=sorted((ROOT/'data/raw/singapore_live').glob('*.json'))
    inputs={path.relative_to(ROOT).as_posix():digest(path) for path in raw_paths}
    protocol=dict(run_id=run_id,started_at=started.isoformat(),seed=115,source_ids=['SRC-LIVE-001'],
        hypothesis='Strict semantic duplicate/integer/identity checks preserve accepted real observations while preventing malformed or repeated feed records from becoming extra parking observations.',
        split='Saved real official snapshots; paired compatibility replay plus explicitly synthetic in-memory mutations; no held-out ML dataset',
        source_hashes=hashes,baseline_revision='7ebfc40',baseline_source_sha256=hashlib.sha256(previous.encode()).hexdigest(),
        input_hashes=inputs,gates=['Every saved real parse result exactly equals prior parser output',
            'Exact/equivalent timestamp duplicates do not add observations',
            'Conflicting valid duplicates and float/boolean counts are rejected',
            '176 software tests pass, including raw rejection retention and append-only history integration'],
        model_accuracy_evaluated=False,model_training_performed=False)
    dump(folder/'protocol.json',protocol)
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text()) for p,h in hashes.items()})
    dump(folder/'baseline_source.json',dict(revision='7ebfc40',source=previous,sha256=protocol['baseline_source_sha256']))
    state['active_validation_jobs']=[dict(run_id=run_id,cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    clock=time.perf_counter()
    try:
        namespace={'__name__':'smart_parking._prior_live','__package__':'smart_parking'}
        exec(compile(previous,'7ebfc40:live.py','exec'),namespace)
        old_parse=namespace['parse_feed'];reports=[]
        for path in raw_paths:
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
            payload=json.loads(path.read_text());before=old_parse(payload);after=parse_feed(payload)
            assert after==before,path
            reports.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path),
                                accepted_rows=len(after),exact_prior_output_match=True))
        payload=json.loads(raw_paths[-1].read_text())
        selected=next(p for item in payload['items'] for p in item['carpark_data']
                      if any(0<int(i['lots_available'])<int(i['total_lots']) for i in p['carpark_info']))
        park=copy.deepcopy(selected);park['carpark_info']=[next(i for i in park['carpark_info'] if 0<int(i['lots_available'])<int(i['total_lots']))]
        fixture=dict(items=[dict(timestamp=payload['items'][0]['timestamp'],carpark_data=[park])])
        duplicate=copy.deepcopy(fixture);duplicate['items'][0]['carpark_data'].append(copy.deepcopy(park))
        assert len(old_parse(duplicate))==2 and len(parse_feed(duplicate))==1
        conflict=copy.deepcopy(duplicate);conflict['items'][0]['carpark_data'][1]['carpark_info'][0]['lots_available']=str(int(park['carpark_info'][0]['lots_available'])+1)
        assert len(old_parse(conflict))==2
        try:parse_feed(conflict)
        except ValueError:conflict_rejected=True
        else:raise AssertionError('Conflicting valid duplicate was accepted')
        test_log=ROOT/'experiments/evidence/HEARTBEAT-20261025T164533Z/unit_tests.txt'
        text=test_log.read_text(encoding='utf-8-sig')
        assert 'Ran 176 tests' in text and text.rstrip().endswith('OK')
        assert all(digest(ROOT/path)==h for path,h in inputs.items())
        assert all(digest(ROOT/path)==h for path,h in hashes.items())
        metrics=dict(real_snapshots=len(reports),real_lot_observations=sum(r['accepted_rows'] for r in reports),
                     real_snapshot_exact_matches=len(reports),synthetic_duplicate_old_rows=2,synthetic_duplicate_new_rows=1,
                     synthetic_conflict_rejected=conflict_rejected,software_tests_passed=176,
                     scientific_accuracy=None)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
                    metrics=metrics,snapshots=reports,validation_gate_passed=True,
                    limitations=['Compatibility on saved snapshots is not proof of every future provider schema',
                                 'Synthetic mutation counts are software checks, not real observations or model accuracy',
                                 'Earlier demo bundle remains a dated copy; this changed module is not rebuilt into it'])
        dump(folder/'run.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run_id,run_type='Paired real-feed software compatibility/adversarial validation',
                 started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids='SRC-LIVE-001',
                 split_ids=protocol['split'],configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
                 architecture='Schema/semantic identity/integer validation, no neural model',model_version='none',
                 epochs=0,batch_size='not applicable',random_seed=115,hardware='CPU',execution_environment=sys.version.split()[0],
                 training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(metrics),
                 logs=folder.relative_to(ROOT).as_posix(),checkpoints='No new weights',code_revision_basis='7ebfc40 plus sealed sources',
                 implementation_sha256=hashes[files[0]],conclusions='Compatibility/adversarial gates pass; no scientific accuracy claim')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run_id)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run_id
        dump(ROOT/'models/live_quality_validation.json',report)
        print(json.dumps(dict(run_id=run_id,metrics=metrics),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False))
        state=json.loads(state_path.read_text());raise
    finally:
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
