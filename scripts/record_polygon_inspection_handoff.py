"""Save the failed box assumption and corrected TRAIN polygon inspection."""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.provenance import digest

E = ROOT / 'experiments/evidence/HEARTBEAT-20261026T053845Z'
TITLE = '## 26 October 2026 / supplied space polygons and conservative source grouping'


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
    failed_id = 'OPEN-SPACE-TRAIN-INSPECTION-20261026T054147720575Z'
    failure = read('experiments/results/' + failed_id + '/run.json')
    tests = read(E / 'software_tests.json')
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 57
    assert state['scheduled_wakeups_completed'] == 38
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert failure['terminal_failure'] and failure['actual_image_pixels_decoded'] == 1
    assert run['summary']['technical_training_sample_gate_passed'] and run['summary']['polygons'] == 294
    assert tests['returncode'] == 0 and 'Ran 227 tests' in tests['stderr']
    assert all(digest(ROOT / p) == h for p, h in {**run['source_hashes'], **run['protected_hashes']}.items())
    assert run['exact_read_members'] == [p for row in run['selection'] for p in [row['path'], row['annotation']]]
    asset = read('models/open_space_asset_qualification.json')
    prior_usage = read('data/manifests/open_space_usage_qualification_v1.json')
    assert digest(ROOT / run['archive']) == run['archive_sha256'] == asset['summary']['archive_sha256']
    review = dict(recorded_at=now, run_id=rid, contact_sheet=run['contact_sheet'], contact_sheet_sha256=digest(ROOT / run['contact_sheet']),
        review_method='Assistant visual inspection of actual generated contact sheet;no model predictions or manual exhaustive relabelling',
        observations=['Supplied rings visibly outline perspective parking-space footprints rather than ordinary axis-aligned boxes',
            'train001/173/345appear in daylight;train518appears at night',
            'Backgrounds/signage/parking arrangement appear related across the four views;camera identities and capture sessions not verified',
            'Some scene regions contain parked vehicles outside supplied annotated space polygons;full-frame annotation exhaustiveness not established'],
        semantic_geometry_plausibility='Qualitative only;not ground-truth accuracy',
        exhaustive_annotation_audited=False, camera_date_independence_verified=False,
        conservative_group='SRC-DS-018:whole-publisher-collection', source_wide_role='development_exposed',
        independent_final_eligible=False, student_or_manual_acceptance=False)
    dump(E / 'visual_review.json', review)
    usage = dict(prior_usage, version=2, run_id=rid, asset_qualification_run=prior_usage['run_id'], recorded_at=now, parent_usage='data/manifests/open_space_usage_qualification_v1.json',
        parent_usage_sha256=digest(ROOT / 'data/manifests/open_space_usage_qualification_v1.json'),
        inspection_run=rid, failed_rectangle_assumption_run=failed_id,
        usage_status='Four TRAIN examples technically qualified;whole source development-exposed,not an independent final cohort',
        image_pixels_decoded=4, labels_semantically_interpreted=294, distinct_train_label_files_interpreted=4, accepted_polygons_in_selected_training_examples=294,
        coordinate_format='YOLO segmentation polygons,not five-token axis-aligned boxes;source rows preserved',
        publisher_validation_or_test_pixels_and_semantic_labels_read=0, semantic_visual_review=review,
        source_splits='518train/144valid/69test are publisher folders only;do not treat them as independent project groups',
        canonical_project_group='SRC-DS-018:whole-publisher-collection', project_role='development_exposed',
        independent_benchmark_admitted=False, independent_final_eligible=False, model_training_admitted=False,
        grouping_basis='Unknown capture dates and visually related perspectives;assign whole collection conservatively after TRAIN inspection',
        pixel_mask_annotation_exhaustiveness_verified=False,
        pending=['Audit broader explicitly TRAIN-only image/label and near-duplicate quality',
            'Before training define source-wide train/development role and loss/ROI semantics without pretending unannotated areas are labelled background',
            'Any changed model final needs genuinely fresh independent canonical groups outside this development-exposed collection'])
    # v1 is an immutable record of the earlier zero-pixel integrity stage.
    dump('data/manifests/open_space_usage_qualification_v2.json', usage)
    pointer = dict(run_id=rid, failed_box_reader_run=failed_id, source_id='SRC-DS-018', source_commit=run['source_commit'],
        train_photos=4, accepted_polygons=294, class_counts=run['summary']['class_counts'], image_dimensions=[1280,640],
        source_group=usage['canonical_project_group'], source_role=usage['project_role'], independent_final_eligible=False,
        model_training_admitted=False, software_tests_passed=227, visual_review=(E/'visual_review.json').relative_to(ROOT).as_posix(),
        usage_qualification='data/manifests/open_space_usage_qualification_v2.json', guide='docs/OPEN_SPACE_DATA_GUIDE.md')
    dump('reports/open_space_training_inspection_latest.json', pointer)
    latest = read('reports/open_space_data_latest.json')
    latest.update(current_inspection=pointer, usage_qualification=pointer['usage_qualification'],
        initial_integrity_stage_images_decoded=0, image_pixels_decoded=4, label_rows_semantically_interpreted=294, current_distinct_image_pixels_decoded=4, current_distinct_train_label_files_interpreted=4)
    dump('reports/open_space_data_latest.json', latest)
    catalog = ROOT / 'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig', newline='') as stream:
        reader=csv.DictReader(stream); fields=reader.fieldnames; sources=list(reader)
    assert len(sources) == 58 and sum(r['source_id']=='SRC-DS-018' for r in sources) == 1
    for row in sources:
        if row['source_id'] == 'SRC-DS-018':
            row.update(used_by='Pinned integrity audit;four fixed TRAIN photos/294segmentation polygons;strict parser/qualitative source inspection only,no models',
                modifications='Original archive intact;four exact TRAIN image/label pairs copied;diagnostic polygon outlines generated with source hashes',
                status='Four TRAIN samples technically qualified;whole source development-exposed,not independent final',
                open_issues='No capture dates/camera identities;related perspectives/day-night scene;annotation exhaustiveness/near duplicates unresolved;not all731images audited;no model training admitted')
    with catalog.open('w', encoding='utf-8', newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    inventory = read('data/dataset_inventory.json')
    inventory['inventoried_at'] = now
    for row in inventory['datasets']:
        if row['source_id'] == 'SRC-DS-018':
            row.update(status=usage['usage_status'], image_pixels_decoded=4, semantic_label_rows_read=294, semantic_train_label_files_interpreted=4,
                inspected_polygons=294, supplied_occupied_polygons=235, supplied_vacant_polygons=59,
                inspection_dimensions=[1280,640], capture_dates_present_in_four_images=0,
                usage_qualification=pointer['usage_qualification'], source_wide_role='development_exposed', independent_final_eligible=False)
    dump('data/dataset_inventory.json', inventory)
    state.update(last_updated_at=now, scheduled_wakeups_completed=39, open_space_training_inspection=pointer)
    state['next_actions'] = [
        'SRC-DS-018 supplies YOLO SEGMENTATION POLYGONS,not box labels. Four preselected TRAIN photos001/173/345/518are1280x640;294valid source polygons(235occupied/59vacant),zero clipping/rejected files. Actual visual review shows perspective spaces,day/night and related parking backgrounds. No EXIF capture dates. See docs/OPEN_SPACE_DATA_GUIDE.md,models/open_space_training_inspection.json and usagev2.',
        'Highest useful next step:bounded broader publisher TRAIN-only geometry/annotation and near-duplicate admission audit,using strict parse_space_polygons. Preserve source text/CRC/hash/pixel provenance;quarantine failures,never invent background labels for unannotated portions. Then design source-wide training/development role plus explicit ROI/loss semantics before any new occupancy/region training. Existing pretrained weights remain unchanged.',
        'Whole SRC-DS-018collection is conservatively development-exposed because dates/session identities unknown and four TRAIN views visually related. Do not use69publisher-test or144valid folders as independent final data. No valid/test pixels/semantic labels read. New model final requires a genuinely fresh canonical group outside this exposed collection;existing consumed PKLot/Birmingham/DAVIS finals remain closed. CNR image-content rights remain unqualified.',
        'Record both experiments honestly:strict box assumption FAILED firstTRAIN syntax gate(56);polygon-specific preselected-four inspection PASSED(57). First failure interrupted artifact counted appended records as0but one TRAINimage had actually decoded;terminal failure report preserves/corrects that history. Four DISTINCT training photos now inspected,not five. No model accuracy/training/promotion this wake;original occupancy candidate failed final retention13/14<95percent remains unpromoted.',
        'Counter57;wakeups39;next separate100-run live checkpoint100;no active jobs;source catalog58.227software tests PASS,14new synthetic parser/selection tests included. Test count is not experiment count. Full424fileoffline package remains dated/unchanged. Main notebooks remain Python/Jupyter.',
        'Singapore last collected2026-10-26T05:34:21.723336+00:00;43snapshots,36258matched persistence targets,MAE4.795797spaces,11472expired targets unscored,matching coverage75.9648percent. Next sensible collection AFTER2026-10-26T06:04:21.723336+00:00;not due this wake. No camera/neural live accuracy. Physical/manual/browser/student mastery/official university documents remain separate.']
    dump('data/automation_state.json', state)
    note = ('The first prespecified TRAIN syntax check failed because source labels are segmentation polygons,class plusXYvertices,often repeating the closing point;the strict five-token box reader correctly rejected them. '+
        'Failure run '+failed_id+' and original code/interrupted evidence retained. Its original interrupted pixel count0meant fully appended records;one TRAINimage actually decoded before parser failure,and terminal failure report corrects this. '+
        'A separate strict polygon reader preserves raw rows/coordinates,handles a repeated closing vertex and tiny explicit rounding,and rejects nonfinite/outside/duplicate/conflicting/self-intersecting/zero-area geometry. '+
        'After the concrete format change,the same four preselected TRAIN indices0/172/344/517(photo001/173/345/518)were inspected:4distinct1280x640photos,294polygons(235supplied occupied/59vacant),0rejected files/rounding corrections,0capture dates in EXIF. '+
        'Actual contact-sheet review shows perspective parking outlines,day/night examples and visually related backgrounds. This is qualitative plausibility,not exhaustive annotation or model accuracy. Some scene areas outside supplied polygons also contain vehicles;do not assume the entire remainder is labelled background. '+
        'No publisher valid/test pixels or semantic labels read. Entire source conservatively marked development-exposed in usagev2 because camera/session dates unknown;publisher test folders are not independent final groups. '+
        'All227software tests pass,including14new synthetic parser/selection tests. Original model/claim bytes and source archive unchanged;no model training/scoring/promotion. Failed box stage55->56,corrected polygon inspection56->57;not perphoto/polygon/test. Wakeups39;58sources;next100-run checkpoint100;no active jobs. '+
        'Live collection not due:latest05:34UTC43snapshots/36,258matched persistence targets/MAE4.795797spaces;nextafter06:04:21UTC. Models remain unchanged. Guide:docs/OPEN_SPACE_DATA_GUIDE.md;pointer:reports/open_space_training_inspection_latest.json.')
    for path in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','docs/DATASET_PROVENANCE.md']:
        append(path, note)
    append('docs/UI_TEST_LOG.md', 'Actual generated TRAIN-only contact sheet visually inspected:four source photos with supplied polygon outlines,sourcefile/preview hashes in the recorded inspection. No app-window/manual/student acceptance or model predictions. The main app/offline package was not changed.')
    append('docs/THIRD_PARTY_SOURCES.md', 'SRC-DS-018current usage:four preselected TRAIN images/294supplied polygon labels inspected;allsource conservatively development-exposed,not final-test eligible. Publisher rights/credit retained. Original archive and asset qualification stage unchanged. See usagev2 and docs/OPEN_SPACE_DATA_GUIDE.md.')
    guide = ROOT / 'docs/OPEN_SPACE_DATA_GUIDE.md'
    old = guide.read_text(encoding='utf-8')
    old = old.replace('No image pixels were decoded,no label rows were interpreted,no model\nwas trained or scored,and no original final test was replayed.',
        'At that initial integrity stage,no image pixels were decoded or label rows\ninterpreted. The later training-only inspection below opened four photos. No\nmodel was trained or scored,and no original final test was replayed.')
    old = old.replace('what the label boxes actually\ncover', 'what the polygon annotations actually\ncover')
    guide.write_text(old, encoding='utf-8')
    append('docs/OPEN_SPACE_DATA_GUIDE.md', 'We opened four TRAIN photos chosen before looking at their contents:train001,173,345and518. Each is1280x640. '+
        'Their files contain294parking-space polygons:235labelled occupied and59labelled vacant. They are perspective outlines,not ordinary rectangular boxes. '+
        'Think of tracing the painted shape of each parking bay. Some photos show daylight and one shows night. '+
        'The initial box-reader failure is saved;the new polygon reader and all227software tests pass. These numbers count supplied annotations,not correct AI predictions. '+
        'There are no capture dates in these four images\u2019EXIF. Their related backgrounds mean the whole source is conservatively development material. '+
        'The publisher\u2019s validation/test photos remain unopened,but cannot be called an independent exam for this project. '+
        'We have not checked every annotation or trained a model with this source. Unannotated scene regions are not automatically empty/background labels. '+
        'Current source decision:`data/manifests/open_space_usage_qualification_v2.json`. '+
        'Visual evidence:`'+run['contact_sheet']+'`. Next:broader TRAIN-only quality audit and a clear training plan with fresh independent final data elsewhere.')
    req = ROOT / 'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig', newline='') as stream:
        reader=csv.DictReader(stream); fields=reader.fieldnames; requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['DATA-02','DATA-03','DL-02','QA-02']:
            row['actual_evidence'] += '; reports/open_space_training_inspection_latest.json; usagev2; tests/test_parking_labels.py'
            row['test_result'] += ';4TRAIN images/294valid source polygons,strict box-failure preserved,polygon parser valid;227software tests'
            row['open_problems'] += ';SRC-DS-018whole collection development-exposed,not independent final;broader annotation/near-duplicate/exhaustiveness audit pending,no new training'
    with req.open('w', encoding='utf-8', newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    dump(E / 'handoff.json', dict(recorded_at=now, completed_trials=57, wakeups=39, source_records=58, next_live_milestone=100,
        successful_inspection_run=rid, failed_assumption_run=failed_id, distinct_train_images_opened=4,
        publisher_valid_test_pixels_and_semantic_labels_read=0, all227software_tests_passed=True, source_role='development_exposed',
        independent_final_eligible=False, no_active_jobs=True, source_model_claim_hashes_unchanged=True, no_model_training_or_accuracy=True))
    print(json.dumps(dict(trials=57, wakeups=39, tests=227, inspected_photos=4, polygons=294), indent=2))


if __name__ == '__main__':
    main()
