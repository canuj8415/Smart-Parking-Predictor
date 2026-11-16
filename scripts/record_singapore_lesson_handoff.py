"""Save actual lesson execution, failed attempts, live receipt and next actions."""
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

E = ROOT/'experiments/evidence/HEARTBEAT-20261026T090849Z'
TITLE = '## 26 October 2026 / executed read-only Singapore Jupyter lesson'


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
    state = read('data/automation_state.json'); run = read('reports/singapore_lesson_latest.json')
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 67
    assert state['last_completed_run'] == run['run_id'] and state['scheduled_wakeups_completed'] == 45
    assert not state['active_training_jobs'] and not state['active_validation_jobs'] and run['lesson_gate_passed']
    assert all(digest(ROOT/p) == h for p, h in {**run['source_hashes'], **run['protected_hashes'], **run['notebook_checks']['input_hashes']}.items())
    assert digest(ROOT/run['notebook']) == run['executed_notebook_sha256']
    assert digest(ROOT/run['development_png']) == run['development_png_sha256']
    assert read(E/'software_tests.json')['returncode'] == 0 and 'Ran 291 tests' in read(E/'software_tests.json')['stderr']
    manifest, config, reservation, selection, model = load_scoring_manifest(ROOT/'data/manifests/singapore_trend_scoring_v1.json')
    assert not (ROOT/config['batch_folder']).exists() and not (ROOT/config['batch_receipt_folder']).exists()
    claims = ROOT/reservation['claim_registry']; assert not claims.exists() or not list(claims.glob('*.claim.json'))
    assert len(run['file_audit']['denied']) == 3 and len(run['network_audit']['denied']) == 1
    assert not run['real_final_evaluated'] and not run['notebook_checks']['model_trained']
    failed = []
    for rid in ['SG-LESSON-20261026T091607886490Z', 'SG-LESSON-20261026T092043218035Z']:
        folder = ROOT/'experiments/results'/rid
        entry = dict(run_id=rid, interrupted=read(folder/'interrupted.json'), protocol_sha256=digest(folder/'protocol.json'),
                     source_notebook_sha256=digest(folder/'source_notebook.json'))
        if (folder/'child_output.json').exists():
            entry['child_output'] = read(folder/'child_output.json')
        failed.append(entry)
    dump(E/'recovery.json', dict(attempts=failed,
        first_attempt='Restricted local child timed out240seconds before notebook outputs. Owned process absence verified before host retry.',
        second_attempt='Host kernel reached first cell; pandas was absent. Optional dataframe dependency removed in favour of standard Python/Jupyter HTML tables.',
        packages_installed=0, actual_successful_run=run['run_id'], interrupted_attempts_added_to_completed_counter=0,
        kernel_runtime_keys_excluded_by_scoped_gitignore=True, original_study_inputs_and_claims_unchanged=True))
    dump(E/'visual_review.json', dict(png=run['development_png'], sha256=run['development_png_sha256'], inspected=True,
        observations='Readable3-method MAE bars,9UTC origin labels,two red regressions,frozen+0.5line,and explicit historical-development/no-final-score footnote.',
        manual_notebook_browser_or_native_app_tested=False))
    live = read('data/processed/singapore_prospective/summary.json')
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
    snapshots = len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    assert snapshots == 49 and live['scores_total'] == 42924 and live['scores_added'] == 1016
    raw_lots = sum(len(p['carpark_info']) for i in payload['items'] for p in i['carpark_data'])
    next_poll = (datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json', dict(receipt=last, snapshot_count=snapshots, accepted_rows=len(rows), raw_lot_records=raw_lots,
        fresh_at_receipt=fresh, freshness_rejections=dict(rejected), bounds_valid=True, duplicate_rows=0,
        cached_app_data_matches=True, manual_ui_tested=False, summary=live, next_sensible_collection_after=next_poll,
        separate100_run_checkpoint_due=False, scope='Previously frozen persistence only;no learned/neural/camera accuracy'))
    now = datetime.now(timezone.utc).isoformat()
    lesson = dict(run_id=run['run_id'], notebook=run['notebook'], executed_notebook_sha256=run['executed_notebook_sha256'],
        code_cells=7, inline_png_outputs=1, guarded_probes_blocked=4, development_windows=9202, global_times=9,
        model_trained=False, real_final_evaluated=False, new_packages_installed=0, archive=run['archive'],
        scientific_plot=run['development_png'], scope='Actual shared-venv Jupyter, archived DEVELOPMENT only; physical offline/new machine/browser/student mastery unverified')
    pointer = read('reports/singapore_forecast_study_latest.json')
    pointer.update(teaching_lesson=lesson, software_tests_passed=291)
    dump('reports/singapore_forecast_study_latest.json', pointer)
    state.update(last_updated_at=now, scheduled_wakeups_completed=46, singapore_forecast_study=pointer,
        singapore_read_only_lesson=lesson, prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=live['scores_total'], mae_spaces=live['baseline_mae_spaces'], scope='Persistence only; not learned/neural/camera accuracy', coverage=live['forecast_coverage']))
    state['next_actions'] = [
        'No new fitting/tuning for frozen Singapore study. Preserve candidate alpha0.30018518518518517; issuance config b68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625, scoring manifest1dc86326f3152ca090572041434e057980e151ee75ea4a2b8292f4385cb3aa1b, reservationbd47defbec2e4e73388b4eb4ad8dd8d04528a04df15ae78242427ca93f5afaca. All posthistorical-cutoff observations are inference context only, never refitting/development.',
        'At each due poll run D:\\deep learning\\.venv\\Scripts\\python.exe scripts/collect_singapore_study.py. Latest49snapshots at09:10:49UTC; next sensible collection AFTER '+next_poll+'. Next09:38wake is slightly early: work on an independent notebook/report/package task until due, then collect once. Avoid unintended60min gaps. Frozen wrapper enforces30minute plan and publisher>=1minute; do not poll per software fixture.',
        'From26October10:00UTC to27October10:00UTC (India15:30to15:30), keep genuinely pre-target learned issuance through the frozen collection wrapper. It needs two fresh same-series/same-capacity observations10-45min apart; actual clock controls issue/commit. Preserve immutable data/processed/singapore_learned_v1/batches plus data/receipts/singapore_learned_v1/*.receipt.json; commit receipt files. No retroactive origins or incomplete-batch repair. Before10:00currentstatusnot_started,zero real learnedbatches.',
        'Do not run real learned final metrics or semantic target/context evaluation before27October10:51UTC. Then run scripts/score_singapore_study.py once under actualclock. It verifies outcome-free issuance,claims global sourceinterval BEFORE targetdecode, scores first RECEIVED qualifying20-45min targets, stops on capacitychange, compares identical matchedIDs, and preserves consumed failures. Frozen gates>=500matches/>=8origins/>=50series/>=75percentcoverage/>=1percentMAEgain/macro-noninferior/maxoriginregression0.5spaces. Missingtargetsunscored. If completed, archive all result-output checksums in addition to existing input/claim/completion evidence; display cachedresults, never re-evaluate changedmethods.',
        'Highest independent next task: assemble a separate portable read-only Singapore lesson10 folder using only its10hash-bound archived inputs,helper,notebook and licence/source notes; preserve existing424-file app+Jupyter package untouched. Validate lesson against an existing known offlineJupyter venv inside the relocatedfolder with actualkernel/no nonloopback Python access. No raw/growing/final inputs or training/collection/scoringcommands in the teaching flow. Do not claim physicaloffline/newmachine/manualbrowser acceptance.',
        'Lesson10 is executed:SG-LESSON-20261026T092240303436Z,7codecells/1inlinePNG/9202pairedDEVELOPMENT rows/9globaltimes; originalsourcecells unchanged, plot visually reviewed. It explains receiptcausality, ridge7.738vs6.958rejection, trend6.310developmentpass, synthetic53.00185prediction and80percentmissing-target arithmetic, frozenfuture gates and studentquestions. No actualfinal/live/neural/camera performance or mastery claimed. Python/JupyterHTMLtables avoid installingpandas. Two interruptedattempts retained (restricted240secondtimeout; hostfirstcellmissingpandas); neither counted as a completedtrial.',
        'All291software tests pass (7new lesson/cohort/table/file-policy fixtures). One completed actualJupytervalidation66->67;wakeups46/source58/nextseparate100-run checkpoint100/no activejobs. Kernel connection keys/caches scopedignored under experiments/results/SG-LESSON-*/kernel. Archive notebooks/PNGs plus diagnostics are preserved. Original3productionweights, candidate/frozen sources and consumedclaims unchanged; no apppromotion. Oldnotebooks have dated recordedexecutions, not a current fullfresh/relocated notebook-suite run.',
        'Official feed09:10UTC:49snapshots,1016new previously frozenpersistence matches,42924total,MAE4.8396235206spaces,1256newbaselineforecasts; missingtargetsunscored. Cachedappdata/rawreceipt/hash/schema/bounds/duplicates/freshness checked; no manualUI. Learnedfuturestudy is distinct and stillunscored. CNRcontentrights unresolved/source018development-exposed/alloldfinalgroupsconsumed; independentvisionchanges needfreshqualifiedgroups. Universitydocs/manualphysicalstudentacceptance remainopen. See docs/SINGAPORE_FORECAST_STUDY.md/docs/PYTHON_WORKFLOW.md.'
    ]
    dump('data/automation_state.json', state)
    inventory = read('data/dataset_inventory.json'); inventory.update(inventoried_at=now, singapore_forecast_study=pointer, singapore_read_only_lesson=lesson)
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
            item['used_by'] += '; executed read-only Jupyterlesson10 on hash-bound archived DEVELOPMENT only, explicit synthetic examples'
    with catalog.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(items)
    note = ('Added notebook10_singapore_forecast_study.ipynb with seven actually executed Jupyter code cells and one inline development PNG. '
        'Reads only10hash-bound archived-development/frozen-metadata inputs; checks matching series/issue/targets and recomputes stored error arithmetic '
        'on the SAME9,202windows/nine collection times. Ridge7.738379vs6.957618persistence remains rejected; trend6.309848is development only. '
        'Synthetic toy prediction53.001852and80percentmatching example are explicitly teaching data. Receipt availability, train cutoff, two slightly '
        'worse origins, variable actual target leads, once-only future rules/licence and unassessed student questions are explained. '
        'Actual shared-venv kernel audits blocked two protected read probes, one study write and external DNS; no successful raw/growing/final reads or '
        'study writes. These are Python-level checks, not OS/physicaloffline/new-machine/browser/manual/mastery acceptance. Saved scientific PNG visually '
        'inspected. First restricted child timed out240seconds; owned processes were absent before host retry. Second host attempt failed firstcell '
        'becausepandaswasnotinstalled; replaced optional tables with escaped standardPython/JupyterHTML, installed0packages, successful host retry. '
        'Both interrupted attempts/protocols/source/diagnostics preserved and excluded from completed count; connection keys/runtime caches scopedignored. '
        '291software tests pass including7new lesson fixtures. One completed lessonvalidation66->67,wakeups46/source58/next100-run checkpoint100/no activejobs. '
        'Official09:10collection adds snapshot49,1,016previously frozen persistence outcomes (42,924total,MAE4.839624spaces),1,256newforecasts. '
        'Raw URL/licence/receipt/hash/normalized history and cached-app schema/bounds/duplicates/freshness checked. Real learned study still has zero '
        'batches/claims/finalmetrics beforeitsoriginwindow; all frozen runtime/candidate/original weights/consumed claims unchanged. No app promotion. '
        'README stale six-final-untested statement corrected to the preserved consumed/failed occupancy replacement result. Existing424-file offline '
        'package and old notebooks/reports remain dated. Next:separate relocated read-only lesson pack and sensiblecollection; no fitting or early scoring. '
        'Evidence:reports/singapore_lesson_latest.json;guide:docs/SINGAPORE_FORECAST_STUDY.md.')
    for path in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/IMPLEMENTATION_STATUS.md', 'docs/TEST_RESULTS.md',
                 'docs/AI_ASSISTANCE_LOG.md', 'docs/DATASET_PROVENANCE.md', 'docs/THIRD_PARTY_SOURCES.md']:
        append(path, note)
    append('docs/UI_TEST_LOG.md', 'Actual saved lesson10 development PNG visually inspected: labels, method values, nine UTC timestamps, two regressions, threshold and scope footnote readable. Actual kernel and HTML-table escaping tests pass; no manual notebook-browser/native-app/student rehearsal performed.')
    req = ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; items = list(reader)
    for item in items:
        if item['requirement_id'] in ['ENV-02', 'DATA-04', 'QA-02']:
            item['actual_evidence'] += '; notebooks/10_singapore_forecast_study.ipynb; reports/singapore_lesson_latest.json'
            item['test_result'] += ';7actualJupytercells/1PNG/4guardedprobes;pairedDEVELOPMENT only;291software tests;no newpackages'
            item['open_problems'] += ';Lesson10notyet in relocated demo; manualbrowser/physicaloffline/student mastery unassessed'
    with req.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL); writer.writeheader(); writer.writerows(items)
    dump(E/'handoff.json', dict(recorded_at=now, completed_trials=67, wakeups=46, source_records=58, next_live_checkpoint_at_run=100,
        lesson=lesson, software_tests_passed=291, interrupted_attempts_retained=2, real_study_unclaimed_unscored=True,
        no_active_jobs=True, next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(completed_trials=67, wakeups=46, tests=291, code_cells=7, raw_snapshots=49,
                         fresh_at_collection=fresh, actual_final_evaluated=False), indent=2))


if __name__ == '__main__':
    main()
