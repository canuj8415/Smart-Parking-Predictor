"""Score the frozen study once after closure; before then report pending only."""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_final import evaluate_study
from smart_parking.singapore_issuance import inside, read


def dump(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    manifest = ROOT/'data/manifests/singapore_trend_scoring_v1.json'
    saved_path = ROOT/'reports/singapore_final_latest.json'
    if saved_path.exists():
        saved = read(saved_path); path = inside(ROOT, saved['result_path'])
        if (saved['scoring_manifest_sha256'] != digest(manifest)
                or digest(path) != saved['result_sha256']
                or digest(path.parent/'completed.json') != saved['completion_sha256']):
            raise ValueError('Archived final result binding changed; do not rescore')
        report = read(path)
        outcome = inside(ROOT, report['claim_path']).with_suffix('.outcome.json')
        if read(outcome)['status'] != 'completed;interval consumed':
            raise ValueError('Global final claim did not complete successfully')
        print(json.dumps(dict(status='archived_completed_result; no new evaluation',
                              result_path=saved['result_path'], metrics=report['metrics']), indent=2))
        return
    state_path = ROOT/'data/automation_state.json'; state = read(state_path)
    if state['active_training_jobs'] or state['active_validation_jobs']:
        raise RuntimeError('Another recorded training/validation job is active')
    # No historical-clock or alternative-method command-line override exists.
    result = evaluate_study(manifest)
    dump(ROOT/'reports/singapore_final_status.json', dict(checked_at=datetime.now(timezone.utc).isoformat(), **result))
    if result['status'] == 'completed':
        path = inside(ROOT, result['result_path']); report = read(path)
        registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream); fields = reader.fieldnames; existing = list(reader)
        if any(row['experiment_id'] == report['run_id'] for row in existing):
            raise ValueError('Final run already registered; no second result is allowed')
        entry = dict(experiment_id=report['run_id'], run_type='Once-only real Singapore aggregate paired final',
            started_at=report['started_at'], finished_at=report['completed_at'], source_ids='SRC-LIVE-001',
            split_ids='Reserved ALL-carpark origins26October10:00UTC to27October10:00UTC; actual pre-target batches only',
            configuration='data/manifests/singapore_trend_scoring_v1.json', architecture='Frozen non-neural trend versus paired issue-count persistence',
            random_seed=133, hardware='CPU', execution_environment=sys.version.split()[0], training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(report['metrics']), logs=path.parent.relative_to(ROOT).as_posix(),
            code_revision_basis='Immutable scoring/issuance source manifests', implementation_sha256=digest(ROOT/'src/smart_parking/singapore_final.py'),
            conclusions='Final gate='+str(report['metrics']['final_gate_passed'])+'; aggregate availability only; app unchanged')
        with registry.open('a', encoding='utf-8', newline='') as stream:
            csv.DictWriter(stream, fieldnames=fields).writerow({key: entry.get(key, '') for key in fields})
        state['completed_run_ids'].append(report['run_id'])
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids']))
        state['last_completed_run'] = report['run_id']; dump(state_path, state)
        dump(saved_path, dict(result_path=result['result_path'], result_sha256=digest(path),
            completion_sha256=digest(path.parent/'completed.json'), scoring_manifest_sha256=digest(manifest),
            final_gate_passed=report['metrics']['final_gate_passed'], production_promoted=False))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
