"""Persist frozen final-scoring implementation and source-compliant collection."""
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed, get_live
from smart_parking.singapore_history import canonical_observation
from smart_parking.singapore_final import load_scoring_manifest

E = ROOT/'experiments/evidence/HEARTBEAT-20261026T083848Z'
TITLE = '## 26 October 2026 / frozen once-only Singapore final scorer'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def dump(path, value):
    (ROOT/path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def append(path, value):
    path = ROOT/path; old = path.read_text(encoding='utf-8')
    assert TITLE not in old
    path.write_text(old.rstrip()+'\n\n'+TITLE+'\n\n'+value+'\n', encoding='utf-8')


def main():
    assert not (E/'handoff.json').exists()
    state = read('data/automation_state.json')
    validation = read('reports/singapore_final_software_validation_latest.json')
    assert state['last_completed_run'] == validation['run_id']
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 66
    assert state['scheduled_wakeups_completed'] == 44 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert validation['data_kind'] == 'synthetic_software_fixture' and all(validation['checks'].values())
    assert all(digest(ROOT/p) == h for p, h in {**validation['source_hashes'], **validation['protected_hashes']}.items())
    fixture_inventory = read(f"experiments/results/{validation['run_id']}/fixture_inventory.json")
    for path, expected in fixture_inventory['file_hashes'].items():
        assert digest(ROOT/fixture_inventory['root']/path) == expected
    manifest_path = ROOT/'data/manifests/singapore_trend_scoring_v1.json'
    manifest, config, reservation, selection, model = load_scoring_manifest(manifest_path)
    assert digest(manifest_path) == read(E/'frozen_scoring.json')['scoring_manifest_sha256']
    assert read(E/'software_tests.json')['returncode'] == 0 and 'Ran 284 tests' in read(E/'software_tests.json')['stderr']
    status = read('reports/singapore_final_status.json')
    assert status['status'] == 'not_ready' and not status['target_json_decoded']
    assert not (ROOT/config['batch_folder']).exists() and not (ROOT/config['batch_receipt_folder']).exists()
    claims = ROOT/reservation['claim_registry']; assert not claims.exists() or not list(claims.glob('*.claim.json'))
    assert not (ROOT/'reports/singapore_final_latest.json').exists()
    live = read('data/processed/singapore_prospective/summary.json')
    receipt_records = [json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    last = next(r for r in reversed(receipt_records) if r['source_id'] == 'SRC-LIVE-001' and r['local_path'].startswith('data/raw/singapore_live/'))
    assert digest(ROOT/last['local_path']) == last['sha256']
    payload = read(last['local_path']); rows = parse_feed(payload)
    assert all(0 <= r['available'] <= r['capacity'] for r in rows)
    assert len(rows) == len({(r['car_park_id'], r['lot_type'], r['observed_at']) for r in rows})
    cached, metadata = get_live(refresh=False)
    assert cached == rows and metadata['cached']
    fresh = 0; rejected = Counter()
    for row in rows:
        try:
            canonical_observation(row, last['accessed_at'], last['local_path'], last['sha256']); fresh += 1
        except ValueError as error:
            rejected[str(error)] += 1
    snapshots = len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    assert snapshots == 48 and live['scores_total'] == 41908 and live['scores_added'] == 1155
    next_poll = (datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json', dict(receipt=last, snapshot_count=snapshots, accepted_rows=len(rows),
        raw_lot_records=sum(len(p['carpark_info']) for i in payload['items'] for p in i['carpark_data']),
        fresh_at_actual_receipt=fresh, freshness_rejections=dict(rejected), duplicate_rows=0, bounds_valid=True,
        cached_application_data_path_matches=True, manual_ui_tested=False, summary=live,
        next_sensible_collection_after=next_poll, separate100_run_checkpoint_due=False,
        scope='Previously frozen persistence feed/integration only; no learned/neural/camera accuracy'))
    now = datetime.now(timezone.utc).isoformat()
    pointer = read('reports/singapore_forecast_study_latest.json')
    pointer.update(final_scoring_callback_implemented=True, scoring_manifest=manifest_path.relative_to(ROOT).as_posix(),
        scoring_manifest_sha256=digest(manifest_path), scoring_frozen_at=manifest['frozen_at'],
        final_scoring_software_validation_run=validation['run_id'], final_scoring_software_validation_only=True,
        software_tests_passed=284, final_performance_evaluated=False, future_final_consumed=False,
        learned_forecasts_issued=False, learned_forecast_batches=0)
    dump('reports/singapore_forecast_study_latest.json', pointer)
    state.update(last_updated_at=now, scheduled_wakeups_completed=45, singapore_forecast_study=pointer,
        prospective_live_summary=live, last_live_baseline_score=dict(outcomes=live['scores_total'], mae_spaces=live['baseline_mae_spaces'],
            scope='Persistence only; not learned/neural/camera accuracy', coverage=live['forecast_coverage']))
    state['next_actions'] = [
        'The forecast candidate, issuer AND final scorer are now frozen for the future Singapore study. Do NOT fit/tune coefficients, gates, matching logic or source modules for this interval. Preserve issuance config b68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625, scoring manifest 1dc86326f3152ca090572041434e057980e151ee75ea4a2b8292f4385cb3aa1b, reservation bd47defbec2e4e73388b4eb4ad8dd8d04528a04df15ae78242427ca93f5afaca and original checkpoint. All posthistorical-cutoff data is inference context only, not refitting/development.',
        'At each due collection run D:\\deep learning\\.venv\\Scripts\\python.exe scripts/collect_singapore_study.py. Current last collection08:39:38UTC/48snapshots, so next sensible poll AFTER '+next_poll+'. Next09:08heartbeat may be slightly early: do independent useful notebook/report work, then collect only once actually due. Avoid a skipped poll becoming an unintended60minute gap. The wrapper preserves30minute plan and publisher minimum1minute; no repeated polling per software fixture.',
        'Real learned origins are26October10:00UTC through27October10:00UTC (India15:30to15:30). Before originstart issuer reportsnot_started. Duringperiod use actual fresh raw receipts and past same-capacity observations, commit immutable data/processed/singapore_learned_v1/batches files plus data/receipts/singapore_learned_v1/*.receipt.json. Include receipt files in local commits. No backdating/retroactive partial-batch repair. Do not change frozen runtime sources when improving separate notebooks/reports.',
        'Final scorer is READY, not evaluated. Do not decode real final targets for learned scoring before27October10:51UTC. Then run D:\\deep learning\\.venv\\Scripts\\python.exe scripts/score_singapore_study.py exactly once. It verifies real issuance/receipt/model/config bindings without target decode, writes a global durable source-period claim BEFORE semantic raw target/context reads, uses first RECEIVED qualifying same-series/capacity target20-45min after actualissue, stops at capacitychanges, reports paired errors/coverage and missingIDs, preserves failed-consumed claims. Beforeclosure command reportsnot_ready; repeated completed command displays saved artifacts, never reruns a changed method. No eligible issuance =>not_evaluable without invented score.',
        'Frozen final gates unchanged: >=500matches, >=8matchedglobalorigins, >=50series, >=75percent targetmatchingcoverage, >=1percent rawMAE gain, macro-origin noninferiority, no origin regression>0.5spaces. Zero baselineMAE cannot claim positive relativegain. All compared errors share identical forecastIDs. Final report needs completed global claim outcome plus completed.json; if writing/registration interrupted, recover from existing immutable artifacts, never re-evaluate or releaseclaims. App promotion remains separate.',
        'Independent next useful product task: add a read-only executed Python/Jupyter teaching notebook for the frozen Singapore study, showing causal inputs, ridge failure vs trend DEVELOPMENT on SAME9202windows, nine-time limitation, planned timed test, source/licence/provenance and missing-target coverage. Notebook must never auto-fit/collect or open unscored final data. Keep dated existing offline bundle/Excel reports intact; assess a new bundle only after validation. Other fresh vision work must avoid all consumed groups; CNRrights unresolved/source018development-exposed.',
        'Completed trial66 is SYNTHETIC software end-to-end validation SG-FINAL-VALIDATION-20261026T085015262524Z: seed133,700issued/688matched/12missing,12origins/60simulatedparks, manufactured slope arithmetic and all numeric gates verified. It is NOT measured forecasting accuracy. All284software tests PASS, including11new final-guard/matching/export/metric fixtures. Counter66/wakeups45/source58/nextseparate100-run checkpoint100/no activejobs. Candidate real DEVELOPMENT remains6.309848vs6.957618spaces, not real final/live accuracy.',
        'Current official feed integration:48snapshots,1155new previouslyfrozen persistence matches,41908total,MAE4.8330151761spaces,1118newbaselineforecasts; missingtargets unscored. Raw/URL/licence/receipt/normalized history preserved. Current real issuer/scorer smokechecks beforeperiod:zero learned batches/no actualfinalclaim/target_json_decodedFalse. Original3productionweights, camera/Birmingham models and consumedclaims unchanged. Missing universityfiles/manual/physicalmachine/student acceptance still open. Read docs/SINGAPORE_FORECAST_STUDY.md and reports/singapore_forecast_study_latest.json.'
    ]
    dump('data/automation_state.json', state)
    inventory = read('data/dataset_inventory.json'); inventory.update(inventoried_at=now, singapore_forecast_study=pointer,
        singapore_final_software_validation=dict(run_id=validation['run_id'], data_kind='synthetic_software_fixture',
            fixture_source_id='SYNTHETIC-FIXTURE-SG-FINAL-001', public_data_source=False, issued=700, matched=688, missing=12))
    for item in inventory['datasets']:
        if item['source_id'] == 'SRC-LIVE-001':
            item.update(raw_path=last['local_path'], provider_timestamp=last['provider_timestamp'], snapshot_count=snapshots,
                observations=len(rows), car_parks=len({r['car_park_id'] for r in rows}),
                raw_lot_records=sum(len(p['carpark_info']) for i in payload['items'] for p in i['carpark_data']),
                prospective_baseline_scored_outcomes=live['scores_total'], prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
                forecast_target_coverage=live['forecast_coverage'], learned_history_study=pointer)
    dump('data/dataset_inventory.json', inventory)
    catalog = ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    assert len(items) == len({r['source_id'] for r in items}) == 58
    for item in items:
        if item['source_id'] == 'SRC-LIVE-001':
            item['used_by'] += '; once-only real-final scorer implemented/frozen, not yet evaluated; separate synthetic pipeline validation'
            item['open_issues'] += '; real future performance pending actual pre-target batches and27October10:51UTC closure; synthetic fixture results are not accuracy'
    with catalog.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(items)
    note = ('The once-only paired final scorer is implemented and frozen at08:53:02UTC, before reserved origins begin26October10:00UTC. '
        'Issuance config, candidate and final rules unchanged. It verifies committed ledger/model/config/receipt bindings without decoding targets, '
        'then claims the entire canonical source interval before opening semantic raw data (origin snapshots can also contain earlier targets). '
        'Raw context is reconstructed after claim, first received qualifying20-45minute target is used, changed capacities stop matching, '
        'missing targets remain unscored, and failed callbacks consume the period. Support/coverage and paired raw/macro/per-origin gates are frozen; '
        'zero baseline error cannot count as a positive relative gain. CSV/unmatched IDs/input hashes/claim outcomes/completion receipts preserved. '
        'Production CLI offers no historical-clock override; before27October10:51UTC it returnsnot_ready, and repeats of completed runs show archives. '
        'Actual smokecheck decoded0real targetJSON/created0real finalclaims/issued0learnedbatches. '
        'One separately recorded SYNTHETIC validation used seed133,14generated snapshots/12origins/60simulatedparks,700issued/688matched/12missing; '
        'full frozen numeric gates, manufactured slope arithmetic, early blocking and once-only behavior passed. These are software fixtures, '
        'not real-world forecasting performance. Actual fixture bytes/claims/logs retained underoutputs/singapore_final_validation with hashed inventory. '
        '284software tests pass including11new final tests. One validation65->66, wakeups45/source58/next100-run checkpoint100/no activejobs. '
        'Official collection08:39UTC added snapshot48 and1,155previously frozen persistence matches:41,908total,MAE4.833015spaces;1,118new forecasts. '
        'Source receipt/hash/schema/bounds/duplicates/freshness and cached app-data path checked; manual UI not tested. '
        'Original model/checkpoint/consumed-claim hashes unchanged. No learned live/final/camera/neural accuracy measured and no app promotion. '
        'Next:read-only executed teaching notebook and sensible30minute collection; protect frozen sources and wait for actual future targets. '
        'Guide:docs/SINGAPORE_FORECAST_STUDY.md; frozen scorer:data/manifests/singapore_trend_scoring_v1.json.')
    for path in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/IMPLEMENTATION_STATUS.md', 'docs/TEST_RESULTS.md',
                 'docs/AI_ASSISTANCE_LOG.md', 'docs/DATASET_PROVENANCE.md', 'docs/THIRD_PARTY_SOURCES.md']:
        append(path, note)
    append('docs/PROJECT_CONSTRAINTS.md',
        'Singapore final scorer is now implemented and FROZEN by data/manifests/singapore_trend_scoring_v1.json. Do not modify frozen '
        'matching/gates/model/issuer/scorer for this interval. No real final semantic target/context decoding for evaluation before '
        '27October10:51UTC and the durable global claim. Synthetic fixture successes are software evidence only. Failures consume; '
        'never repeat changed-method evaluation or repair late forecasts. Display archived completed results only. Real study remains unscored.')
    req = ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    for item in items:
        if item['requirement_id'] in ['DATA-04', 'DATA-03', 'QA-02']:
            item['actual_evidence'] += '; data/manifests/singapore_trend_scoring_v1.json; reports/singapore_final_software_validation_latest.json'
            item['test_result'] += ';284software tests; SYNTHETIC700issued/688matches/12missing; real scorer returnsnot_ready withouttargetdecode'
            item['open_problems'] = item['open_problems'].replace('final callback unfinished', 'final callback implemented/frozen, actual future performance pending')
    with req.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL); writer.writeheader(); writer.writerows(items)
    dump(E/'handoff.json', dict(recorded_at=now, completed_trials=66, wakeups=45, source_records=58, next_live_checkpoint_at_run=100,
        study=pointer, software_tests_passed=284, real_final_still_unclaimed_unscored=True,
        original_models_claims_unchanged=True, no_active_jobs=True, next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(completed_trials=66, wakeups=45, tests=284, raw_snapshots=snapshots,
                         fresh_at_collection=fresh, real_final_evaluated=False), indent=2))


if __name__ == '__main__':
    main()
