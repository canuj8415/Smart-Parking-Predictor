"""Freeze a passing candidate, issuance implementation and final scoring plan."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_history import aware_utc
from smart_parking.singapore_issuance import load_candidate


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def exclusive(path, data):
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    run = read('models/singapore_trend_development.json')
    assert run['development_gate_passed'] and all(run['checks'].values())
    assert all(digest(ROOT/p) == h for p, h in {**run['source_hashes'], **run['protected_hashes']}.items())
    selection = read('models/singapore_trend_selection.json')
    assert selection == run['selection']
    assert digest(ROOT/selection['checkpoint']) == selection['checkpoint_sha256']
    assert digest(ROOT/run['dataset']) == run['dataset_sha256']
    assert digest(ROOT/run['reservation']) == run['reservation_sha256']
    reservation = read(run['reservation'])
    now = datetime.now(timezone.utc)
    if now >= aware_utc(reservation['final_origin_start']):
        raise ValueError('Study cannot be activated or re-frozen after its origin period starts')
    frozen_selection = ROOT/'data/manifests/singapore_trend_frozen_selection_v1.json'
    config_path = ROOT/'data/manifests/singapore_trend_issuance_v1.json'
    assert not frozen_selection.exists() and not config_path.exists()
    sources = ['scripts/freeze_singapore_trend_study.py', 'scripts/collect_singapore_study.py',
               'src/smart_parking/singapore_issuance.py', 'src/smart_parking/singapore_trend.py',
               'src/smart_parking/singapore_history.py', 'src/smart_parking/singapore_holdouts.py',
               'src/smart_parking/live.py', 'src/smart_parking/prospective.py', 'src/smart_parking/provenance.py']
    config = dict(schema_version=1, source_id='SRC-LIVE-001', frozen_at=now.isoformat(),
        reservation=run['reservation'], reservation_sha256=run['reservation_sha256'],
        selection=frozen_selection.relative_to(ROOT).as_posix(), selection_sha256=digest(ROOT/'models/singapore_trend_selection.json'),
        development_run=run['run_id'], development_run_sha256=digest(ROOT/f"experiments/results/{run['run_id']}/run.json"),
        runtime_source_hashes={p: digest(ROOT/p) for p in sources}, acquisition_receipts='data/resource_receipts.jsonl',
        batch_folder='data/processed/singapore_learned_v1/batches', batch_receipt_folder='data/receipts/singapore_learned_v1',
        cadence_minutes=30, minimum_publisher_poll_interval_seconds=60,
        matching_protocol=dict(source_consistent=True, same_carpark_lot_capacity=True,
            target_observed_minutes_after_actual_issue=[20, 45], target_delivered_minutes_after_issue_max=51,
            target_freshness_at_receipt_seconds_max=180,
            capacity_change_policy='Stop search on first fresh changed-capacity observation; never bridge regimes',
            target_selection='First RECEIVED qualifying target, tied by source observed time; no hindsight revisions',
            missing_targets='Unscored; report coverage, not zero error',
            comparison='Learned and issue-count persistence on identical matched forecast IDs'),
        final_gate=dict(min_matched_forecasts=500, min_global_matched_origins=8, min_matched_series=50,
            min_matched_fraction_of_resolved_forecasts=.75, raw_mae_relative_improvement_min=.01,
            macro_origin_mae_noninferior=True, max_each_origin_mae_regression_spaces=.5,
            no_score_before=reservation['final_target_end']),
        final_claim_policy='Global canonical-source overlap-aware claim before target-scoring callback; failure consumes; no partial peeking',
        temporal_evidence='Actual local UTC clock and immutable local receipts, not external timestamp attestation',
        activation='Research prospective issuance only; application model unchanged; no learned final score yet',
        licence='Singapore Open Data Licence 1.0; official data.gov.sg feed under accepted terms')
    exclusive(frozen_selection, (ROOT/'models/singapore_trend_selection.json').read_bytes())
    exclusive(config_path, (json.dumps(config, indent=2)+'\n').encode('utf-8'))
    load_candidate(config_path, ROOT)
    evidence = ROOT/'experiments/evidence/HEARTBEAT-20261026T080848Z'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence/'frozen_study.json').write_text(json.dumps(dict(frozen_at=now.isoformat(),
        config=config_path.relative_to(ROOT).as_posix(), config_sha256=digest(config_path),
        frozen_selection_sha256=digest(frozen_selection), checkpoint_sha256=selection['checkpoint_sha256'],
        final_values_read=0, forecast_batches_issued=0, production_promoted=False), indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(config=config_path.relative_to(ROOT).as_posix(), sha256=digest(config_path),
                         frozen_at=now.isoformat(), origin_start=reservation['final_origin_start']), indent=2))


if __name__ == '__main__':
    main()
