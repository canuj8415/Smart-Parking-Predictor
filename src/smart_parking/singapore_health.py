"""Integrity checks for logged forecasts; never decode raw targets or score them.

Raw input bytes are hashed once per path. Their semantic counts are deliberately
not revalidated here, because a later origin can also be an earlier target.
That verification belongs inside the frozen once-only final callback.
"""
import hashlib
import math
from datetime import timedelta
from pathlib import Path
from .provenance import ROOT, digest
from .singapore_history import aware_utc
from .singapore_issuance import inside, read, records, utc_now, load_candidate
from .singapore_final import FORECAST_FIELDS
from .singapore_trend import predict_available


def check_issuance(config_path, *, root=ROOT, as_of=None):
    config, reservation, selection, model = load_candidate(config_path, root)
    now = aware_utc(as_of or utc_now().isoformat())
    config_sha = digest(config_path)
    index = {}
    for item in records(inside(root, config['acquisition_receipts'])):
        if item['source_id'] != config['source_id'] or not item['local_path'].startswith('data/raw/singapore_live/'):
            continue
        previous = index.get(item['local_path'])
        if previous is not None and previous != item:
            raise ValueError('Conflicting source-acquisition metadata')
        index[item['local_path']] = item
    receipt_folder = inside(root, config['batch_receipt_folder'])
    batch_folder = inside(root, config['batch_folder'])
    if (receipt_folder/'issuance.lock').exists():
        raise ValueError('An issuance write is active; check after it finishes')
    hashes = {}; raw_hashes = {}; identifiers = set(); origins = {}; series = set(); saved_batches = set()
    def source_hash(receipt):
        name = receipt['local_path']
        if not name.startswith('data/raw/singapore_live/') or receipt != index.get(name):
            raise ValueError('Forecast input receipt is absent or changed in the acquisition log')
        if name not in raw_hashes:
            raw_hashes[name] = digest(inside(root, name))
        if raw_hashes[name] != receipt['sha256']:
            raise ValueError('Receipted raw input bytes changed')
    receipt_paths = sorted(receipt_folder.glob('*.receipt.json'))
    for path in receipt_paths:
        saved = read(path)
        if (saved['source_id'] != config['source_id'] or saved['config_sha256'] != config_sha
                or saved['reservation_sha256'] != config['reservation_sha256']
                or saved['selection_sha256'] != config['selection_sha256']
                or saved['learned_performance_evaluated'] is not False):
            raise ValueError('Batch receipt does not bind the frozen outcome-free study')
        issue = aware_utc(saved['issued_at']); committed = aware_utc(saved['committed_at'])
        finalized = aware_utc(saved['finalized_at']); end = aware_utc(reservation['final_origin_end'])
        if not (aware_utc(reservation['final_origin_start']) <= issue < end
                and issue <= committed <= finalized < min(end, issue+timedelta(minutes=3)) and finalized <= now):
            raise ValueError('Invalid or future issue/commit/receipt time')
        batch_path = inside(root, saved['batch_path'])
        if not batch_path.is_relative_to(batch_folder) or batch_path in saved_batches:
            raise ValueError('Batch is outside the configured folder or receipted twice')
        actual_sha = digest(batch_path)
        if actual_sha != saved['batch_sha256']:
            raise ValueError('Committed batch checksum changed')
        batch = records(batch_path)
        if type(saved['forecasts']) is not int or len(batch) != saved['forecasts'] or not batch:
            raise ValueError('Batch forecast count changed')
        saved_batches.add(batch_path)
        hashes[path.relative_to(Path(root).resolve()).as_posix()] = digest(path)
        hashes[saved['batch_path']] = actual_sha
        for row in batch:
            if set(row) != FORECAST_FIELDS:
                raise ValueError('Unknown or outcome fields in issuance metadata')
            if (row['source_id'] != config['source_id'] or row['method'] != model['method']
                    or row['checkpoint_sha256'] != selection['checkpoint_sha256']
                    or row['reservation_sha256'] != config['reservation_sha256']
                    or row['issuance_config_sha256'] != config_sha
                    or row['issued_at'] != saved['issued_at'] or row['committed_at'] != saved['committed_at']):
                raise ValueError('Forecast identity differs from its frozen batch/model')
            if (aware_utc(row['earliest_target']) != issue+timedelta(minutes=20)
                    or aware_utc(row['latest_target']) != issue+timedelta(minutes=45)):
                raise ValueError('Declared target window changed')
            for field in ['origin_receipt', 'previous_receipt']:
                receipt = row[field]
                if receipt['source_id'] != config['source_id'] or aware_utc(receipt['accessed_at']) > issue:
                    raise ValueError('Input receipt was unavailable at issue time')
                source_hash(receipt)
            if (row['origin_receipt']['local_path'] != saved['origin_snapshot']
                    or row['origin_available_at'] != row['origin_receipt']['accessed_at']
                    or row['previous_available_at'] != row['previous_receipt']['accessed_at']):
                raise ValueError('Stored availability times differ from original receipts')
            observed = aware_utc(row['origin_observed_at']); provider = aware_utc(row['origin_provider_time'])
            if (not observed <= provider <= issue+timedelta(seconds=30)
                    or issue-observed > timedelta(minutes=3)
                    or issue-aware_utc(row['origin_available_at']) > timedelta(minutes=3)):
                raise ValueError('Origin was stale or invalid at actual issue time')
            capacity = row['capacity']; prediction = row['predicted_available']
            if (type(capacity) is not int or capacity <= 0 or type(prediction) not in (int, float)
                    or not math.isfinite(prediction) or not 0 <= prediction <= capacity
                    or type(row['persistence_available']) is not int or row['persistence_available'] != row['origin_available']
                    or not math.isclose(prediction, predict_available(model, [row])[0], abs_tol=1e-9)):
                raise ValueError('Prediction bounds or frozen-model reproduction failed')
            if any(not isinstance(row.get(k), str) or not row[k].strip() for k in ['car_park_id', 'lot_type']):
                raise ValueError('Missing forecast series identity')
            identity = '|'.join([config['source_id'], selection['checkpoint_sha256'], config['reservation_sha256'],
                                 row['car_park_id'], row['lot_type'], row['origin_observed_at']])
            expected_id = hashlib.sha256(identity.encode()).hexdigest()
            if row['forecast_id'] != expected_id or expected_id in identifiers:
                raise ValueError('Changed or duplicate forecast ID')
            identifiers.add(expected_id); series.add((row['car_park_id'], row['lot_type']))
        origin = origins.setdefault(saved['issued_at'], dict(issued_at=saved['issued_at'], forecasts=0,
            earliest_target=(issue+timedelta(minutes=20)).isoformat(), latest_target=(issue+timedelta(minutes=45)).isoformat(),
            committed_at=saved['committed_at'], finalized_at=saved['finalized_at']))
        origin['forecasts'] += len(batch)
    unreceipted = sorted(p.relative_to(Path(root).resolve()).as_posix() for p in batch_folder.glob('*.jsonl') if p not in saved_batches)
    return dict(checked_at=now.isoformat(), source_id=config['source_id'],
        status='attention_unreceipted_batches' if unreceipted else ('healthy' if identifiers else 'no_eligible_forecasts_yet'),
        batch_receipts=len(receipt_paths), forecasts_logged=len(identifiers), unique_series=len(series), global_origins=len(origins),
        origins=[origins[k] for k in sorted(origins)], unreceipted_batches=unreceipted,
        checkpoint_sha256=selection['checkpoint_sha256'], issuance_config_sha256=config_sha,
        reservation_sha256=config['reservation_sha256'], receipt_and_batch_hashes=hashes, raw_input_hashes=raw_hashes,
        raw_files_hashed_once=len(raw_hashes), predictions_within_capacity=True, frozen_predictions_reproduced=True,
        target_json_decoded=False, raw_semantic_context_verified=False, performance_evaluated=False, final_claim_created=False,
        scope='Logged pre-target metadata integrity only. Raw bytes hashed, not decoded. Local receipts are not external timestamp attestations; final semantic verification remains once-only.')
