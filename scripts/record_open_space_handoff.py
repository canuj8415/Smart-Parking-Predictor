"""Save the new publisher source and next-step limitations without model claims."""
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.provenance import digest, receipt
from smart_parking.live import parse_feed

E = ROOT / 'experiments/evidence/HEARTBEAT-20261026T032043Z'
SID = 'SRC-DS-018'
TITLE = '## 26 October 2026 / new publisher-original parking archive verified'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def dump(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def append(path, body):
    path = ROOT / path
    text = path.read_text(encoding='utf-8')
    assert TITLE not in text
    path.write_text(text.rstrip() + '\n\n' + TITLE + '\n\n' + body + '\n', encoding='utf-8')


def main():
    assert not (E / 'handoff.json').exists()
    now = datetime.now(timezone.utc).isoformat()
    state = read('data/automation_state.json')
    rid = state['last_completed_run']
    run = read('experiments/results/' + rid + '/run.json')
    summary = run['summary']
    assert rid.startswith('OPEN-SPACE-ASSETS-') and run['asset_integrity_gate_passed']
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 55
    assert state['scheduled_wakeups_completed'] == 37
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert all(digest(ROOT / p) == h for p, h in {**run['source_hashes'], **run['protected_hashes']}.items())
    assert digest(ROOT / summary['archive']) == summary['archive_sha256']
    metadata = ROOT / run['metadata_path']
    assert digest(metadata) == run['metadata_sha256']
    receipt(SID, metadata, 'https://api.github.com/repos/bermalA/open-space-parking-dataset/git/trees/' + run['commit'] + '?recursive=1',
        'Pinned GitHub connector metadata/rights text serialized locally;not original HTTP response bytes',
        connector_response_serialized=True, original_http_bytes=False, commit=run['commit'], exact_per_request_time_captured=False)
    catalog = ROOT / 'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; sources = list(reader)
    assert len(sources) == 57 and not any(r['source_id'] == SID for r in sources)
    record = dict(source_id=SID, resource_type='dataset;publisher archive qualification', resource='Open-Space Parking Occupancy Dataset',
        original_creator='bermalA (publisher repository handle);dataset authors unnamed in README',
        source_url='https://github.com/bermalA/open-space-parking-dataset', download_url=run['acquisition_receipt']['source_url'],
        access_date=run['acquisition_receipt']['accessed_at'][:10], access_time_precision='Exact archive UTC in receipt;connector metadata per-request time not captured',
        version=run['commit'], license='CC BY4.0;publisher LICENSE and README explicitly cover dataset and original photos/labels',
        permission='Publisher explicitly declares all images/annotations author-created;local attributed inspection permitted;model/benchmark admission pending',
        original_size=str(summary['archive_bytes'])+'archive bytes;'+str(summary['uncompressed_file_bytes'])+'uncompressed bytes',
        local_location=summary['archive'], sha256=summary['archive_sha256'], purpose='Fresh parking-image source for future occupancy/region work',
        used_by='Pinned archive/Git-tree qualification only;no model training/scoring', modifications='Original archive intact;only exact README/LICENSE/data.yaml recovered;all files hashed,images not pixel-decoded',
        attribution='bermalA/open-space-parking-dataset (2025),Open-Space Parking Occupancy Dataset,CC BY4.0;paper citation incomplete',
        status='Acquired;1465publisher Git blob identities verified;not benchmark-admitted',
        open_issues='Camera/capture dates,near duplicates,dimensions,annotation geometry/exhaustiveness/content provenance not independently verified;publisher split names not grouped holdouts')
    with catalog.open('a', encoding='utf-8', newline='') as stream:
        csv.DictWriter(stream, fieldnames=fields).writerow({k: record.get(k, '') for k in fields})
    live = read('data/processed/singapore_prospective/summary.json')
    receipts = [json.loads(line) for line in (ROOT / 'data/resource_receipts.jsonl').read_text().splitlines()]
    latest = next(r for r in reversed(receipts) if r['source_id'] == 'SRC-LIVE-001')
    assert digest(ROOT / latest['local_path']) == latest['sha256']
    payload = read(latest['local_path']); rows = parse_feed(payload)
    raw_lots = sum(len(park['carpark_info']) for item in payload['items'] for park in item['carpark_data'])
    assert all(0 <= r['available'] <= r['capacity'] for r in rows)
    assert len(rows) == len({(r['car_park_id'], r['lot_type'], r['observed_at']) for r in rows})
    snapshots = len(list((ROOT / 'data/raw/singapore_live').glob('*.json')))
    next_poll = (datetime.fromisoformat(live['checked_at']) + timedelta(minutes=30)).isoformat()
    dump(E / 'live_checks.json', dict(receipt=latest, summary=live, snapshot_count=snapshots, accepted_rows=len(rows),
        raw_lot_records=raw_lots, invalid_capacity_excluded=raw_lots-len(rows), bounds_valid=True, duplicate_rows=0,
        next_sensible_collection_after=next_poll, separate_100_run_checkpoint_due=False,
        scope='Collection gap leaves earlier targets missing,not zero error;no matching delayed scores added,no neural/camera accuracy'))
    pointer = dict(run_id=rid, source_id=SID, commit=run['commit'], archive=summary['archive'], archive_sha256=summary['archive_sha256'],
        files_verified=1465, images=731, label_files=731, image_pixels_decoded=0, label_rows_semantically_interpreted=0,
        asset_integrity_gate_passed=True, independent_benchmark_admitted=False, guide='docs/OPEN_SPACE_DATA_GUIDE.md',
        usage_qualification='data/manifests/open_space_usage_qualification_v1.json')
    dump('reports/open_space_data_latest.json', pointer)
    inventory = read('data/dataset_inventory.json')
    assert not any(r['source_id'] == SID for r in inventory['datasets'])
    inventory['datasets'].append(dict(source_id=SID, status='Pinned originals and metadata verified;image/label/group admission pending',
        raw_archive=summary['archive'], archive_bytes=summary['archive_bytes'], uncompressed_bytes=summary['uncompressed_file_bytes'],
        sha256=summary['archive_sha256'], commit=run['commit'], images=731, annotation_files=731, files_verified=1465,
        image_pixels_decoded=0, semantic_label_rows_read=0, used_for_model_training=False, used_for_model_evaluation=False,
        publisher_splits=summary['publisher_image_split_counts'], camera_ids=None, capture_dates=None, near_duplicates_audited=False,
        usage_qualification=pointer['usage_qualification']))
    for row in inventory['datasets']:
        if row['source_id'] == 'SRC-LIVE-001':
            row.update(raw_path=latest['local_path'], provider_timestamp=latest['provider_timestamp'], snapshot_count=snapshots,
                observations=len(rows), car_parks=len({r['car_park_id'] for r in rows}), raw_lot_records=raw_lots,
                prospective_baseline_scored_outcomes=live['scores_total'], prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
                forecast_target_coverage=live['forecast_coverage'])
    inventory['inventoried_at'] = now
    dump('data/dataset_inventory.json', inventory)
    state.update(last_updated_at=now, scheduled_wakeups_completed=38, open_space_asset_qualification=pointer,
        prospective_live_summary=live, last_live_baseline_score=dict(outcomes=live['scores_total'], mae_spaces=live['baseline_mae_spaces'],
            scope='Persistence only;no new matches this wake,not neural/camera accuracy', coverage=live['forecast_coverage']))
    state['next_actions'] = [
        'New source SRC-DS-018:publisher-original Open-Space Parking dataset,commit '+run['commit']+'.94,163,307byte archive/1465files/731image-label pairs all match publisher Git blob hashes. Original archive preserved;only README/LICENSE/data.yaml extracted. No pixels/semantic label rows decoded. See docs/OPEN_SPACE_DATA_GUIDE.md and reports/open_space_data_latest.json.',
        'Next:bounded hypothesis-driven image/label admission using only explicitly preselected publisher TRAIN examples for dimension/EXIF/box-meaning review,plus labelled software tests for a strict finite normalized YOLO parser. Do not train/score first or treat69publisher-test/144valid images as independent final groups:camera/dates/near duplicates unknown. Decide honest source-wide training/development role or valid grouped protocol BEFORE any model use;whole collection may be needed as one group. No cross-source accuracy claim from random publisher splits.',
        'Original occupancy models remain active. Separate candidate failed frozen rainy-group retention13/14<95percent;no promotion. All consumed PKLot/Birmingham/DAVIS final groups remain closed,including3latest whole groups/171sourceframes. Any changed-method final needs genuinely fresh canonical groups and a new prespecified reservation/claim;never waive the failed rule.',
        'CNR image-content rights still unqualified;144965metadata rows qualified/32079reserved images unopened. This new original-content declaration belongs only to SRC-DS-018,not CNR or third-party mirror datasets. Preserve every source licence separately;no private access/author messages/bypass.',
        'Counter55;wakeups38;next separate100-run live checkpoint100;no active jobs. Source catalog58. Singapore43snapshots,latest '+live['checked_at']+':0new matched scores after collection gap,36258total,persistence MAE4.795797spaces;11472expired missing targets unscored,matching coverage75.9648percent.1159new forecasts frozen. Next sensible collection AFTER '+next_poll+';no synthetic zero scores or camera/neural live accuracy.',
        'Verified424fileoffline package remains unchanged;do not refresh merely for a new inventory record. Only notebook08ofnine is packaged. Actual213shared-runtime tests and previous fresh app/Jupyter checks remain separately dated;current run is one data-integrity qualification,not model training. Physical/manual/browser/student mastery/official university docs remain open.']
    dump('data/automation_state.json', state)
    note = ('New SRC-DS-018 is the publisher repository bermalA/open-space-parking-dataset,not a CNR mirror. Its README explicitly declares author-created images/annotations and LICENSE declares dataset CC BY4.0. '+
        'Pinned commit '+run['commit']+' yields731photos/731matching label files (publisher518train/144valid/69test). A bounded94,163,307byte original archive was acquired;all1465file sizes/Git blob identities verified,102,520,255uncompressed bytes. '+
        'No exact JPEG Git-blob duplicates found;this does not establish absence of near duplicates or source independence. Encoded image/label bytes were streamed/decompressed for hashes,but zero image pixels decoded and zero semantic annotation rows interpreted. Only three exact metadata files were extracted. '+
        'Camera/capture dates,dimensions,geometry/exhaustiveness and source-content provenance are not independently verified. Publisher handle is recorded;paper citation incomplete. Image rights basis is this publisher declaration,not CNR terms. No training/scoring or benchmark admission. '+
        'Original models/claims/earlier package remain unchanged. One completed asset-integrity trial advances54->55;wakeups38;catalog58;next100-run checkpoint100. '+
        'Official Singapore snapshot43was collected at05:34UTC after a gap:0new matching later outcomes,36,258total,persistence MAE4.795797spaces.11,472expired targets remain unscored;matching coverage75.9648percent,not accuracy.1,159new forecasts frozen. '+
        'Guide:docs/OPEN_SPACE_DATA_GUIDE.md;exact source URL/commit/local SHA and acquisition UTC in data/resource_receipts.jsonl;raw archive in data/raw/open_space_official/. Next:bounded train-only geometry/label/group admission,not automatic random-split benchmarking.')
    for path in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/IMPLEMENTATION_STATUS.md', 'docs/TEST_RESULTS.md', 'docs/AI_ASSISTANCE_LOG.md', 'docs/DATASET_PROVENANCE.md', 'docs/SOURCE_REGISTRY.md', 'docs/THIRD_PARTY_SOURCES.md', 'docs/LICENSING_RECORD.md']:
        append(path, note)
    append('docs/CNRPARK_DATA_QUALIFICATION.md', 'A separate source SRC-DS-018 explicitly declares original photos/labels and CC BY4.0. Its731pairs are acquired/byte-qualified,with model/group admission pending. '+
        'See docs/OPEN_SPACE_DATA_GUIDE.md. This does not alter the CNR image-content decision:all CNR images remain unopened and not model-authorized.')
    req = ROOT / 'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig', newline='') as stream:
        reader=csv.DictReader(stream); fields=reader.fieldnames; requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['DATA-01', 'DATA-02', 'DATA-03']:
            row['actual_evidence'] += '; reports/open_space_data_latest.json; models/open_space_asset_qualification.json'
            row['test_result'] += ';SRC-DS-018731publisher-original image/label pairs/1465Git blobs verified,no pixel decode/model use;58sources'
            row['open_problems'] += ';New source camera/dates/near duplicates/geometry unqualified;publisher split not admitted as grouped final'
    with req.open('w', encoding='utf-8', newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    dump(E / 'handoff.json', dict(recorded_at=now, heartbeat_trigger='2026-10-26T03:20:43.657Z', actual_archive_started_at=run['started_at'],
        run_id=rid, completed_trials=55, wakeups=38, source_records=58, next_live_milestone=100, no_active_jobs=True,
        source_pointer=pointer, source_record=record, source_hashes_unchanged=True, protected_models_and_claims_unchanged=True,
        source_pixels_decoded=0, semantic_target_rows_read=0, no_new_model_accuracy=True, next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(run_id=rid, trials=55, sources=58, snapshots=snapshots, next_poll=next_poll), indent=2))


if __name__ == '__main__':
    main()
