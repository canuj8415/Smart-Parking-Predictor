"""Recover one completed worker after its parent's duplicate-duration reporting error.

Never repeats inference; retains original protocol, code, stdout and error evidence.
Worker wall timestamps are derived from retained file metadata, not measured stamps.
"""
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.provenance import digest


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def recover():
    out = ROOT / 'experiments/results/ASSIGNMENT-API-20261027T012959957197Z'
    protocol = out / 'protocol.json'
    p = read(protocol)
    assert digest(protocol) == read(out / 'protocol_binding.json')['sha256']
    assert not (out / 'run.json').exists()
    original = ROOT / 'experiments/evidence/HEARTBEAT-20261027T010907Z/assignment_api_runner_before_reporting_fix.py'
    for f, h in {**p['source_hashes'], **p['input_hashes'], **p['protected_hashes']}.items():
        source = original if f == 'scripts/validate_assignment_api.py' else ROOT / f
        assert digest(source) == h, f
    error = read(out / 'interrupted.json')
    assert error['error'] == 'TypeError' and 'duration_seconds' in error['detail']
    assert not (out / 'stderr.txt').read_text().strip()
    assert (out / 'stdout.txt').read_text().count('Completed real TRAIN API case') == 3
    w = read(out / 'worker.json')
    assert len(w['cases']) == 3 and all(c['api_contract_passed'] for c in w['cases'])
    assert w['model_calls'] == p['maximum_model_calls']
    assert w['peak_rss_bytes'] <= p['maximum_worker_rss_bytes'] and w['duration_seconds'] < p['maximum_worker_seconds']
    for i in range(3):
        assert (out / f'analysis_{i}.json').exists() and (out / f'preview_{i}.png').exists()
    state_path = ROOT / 'data/automation_state.json'
    s = read(state_path)
    assert not s['active_training_jobs'] and not s['active_validation_jobs']
    assert p['run_id'] not in s['completed_run_ids']
    registry = ROOT / 'experiments/EXPERIMENT_REGISTRY.csv'
    with registry.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        assert all(row['experiment_id'] != p['run_id'] for row in reader)
    finish = datetime.fromtimestamp((out / 'worker.json').stat().st_mtime, timezone.utc)
    start = finish - timedelta(seconds=w['duration_seconds'])
    recovery = dict(recorded_at=datetime.now(timezone.utc).isoformat(),
                    reason=error, original_runner=original.relative_to(ROOT).as_posix(),
                    original_runner_sha256=digest(original), recovery_code_sha256=digest(__file__),
                    inference_repeated=False, worker_hashes={f.name:digest(f) for f in out.glob('analysis_*.json')},
                    worker_json_sha256=digest(out / 'worker.json'),
                    timestamp_basis='Worker file modification UTC minus measured worker duration; derived, not captured worker wall timestamps',
                    parent_duration_seconds=None)
    r = dict(run_id=p['run_id'], started_at=start.isoformat(), finished_at=finish.isoformat(),
             seed=p['seed'], protocol_sha256=digest(protocol), **w, recovery=recovery,
             integration_gate_passed=True, model_parameters_unchanged=True,
             classification_thresholds_unchanged=True, assignment_semantics_preserved=True,
             final_pixels_or_labels_opened=False, scope=p['scope'])
    dump(out / 'run.json', r)
    dump(ROOT / 'models/assignment_api_validation.json', r)
    dump(ROOT / 'reports/assignment_api_latest.json', r)
    row = dict(experiment_id=p['run_id'], run_type='Actual4KTRAIN FasterRCNN API/schema/resource integration',
               started_at=r['started_at'], finished_at=r['finished_at'], source_ids=';'.join(p['source_ids']),
               split_ids='3 previously exposed TRAIN photos; labels not scored; TEST closed',
               configuration=protocol.relative_to(ROOT).as_posix(), architecture='Existing FasterRCNN+original classifier with bounded assignment',
               random_seed=p['seed'], hardware='CPU4threads/isolated capped worker', execution_environment=sys.version.split()[0],
               training_duration=w['duration_seconds'], evaluation_metrics=json.dumps(r), logs=out.relative_to(ROOT).as_posix(),
               checkpoints='Original weights unchanged', code_revision_basis='145bdc7 plus allocation-only integration',
               implementation_sha256=digest(original), conclusions='API integration pass; reporting error recovered without inference; timestamps derived; not accuracy acceptance')
    with registry.open('a', encoding='utf-8', newline='') as f:
        csv.DictWriter(f, fieldnames=fields).writerow({k:row.get(k, '') for k in fields})
    s['completed_run_ids'].append(p['run_id'])
    s['completed_recorded_runs_since_schedule'] = len(set(s['completed_run_ids']))
    s['last_completed_run'] = p['run_id']
    s['assignment_api_validation'] = r
    dump(state_path, s)
    print(json.dumps(dict(run_id=p['run_id'], count=s['completed_recorded_runs_since_schedule'], recovered=True, inference_repeated=False)))


if __name__ == '__main__':
    recover()
