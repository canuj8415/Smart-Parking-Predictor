"""Check pre-target log integrity only; routine checks never add trial counts."""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_health import check_issuance
from smart_parking.singapore_final import load_scoring_manifest


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-trial', action='store_true', help='One first-integration validation record for this checker version')
    args = parser.parse_args()
    start = datetime.now(timezone.utc); timer = time.monotonic()
    config_path = ROOT/'data/manifests/singapore_trend_issuance_v1.json'
    scoring_path = ROOT/'data/manifests/singapore_trend_scoring_v1.json'
    manifest, config, reservation, selection, model = load_scoring_manifest(scoring_path)
    state_path = ROOT/'data/automation_state.json'; state = read(state_path)
    marker = ROOT/'models/singapore_issuance_health_validation.json'
    folder = None
    paths = ['scripts/check_singapore_issuance_health.py', 'src/smart_parking/singapore_health.py', 'tests/test_singapore_health.py']
    hashes = {p: digest(ROOT/p) for p in paths}
    protected = {**read(ROOT/'models/singapore_trend_development.json')['protected_hashes'], **manifest['implementation_hashes']}
    protected.update({config_path.relative_to(ROOT).as_posix(): digest(config_path), scoring_path.relative_to(ROOT).as_posix(): digest(scoring_path),
        config['selection']: digest(ROOT/config['selection']), selection['checkpoint']: digest(ROOT/selection['checkpoint'])})
    if args.record_trial:
        if marker.exists():
            raise ValueError('This component integration trial is already recorded; use the routine command without --record-trial')
        assert not state['active_training_jobs'] and not state['active_validation_jobs']
        tests = read(ROOT/'experiments/evidence/HEARTBEAT-20261026T120852Z/software_tests.json')
        assert tests['returncode'] == 0 and 'Ran 302 tests' in tests['stderr']
        run_id = 'SG-ISSUANCE-CHECK-'+start.strftime('%Y%m%dT%H%M%S%fZ')
        folder = ROOT/'experiments/results'/run_id; folder.mkdir(parents=True, exist_ok=False)
        protocol = dict(run_id=run_id, started_at=start.isoformat(), seed=136, source_ids=['SRC-LIVE-001'],
            data_kind='real_pre_target_forecast_metadata', source_hashes=hashes, protected_hashes=protected,
            hypothesis='The first actual frozen-study batch is complete, unique, model-bound and timely, with raw input checksums verified without semantic target reads or performance scoring.',
            gates=['At least one genuinely committed real forecast', 'All batch/receipt/config/model/ID/timing/bounds checks pass',
                   'No unknown/outcome fields; raw byte hashes cached once per path', 'No unreceipted partial batches',
                   'No target JSON decoded, semantic source verification or learned error/coverage/accuracy computed',
                   'Original models, frozen methods and existing final claims unchanged;302software tests pass'],
            future_final_evaluated=False, model_training=False,
            boundary='Raw semantic context authentication remains inside the once-only final callback, not this health check')
        dump(folder/'protocol.json', protocol)
        dump(folder/'implementation_sources.json', {p: dict(sha256=h, source=(ROOT/p).read_text(encoding='utf-8')) for p, h in hashes.items()})
        state['active_validation_jobs'] = [dict(run_id=run_id, pid=os.getpid(), phase='One first real metadata integrity validation')]
        dump(state_path, state)
    try:
        health = check_issuance(config_path)
        health['scoring_manifest_sha256'] = digest(scoring_path)
        dump(ROOT/'reports/singapore_issuance_health_latest.json', health)
        if folder is not None:
            checks = dict(actual_forecasts_present=health['forecasts_logged'] > 0,
                logged_metadata_integrity=health['status'] == 'healthy', no_unreceipted_batches=not health['unreceipted_batches'],
                target_json_not_decoded=not health['target_json_decoded'], learned_performance_not_evaluated=not health['performance_evaluated'],
                semantic_context_not_opened=not health['raw_semantic_context_verified'], no_final_claim_created=not health['final_claim_created'])
            assert all(checks.values())
            assert all(digest(ROOT/p) == h for p, h in {**hashes, **protected, **health['receipt_and_batch_hashes'], **health['raw_input_hashes']}.items())
            finished = datetime.now(timezone.utc).isoformat()
            report = dict(protocol, finished_at=finished, duration_seconds=time.monotonic()-timer, health=health,
                checks=checks, all_gates_passed=True, software_tests_passed=302,
                scope='Operational metadata integration only; no learned/camera/neural accuracy, target coverage or final result')
            dump(folder/'run.json', report); dump(marker, report)
            registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
            with registry.open(encoding='utf-8-sig', newline='') as stream:
                fields = csv.DictReader(stream).fieldnames
            entry = dict(experiment_id=run_id, run_type='First real pre-target issuance metadata integration; no accuracy',
                started_at=start.isoformat(), finished_at=finished, source_ids='SRC-LIVE-001', split_ids='Reserved future study logged predictions only; no target decode',
                configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(), architecture='Metadata-only integrity checker with raw-byte hash cache',
                random_seed=136, hardware='CPU', execution_environment=sys.version.split()[0], training_duration=report['duration_seconds'],
                evaluation_metrics=json.dumps(dict(checks=checks, forecasts=health['forecasts_logged'], batch_receipts=health['batch_receipts'],
                    global_origins=health['global_origins'], raw_files_hashed_once=health['raw_files_hashed_once'], performance_evaluated=False)),
                logs=folder.relative_to(ROOT).as_posix(), code_revision_basis='d9234b0 plus sealed source snapshots',
                implementation_sha256=hashes[paths[0]], conclusions='Metadata integration passes; no semantic raw context or target outcome verification; future final remains closed')
            with registry.open('a', encoding='utf-8', newline='') as stream:
                csv.DictWriter(stream, fieldnames=fields).writerow({k: entry.get(k, '') for k in fields})
            state = read(state_path); state['completed_run_ids'].append(run_id)
            state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids'])); state['last_completed_run'] = run_id
        print(json.dumps({k: health[k] for k in ['status', 'forecasts_logged', 'batch_receipts', 'global_origins',
            'raw_files_hashed_once', 'target_json_decoded', 'raw_semantic_context_verified', 'performance_evaluated']}, indent=2))
    except BaseException as error:
        if folder is not None:
            dump(folder/'interrupted.json', dict(error=type(error).__name__, detail=str(error), completed_run_counted=False))
            state = read(state_path)
        raise
    finally:
        if folder is not None:
            state['active_validation_jobs'] = []; dump(state_path, state)


if __name__ == '__main__':
    main()
