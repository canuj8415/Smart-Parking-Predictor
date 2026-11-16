"""Save the first real pre-target batch and metadata-only validation milestone."""
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

E = ROOT/'experiments/evidence/HEARTBEAT-20261026T120852Z'
TITLE = '## 26 October 2026 / first real pre-target batch and metadata-only health'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def dump(path, value):
    (ROOT/path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def append(path, value):
    path = ROOT/path; old = path.read_text(encoding='utf-8'); assert TITLE not in old
    path.write_text(old.rstrip()+'\n\n'+TITLE+'\n\n'+value+'\n', encoding='utf-8')


def main():
    assert not (E/'handoff.json').exists()
    state = read('data/automation_state.json'); run = read('models/singapore_issuance_health_validation.json')
    health = read('reports/singapore_issuance_health_latest.json')
    assert state['last_completed_run'] == run['run_id']
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 69
    assert state['scheduled_wakeups_completed'] == 47 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['all_gates_passed'] and all(run['checks'].values()) and health['status'] == 'healthy'
    assert health['forecasts_logged'] == 1110 and health['batch_receipts'] == health['global_origins'] == 1
    assert not health['target_json_decoded'] and not health['performance_evaluated'] and not health['raw_semantic_context_verified']
    assert all(digest(ROOT/p) == h for p, h in {**run['source_hashes'], **run['protected_hashes'],
        **health['receipt_and_batch_hashes'], **health['raw_input_hashes']}.items())
    assert read(E/'software_tests.json')['returncode'] == 0 and 'Ran 302 tests' in read(E/'software_tests.json')['stderr']
    assert read(E/'routine_cli_check.json')['completed_trials_before'] == read(E/'routine_cli_check.json')['completed_trials_after'] == 69
    manifest, config, reservation, selection, model = load_scoring_manifest(ROOT/'data/manifests/singapore_trend_scoring_v1.json')
    batch_receipts = list((ROOT/config['batch_receipt_folder']).glob('*.receipt.json')); assert len(batch_receipts) == 1
    receipt = read(batch_receipts[0]); assert receipt['forecasts'] == 1110
    claims = ROOT/reservation['claim_registry']; assert not claims.exists() or not list(claims.glob('*.claim.json'))
    live = read('data/processed/singapore_prospective/summary.json')
    assert live['scores_total'] == 45214 and live['scores_added'] == 1126
    source_receipts = [json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    last = next(r for r in reversed(source_receipts) if r['source_id'] == 'SRC-LIVE-001' and r['local_path'].startswith('data/raw/singapore_live/'))
    assert digest(ROOT/last['local_path']) == last['sha256']
    payload = read(last['local_path']); rows = parse_feed(payload); fresh = 0; rejected = Counter()
    assert all(0 <= r['available'] <= r['capacity'] for r in rows)
    assert len(rows) == len({(r['car_park_id'], r['lot_type'], r['observed_at']) for r in rows})
    cached, metadata = get_live(False); assert cached == rows and metadata['cached']
    for row in rows:
        try:
            canonical_observation(row, last['accessed_at'], last['local_path'], last['sha256']); fresh += 1
        except ValueError as error:
            rejected[str(error)] += 1
    snapshots = len(list((ROOT/'data/raw/singapore_live').glob('*.json'))); assert snapshots == 52
    raw_lots = sum(len(p['carpark_info']) for i in payload['items'] for p in i['carpark_data'])
    next_poll = (datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json', dict(receipt=last, snapshot_count=snapshots, accepted_rows=len(rows), raw_lot_records=raw_lots,
        fresh_at_receipt=fresh, freshness_rejections=dict(rejected), duplicate_rows=0, bounds_valid=True,
        cached_app_data_matches=True, manual_ui_tested=False, summary=live, first_learned_batch_receipt=receipt,
        batch_receipt_path=batch_receipts[0].relative_to(ROOT).as_posix(), batch_receipt_sha256=digest(batch_receipts[0]),
        next_sensible_collection_after=next_poll, separate100_run_checkpoint_due=False,
        scope='Feed/persistence integration plus pre-target metadata only; no learned/camera/neural error or target matching'))
    now = datetime.now(timezone.utc).isoformat()
    issuance = dict(first_issued_at=receipt['issued_at'], first_committed_at=receipt['committed_at'], first_finalized_at=receipt['finalized_at'],
        forecasts_logged=1110, batch_receipts=1, global_origins=1, unique_series=health['unique_series'],
        first_target_window=[health['origins'][0]['earliest_target'], health['origins'][0]['latest_target']],
        metadata_status='healthy', raw_files_hashed_once=2, semantic_context_verified=False, performance_evaluated=False,
        receipt_path=batch_receipts[0].relative_to(ROOT).as_posix(), receipt_sha256=digest(batch_receipts[0]),
        health_report='reports/singapore_issuance_health_latest.json', validation_run=run['run_id'],
        scope='Logged pre-target forecast metadata; not accuracy or source-count authentication')
    pointer = read('reports/singapore_forecast_study_latest.json')
    pointer.update(learned_forecasts_issued=True, learned_forecast_batches=1, learned_forecasts_logged=1110,
        learned_global_origins=1, operational_issuance=issuance, learned_live_performance_evaluated=False,
        final_performance_evaluated=False, future_final_consumed=False, software_tests_passed=302)
    dump('reports/singapore_forecast_study_latest.json', pointer)
    state.update(last_updated_at=now, scheduled_wakeups_completed=48, singapore_forecast_study=pointer,
        singapore_issuance_health=issuance, prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=live['scores_total'], mae_spaces=live['baseline_mae_spaces'],
            scope='Persistence only; not learned/neural/camera accuracy', coverage=live['forecast_coverage']))
    state['next_actions'] = [
        'TOP PRIORITY next wake: collect once AFTER '+next_poll+' with D:\\deep learning\\.venv\\Scripts\\python.exe scripts/collect_singapore_study.py. At12:38wake this may be <60seconds early: use actual UTC clock, a short independent read, or one bounded <=60second wait, then perform the due acquisition rather than ending with an early skip. Keep30minute source plan and publisher>=1minute. The next reading can also supply real targets for older forecasts, but no interim learned scoring is allowed.',
        'First genuine learned batch is active:1110forecasts issued2026-10-26T12:09:52.404825Z, committed12:09:52.868374Z, finalized12:09:52.907664Z. Targetwindow12:29:52–12:54:52UTC,1110unique series/1origin/1receipt. Receipt data/receipts/singapore_learned_v1/c5be93bcb4e09bb2d168d6cc597c8c51120af080bc9ba0e824535019bb2ec754.receipt.json SHA0425593a1b16be38b8faf3435f014fd307568ef214ba0d3f4a4daaa842fbd49c. BatchSHA d97bd40c2a0802c20ea71d479d715602fdf5703ab4f6f875ff1e8f890280f077. Preserve files unchanged; no forecast backfill or partial-batch repair.',
        'After each due collection, run scripts/check_singapore_issuance_health.py WITHOUT --record-trial. It checks only outcome-free issuance metadata, source-receipt membership, byte hashes cached once/path, bounds/times/uniqueIDs and reproduction from fixed savedinputs. It does NOT decode raw JSON, verify semantic sourcecounts, match targets, compute learned error/coverage, create claims or add experimentcounts. --record-trial is version1first-integration-only and now blocks repeats. If attention/error occurs, preserve evidence and investigate without modifying frozen batch or methods.',
        'Freeze remains exact:alpha0.30018518518518517/checkpointb11dd08ff444affb92de3841a23ef6de0b63833d270f748df4ff654426e1851f; issuance configb68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625; scoring1dc86326f3152ca090572041434e057980e151ee75ea4a2b8292f4385cb3aa1b; reservationbd47defbec2e4e73388b4eb4ad8dd8d04528a04df15ae78242427ca93f5afaca. No source/runtime/model/gate edits or new fitting for current originperiod26October10:00UTC–27October10:00UTC. Frozen selection JSON still describes its preperiod state; do not rewrite it to update issuance status. Currentstatus is in reports/singapore_forecast_study_latest.json.',
        'Real learned final remains CLOSED until27October10:51UTC. Then run scripts/score_singapore_study.py once: global durable claim BEFORE semantic rawcontext/targetreads, first RECEIVED fresh20-45min target, stopcapacitychange, same pairedIDs, missingunscored. Gates>=500matches/>=8origins/>=50series/>=75percentcoverage/>=1percentMAEgain/macro-noninferior/maxoriginregression0.5spaces. Raw semantic context authentication remains in that callback, not the health monitor. Failures consume; never silently repair/delete data to improve a score. Archive all outputchecksums plus input/claim/completion records after valid completion; display archivedresult on repeats. No apppromotion yet.',
        'Highest independent next task after reliable timed issuance: publisher-backed qualification of genuinely fresh parking-region/traffic-segmentation annotations or resolution of CNR individual-image content rights. Use primary source/licence/acquisition evidence; no CNRimageuse whileunqualified, no inferred backgroundnegatives from unknown source018support, no replay of consumed PKLot/Birmingham/DAVIS finalgroups. Reserve new source/camera/date/sequence finalgroups before changed methods. Stop similar source-head grids alreadyrejected. Existing lesson and separate portablecopy are complete within stated scope; do not spend cycles revalidating unchanged packages.',
        'Current52official snapshots at12:09UTC:1126new frozen persistence matches,45214total,MAE4.9788782236spaces;1280newbaselineforecasts. This is a different cohort from historical9202development (trend6.309848vs6.957618) and from the new1110learner forecasts. Do not compare rollingbaseline MAE to development MAE as model improvement. Existing09:43–11:39collection gap and missed origins remainunfilled. All fresh acquisitions have rawURL/time/licence/checksum/normalized observations; no camera accuracy from aggregatecounts.',
        'One completed metadata integration trial68->69;wakeups48/source58/nextseparate100-run official-live checkpoint100/no activejobs.302software tests PASS(7new synthetic health fixtures). Real1110predictions and synthetic fixtures are distinct; neither count is an accuracy percentage or number of runs. Default routineCLI verified leaves counter69 unchanged. Original3productionweights, candidate/frozen sources and consumedclaims unchanged. Python/Jupyter retained; no new packages/paidservices/publication. Universitydocs/physicaloffline/newmachine/manualbrowser/student mastery remainopen. See docs/SINGAPORE_ISSUANCE_HEALTH.md.'
    ]
    dump('data/automation_state.json', state)
    inventory = read('data/dataset_inventory.json'); inventory.update(inventoried_at=now, singapore_forecast_study=pointer,
        singapore_issuance_health=issuance)
    for item in inventory['datasets']:
        if item['source_id'] == 'SRC-LIVE-001':
            item.update(raw_path=last['local_path'], provider_timestamp=last['provider_timestamp'], snapshot_count=snapshots,
                observations=len(rows), car_parks=len({r['car_park_id'] for r in rows}), raw_lot_records=raw_lots,
                prospective_baseline_scored_outcomes=live['scores_total'], prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
                forecast_target_coverage=live['forecast_coverage'], learned_history_study=pointer, learned_issuance_metadata=issuance)
    dump('data/dataset_inventory.json', inventory)
    catalog = ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    assert len(items) == len({r['source_id'] for r in items}) == 58
    for item in items:
        if item['source_id'] == 'SRC-LIVE-001':
            item['original_size'] = '52 immutable official snapshots; per-file bytes and acquisition times in resource receipts'
            item['used_by'] += '; first1110genuine pre-target trendforecasts/1batch at12:09UTC; metadata-only hash/timing/bounds/ID integration pass'
            item['open_issues'] += '; real learned error/coverage/final accuracy unscored; semantic rawcount verification deferred to once-only final callback'
    with catalog.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(items)
    note = ('The frozen issuer saved its first real batch: 1,110 forecasts issued 12:09:52.404825 UTC, committed 12:09:52.868374, '
        'receipted 12:09:52.907664; target window 12:29:52–12:54:52 UTC. This is pre-target logging evidence, not accuracy. '
        'The separate metadata-only health checker validates frozen model/config/batch/receipt identities, strict outcome-free schema, '
        'unique IDs, availability/issue/commit times, physical bounds and reproduction from saved inputs. Two original raw files are hashed '
        'once each, never decoded. Raw semantic context authentication is deliberately deferred to the once-only final callback, since an '
        'origin may also contain earlier targets. No learned error, matching coverage, final claim or app promotion. Routine CLI adds no trial '
        'count; first-integration record is one-time and repeat registration is blocked. All 302 software tests pass, including seven new '
        'synthetic health cases for no raw/target decoding, changed bytes, duplicate IDs, outcome smuggling, wrong predictions, invalid times '
        'and partial batches. One real metadata validation advances 68->69, completed wakeups48/source58/next100-run checkpoint100/no active jobs. '
        'Official snapshot52 at12:09 adds1,126previously frozen persistence matches:45,214total,MAE4.978878spaces;1,280newbaselineforecasts. '
        'Rolling baseline, historical development and new learned batch are different cohorts. Earlier collection gap stays unfilled. '
        'Raw/source/licence/receipt/normalized/cache/schema/bounds/freshness checks retained. All frozen candidate/issuer/scorer/reservation, '
        'original production weights and consumed claims unchanged; no learned interim/final/camera/neural score. '
        'Next:collect after12:39:49UTC, routine metadata health without new trial, then genuinely fresh publisher-qualified region/traffic '
        'annotations rather than repeated package checks. Guide:docs/SINGAPORE_ISSUANCE_HEALTH.md; current status:reports/singapore_forecast_study_latest.json.')
    for path in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/IMPLEMENTATION_STATUS.md', 'docs/TEST_RESULTS.md',
                 'docs/AI_ASSISTANCE_LOG.md', 'docs/DATASET_PROVENANCE.md', 'docs/THIRD_PARTY_SOURCES.md']:
        append(path, note)
    append('docs/PROJECT_CONSTRAINTS.md', 'Metadata-only issuance health checks may run before final closure: validate logged fields and byte hashes without decoding raw context/targets or computing learned errors/coverage. Do not wire the new health helper into the frozen scientific controller, prefilter final forecasts based on outcomes, or repair/delete failed batches. The final raw-semantic check stays inside the once-only claimed callback. Routine health/collection does not create new experiment counts.')
    req = ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    for item in items:
        if item['requirement_id'] in ['DATA-04', 'DATA-03', 'QA-02']:
            item['actual_evidence'] += '; reports/singapore_issuance_health_latest.json; models/singapore_issuance_health_validation.json'
            item['test_result'] += ';1110real pre-target forecasts/1batch;metadata integrity pass;302software tests;no learned outcomes scored'
            item['open_problems'] += ';Actual learned target error/coverage/final acceptance pending fixed27October10:51UTC closure'
    with req.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL); writer.writeheader(); writer.writerows(items)
    dump(E/'handoff.json', dict(recorded_at=now, completed_trials=69, completed_wakeups=48, source_records=58,
        next_live_checkpoint_at_run=100, issuance=issuance, software_tests_passed=302, actual_final_claims=0,
        real_final_evaluated=False, no_active_jobs=True, next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(completed_trials=69, completed_wakeups=48, tests=302, snapshots=52,
                         learned_forecasts=1110, learned_batches=1, performance_evaluated=False), indent=2))


if __name__ == '__main__':
    main()
