"""Locally timestamped immutable forecast batches; never score targets here.

Acquisition receipts supply availability times. The CLI uses the current clock,
not a caller-supplied historical issue time. These are local audit records, not
external timestamp attestations or camera authentication.
"""
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .live import parse_feed
from .provenance import ROOT, digest
from .singapore_history import aware_utc, canonical_observation, deduplicate_observations
from .singapore_holdouts import validate_reservation
from .singapore_trend import predict_available


def utc_now():
    return datetime.now(timezone.utc)


def inside(root, name):
    path = (Path(root)/name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('Study path must remain inside project')
    return path


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def records(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def load_candidate(config_path, root=ROOT):
    config = read(config_path)
    if config['source_id'] != 'SRC-LIVE-001':
        raise ValueError('Wrong canonical study source')
    for name, expected in config['runtime_source_hashes'].items():
        if digest(inside(root, name)) != expected:
            raise ValueError('Frozen issuance implementation changed')
    reservation_path = inside(root, config['reservation'])
    selection_path = inside(root, config['selection'])
    if digest(reservation_path) != config['reservation_sha256'] or digest(selection_path) != config['selection_sha256']:
        raise ValueError('Frozen reservation or candidate selection changed')
    reservation = validate_reservation(read(reservation_path))
    selection = read(selection_path)
    checkpoint = inside(root, selection['checkpoint'])
    if (selection['source_id'] != config['source_id'] or selection['development_gate_passed'] is not True
            or selection['reservation_sha256'] != config['reservation_sha256']
            or digest(checkpoint) != selection['checkpoint_sha256']
            or not aware_utc(selection['frozen_at']) <= aware_utc(config['frozen_at']) < aware_utc(reservation['final_origin_start'])):
        raise ValueError('Candidate was not qualified and frozen before the final period')
    return config, reservation, selection, read(checkpoint)


def _observations(root, receipt):
    path = inside(root, receipt['local_path'])
    if digest(path) != receipt['sha256']:
        raise ValueError('Acquired raw snapshot checksum changed')
    result = []
    for row in parse_feed(read(path)):
        try:
            result.append(canonical_observation(row, receipt['accessed_at'], receipt['local_path'], receipt['sha256']))
        except ValueError:
            # Original rows remain in the immutable raw snapshot, with the
            # accepted/excluded counts recorded in the batch receipt.
            continue
    return result


def _write_exclusive(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def issue_forecasts(config_path, *, root=ROOT, clock=utc_now):
    config, reservation, selection, model = load_candidate(config_path, root)
    now = clock().astimezone(timezone.utc)
    start = aware_utc(reservation['final_origin_start'])
    end = aware_utc(reservation['final_origin_end'])
    if now < start:
        return dict(status='not_started', issued=0, origin_start=start.isoformat(), learned_performance_evaluated=False)
    if now >= end:
        return dict(status='origin_period_closed', issued=0, learned_performance_evaluated=False)
    receipts = []
    by_path = {}
    for item in records(inside(root, config['acquisition_receipts'])):
        if item['source_id'] != config['source_id'] or not item['local_path'].startswith('data/raw/singapore_live/'):
            continue
        at = aware_utc(item['accessed_at'])
        if at > now or at < now-timedelta(minutes=51):
            continue
        old = by_path.get(item['local_path'])
        if old and (old['sha256'] != item['sha256'] or old['accessed_at'] != item['accessed_at']):
            raise ValueError('Conflicting acquisition receipt for one raw snapshot')
        by_path[item['local_path']] = item
    receipts = sorted(by_path.values(), key=lambda item: item['accessed_at'])
    if not receipts or now-aware_utc(receipts[-1]['accessed_at']) > timedelta(minutes=3):
        return dict(status='no_fresh_receipt', issued=0, learned_performance_evaluated=False)
    origin_receipt = receipts[-1]
    origin_rows = _observations(root, origin_receipt)
    previous_rows = []
    receipt_by_path = {item['local_path']: item for item in receipts}
    for item in receipts[:-1]:
        previous_rows.extend(_observations(root, item))
    previous_rows, conflicts, duplicates = deduplicate_observations(previous_rows)
    series = {}
    for row in previous_rows:
        series.setdefault((row['car_park_id'], row['lot_type']), []).append(row)
    excluded = Counter()
    batch = []
    for origin in origin_rows:
        key = (origin['car_park_id'], origin['lot_type'])
        observed = aware_utc(origin['observed_at'])
        if observed > now or now-observed > timedelta(minutes=3):
            excluded['origin_stale_at_actual_issue'] += 1
            continue
        candidates = [row for row in series.get(key, []) if aware_utc(row['observed_at']) < observed]
        if not candidates:
            excluded['no_previous_observation'] += 1
            continue
        # Use the nearest known source observation; never skip a changed
        # capacity regime or a too-short gap to find a convenient older row.
        previous = max(candidates, key=lambda row: row['observed_at'])
        if previous['capacity'] != origin['capacity']:
            excluded['previous_capacity_changed'] += 1
            continue
        gap = (observed-aware_utc(previous['observed_at'])).total_seconds()/60
        context = dict(capacity=origin['capacity'], origin_available=origin['available'],
            previous_available=previous['available'], issued_at=now.isoformat(),
            origin_available_at=origin['available_at'], previous_available_at=previous['available_at'],
            origin_observed_at=origin['observed_at'], previous_observed_at=previous['observed_at'], previous_gap_minutes=gap)
        try:
            prediction = predict_available(model, [context])[0]
        except ValueError:
            excluded['invalid_past_context_or_gap'] += 1
            continue
        identity = '|'.join([config['source_id'], selection['checkpoint_sha256'], config['reservation_sha256'],
                             key[0], key[1], origin['observed_at']])
        batch.append(dict(context, forecast_id=hashlib.sha256(identity.encode()).hexdigest(),
            source_id=config['source_id'], car_park_id=key[0], lot_type=key[1],
            method=model['method'], predicted_available=prediction, persistence_available=origin['available'],
            origin_provider_time=origin['feed_timestamp'], origin_receipt=origin_receipt,
            previous_receipt=receipt_by_path[previous['snapshot']],
            checkpoint_sha256=selection['checkpoint_sha256'], reservation_sha256=config['reservation_sha256'],
            issuance_config_sha256=digest(config_path),
            earliest_target=(now+timedelta(minutes=20)).isoformat(), latest_target=(now+timedelta(minutes=45)).isoformat(),
            scope='Real pre-target aggregate forecast; no outcome/error stored; variable 20-45min horizon'))
    batch_folder = inside(root, config['batch_folder'])
    receipt_folder = inside(root, config['batch_receipt_folder'])
    batch_folder.mkdir(parents=True, exist_ok=True)
    receipt_folder.mkdir(parents=True, exist_ok=True)
    lock = receipt_folder/'issuance.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd)
    try:
        seen = set()
        for path in sorted(receipt_folder.glob('*.receipt.json')):
            saved = read(path)
            original = inside(root, saved['batch_path'])
            if digest(original) != saved['batch_sha256']:
                raise ValueError('Previously committed forecast batch changed')
            for forecast in records(original):
                if forecast['forecast_id'] in seen:
                    raise ValueError('Duplicate forecast identity in committed batches')
                seen.add(forecast['forecast_id'])
        added = [row for row in batch if row['forecast_id'] not in seen]
        if not added:
            return dict(status='no_new_eligible_observations', issued=0, excluded=dict(excluded), learned_performance_evaluated=False)
        committed = clock().astimezone(timezone.utc)
        if not now <= committed < min(end, now+timedelta(minutes=3)):
            raise ValueError('Clock moved or issuance took too long; no backdated predictions')
        for row in added:
            row['committed_at'] = committed.isoformat()
        # A fixed raw-snapshot identifier prevents retries after a partial
        # write from retroactively repairing an unreceipted batch.
        batch_path = batch_folder/(origin_receipt['sha256']+'.jsonl')
        receipt_path = receipt_folder/(origin_receipt['sha256']+'.receipt.json')
        _write_exclusive(batch_path, ''.join(json.dumps(row)+'\n' for row in added))
        finalized = clock().astimezone(timezone.utc)
        if not committed <= finalized < min(end, now+timedelta(minutes=3)):
            raise ValueError('Batch did not finish in time; unreceipted batch is ineligible')
        receipt = dict(source_id=config['source_id'], issued_at=now.isoformat(), committed_at=committed.isoformat(),
            finalized_at=finalized.isoformat(), batch_path=batch_path.relative_to(Path(root).resolve()).as_posix(),
            batch_sha256=digest(batch_path), forecasts=len(added), config_sha256=digest(config_path),
            reservation_sha256=config['reservation_sha256'], selection_sha256=config['selection_sha256'],
            origin_snapshot=origin_receipt['local_path'], original_fresh_rows=len(origin_rows),
            previous_conflicts_quarantined=len(conflicts), previous_exact_duplicates_collapsed=duplicates,
            excluded=dict(excluded), learned_performance_evaluated=False)
        _write_exclusive(receipt_path, json.dumps(receipt, indent=2)+'\n')
        return dict(status='issued', issued=len(added), receipt_path=receipt_path.relative_to(Path(root).resolve()).as_posix(),
                    receipt_sha256=digest(receipt_path), learned_performance_evaluated=False)
    finally:
        lock.unlink(missing_ok=True)
