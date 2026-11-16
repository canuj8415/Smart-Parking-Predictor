"""Preserve one passing development trial and the pre-period issuance freeze."""
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_issuance import load_candidate
from smart_parking.singapore_trend import predict_available

E = ROOT/'experiments/evidence/HEARTBEAT-20261026T080848Z'
TITLE = '## 26 October 2026 / MAE-aligned Singapore trend and frozen prospective issuer'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def dump(path, value):
    (ROOT/path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def append(path, text):
    path = ROOT/path
    old = path.read_text(encoding='utf-8')
    assert TITLE not in old
    path.write_text(old.rstrip()+'\n\n'+TITLE+'\n\n'+text+'\n', encoding='utf-8')


def main():
    assert not (E/'handoff.json').exists()
    run = read('models/singapore_trend_development.json')
    state = read('data/automation_state.json')
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 65
    assert state['last_completed_run'] == run['run_id'] and state['scheduled_wakeups_completed'] == 43
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['development_gate_passed'] and all(run['checks'].values())
    assert all(digest(ROOT/p) == h for p, h in {**run['source_hashes'], **run['protected_hashes']}.items())
    assert digest(ROOT/run['dataset']) == run['dataset_sha256']
    assert digest(ROOT/run['reservation']) == run['reservation_sha256']
    config_path = ROOT/'data/manifests/singapore_trend_issuance_v1.json'
    config, reservation, selection, model = load_candidate(config_path)
    assert digest(config_path) == read(E/'frozen_study.json')['config_sha256']
    tests = read(E/'software_tests.json')
    assert tests['returncode'] == 0 and 'Ran 273 tests' in tests['stderr']
    status = read('reports/singapore_issuance_latest.json')
    assert status['study_issuance']['status'] == 'not_started' and status['study_issuance']['issued'] == 0
    assert not (ROOT/config['batch_folder']).exists() and not (ROOT/config['batch_receipt_folder']).exists()
    claims = ROOT/reservation['claim_registry']
    assert not claims.exists() or not list(claims.glob('*.claim.json'))
    observations = ROOT/f"experiments/results/{run['run_id']}/observations.csv"
    assert digest(observations) == run['observations_sha256']
    with observations.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 9202 and all(row['role'] == 'development' for row in rows)
    predictions = predict_available(model, rows)
    assert max(abs(p-float(row['learned_available'])) for p, row in zip(predictions, rows)) < 1e-9
    assert math.isclose(math.fsum(abs(p-int(row['target_available'])) for p, row in zip(predictions, rows))/len(rows), run['candidate']['mae_spaces'], abs_tol=1e-9)
    # Small statistical checkpoints are also kept in the tracked experiment,
    # alongside the original operational checkpoint, with identical bytes.
    archived_model = observations.parent/'model.json'
    with archived_model.open('xb') as stream:
        stream.write((ROOT/selection['checkpoint']).read_bytes())
    assert digest(archived_model) == selection['checkpoint_sha256']
    now = datetime.now(timezone.utc).isoformat()
    improvement = 1-run['candidate']['mae_spaces']/run['persistence']['mae_spaces']
    pointer = read('reports/singapore_forecast_study_latest.json')
    pointer.update(trend_run=run['run_id'], trend_coefficient=run['fitted_coefficient'],
        trend_development_mae=run['candidate']['mae_spaces'], trend_development_macro_origin_mae=run['candidate']['macro_origin_mae_spaces'],
        same_cohort_persistence_mae=run['persistence']['mae_spaces'], trend_relative_improvement=improvement,
        trend_development_gate_passed=True, ridge_development_gate_passed=False,
        development_gate_passed=True, selected_method=selection['selected_method'],
        selected_research_method=selection['selected_method'], application_integration=False,
        production_promoted=False, issuance_implemented=True, issuance_config=config_path.relative_to(ROOT).as_posix(),
        issuance_config_sha256=digest(config_path), issuance_frozen_at=config['frozen_at'],
        learned_forecasts_issued=False, learned_forecast_batches=0, learned_live_performance_evaluated=False,
        final_scoring_callback_implemented=False, software_tests_passed=273)
    dump('reports/singapore_forecast_study_latest.json', pointer)
    state.update(last_updated_at=now, scheduled_wakeups_completed=44, singapore_forecast_study=pointer)
    live = read('data/processed/singapore_prospective/summary.json')
    next_poll = (datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    state['next_actions'] = [
        'Highest priority: implement and test the once-only learned final matching/scoring callback on SYNTHETIC fixtures before final origins begin. Keep the already frozen matching/support/improvement rules in data/manifests/singapore_trend_issuance_v1.json. Freeze a separate scoring implementation manifest before 2026-10-26T10:00Z. Never open real final outcomes for scoring until 2026-10-27T10:51Z; no partial learned metrics. Existing baseline can remain independent.',
        'Qualified RESEARCH candidate SG-LAD-20261026T081112980974Z: train-only lower weighted-median alpha=0.30018518518518517, bounded [0,1], fixed past30minute trend, no intercept/neural model. SAME 9202 DEVELOPMENT windows: MAE6.3098475293 vs6.9576179092 persistence (9.3102percent reduction); macro6.3060759826 vs6.9538444734. All prespecified gates pass, worst per-origin regression0.4256136034 <0.5spaces. Only9global development times; not a live/final accuracy claim.',
        'Do NOT refit/tune this reserved study. The coefficient, candidate selection, 46 historical snapshots/18393train/9202development, source hashes, and global future reservation are frozen. No post-07:46:23UTC26October observations for fitting/development. Future inference may use already received context with fixed parameters. Ridge failure7.738vs6.958 and all older failed studies remain preserved.',
        'At each due collection run D:\\deep learning\\.venv\\Scripts\\python.exe scripts/collect_singapore_study.py. It preserves official acquisition/normalized/baseline mechanisms, enforces the 30minute plan, then calls the frozen issuer. Before10:00Z it returns not_started. During ALL-carpark origin interval26October10:00Z to27October10:00Z it issues only truly fresh observed contexts with local current-clock commit times, raw receipt/model/config hashes, unique observation IDs, exclusive fsynced batches and separate immutable receipts. No retrospective origins or outcome fields. No app promotion.',
        'Future learned batch paths: data/processed/singapore_learned_v1/batches/*.jsonl; immutable receipts data/receipts/singapore_learned_v1/*.receipt.json. Include new receipt files in local checkpoints. Partial unreceipted batches are ineligible and must not be repaired retroactively. Local clock records are audit evidence, not external timestamp attestation. Preserve frozen config SHA b68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625 and reservation SHA bd47defbec2e4e73388b4eb4ad8dd8d04528a04df15ae78242427ca93f5afaca.',
        'Final protocol already frozen: first RECEIVED fresh same-series/same-capacity target observed20-45min after ACTUAL issue, received by51min; stop at fresh capacity change, no hindsight revision selection. Compare learned and issue-count persistence on identical forecast IDs. Require >=500matches, >=8global matched origins, >=50series, >=75percent matching coverage, >=1percent raw MAE gain, macro-origin noninferiority, no per-origin regression>0.5spaces. Missing targets unscored. Use singapore_holdouts.final_once only after complete closure with verified issuance ledger and global durable overlap claim BEFORE opening targets. Failures consume; no zero/perfection claim.',
        'Counter65; wakeups44; source58; next separate100-run official-live checkpoint100; no active jobs/locks. 273software tests pass (6trend incl100synthetic optimizer problems;7issuance fixtures; not13new experiments). Original models/consumed final claims unchanged. Candidate is research-only. CNR content rights unresolved; source018 collection development-exposed. Current offline package/Excel comparison remain dated; no new GUI/nativeExcel/manual/student/university acceptance.',
        'No network collection this wakeup: last official snapshot07:55:17UTC,47snapshots/40753frozen persistence outcomes/MAE4.8281108139. Next sensible acquisition AFTER '+next_poll+'. Use the new study collection wrapper on next wakeup. It will keep source cadence and issue zero outside reserved origins. Rolling baseline cohort differs from historical development. See docs/SINGAPORE_FORECAST_STUDY.md for student explanation.'
    ]
    dump('data/automation_state.json', state)
    inventory = read('data/dataset_inventory.json')
    inventory.update(inventoried_at=now, singapore_forecast_study=pointer)
    for item in inventory['datasets']:
        if item['source_id'] == 'SRC-LIVE-001':
            item['learned_history_study'] = pointer
    dump('data/dataset_inventory.json', inventory)
    catalog = ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    assert len(items) == len({item['source_id'] for item in items}) == 58
    for item in items:
        if item['source_id'] == 'SRC-LIVE-001':
            item['used_by'] += '; one train-only absolute-error trend trial passed chronological development; research issuer frozen before future origins'
            item['open_issues'] += '; 6.30985vs6.95762spaces on SAME9202development windows only; no learned live/final score; final callback unfinished'
    with catalog.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(items)
    note = ('A single MAE-aligned trend learner fitted alpha=0.3001851852 on the sealed 18,393 training windows. '
        'On the SAME 9,202 development windows it measured 6.309848 spaces MAE versus 6.957618 persistence, a 9.31% reduction; '
        'equal-origin MAE 6.306076 versus 6.953844. The rules were saved before fitting: at least 1% overall gain, macro-origin '
        'noninferiority, every origin regression <=0.5 spaces, physical bounds. All pass; two origins regress slightly, worst 0.425614. '
        'Only nine global development times; this is not live/final/neural/camera accuracy. No validation grid or refit. '
        'The prior ridge failure is preserved. Candidate checkpoint SHA '+selection['checkpoint_sha256']+'. '
        'Research selection and issuer/config frozen at 08:16:03 UTC, before the unchanged ALL-carpark future origin interval '
        '26 October 10:00 UTC–27 October 10:00 UTC. Actual pre-period smoke check returns not_started/zero issued; '
        'no real learned batches, outcomes, or final claims. Exclusive local-clock batches bind original receipts, two causal counts, '
        'model/config/reservation hashes; duplicates, stale/future inputs, changed capacity/checkpoints/batches and delayed writes are blocked. '
        'Local audit times are not external attestations. Final scoring callback remains unfinished; its matching/support/gates are already '
        'frozen in data/manifests/singapore_trend_issuance_v1.json. No real final scoring before 27 October 10:51 UTC. '
        'All 273 software tests pass, including six synthetic trend tests (100 seeded optimizer fixtures within one test) and seven issuance '
        'tests. One completed training/development experiment advances 64->65, wakeups 44, sources 58, next100-run checkpoint100, no active jobs. '
        'No network collection this wakeup: existing 47 snapshots/40,753 rolling persistence outcomes remain a different cohort. '
        'Original application models and consumed claims unchanged. Next: synthetic final callback + scoring-code freeze, then scheduled '
        'collection/real pre-target issuance with scripts/collect_singapore_study.py. No more fitting for this study. '
        'Guide: docs/SINGAPORE_FORECAST_STUDY.md; pointer: reports/singapore_forecast_study_latest.json.')
    for path in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/IMPLEMENTATION_STATUS.md',
                 'docs/TEST_RESULTS.md', 'docs/AI_ASSISTANCE_LOG.md', 'docs/DATASET_PROVENANCE.md', 'docs/THIRD_PARTY_SOURCES.md']:
        append(path, note)
    append('docs/PROJECT_CONSTRAINTS.md',
        'The Singapore trend coefficient, 46-snapshot historical split, candidate selection and issuance implementation/config are now '
        'FROZEN for the reserved ALL-carpark origin period 26 October10:00UTC to27 October10:00UTC. Do not refit or tune on post-cutoff data. '
        'Use fixed parameters with already available inference context only. Real forecast batches must be committed before targets; no backdating. '
        'No learned partial/final scoring before 27 October10:51UTC or outside the global durable once-only claim. Final callback remains to be '
        'implemented on synthetic fixtures under the already frozen scoring plan. Original production app unchanged; development pass is not final acceptance.')
    req = ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    for item in items:
        if item['requirement_id'] in ['DATA-04', 'DATA-03', 'QA-02']:
            item['actual_evidence'] += '; models/singapore_trend_development.json; data/manifests/singapore_trend_issuance_v1.json'
            item['test_result'] += '; Trend DEVELOPMENT6.30985vs6.95762spaces; gate pass; 273software tests; zero actual pre-period forecasts'
            item['open_problems'] += '; Learned future performance unscored; final callback unfinished; nine development times only'
    with req.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL); writer.writeheader(); writer.writerows(items)
    dump(E/'handoff.json', dict(recorded_at=now, completed_trials=65, wakeups=44, source_records=58,
        next_live_checkpoint_at_run=100, study=pointer, all273software_tests_passed=True,
        no_real_learned_forecasts_or_final_claims=True, original_models_claims_unchanged=True,
        no_active_jobs=True, next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(completed_trials=65, wakeups=44, development_mae=run['candidate']['mae_spaces'],
                         relative_improvement=improvement, future_scored=False, source_records=58), indent=2))


if __name__ == '__main__':
    main()
