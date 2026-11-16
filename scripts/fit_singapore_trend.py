"""One fixed MAE-aligned trend hypothesis on the existing sealed past cohort."""
import csv
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_history import aware_utc
from smart_parking.singapore_holdouts import assert_history_allowed, validate_reservation
from smart_parking.singapore_trend import fit_trend, predict_available


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def dump(path, value):
    path = ROOT/path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def scores(rows, predictions):
    if len(rows) != len(predictions) or not rows:
        raise ValueError('Nonempty identical scoring cohorts required')
    groups = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        groups[row['issued_at']].append(abs(prediction-int(row['target_available'])))
    origin_mae = {key: math.fsum(value)/len(value) for key, value in sorted(groups.items())}
    return dict(samples=len(rows), mae_spaces=math.fsum(sum(v) for v in groups.values())/len(rows),
                macro_origin_mae_spaces=math.fsum(origin_mae.values())/len(groups),
                global_origins=len(groups), per_origin_mae_spaces=origin_mae)


def main():
    start = datetime.now(timezone.utc)
    state = read('data/automation_state.json')
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    admission = read('models/singapore_history_admission.json')
    assert admission['summary']['exploratory_history_gate_passed']
    reservation = validate_reservation(read(admission['reservation']))
    assert digest(ROOT/admission['reservation']) == admission['reservation_sha256']
    if start >= aware_utc(reservation['model_freeze_deadline']):
        raise ValueError('Too late to fit a candidate for this reserved final period')
    dataset = next(p for p in admission['derived_files'] if p.endswith('examples.csv'))
    assert digest(ROOT/dataset) == admission['derived_files'][dataset]
    protected = admission['protected_hashes']
    assert all(digest(ROOT/p) == h for p, h in protected.items())
    with (ROOT/dataset).open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        assert row['source_id'] == 'SRC-LIVE-001'
        assert_history_allowed(reservation, row['target_available_at'], row['target_observed_at'])
        assert_history_allowed(reservation, row['origin_available_at'], row['origin_observed_at'])
        assert aware_utc(row['previous_available_at']) < aware_utc(row['issued_at'])
        if row['role'] == 'train':
            assert aware_utc(row['issued_at']) < aware_utc(reservation['training_cutoff'])
            assert aware_utc(row['target_available_at']) <= aware_utc(reservation['training_cutoff'])
        else:
            assert row['role'] == 'development'
            assert aware_utc(row['issued_at']) >= aware_utc(reservation['training_cutoff'])
    train = [row for row in rows if row['role'] == 'train']
    development = [row for row in rows if row['role'] == 'development']
    assert len(train) == 18393 and len(development) == 9202
    run_id = 'SG-LAD-'+start.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT/'experiments/results'/run_id
    folder.mkdir(parents=True, exist_ok=False)
    paths = ['scripts/fit_singapore_trend.py', 'src/smart_parking/singapore_trend.py',
             'src/smart_parking/singapore_history.py', 'src/smart_parking/singapore_holdouts.py']
    hashes = {p: digest(ROOT/p) for p in paths}
    protocol = dict(run_id=run_id, started_at=start.isoformat(), seed=132,
        source_ids=['SRC-LIVE-001'], source_hashes=hashes, protected_hashes=protected,
        hypothesis='A single training-only constrained absolute-error trend coefficient improves space-count MAE over persistence without material per-origin regression.',
        admission_run=admission['run_id'], dataset=dataset, dataset_sha256=digest(ROOT/dataset),
        reservation=admission['reservation'], reservation_sha256=admission['reservation_sha256'],
        training_cutoff=reservation['training_cutoff'], historical_cutoff=reservation['historical_cutoff'],
        method='same_source_lad_trend_v1', coefficient_bounds=[0, 1], nominal_horizon_minutes=30,
        fit='Lower weighted median of (target-current)/past30min_change, weights abs(past30min_change), restricted to [0,1]; zero-change rows add a constant',
        objective='Unclipped space-increment absolute error; inference predictions clipped to physical capacity afterwards',
        features='Two already received same-capacity counts; past observed-time gap only; no actual future lead/target features',
        preprocessing='None', search='One exact fit; no development grid, refit or alternative coefficients',
        development_gate=dict(raw_mae_relative_improvement_min=.01, macro_origin_mae_noninferior=True,
                              max_each_origin_mae_regression_spaces=.5, finite_within_capacity=True),
        scope='Development-only non-neural aggregate availability study; 18 train and 9 development global origins; future final unconsumed')
    dump(folder/'protocol.json', protocol)
    dump(folder/'implementation_sources.json',
         {p: dict(sha256=h, source=(ROOT/p).read_text(encoding='utf-8')) for p, h in hashes.items()})
    lock = ROOT/'outputs/training_locks/singapore_study.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode()); os.close(fd)
    state['active_training_jobs'] = [dict(run_id=run_id, pid=os.getpid(), phase='Single train-only weighted-median fit')]
    dump('data/automation_state.json', state)
    timer = time.monotonic()
    try:
        model = fit_trend(train)
        predictions = predict_available(model, development)
        candidate = scores(development, predictions)
        persistence = scores(development, [int(row['origin_available']) for row in development])
        regressions = {key: value-persistence['per_origin_mae_spaces'][key]
                       for key, value in candidate['per_origin_mae_spaces'].items()}
        checks = dict(raw_mae_improves_at_least1percent=candidate['mae_spaces'] <= .99*persistence['mae_spaces'],
                      macro_origin_noninferior=candidate['macro_origin_mae_spaces'] <= persistence['macro_origin_mae_spaces'],
                      no_origin_regresses_more_than_half_space=max(regressions.values()) <= .5,
                      finite_and_bounded=all(math.isfinite(p) and 0 <= p <= int(r['capacity']) for p, r in zip(predictions, development)))
        checkpoint = ROOT/'models/checkpoints/singapore_trend'/run_id/'model.json'
        dump(checkpoint, dict(model, source_id='SRC-LIVE-001', run_id=run_id,
                             reservation_sha256=protocol['reservation_sha256'], training_cutoff=reservation['training_cutoff']))
        assert predict_available(read(checkpoint), development) == predictions
        frozen = datetime.now(timezone.utc).isoformat()
        assert aware_utc(frozen) < aware_utc(reservation['model_freeze_deadline'])
        selection = dict(run_id=run_id, source_id='SRC-LIVE-001', method=model['method'],
            development_gate_passed=all(checks.values()), checkpoint=checkpoint.relative_to(ROOT).as_posix(),
            checkpoint_sha256=digest(checkpoint), reservation_sha256=protocol['reservation_sha256'],
            frozen_at=frozen, selected_method=model['method'] if all(checks.values()) else 'persistence',
            prospective_forecasts_issued=False, scope='No final score or operational learned issuance yet')
        with (folder/'observations.csv').open('x', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(development[0])+['learned_available', 'learned_absolute_error'])
            writer.writeheader()
            for row, prediction in zip(development, predictions):
                writer.writerow(dict(row, learned_available=prediction, learned_absolute_error=abs(prediction-int(row['target_available']))))
        assert all(digest(ROOT/p) == h for p, h in {**hashes, **protected}.items())
        assert digest(ROOT/dataset) == protocol['dataset_sha256']
        assert digest(ROOT/protocol['reservation']) == protocol['reservation_sha256']
        report = dict(protocol, finished_at=frozen, duration_seconds=time.monotonic()-timer,
            protocol_sha256=digest(folder/'protocol.json'), training_examples=len(train), development_examples=len(development),
            fitted_coefficient=model['coefficient'], informative_training_examples=model['informative_training_examples'],
            candidate=candidate, persistence=persistence, per_origin_mae_regression_spaces=regressions,
            checks=checks, development_gate_passed=all(checks.values()), selection=selection,
            checkpoint_roundtrip_verified=True, future_values_read=0, neural_model_trained=False,
            final_performance_evaluated=False, observations_sha256=digest(folder/'observations.csv'))
        dump(folder/'run.json', report)
        dump('models/singapore_trend_development.json', report)
        dump('models/singapore_trend_selection.json', selection)
        registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig', newline='') as stream:
            fields = csv.DictReader(stream).fieldnames
        entry = dict(experiment_id=run_id, run_type='Single MAE-aligned Singapore trend fit; chronological development only',
            started_at=start.isoformat(), finished_at=frozen, source_ids='SRC-LIVE-001',
            split_ids='Frozen 18393 train / 9202 development; future global final reserved',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(), architecture='One bounded trend coefficient, no intercept',
            optimizer='Exact weighted median; no iterative search', random_seed=132, hardware='CPU', execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds'], evaluation_metrics=json.dumps(dict(coefficient=model['coefficient'], candidate=candidate, persistence=persistence, checks=checks)),
            logs=folder.relative_to(ROOT).as_posix(), checkpoints=selection['checkpoint'],
            code_revision_basis='efe282c plus sealed source snapshots', implementation_sha256=hashes[paths[0]],
            conclusions='Development gate='+str(report['development_gate_passed'])+'; non-neural; future final unscored; no retrospective issuance')
        with registry.open('a', encoding='utf-8', newline='') as stream:
            csv.DictWriter(stream, fieldnames=fields).writerow({key: entry.get(key, '') for key in fields})
        state = read('data/automation_state.json')
        state['completed_run_ids'].append(run_id)
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids']))
        state['last_completed_run'] = run_id
        print(json.dumps(dict(run_id=run_id, coefficient=model['coefficient'], candidate=candidate, persistence=persistence,
                              checks=checks, selected_method=selection['selected_method']), indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json', dict(error=type(error).__name__, detail=str(error), completed_run_counted=False))
        state = read('data/automation_state.json')
        raise
    finally:
        state['active_training_jobs'] = []
        dump('data/automation_state.json', state)
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
