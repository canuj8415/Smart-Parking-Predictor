"""Record the dated, verified forecast/export refresh without replaying models."""
import csv
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed

E = ROOT / 'experiments/evidence/HEARTBEAT-20261026T025043Z'
RID = 'COMBINED-DEMO-20261026T025712811956Z'
TITLE = '## 26 October 2026 / forecast exports verified in the refreshed offline copy'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def append(path, body):
    path = ROOT / path
    old = path.read_text(encoding='utf-8')
    assert TITLE not in old, path
    path.write_text(old.rstrip() + '\n\n' + TITLE + '\n\n' + body + '\n', encoding='utf-8')


def main():
    assert not (E / 'handoff.json').exists(), 'Dated handoff already recorded'
    state = read('data/automation_state.json')
    run = read('experiments/results/' + RID + '/run.json')
    independent = read(E / 'independent_checks.json')
    package = ROOT / run['package']
    assert state['last_completed_run'] == independent['run_id'] == RID
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 54
    assert state['scheduled_wakeups_completed'] == 36
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['combined_demo_gate_passed'] and independent['genuine_jupyter_kernel_verified']
    assert independent['expected_installed_packages_verified'] == 107
    assert independent['original_package_payload_and_ready_files_unchanged']
    assert all(digest(ROOT / p) == h for p, h in {**run['source_hashes'], **run['protected_hashes']}.items())
    assert all(digest(package / p['path']) == p['sha256'] for p in run['payload'])
    now = datetime.now(timezone.utc).isoformat()
    previous = read('reports/offline_demo_latest.json')
    assert previous['run_id'] == run['previous_demo']
    for path in ['reports/offline_demo_latest.json', 'reports/demo_package_latest.json', 'models/combined_offline_demo_package.json']:
        destination = E / 'previous_latest' / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    pointer = dict(run_id=RID, kind='Selected offline demo with forecast variant labels and exports', path=run['package'],
        files=run['payload_files'], bytes=run['payload_bytes'], manifest_sha256=digest(package / 'BUNDLE_MANIFEST.json'),
        validation_sha256=digest(package / 'COMBINED_VALIDATION.json'), guide='docs/COMBINED_OFFLINE_DEMO_GUIDE.md',
        fresh_package_environment=run['package'] + '/.venv', python=run['package'] + '/.venv/Scripts/python.exe',
        fresh_package_install_verified=True, runtime_reused=False, existing_base_python_reused=True,
        physical_network_disconnection_verified=False, new_machine_verified=False, visible_manual_acceptance=False,
        installer_wheels=107, installer_bytes=257829508, actual_copied_folder_kernel_verified=True,
        included_notebooks=run['selected_notebooks'], excluded_notebooks=run['excluded_notebooks'],
        forecast_methods=independent['forecast_methods_verified'], cached_live_snapshot=run['cached_live_snapshot'],
        cached_live_provider_timestamp=run['cached_live_provider_timestamp'], cached_live_sha256=run['cached_live_sha256'],
        previous_run=previous['run_id'], previous_pointer_archive=(E / 'previous_latest/reports/offline_demo_latest.json').relative_to(ROOT).as_posix(),
        scientific_accuracy_evaluated=False, model_training_performed=False)
    write('reports/offline_demo_latest.json', pointer)
    write('reports/demo_package_latest.json', pointer)
    write('models/combined_offline_demo_package.json', run)
    folder = ROOT / 'experiments/results' / RID
    write(E / 'probe_outputs.json', {name: dict(stdout=(folder / (name + '_stdout.txt')).read_text(encoding='utf-8'),
        stderr=(folder / (name + '_stderr.txt')).read_text(encoding='utf-8')) for name in ['install', 'app', 'notebook']})
    for result in run['app_validation']['forecast_method_exports']:
        source = package / result['export']
        destination = E / 'forecast_exports' / result['method_id']
        destination.mkdir(parents=True, exist_ok=False)
        for name in ['forecast.png', 'forecasts.csv', 'forecast_report.json', 'export_metadata.json']:
            shutil.copyfile(source / name, destination / name)
            assert digest(source / name) == digest(destination / name)
    receipts = [json.loads(line) for line in (ROOT / 'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    latest = next(r for r in reversed(receipts) if r['source_id'] == 'SRC-LIVE-001')
    assert digest(ROOT / latest['local_path']) == latest['sha256']
    live = read('data/processed/singapore_prospective/summary.json')
    payload = read(latest['local_path'])
    rows = parse_feed(payload)
    raw_lots = sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0 <= r['available'] <= r['capacity'] for r in rows)
    assert len(rows) == len({(r['car_park_id'], r['lot_type'], r['observed_at']) for r in rows})
    snapshots = len(list((ROOT / 'data/raw/singapore_live').glob('*.json')))
    next_poll = (datetime.fromisoformat(live['checked_at']) + timedelta(minutes=30)).isoformat()
    write(E / 'live_checkpoint.json', dict(receipt=latest, summary=live, snapshot_count=snapshots,
        raw_lot_records=raw_lots, accepted_rows=len(rows), invalid_capacity_excluded=raw_lots - len(rows),
        bounds_valid=True, duplicate_rows=0, next_sensible_collection_after=next_poll, separate_100_run_checkpoint_due=False,
        scope='Causal delayed persistence scoring and feed integration only;not neural/camera accuracy. Frozen offline cache is separately dated.'))
    inventory = read('data/dataset_inventory.json')
    inventory.update(inventoried_at=now, combined_offline_demo=pointer)
    for item in inventory['datasets']:
        if item['source_id'] == 'SRC-LIVE-001':
            item.update(car_parks=len({r['car_park_id'] for r in rows}), observations=len(rows), raw_lot_records=raw_lots,
                raw_path=latest['local_path'], provider_timestamp=latest['provider_timestamp'], snapshot_count=snapshots,
                prospective_baseline_scored_outcomes=live['scores_total'], prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
                forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json', inventory)
    state.update(last_updated_at=now, scheduled_wakeups_completed=37, combined_offline_demo=pointer,
        prospective_live_summary=live, last_live_baseline_score=dict(outcomes=live['scores_total'],
            mae_spaces=live['baseline_mae_spaces'], scope='Persistence only;not neural/camera accuracy', coverage=live['forecast_coverage']))
    state['next_actions'] = [
        'Refreshed selected offline package gate PASSES:424payload files/807000528bytes;fresh local107-package no-index/hash-locked install;both actual hidden detector options,forecast variant labels/PNG/CSV/JSON exports,selection-change invalidation and genuine Jupyter08kernel pass. Old419filepackage unchanged. See reports/offline_demo_latest.json/docs/COMBINED_OFFLINE_DEMO_GUIDE.md. Do not repeat identical builds to inflate counts.',
        'Highest scientific priority:qualify authoritative individual-image usage permission for CNR or another legitimate labelled camera source. CNR144965metadata records/32079reserved final images remain unopened and image-use-unqualified. Preserve archive and metadata;do not decode/train/score without rights. No private CCTV/accounts/author contact/bypass.',
        'Occupancy candidate remains unpromoted:failed final rainy-view retention13/14<95percent. Six final photos/three whole groups/171sourceframes CONSUMED plus older image,Birmingham and DAVIS finals. No tuning/re-evaluating changed methods on consumed groups;reserve genuinely fresh canonical groups before new candidate final. Original models and frozen prediction reports unchanged.',
        'Counter54;next separate100-run live checkpoint100;no active jobs. Source catalog57 unchanged. Latest live observation '+live['checked_at']+':42snapshots,36258matched earlier persistence targets,MAE4.795797spaces. Next sensible collection AFTER '+next_poll+';missing targets remain unscored. Offline copy retains snapshot41from02:30UTC,not the main history latest42from03:00UTC.',
        'Both forecast variants are LSTMs;archived reports/own cohort/MAE/lead remain historical Birmingham,not Singapore neural forecasting. Full213software tests passed in prior shared-runtime check;this wake is one fresh package integration,not213new tests or model training.',
        'Only notebook08ofnine is packaged;full data/other8remain main project. Existing base Python/Windows/Tk reused. Visible/manual/browser/physical-disconnection/new-machine/student mastery/official university-doc checks remain separate. App-stage legacy scope text concerns its own substage;combined report separately proves fresh install and genuine copied-folder Jupyter.']
    write('data/automation_state.json', state)
    note = ('The refreshed selected demo passes its frozen combined gate in415.75seconds:424payload files (807,000,528bytes),107original installer wheels and a NEW package-local environment with all107installed versions independently verified. '
        'Actual hidden native checks exercise both detectors on one training image,semantic preview,2D/3D teaching examples,SVD,two already-seen video frames,cached live data and both archived forecast variants. '
        'Original LSTM and Group-relative residual LSTM each retain their own plot legend,run/checkpoint/prediction identity and exact PNG/CSV/JSON exports. Report/park changes clear the previous plot/export. Export PNGs were visually inspected. '
        'A genuine copied-folder Jupyter kernel executes notebook08with one inline PNG;only08ofnine notebooks is included. Existing-environment overwrite is refused. Normal app Python socket attempts:zero;installer/Jupyter audit denials:zero. Separate deliberate original-project read/DNS probes are blocked. Python guards do not isolate native-extension IO or physically disconnect the laptop. '
        'All424payload hashes,protected model/claim bytes and all419earlier-package payload bytes remain unchanged. No model training,new scientific scoring,consumed final replay,new-machine or visible/manual/student acceptance. Prior213shared-runtime software tests remain separately dated. '
        'Counter53->54 counts one integration trial;wakeups37,next100-run live checkpoint100,no active jobs. Source catalog57unchanged;installer copying is not new acquisition. '
        'Offline cache is snapshot41/provider2026-10-26T10:29:36+08:00;main history has42snapshots/provider11:00:36+08:00. Main causal persistence scores36,258targets,MAE4.795797spaces;missing targets unscored,not neural/camera accuracy. '
        'Evidence:experiments/results/'+RID+'/run.json;experiments/evidence/HEARTBEAT-20261026T025043Z/independent_checks.json. Start:docs/COMBINED_OFFLINE_DEMO_GUIDE.md. Next:legitimate fresh labels;failed occupancy final remains unpromoted.')
    for path in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/IMPLEMENTATION_STATUS.md', 'docs/TEST_RESULTS.md', 'docs/UI_TEST_LOG.md', 'docs/AI_ASSISTANCE_LOG.md']:
        append(path, note)
    append('docs/DATASET_PROVENANCE.md', 'No new scientific dataset or wheel acquisition. All copied assets retain original source IDs/hashes/notices. '+
        'Singapore SRC-LIVE-001 raw '+latest['local_path']+' SHA256 '+latest['sha256']+';source '+latest['source_url']+';'+latest['license']+'. '+
        'Normalized observations:data/processed/singapore_live_observations.csv;immutable receipt:data/resource_receipts.jsonl;delayed baseline summary:data/processed/singapore_prospective/summary.json. '+
        '42snapshots,36,258matched persistence targets,MAE4.795797spaces;missing-target coverage is separate. The frozen offline payload intentionally retains the earlier02:30UTC snapshot. No neural/camera live accuracy.')
    guide = ROOT / 'docs/COMBINED_OFFLINE_DEMO_GUIDE.md'
    text = guide.read_text(encoding='utf-8').replace('the other seven notebooks', 'the other eight notebooks')
    guide.write_text(text, encoding='utf-8')
    append('docs/COMBINED_OFFLINE_DEMO_GUIDE.md', 'Current checked folder: `'+run['package']+'`. It already has the verified `.venv`;skip installation on this laptop and use the launch commands above. '+
        'The fresh107-package install,both detector routes and genuine notebook08kernel passed. Choose **Original experiment** or **Later-date check**,then **Show held-out forecast** and **Save forecast results**. '+
        'The legend/export identifies **Original LSTM** or **Group-relative residual LSTM**. Saving writes PNG,CSV,report JSON and checksum metadata for the displayed selection;changing report/park clears it. '+
        'These are saved Birmingham results. See `docs/FORECAST_REPORTS_GUIDE.md`. Only notebook08ofnine is included. The cached Singapore reading is provider `2026-10-26T10:29:36+08:00`,so it can show STALE. '+
        'The earlier419-file demo remains intact. Full-training/physical/new-machine/manual/student acceptance remains separate.')
    append('docs/DEMO_PACKAGE_GUIDE.md', 'The latest pointer now selects '+RID+' (424files),including the forecast export fix. '+
        'Use docs/COMBINED_OFFLINE_DEMO_GUIDE.md;only notebook08ofnine is included. Historical package counts below describe previous dated copies.')
    path = ROOT / 'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; requirements = list(reader)
    for row in requirements:
        if row['requirement_id'] in ['PKG-01', 'OFF-01']:
            row.update(actual_evidence='reports/offline_demo_latest.json; models/combined_offline_demo_package.json; docs/COMBINED_OFFLINE_DEMO_GUIDE.md',
                test_result='424payload files/807000528bytes;fresh107-package no-index/hash-locked venv;both detector and forecast-export routes;genuine notebook08kernel pass;old419filecopy preserved',
                open_problems='Only notebook08ofnine/full training data excluded;base Windows/Python/Tk reused;native IO/physical/new-machine/manual/student/official acceptance separate',
                next_action='Preserve current package;prioritize legitimate fresh labels and remaining acceptance;do not repeat identical builds')
        if row['requirement_id'] in ['APP-01', 'APP-02', 'QA-02']:
            row['actual_evidence'] += '; experiments/results/'+RID+'/run.json'
            row['test_result'] += ';Fresh copied-folder forecast variant labels/PNG/CSV/JSON/selection invalidation pass;not new accuracy'
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL); writer.writeheader(); writer.writerows(requirements)
    write(E / 'handoff.json', dict(saved_at=now, run_id=RID, completed_trials=54, wakeups=37, next_live_milestone=100,
        source_records=57, pointer=pointer, independent_checks=independent, no_active_jobs=True, no_training_or_new_accuracy=True,
        export_pngs_visually_inspected=True, live_snapshots=snapshots, next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(run_id=RID, trials=54, wakeups=37, snapshots=snapshots, next_poll=next_poll), indent=2))


if __name__ == '__main__':
    main()
