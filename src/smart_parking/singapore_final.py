"""Once-only paired final scoring of genuinely receipted forecast batches.

No target JSON is decoded before the global interval claim. The candidate,
issuer, matching rules and scoring implementation must all predate the period.
Local receipt times are audit evidence, not external timestamp attestations.
"""
import hashlib
import json
import math
import time
import csv
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from .provenance import ROOT, digest
from .singapore_history import aware_utc
from .singapore_holdouts import final_once
from .singapore_issuance import (inside, read, records, utc_now, load_candidate,
                                _observations, _write_exclusive)
from .singapore_trend import predict_available

FORECAST_FIELDS = set('capacity origin_available previous_available issued_at origin_available_at previous_available_at origin_observed_at previous_observed_at previous_gap_minutes forecast_id source_id car_park_id lot_type method predicted_available persistence_available origin_provider_time origin_receipt previous_receipt checkpoint_sha256 reservation_sha256 issuance_config_sha256 earliest_target latest_target scope committed_at'.split())


def load_scoring_manifest(path, root=ROOT):
    manifest = read(path)
    config_path = inside(root, manifest['issuance_config'])
    if digest(config_path) != manifest['issuance_config_sha256']:
        raise ValueError('Frozen issuance configuration changed')
    config, reservation, selection, model = load_candidate(config_path, root)
    if (manifest['source_id'] != config['source_id']
            or not aware_utc(config['frozen_at']) <= aware_utc(manifest['frozen_at']) < aware_utc(reservation['final_origin_start'])):
        raise ValueError('Scoring implementation was not frozen before origins')
    for name, expected in manifest['implementation_hashes'].items():
        if digest(inside(root, name)) != expected:
            raise ValueError('Frozen scoring implementation changed')
    return manifest, config, reservation, selection, model


def _acquisition_index(config, root):
    path = inside(root, config['acquisition_receipts'])
    original = path.read_bytes()
    index = {}
    for line in original.decode('utf-8').splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item['source_id'] != config['source_id'] or not item['local_path'].startswith('data/raw/singapore_live/'):
            continue
        aware_utc(item['accessed_at'])
        previous = index.get(item['local_path'])
        if previous and (previous['sha256'] != item['sha256'] or previous['accessed_at'] != item['accessed_at']):
            raise ValueError('Conflicting original acquisition receipts')
        index[item['local_path']] = item
    return index, path, original


def _verified_batches(config, reservation, selection, model, index, config_sha, root):
    """Read outcome-free issuance records and hash raw bytes, without decoding."""
    folder = inside(root, config['batch_receipt_folder'])
    batches = inside(root, config['batch_folder'])
    if (folder/'issuance.lock').exists():
        raise ValueError('Issuance write still in progress')
    forecasts = []
    seen = set()
    inputs = {}
    receipted = set()
    for path in sorted(folder.glob('*.receipt.json')):
        saved = read(path)
        if (saved['source_id'] != config['source_id'] or saved['config_sha256'] != config_sha
                or saved['selection_sha256'] != config['selection_sha256']
                or saved['reservation_sha256'] != config['reservation_sha256']):
            raise ValueError('Batch receipt belongs to another frozen study')
        issue = aware_utc(saved['issued_at']); committed = aware_utc(saved['committed_at'])
        finalized = aware_utc(saved['finalized_at'])
        if not (aware_utc(reservation['final_origin_start']) <= issue < aware_utc(reservation['final_origin_end'])
                and issue <= committed <= finalized < min(issue+timedelta(minutes=3), aware_utc(reservation['final_origin_end']))):
            raise ValueError('Batch was not completed at a valid real issue time')
        batch_path = inside(root, saved['batch_path'])
        if not batch_path.is_relative_to(batches) or digest(batch_path) != saved['batch_sha256']:
            raise ValueError('Committed batch moved or changed')
        batch = records(batch_path)
        if len(batch) != saved['forecasts'] or not batch:
            raise ValueError('Committed batch count changed')
        inputs[path.relative_to(Path(root).resolve()).as_posix()] = digest(path)
        inputs[saved['batch_path']] = saved['batch_sha256']
        receipted.add(batch_path)
        for row in batch:
            if set(row) != FORECAST_FIELDS:
                raise ValueError('Unknown/outcome fields in pre-target issuance ledger')
            if (row['source_id'] != config['source_id'] or row['method'] != model['method']
                    or row['checkpoint_sha256'] != selection['checkpoint_sha256']
                    or row['reservation_sha256'] != config['reservation_sha256']
                    or row['issuance_config_sha256'] != config_sha
                    or row['issued_at'] != saved['issued_at'] or row['committed_at'] != saved['committed_at']):
                raise ValueError('Forecast/model/batch identity mismatch')
            if (aware_utc(row['earliest_target']) != issue+timedelta(minutes=20)
                    or aware_utc(row['latest_target']) != issue+timedelta(minutes=45)):
                raise ValueError('Frozen target window changed')
            if row['origin_receipt']['local_path'] != saved['origin_snapshot']:
                raise ValueError('Origin snapshot differs from batch receipt')
            for key in ['origin_receipt', 'previous_receipt']:
                receipt = row[key]
                if receipt != index.get(receipt['local_path']) or aware_utc(receipt['accessed_at']) > issue:
                    raise ValueError('Input was not in the actual acquisition log before issue')
                if digest(inside(root, receipt['local_path'])) != receipt['sha256']:
                    raise ValueError('Original acquired input bytes changed')
                inputs[receipt['local_path']] = receipt['sha256']
            if (row['origin_available_at'] != row['origin_receipt']['accessed_at']
                    or row['previous_available_at'] != row['previous_receipt']['accessed_at']):
                raise ValueError('Feature availability times differ from receipts')
            identity = '|'.join([config['source_id'], selection['checkpoint_sha256'], config['reservation_sha256'],
                                  row['car_park_id'], row['lot_type'], row['origin_observed_at']])
            expected = hashlib.sha256(identity.encode()).hexdigest()
            if row['forecast_id'] != expected or expected in seen:
                raise ValueError('Changed or duplicate frozen forecast identity')
            if (not math.isclose(row['predicted_available'], predict_available(model, [row])[0], abs_tol=1e-9)
                    or type(row['persistence_available']) is not int
                    or row['persistence_available'] != row['origin_available']):
                raise ValueError('Stored predictions differ from the frozen model or last count')
            seen.add(expected); forecasts.append(row)
    unreceipted = sorted(p.relative_to(Path(root).resolve()).as_posix()
                        for p in batches.glob('*.jsonl') if p not in receipted)
    return forecasts, inputs, unreceipted


def _claim_path(reservation, root):
    start = aware_utc(reservation['final_origin_start']).isoformat()
    end = aware_utc(reservation['final_target_end']).isoformat()
    identity = hashlib.sha256(('SRC-LIVE-001|'+start+'|'+end).encode()).hexdigest()
    return inside(root, reservation['claim_registry'])/(identity+'.claim.json')


def _score_targets(forecasts, receipts, config, reservation, selection, run_id, root):
    claim = read(_claim_path(reservation, root))
    if (claim['run_id'] != run_id or claim['canonical_source'] != config['source_id']
            or claim['reservation_sha256'] != config['reservation_sha256']
            or claim['checkpoint_sha256'] != selection['checkpoint_sha256']):
        raise ValueError('Canonical durable final claim is required before opening targets')
    cache = {}
    used_hashes = {}
    def observations(receipt):
        name = receipt['local_path']
        if name not in cache:
            cache[name] = _observations(root, receipt)
            used_hashes[name] = receipt['sha256']
        return cache[name]
    # Reconstruct each saved issue context from bound raw inputs only AFTER the
    # claim: an origin snapshot can also contain outcomes for an earlier issue.
    for row in forecasts:
        identity = (row['car_park_id'], row['lot_type'])
        for which, value_key, time_key in [('origin', 'origin_available', 'origin_observed_at'),
                                          ('previous', 'previous_available', 'previous_observed_at')]:
            candidates = [r for r in observations(row[which+'_receipt'])
                          if (r['car_park_id'], r['lot_type']) == identity and r['observed_at'] == row[time_key]]
            if len(candidates) != 1 or candidates[0]['capacity'] != row['capacity'] or candidates[0]['available'] != row[value_key]:
                raise ValueError('Stored forecast context does not match its original raw snapshot')
            if which == 'origin' and candidates[0]['feed_timestamp'] != row['origin_provider_time']:
                raise ValueError('Stored origin provider timestamp differs from raw snapshot')
    earliest = min(aware_utc(row['issued_at']) for row in forecasts)
    closed = aware_utc(reservation['final_target_end'])
    targets = defaultdict(list)
    for receipt in sorted(receipts.values(), key=lambda r: (aware_utc(r['accessed_at']), r['local_path'])):
        at = aware_utc(receipt['accessed_at'])
        if not earliest < at <= closed:
            continue
        for row in sorted(observations(receipt), key=lambda r: aware_utc(r['observed_at'])):
            targets[(row['car_park_id'], row['lot_type'])].append(row)
    matched = []; missing = []
    for forecast in forecasts:
        issue = aware_utc(forecast['issued_at']); target = None; reason = 'no_admissible_later_target'
        for row in targets.get((forecast['car_park_id'], forecast['lot_type']), []):
            arrived = aware_utc(row['available_at']); observed = aware_utc(row['observed_at'])
            if arrived <= issue or observed <= issue:
                continue
            if arrived > issue+timedelta(minutes=51):
                break
            if row['capacity'] != forecast['capacity']:
                reason = 'fresh_capacity_change_before_match'; break
            if issue+timedelta(minutes=20) <= observed <= issue+timedelta(minutes=45):
                target = row; break
        if target is None:
            missing.append(dict(forecast_id=forecast['forecast_id'], issued_at=forecast['issued_at'], reason=reason))
            continue
        actual = target['available']
        matched.append(dict(forecast_id=forecast['forecast_id'], source_id=config['source_id'],
            car_park_id=forecast['car_park_id'], lot_type=forecast['lot_type'], capacity=forecast['capacity'],
            issued_at=forecast['issued_at'], target_observed_at=target['observed_at'], target_available_at=target['available_at'],
            actual_target_lead_minutes=(aware_utc(target['observed_at'])-issue).total_seconds()/60,
            predicted_available=forecast['predicted_available'], persistence_available=forecast['persistence_available'],
            actual_available=actual, learned_absolute_error=abs(forecast['predicted_available']-actual),
            persistence_absolute_error=abs(forecast['persistence_available']-actual),
            target_snapshot=target['snapshot'], target_snapshot_sha256=target['snapshot_sha256']))
    return matched, missing, used_hashes


def paired_metrics(forecasts, matched, config):
    n = len(matched); total = len(forecasts)
    identities = {row['forecast_id'] for row in forecasts}
    if (not total or len(identities) != total or len({row['forecast_id'] for row in matched}) != n
            or any(row['forecast_id'] not in identities for row in matched)
            or any(not math.isfinite(row[key]) or row[key] < 0 for row in matched
                   for key in ['learned_absolute_error', 'persistence_absolute_error'])):
        raise ValueError('Nonempty unique forecast/match cohort required')
    groups = defaultdict(list)
    for row in matched:
        groups[row['issued_at']].append(row)
    learned = math.fsum(r['learned_absolute_error'] for r in matched)/n if n else None
    baseline = math.fsum(r['persistence_absolute_error'] for r in matched)/n if n else None
    by_origin = {key: dict(samples=len(rows), learned_mae=math.fsum(r['learned_absolute_error'] for r in rows)/len(rows),
                           persistence_mae=math.fsum(r['persistence_absolute_error'] for r in rows)/len(rows))
                 for key, rows in sorted(groups.items())}
    macro = math.fsum(v['learned_mae'] for v in by_origin.values())/len(groups) if n else None
    macro_base = math.fsum(v['persistence_mae'] for v in by_origin.values())/len(groups) if n else None
    worst = max(v['learned_mae']-v['persistence_mae'] for v in by_origin.values()) if n else None
    series = len({(r['car_park_id'], r['lot_type']) for r in matched})
    gates = config['final_gate']
    checks = dict(minimum_matched_forecasts=n >= gates['min_matched_forecasts'],
        minimum_global_origins=len(groups) >= gates['min_global_matched_origins'],
        minimum_series=series >= gates['min_matched_series'],
        matching_coverage=n/total >= gates['min_matched_fraction_of_resolved_forecasts'],
        raw_mae_gain=bool(n and baseline > 0 and learned <= (1-gates['raw_mae_relative_improvement_min'])*baseline),
        macro_origin_noninferior=bool(n and macro <= macro_base),
        no_material_origin_regression=bool(n and worst <= gates['max_each_origin_mae_regression_spaces']))
    return dict(forecasts=total, matched=n, expired_unmatched=total-n, matched_fraction=n/total,
        global_matched_origins=len(groups), matched_series=series, learned_mae_spaces=learned,
        persistence_same_cohort_mae_spaces=baseline, macro_origin_learned_mae=macro, macro_origin_persistence_mae=macro_base,
        relative_improvement=(1-learned/baseline) if n and baseline > 0 else None,
        worst_origin_mae_regression_spaces=worst, by_origin=by_origin, checks=checks,
        final_gate_passed=all(checks.values()), accuracy_evaluable=bool(n),
        missing_target_policy='No invented observations or zero errors; paired metrics use identical matched IDs')


def evaluate_study(manifest_path, *, root=ROOT, clock=utc_now):
    timer = time.monotonic(); now = clock()
    manifest, config, reservation, selection, model = load_scoring_manifest(manifest_path, root)
    if aware_utc(now.isoformat()) < aware_utc(reservation['final_target_end']):
        return dict(status='not_ready', no_score_before=reservation['final_target_end'],
                    learned_performance_evaluated=False, target_json_decoded=False)
    if config['final_gate']['no_score_before'] != reservation['final_target_end']:
        raise ValueError('Frozen final closure differs from the reservation')
    if _claim_path(reservation, root).exists():
        raise ValueError('Final interval already consumed; read archived result, never rescore')
    config_path = inside(root, manifest['issuance_config']); config_sha = digest(config_path)
    index, acquisition_path, acquisition_bytes = _acquisition_index(config, root)
    forecasts, inputs, unreceipted = _verified_batches(config, reservation, selection, model, index, config_sha, root)
    if not forecasts:
        return dict(status='not_evaluable_no_eligible_issuance', learned_performance_evaluated=False,
                    target_json_decoded=False, unreceipted_batches=unreceipted)
    run_id = 'SG-FINAL-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    folder = inside(root, 'experiments/results/'+run_id); folder.mkdir(parents=True, exist_ok=False)
    ledger = folder/'forecast_ledger.jsonl'
    _write_exclusive(ledger, ''.join(json.dumps(row)+'\n' for row in forecasts))
    guard_selection = dict(selection, forecast_ledger=ledger.relative_to(Path(root).resolve()).as_posix(),
        forecast_ledger_sha256=digest(ledger), original_preperiod_selection_sha256=config['selection_sha256'],
        ledger_attachment_scope='Derived after closure from immutable pre-target batches; candidate was frozen earlier')
    guard_path = folder/'guard_selection.json'; _write_exclusive(guard_path, json.dumps(guard_selection, indent=2)+'\n')
    _write_exclusive(folder/'acquisition_receipts_snapshot.json', json.dumps(list(index.values()), indent=2)+'\n')
    inputs.update({manifest['issuance_config']: config_sha,
                   Path(manifest_path).resolve().relative_to(Path(root).resolve()).as_posix(): digest(manifest_path),
                   config['selection']: config['selection_sha256'],
                   config['reservation']: config['reservation_sha256']})
    def callback(value):
        matched, missing, targets = _score_targets(forecasts, index, config, value, selection, run_id, root)
        metrics = paired_metrics(forecasts, matched, config)
        hashes = {**inputs, **targets}
        if any(digest(inside(root, name)) != expected for name, expected in hashes.items()):
            raise ValueError('Final inputs changed during evaluation')
        if acquisition_path.read_bytes()[:len(acquisition_bytes)] != acquisition_bytes:
            raise ValueError('Historical acquisition log was rewritten during scoring')
        if matched:
            with (folder/'observations.csv').open('x', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(matched[0])); writer.writeheader(); writer.writerows(matched)
        _write_exclusive(folder/'unmatched.json', json.dumps(missing, indent=2)+'\n')
        report = dict(run_id=run_id, started_at=now.isoformat(), completed_at=clock().isoformat(),
            duration_seconds=time.monotonic()-timer, source_ids=[config['source_id']], seed=133,
            metrics=metrics, input_hashes=hashes, implementation_hashes=manifest['implementation_hashes'],
            scoring_manifest_sha256=digest(manifest_path), issuance_config_sha256=config_sha,
            checkpoint_sha256=selection['checkpoint_sha256'], forecast_ledger_sha256=digest(ledger),
            unreceipted_batches_excluded=unreceipted, missing_reasons=dict(Counter(r['reason'] for r in missing)),
            claim_path=_claim_path(value, root).relative_to(Path(root).resolve()).as_posix(),
            data_kind=config.get('data_kind', 'real_public_observations'),
            scope=('Synthetic software fixture; no measured parking accuracy' if config.get('data_kind') == 'synthetic_software_fixture'
                   else 'Real aggregate availability only; variable20-45minute horizon; no neural/camera/Birmingham-transfer accuracy'),
            validity='Requires completed global claim outcome AND completion receipt; failure never reopens interval')
        _write_exclusive(folder/'run.json', json.dumps(report, indent=2)+'\n')
        return report
    result = final_once(inside(root, config['reservation']), guard_path, inside(root, selection['checkpoint']), run_id,
        callback, as_of=now.isoformat(), receipts=inside(root, reservation['claim_registry']),
        expected_reservation_sha256=config['reservation_sha256'], root=root)
    _write_exclusive(folder/'completed.json', json.dumps(dict(run_id=run_id, run_sha256=digest(folder/'run.json'),
        completed_at=clock().isoformat(), status='completed; source interval consumed'), indent=2)+'\n')
    return dict(status='completed', run_id=run_id, result_path=(folder/'run.json').relative_to(Path(root).resolve()).as_posix(),
                learned_performance_evaluated=True, metrics=result['metrics'])
