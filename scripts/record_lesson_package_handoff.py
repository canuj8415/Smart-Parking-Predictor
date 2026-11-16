"""Persist relocated lesson evidence and honest resumed-collection status."""
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.lesson_package import verify_payload
from smart_parking.live import parse_feed, get_live
from smart_parking.singapore_history import canonical_observation
from smart_parking.singapore_final import load_scoring_manifest

E = ROOT/'experiments/evidence/HEARTBEAT-20261026T113851Z'
TITLE = '## 26 October 2026 / relocated read-only lesson and resumed live collection'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def dump(path, value):
    (ROOT/path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def append(path, value):
    path = ROOT/path; old = path.read_text(encoding='utf-8'); assert TITLE not in old
    path.write_text(old.rstrip()+'\n\n'+TITLE+'\n\n'+value+'\n', encoding='utf-8')


def main():
    assert not (E/'handoff.json').exists()
    state = read('data/automation_state.json'); run = read('reports/singapore_lesson_package_latest.json')
    assert state['last_completed_run'] == run['run_id'] and state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 68
    assert state['scheduled_wakeups_completed'] == 46 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['portable_lesson_gate_passed'] and run['all_payload_and_original_hashes_unchanged']
    assert all(digest(ROOT/p) == h for p, h in {**run['source_hashes'], **run['protected_hashes']}.items())
    package = ROOT/run['package']; package_manifest = read(package/'PACKAGE_MANIFEST.json')
    assert digest(package/'PACKAGE_MANIFEST.json') == run['package_manifest_sha256']
    assert verify_payload(package, package_manifest) == run['payload']
    assert run['payload']['files'] == 22 and run['payload']['bytes'] == 10100681
    assert digest(ROOT/run['archive']/'PACKAGE_MANIFEST.json') == run['package_manifest_sha256']
    assert digest(ROOT/run['archive']/'README.md') == digest(package/'README.md')
    assert read(E/'software_tests.json')['returncode'] == 0 and 'Ran 295 tests' in read(E/'software_tests.json')['stderr']
    manifest, config, reservation, selection, model = load_scoring_manifest(ROOT/'data/manifests/singapore_trend_scoring_v1.json')
    actual_receipts = list((ROOT/config['batch_receipt_folder']).glob('*.receipt.json'))
    actual_batches = list((ROOT/config['batch_folder']).glob('*.jsonl'))
    assert not actual_receipts and not actual_batches
    claims = ROOT/reservation['claim_registry']; assert not claims.exists() or not list(claims.glob('*.claim.json'))
    issue_status = read('reports/singapore_issuance_latest.json')['study_issuance']
    assert issue_status['issued'] == 0 and issue_status['status'] == 'no_new_eligible_observations'
    live = read('data/processed/singapore_prospective/summary.json')
    assert live['scores_total'] == 44088 and live['scores_added'] == 0
    receipts = [json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    last = next(r for r in reversed(receipts) if r['source_id'] == 'SRC-LIVE-001' and r['local_path'].startswith('data/raw/singapore_live/'))
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
    snapshots = len(list((ROOT/'data/raw/singapore_live').glob('*.json'))); assert snapshots == 51
    raw_lots = sum(len(p['carpark_info']) for i in payload['items'] for p in i['carpark_data'])
    next_poll = (datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json', dict(receipt=last, snapshot_count=snapshots, accepted_rows=len(rows), raw_lot_records=raw_lots,
        fresh_at_receipt=fresh, freshness_rejections=dict(rejected), bounds_valid=True, duplicate_rows=0, cached_app_data_matches=True,
        collection_history_gap=read(E/'interim.json'), summary=live, study_issuance=issue_status, actual_learned_batches=0,
        next_sensible_collection_after=next_poll, scope='Persistence integration only; no learned/camera/neural performance score'))
    dump(E/'visual_review.json', dict(inspected_png=f"experiments/results/{run['run_id']}/development_1.png",
        sha256=digest(ROOT/f"experiments/results/{run['run_id']}/development_1.png"), visually_inspected=True,
        observation='Relocated-environment chart has readable method MAEs, nine UTC origins, two regressions, threshold and development-only footnote.',
        manual_browser_native_app_or_physical_offline_tested=False))
    now = datetime.now(timezone.utc).isoformat()
    pack = dict(run_id=run['run_id'], path=run['package'], payload_files=22, payload_bytes=10100681,
        manifest_sha256=run['package_manifest_sha256'], code_cells=7, inline_png_outputs=1, archived_inputs=10,
        original_acquisition_receipts=46, dependency_origins_verified=True, all_payload_bytes_unchanged=True,
        existing_offline_venv=run['python'], runtime_included=False, new_install_performed=False,
        original_full_app_demo_replaced=False, real_final_evaluated=False, guide='docs/SINGAPORE_LESSON_PACKAGE.md')
    pointer = read('reports/singapore_forecast_study_latest.json')
    pointer.update(read_only_lesson_package=pack, software_tests_passed=295, learned_forecast_batches=0,
        learned_forecasts_issued=False, final_performance_evaluated=False, future_final_consumed=False)
    dump('reports/singapore_forecast_study_latest.json', pointer)
    state.update(last_updated_at=now, scheduled_wakeups_completed=47, singapore_forecast_study=pointer,
        singapore_read_only_lesson_package=pack, prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=live['scores_total'], mae_spaces=live['baseline_mae_spaces'],
            scope='Persistence only,not learned/neural/camera accuracy', coverage=live['forecast_coverage']))
    state.pop('in_progress_work', None)
    state['last_collection_gap'] = read(E/'interim.json')
    state['next_actions'] = [
        'TOP PRIORITY next wake: collect once AFTER '+next_poll+' using D:\\deep learning\\.venv\\Scripts\\python.exe scripts/collect_singapore_study.py. At12:08wake it is about1minute early: do a bounded independent task, then collect when due. The11:39snapshot is now the legitimate previous context for new12:09origins. Do not let an early skip become an unlogged60minute gap. Source cadence30minutes, minimum1minute; no per-fixture polling.',
        'Actual collection gap09:43:36to11:39:26UTC(~116minutes) preserved. No saved intermediate observations or forecasts were invented. At11:39the frozen issuer correctly returned0forecasts:1209no_previous_observation/6stale_at_issue. Empty real batch/receipt folders exist but have0files. Next fresh reading can form legitimate two-observation context. Do not backdate or fill missed origins, shift the reservation or retune alpha/gates based on this gap. Intermediate heartbeat triggers were coalesced while work was pending, not counted as completed trials/wakeups.',
        'Keep frozen Singapore candidate alpha0.30018518518518517, issuance configb68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625, scoring manifest1dc86326f3152ca090572041434e057980e151ee75ea4a2b8292f4385cb3aa1b and reservationbd47defbec2e4e73388b4eb4ad8dd8d04528a04df15ae78242427ca93f5afaca unchanged. Originwindow26October10:00UTC–27October10:00UTC is ongoing. New postcutoff observations are inference context only, not training/development. No runtime edits or checkpoint replacement for this study.',
        'Once actual learned batches exist, inspect only issuance metadata/receipts, prediction bounds/IDs/times and byte hashes for operational health; do NOT compute interim learned errors or decode target data for scoring. A small separate metadata-only health checker could help, with synthetic tests and no frozen-source edits. Commit immutable data/receipts/singapore_learned_v1/*.receipt.json; keep raw/batch data locally with hashes. Failures/incomplete batches must remain unmodified and ineligible, not repaired retroactively.',
        'No real learned final scoring before27October10:51UTC. Then use scripts/score_singapore_study.py once underactualclock, with durable global claim before targetdecode, first RECEIVED qualifying20-45min target/samecapacity, missingtargetsunscored and paired-ID comparison. Frozen gates>=500matches/>=8origins/>=50series/>=75percentcoverage/>=1percentMAEgain/macro-noninferior/maxoriginregression0.5spaces. Aftercompletion archive outputchecksums plus existing input/claim/completion evidence. Failures consume; display archivedcompletedresults rather than reevaluate. App integration remains separate.',
        'Independent next useful work after reliable due collection: qualify genuinely licensed new parking-region/traffic-segmentation source/labels or resolve CNRindividual-content rights using publisher evidence. Do not use CNRimages while unqualified, infer unlabelled-background negatives from source018polygons, or revisit any consumed image/Birmingham/DAVIS groups. Reserve genuinely fresh final groups before changed vision methods. Avoid further similar source-head grids already rejected. Existing portablelesson task is complete within its stated local-runtime scope.',
        'New separate lesson folder outputs/singapore_lesson_packages/SG-LESSON-PACK-20261026T114219733927Z:22payloadfiles/10100681bytes plusmanifest,10archivedinputs/46originalreceipts. Actual7-cell kernel ran using the existing offline-installed Jupyter venv, copy-local helper and5venv-local dependency origins verified; PNG reviewed; all payloadbytes unchanged and4expectedprobesblocked. No newpackages/install/runtime included, no physicaloffline/newmachine/manualbrowser/student mastery claim. Publicverifier/launcherhelp pass. Existing424-file full appbundle unchanged; mainlesson10cachedoutputs/source unchanged.',
        'Counter68;completedwakeups47;source58;next separate100-run official-live checkpoint100;no activejobs.295software tests PASS(4new package path/integrity fixtures). One completed relocatedvalidation67->68, not perfile/cell/probe. Prior2lessoninterruptions preserved. Current51real snapshots/44088frozen persistence outcomes/MAE4.8937806206spaces;11:39adds0matches/1220newbaselineforecasts aftergap. Different cohort from9202historical DEVELOPMENT (trend6.309848vs6.957618), not learnedlive/camera accuracy. Universitydocs/physical/manual/student acceptance remainopen. See docs/SINGAPORE_LESSON_PACKAGE.md and savedinterim/evidence.'
    ]
    dump('data/automation_state.json', state)
    inventory = read('data/dataset_inventory.json'); inventory.update(inventoried_at=now, singapore_forecast_study=pointer,
        singapore_read_only_lesson_package=pack)
    for item in inventory['datasets']:
        if item['source_id'] == 'SRC-LIVE-001':
            item.update(raw_path=last['local_path'], provider_timestamp=last['provider_timestamp'], snapshot_count=snapshots,
                observations=len(rows), car_parks=len({r['car_park_id'] for r in rows}), raw_lot_records=raw_lots,
                prospective_baseline_scored_outcomes=live['scores_total'], prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
                forecast_target_coverage=live['forecast_coverage'], learned_history_study=pointer)
    dump('data/dataset_inventory.json', inventory)
    catalog = ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    assert len(items) == len({r['source_id'] for r in items}) == 58
    for item in items:
        if item['source_id'] == 'SRC-LIVE-001':
            item['used_by'] += '; separate22-file relocated lesson copy, original46historical receipts/attribution, actual existing-offline-venv execution'
            item['original_size'] = '51 immutable official snapshots; per-file byte sizes and actual acquisition times in resource receipts'
            item['open_issues'] = item['open_issues'].replace('final callback unfinished', 'final callback implemented/frozen; actual final performance pending')
            item['open_issues'] += ';09:43–11:39collection gap retained;0actuallearnedbatches at11:39due missing previous fresh context,no backfill'
    with catalog.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(items)
    note = ('Built a separate read-only Singapore lesson copy:22payloadfiles/10,100,681bytes plus checksummanifest,10archived inputs, '
        'small statistical checkpoint, helper code and46original historical acquisition receipts with HDB/data.gov.sg attribution/licence. '
        'No raw/growing/final data, production neural weights, trainer/collector/scorer or runtime included. Actual relocated seven-cell Jupyter '
        'execution passed in the previously offline-installed local venv; helper origin is the copiedfolder and5dependency origins are inside '
        'that selectedvenv. File/socket audits and expectedprobes pass, PNG visually reviewed, every payloadbyte remains unchanged; launcher '
        'writes executed copies only. Verifier and publiclauncherhelp pass. This is not a new install, newmachine, physicaldisconnection, '
        'manualbrowser or studentmastery test. Existing424-file appbundle and originallesson remain untouched. '
        '295software tests pass including4new package path/integrity fixtures. One relocatedvalidation67->68, completedwakeups47/source58, '
        'next100-run checkpoint100/no activejobs. Work spans coalesced heartbeat triggers; no unperformed iterations counted. '
        'Official09:43collection added snapshot50/1164previously frozen persistence matches; after no saved collections until11:39, '
        'snapshot51 adds0matches/1220newbaselineforecasts. Total44,088outcomes,MAE4.893781spaces; missingtargets stayunscored. '
        'The ongoing frozen learnedstudy issued0at11:39because previousfresh context was unavailable(1209excluded,6stale); no backdated '
        'origins or invented observations. Actualemptybatchfolders contain0files, globalfinalclaimabsent. Next legitimate context collection '
        'after12:09:26UTC. Candidate, issuer/scorer/configs, originalweights and consumedclaims unchanged; no learned interim/final/camera '
        'accuracy evaluated and no app promotion. Next:timely prospectiveissuance and metadata-only health checks, then publisher-backed '
        'fresh region/traffic segmentation-source qualification. Guide:docs/SINGAPORE_LESSON_PACKAGE.md; evidence:reports/singapore_lesson_package_latest.json.')
    for path in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/IMPLEMENTATION_STATUS.md', 'docs/TEST_RESULTS.md',
                 'docs/AI_ASSISTANCE_LOG.md', 'docs/DATASET_PROVENANCE.md', 'docs/THIRD_PARTY_SOURCES.md']:
        append(path, note)
    append('docs/UI_TEST_LOG.md', 'Relocated-environment saved development PNG visually inspected and readable. Actual kernel, payload verifier and launcher help pass. No manual notebook-browser/native-app/new-machine/physical-disconnection/student rehearsal claimed.')
    req = ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    for item in items:
        if item['requirement_id'] in ['ENV-02', 'DATA-04', 'QA-02']:
            item['actual_evidence'] += '; reports/singapore_lesson_package_latest.json; docs/SINGAPORE_LESSON_PACKAGE.md'
            item['test_result'] += ';relocated lesson7cells/22payloadfiles/10.10MB/existingofflinevenv;295software tests;source/dependency origins verified'
            item['open_problems'] = item['open_problems'].replace('Lesson10notyet in relocated demo', 'Lesson10has separate validated localcopy;runtime not included')
    with req.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL); writer.writeheader(); writer.writerows(items)
    dump(E/'handoff.json', dict(recorded_at=now, completed_trials=68, completed_wakeups=47, source_records=58,
        next_live_checkpoint_at_run=100, lesson_package=pack, software_tests_passed=295, actual_learned_batches=0,
        real_final_claims_or_scores=0, collection_gap_preserved=True, no_active_jobs=True, next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(completed_trials=68, wakeups=47, tests=295, payload_files=22, snapshots=51,
                         fresh_at_collection=fresh, learned_batches=0, final_evaluated=False), indent=2))


if __name__ == '__main__':
    main()
