"""Bind the tested final scorer before the already reserved origin period."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_history import aware_utc
from smart_parking.singapore_issuance import load_candidate, _write_exclusive
from smart_parking.singapore_final import load_scoring_manifest


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def main():
    config_path = ROOT/'data/manifests/singapore_trend_issuance_v1.json'
    config, reservation, selection, model = load_candidate(config_path)
    assert digest(config_path) == 'b68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625'
    validation = read('reports/singapore_final_software_validation_latest.json')
    assert validation['data_kind'] == 'synthetic_software_fixture' and all(validation['checks'].values())
    assert all(digest(ROOT/p) == h for p, h in validation['source_hashes'].items())
    evidence = ROOT/'experiments/evidence/HEARTBEAT-20261026T083848Z'
    tests = read(evidence/'software_tests.json')
    assert tests['returncode'] == 0 and 'Ran 284 tests' in tests['stderr']
    now = datetime.now(timezone.utc)
    if not aware_utc(config['frozen_at']) < now < aware_utc(reservation['final_origin_start']):
        raise ValueError('Final scoring implementation must be frozen before origins start')
    path = ROOT/'data/manifests/singapore_trend_scoring_v1.json'
    assert not path.exists()
    sources = {**config['runtime_source_hashes'], **{p: digest(ROOT/p) for p in [
        'src/smart_parking/singapore_final.py', 'scripts/score_singapore_study.py',
        'scripts/freeze_singapore_scoring.py', 'scripts/validate_singapore_final.py',
        'tests/test_singapore_final.py']}}
    value = dict(schema_version=1, source_id='SRC-LIVE-001', frozen_at=now.isoformat(),
        issuance_config=config_path.relative_to(ROOT).as_posix(), issuance_config_sha256=digest(config_path),
        reservation_sha256=config['reservation_sha256'], checkpoint_sha256=selection['checkpoint_sha256'],
        implementation_hashes=sources, final_target_end=reservation['final_target_end'],
        plan='Use the unchanged matching/support/improvement rules in the frozen issuance configuration',
        boundary='No target JSON decoding before full closure and durable global claim; callbacks fail closed and consume interval',
        no_issuance_policy='No eligible forecasts means not evaluable; no target JSON decode or fabricated score',
        repeat_policy='Only display an archived completed result; never run a changed method on this interval',
        software_validation_run=validation['run_id'], software_tests_passed=284,
        scope='Local audit evidence only; actual final performance unscored, app unchanged')
    _write_exclusive(path, json.dumps(value, indent=2)+'\n')
    load_scoring_manifest(path)
    _write_exclusive(evidence/'scoring_sources.json', json.dumps({p: dict(sha256=h, source=(ROOT/p).read_text(encoding='utf-8'))
                                                               for p, h in sources.items()}, indent=2)+'\n')
    _write_exclusive(evidence/'frozen_scoring.json', json.dumps(dict(frozen_at=now.isoformat(),
        scoring_manifest=path.relative_to(ROOT).as_posix(), scoring_manifest_sha256=digest(path),
        unchanged_issuance_config_sha256=digest(config_path), checkpoint_sha256=selection['checkpoint_sha256'],
        actual_final_performance_evaluated=False, actual_final_claim_created=False), indent=2)+'\n')
    print(json.dumps(dict(frozen_at=now.isoformat(), scoring_manifest=path.relative_to(ROOT).as_posix(),
                         sha256=digest(path), no_score_before=reservation['final_target_end']), indent=2))


if __name__ == '__main__':
    main()
