"""One seeded end-to-end SOFTWARE validation; never a real forecast score."""
import csv
import json
import math
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_issuance import issue_forecasts
from smart_parking.singapore_final import evaluate_study


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    start = datetime.now(timezone.utc); timer = time.monotonic()
    run_id = 'SG-FINAL-VALIDATION-'+start.strftime('%Y%m%dT%H%M%S%fZ')
    state_path = ROOT/'data/automation_state.json'; state = read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    folder = ROOT/'experiments/results'/run_id; folder.mkdir(parents=True, exist_ok=False)
    fixture = ROOT/'outputs/singapore_final_validation'/run_id; fixture.mkdir(parents=True, exist_ok=False)
    paths = ['scripts/validate_singapore_final.py', 'src/smart_parking/singapore_final.py',
             'src/smart_parking/singapore_issuance.py', 'src/smart_parking/singapore_holdouts.py',
             'src/smart_parking/singapore_history.py', 'src/smart_parking/singapore_trend.py']
    hashes = {p: digest(ROOT/p) for p in paths}
    protected = read('models/singapore_trend_development.json')['protected_hashes']
    protocol = dict(run_id=run_id, started_at=start.isoformat(), seed=133,
        source_ids=['SYNTHETIC-FIXTURE-SG-FINAL-001'], data_kind='synthetic_software_fixture',
        fixture_creator='Local deterministic generator in scripts/validate_singapore_final.py',
        hypothesis='The real frozen support/improvement gates can be executed end-to-end on a fully synthetic timed cohort with missing targets, strict claim timing and no repeat final callback.',
        source_hashes=hashes, protected_hashes=protected, source_is_public_data=False,
        fixture_plan=dict(series=60, origins=12, source_snapshots=14, capacity=10000,
            trend='Seeded integer slope per series; deliberately manufactured predictable data, not empirical accuracy',
            missing='Omit parks divisible by17 from every fourth synthetic snapshot',
            timestamps='Simulated January2026 timestamps, isolated under outputs/singapore_final_validation'),
        gates=['Use unchanged numeric final support/improvement gates from the real frozen study',
               'No target decode or claim before closure', '>=500 paired matches across >=8origins/50series',
               'Missing targets counted, not assigned zero errors', 'Paired error arithmetic matches known generated slopes',
               'Second final call rejected; original project checkpoints/reservation/config unchanged'],
        no_real_targets_read=True, model_training_performed=False)
    dump(folder/'protocol.json', protocol)
    dump(folder/'implementation_sources.json', {p: dict(sha256=h, source=(ROOT/p).read_text(encoding='utf-8')) for p, h in hashes.items()})
    state['active_validation_jobs'] = [dict(run_id=run_id, cancel_file=(folder/'CANCEL').relative_to(ROOT).as_posix())]
    dump(state_path, state)
    try:
        real_config = read('data/manifests/singapore_trend_issuance_v1.json')
        real_config_sha = digest(ROOT/'data/manifests/singapore_trend_issuance_v1.json')
        reservation_sha = digest(ROOT/real_config['reservation'])
        model_path = ROOT/read(real_config['selection'])['checkpoint']
        (fixture/'model.json').write_bytes(model_path.read_bytes())
        source_copy = fixture/'fixture_source.py'
        source_copy.write_bytes((ROOT/'src/smart_parking/singapore_final.py').read_bytes())
        origin_start = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
        end = origin_start+timedelta(hours=6)
        reservation = dict(source_id='SRC-LIVE-001', carparks_scope='ALL',
            created_at='2026-01-01T00:00:00+00:00', historical_cutoff='2026-01-01T00:00:00+00:00',
            final_origin_start=origin_start.isoformat(), final_origin_end=end.isoformat(),
            final_target_end=(end+timedelta(minutes=51)).isoformat(), claim_registry='claims')
        dump(fixture/'reservation.json', reservation)
        selection = dict(source_id='SRC-LIVE-001', development_gate_passed=True,
            checkpoint='model.json', checkpoint_sha256=digest(fixture/'model.json'),
            reservation_sha256=digest(fixture/'reservation.json'), frozen_at='2026-01-01T00:01:00+00:00')
        dump(fixture/'selection.json', selection)
        config = dict(real_config, data_kind='synthetic_software_fixture', frozen_at='2026-01-01T00:02:00+00:00',
            reservation='reservation.json', reservation_sha256=digest(fixture/'reservation.json'),
            selection='selection.json', selection_sha256=digest(fixture/'selection.json'),
            acquisition_receipts='receipts.jsonl', batch_folder='batches', batch_receipt_folder='batch_receipts',
            runtime_source_hashes={'fixture_source.py': digest(source_copy)},
            final_gate=dict(real_config['final_gate'], no_score_before=reservation['final_target_end']))
        dump(fixture/'config.json', config)
        dump(fixture/'scoring.json', dict(source_id='SRC-LIVE-001', issuance_config='config.json',
            issuance_config_sha256=digest(fixture/'config.json'), frozen_at='2026-01-01T00:03:00+00:00',
            implementation_hashes={'fixture_source.py': digest(source_copy)}))
        rng = random.Random(133); slopes = [rng.randint(-10, 10) for _ in range(60)]
        receipts = []; batches = []
        for k in range(14):
            if (folder/'CANCEL').exists():
                raise InterruptedError('Synthetic validation cancelled; fixtures retained')
            at = origin_start+timedelta(minutes=30*(k-1))
            parks = []
            for park in range(60):
                if k and k % 4 == 0 and park % 17 == 0:
                    continue
                value = 1000+park*20+k*slopes[park]
                parks.append(dict(carpark_number='SYNTHETIC-'+str(park), update_datetime=at.isoformat(),
                    carpark_info=[dict(lot_type='C', total_lots='10000', lots_available=str(value))]))
            name = 'data/raw/singapore_live/synthetic_'+str(k)+'.json'
            dump(fixture/name, dict(items=[dict(timestamp=at.isoformat(), carpark_data=parks)]))
            receipts.append(dict(source_id='SRC-LIVE-001', local_path=name, sha256=digest(fixture/name),
                                 accessed_at=at.isoformat(), data_kind='synthetic_software_fixture'))
            (fixture/'receipts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in receipts), encoding='utf-8')
            if 1 <= k <= 12:
                issue = at+timedelta(seconds=1)
                batches.append(issue_forecasts(fixture/'config.json', root=fixture, clock=lambda: issue))
        early = evaluate_study(fixture/'scoring.json', root=fixture, clock=lambda: end)
        assert early['status'] == 'not_ready' and not (fixture/'claims').exists()
        closed = end+timedelta(minutes=51)
        result = evaluate_study(fixture/'scoring.json', root=fixture, clock=lambda: closed)
        metrics = result['metrics']; assert metrics['final_gate_passed']
        assert metrics['expired_unmatched'] > 0 and metrics['forecasts'] == sum(b['issued'] for b in batches)
        assert math.isclose(metrics['relative_improvement'], read(model_path)['coefficient'], abs_tol=1e-10)
        try:
            evaluate_study(fixture/'scoring.json', root=fixture, clock=lambda: closed)
        except ValueError:
            repeated_blocked = True
        else:
            repeated_blocked = False
        assert repeated_blocked
        assert digest(ROOT/'data/manifests/singapore_trend_issuance_v1.json') == real_config_sha
        assert digest(ROOT/real_config['reservation']) == reservation_sha
        assert all(digest(ROOT/p) == h for p, h in {**hashes, **protected}.items())
        fixture_hashes = {p.relative_to(fixture).as_posix(): digest(p) for p in sorted(fixture.rglob('*')) if p.is_file()}
        dump(folder/'fixture_inventory.json', dict(root=fixture.relative_to(ROOT).as_posix(),
             data_kind='synthetic_software_fixture', generator_seed=133, file_hashes=fixture_hashes))
        finished = datetime.now(timezone.utc).isoformat()
        report = dict(protocol, finished_at=finished, duration_seconds=time.monotonic()-timer,
            fixture_result_path=(fixture/result['result_path']).relative_to(ROOT).as_posix(),
            fixture_inventory_sha256=digest(folder/'fixture_inventory.json'), synthetic_metrics=metrics,
            checks=dict(early_blocked=True, full_frozen_numeric_gates_pass=True, missing_targets_unscored=True,
                        expected_slope_arithmetic=True, repeat_final_blocked=repeated_blocked, real_protected_inputs_unchanged=True),
            scope='Software validation only; manufactured predictability is not real-world forecasting accuracy')
        dump(folder/'run.json', report)
        dump(ROOT/'reports/singapore_final_software_validation_latest.json', report)
        registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig', newline='') as stream:
            fields = csv.DictReader(stream).fieldnames
        entry = dict(experiment_id=run_id, run_type='Synthetic end-to-end final scorer validation; no real accuracy',
            started_at=start.isoformat(), finished_at=finished, source_ids='SYNTHETIC-FIXTURE-SG-FINAL-001',
            split_ids='Generated isolated fixture; no real holdout read', configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Frozen trend issuer, global temporal claim, paired scorer', random_seed=133, hardware='CPU',
            execution_environment=sys.version.split()[0], training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(dict(checks=report['checks'], synthetic_metrics=metrics)),
            logs=folder.relative_to(ROOT).as_posix(), code_revision_basis='ee92d70 plus sealed source snapshots',
            implementation_sha256=hashes[paths[0]], conclusions='Software checks pass; synthetic fixtures are not real forecast accuracy')
        with registry.open('a', encoding='utf-8', newline='') as stream:
            csv.DictWriter(stream, fieldnames=fields).writerow({key: entry.get(key, '') for key in fields})
        state = read(state_path); state['completed_run_ids'].append(run_id)
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids'])); state['last_completed_run'] = run_id
        print(json.dumps(dict(run_id=run_id, checks=report['checks'], issued=metrics['forecasts'],
            matched=metrics['matched'], unmatched=metrics['expired_unmatched'], origins=metrics['global_matched_origins'],
            series=metrics['matched_series'], scope=report['scope']), indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json', dict(error=type(error).__name__, detail=str(error), completed_run_counted=False))
        state = read(state_path)
        raise
    finally:
        state['active_validation_jobs'] = []; dump(state_path, state)


if __name__ == '__main__':
    main()
