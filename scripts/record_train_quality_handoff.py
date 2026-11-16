"""Save all-TRAIN audit provenance and the next bounded development study."""
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed

E=ROOT/'experiments/evidence/HEARTBEAT-20261026T060846Z'
TITLE='## 26 October 2026 / complete TRAIN audit with quarantine and unknown-aware support'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def dump(path,value):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def append(path,body):
    path=ROOT/path;old=path.read_text(encoding='utf-8');assert TITLE not in old
    path.write_text(old.rstrip()+'\n\n'+TITLE+'\n\n'+body+'\n',encoding='utf-8')


def main():
    assert not (E/'handoff.json').exists()
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');rid=state['last_completed_run']
    run=read('experiments/results/'+rid+'/run.json');summary=run['summary'];tests=read(E/'software_tests.json')
    assert run['audit_completed'] and summary['train_images_audited']==518 and summary['accepted_image_label_pairs']==517
    assert summary['quarantined_image_label_pairs']==1 and summary['accepted_polygons']==39068
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==58 and state['scheduled_wakeups_completed']==39
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert tests['returncode']==0 and 'Ran 233 tests' in tests['stderr']
    assert all(digest(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes'],**run['derived_files'],**run['preview_files']}.items())
    assert digest(ROOT/run['source_archive'])==run['source_archive_sha256']
    frames=read(next(p for p in run['derived_files'] if p.endswith('frames.json')))
    accepted=[x for x in frames if x['status']=='accepted_syntax']
    union=sum(x['coverage']['supplied_union_pixels'] for x in accepted)
    review=dict(recorded_at=now,run_id=rid,actual_preview_files=['train_001_support.png','train_518_support.png'],
        method='Assistant inspected actual side-by-side TRAIN photo/support PNGs;no model inference or exhaustive manual relabelling',
        observations=['Outside supplied space polygons remains gray unknown','Day/night supplied occupied/vacant classes retain their own colors',
            'Conflicting source-class raster support remains unknown,not a chosen class'],
        diagnostic_resolution=[320,160],supplied_union_pixels=union,conflict_pixels=summary['diagnostic_conflict_pixels'],
        conflict_fraction_of_union=summary['diagnostic_conflict_pixels']/union,
        maximum_per_frame_conflict_fraction=max(x['coverage']['conflict_fraction_of_supplied_union'] for x in accepted),
        conflict_interpretation='Includes rasterized shared boundaries;not measured annotation error or model accuracy',
        mixed_format_quarantine=dict(image='train/images/train_328.jpg',source_line=69,tokens=5,
            reason='One five-token box row in a polygon file;whole69-row file quarantined under frozen strict policy,no partial salvage/repair'))
    dump(E/'visual_and_quarantine_review.json',review)
    prior=read('data/manifests/open_space_usage_qualification_v2.json')
    usage=dict(prior,version=3,run_id=rid,recorded_at=now,parent_usage='data/manifests/open_space_usage_qualification_v2.json',
        parent_usage_sha256=digest(ROOT/'data/manifests/open_space_usage_qualification_v2.json'),
        usage_status='All518publisher TRAIN photos audited;517syntactically accepted/one whole mixed-format file quarantined',
        image_pixels_decoded=518,distinct_train_label_files_interpreted=518,labels_semantically_interpreted=39137,
        accepted_source_polygon_rows=39068,quarantined_source_label_rows=69,
        source_splits='TRAIN only decoded/interpreted;144valid/69test folders remain semantically unopened and not independent final groups',
        source_wide_role='development_exposed',independent_final_eligible=False,independent_benchmark_admitted=False,
        model_training_admitted=False,occupancy_crop_preparation_admitted=True,
        region_background_negative_labels_created=False,unlabelled_or_conflicting_class_support='255unknown',
        all_train_annotation_files_valid=False,quality_audit=summary,
        pending=['Prepare bounded masked occupancy crops from517accepted pairs and freeze a development-only source-balanced head protocol',
            'Keep source class conflicts/unlabelled areas unknown;no invented parking/background mask negatives',
            'Validate only on existing PKLot development,do not replay finals or promote without fresh independent final evidence'])
    dump('data/manifests/open_space_usage_qualification_v3.json',usage)
    pointer=dict(run_id=rid,source_id='SRC-DS-018',summary=summary,derived_files=run['derived_files'],original_copies=run['original_copies'],
        usage_qualification='data/manifests/open_space_usage_qualification_v3.json',guide='docs/OPEN_SPACE_DATA_GUIDE.md',software_tests_passed=233)
    dump('reports/open_space_train_audit_latest.json',pointer)
    latest=read('reports/open_space_data_latest.json');latest.update(current_train_audit=pointer,usage_qualification=pointer['usage_qualification'],
        image_pixels_decoded=518,label_rows_semantically_interpreted=39137,current_distinct_image_pixels_decoded=518,current_distinct_train_label_files_interpreted=518)
    dump('reports/open_space_data_latest.json',latest)
    live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
    last=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert digest(ROOT/last['local_path'])==last['sha256']
    payload=read(last['local_path']);rows=parse_feed(payload)
    raw_lots=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in rows) and len(rows)==len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    next_poll=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json',dict(receipt=last,summary=live,snapshot_count=snapshots,accepted_rows=len(rows),raw_lot_records=raw_lots,
        invalid_capacity_excluded=raw_lots-len(rows),bounds_valid=True,duplicate_rows=0,next_sensible_collection_after=next_poll,
        separate100_run_checkpoint_due=False,scope='Causal frozen persistence scoring only;not neural forecast or camera accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-018':item.update(status=usage['usage_status'],image_pixels_decoded=518,semantic_label_rows_read=39137,
            semantic_train_label_files_interpreted=518,inspected_polygons=39068,supplied_occupied_polygons=28604,supplied_vacant_polygons=10464,
            capture_dates_present_in_audited_images=0,usage_qualification=pointer['usage_qualification'],train_quality_audit=pointer)
        if item['source_id']=='SRC-LIVE-001':item.update(raw_path=last['local_path'],provider_timestamp=last['provider_timestamp'],snapshot_count=snapshots,
            observations=len(rows),car_parks=len({r['car_park_id'] for r in rows}),raw_lot_records=raw_lots,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    dump('data/dataset_inventory.json',inventory)
    catalog=ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==58
    for item in sources:
        if item['source_id']=='SRC-DS-018':item.update(used_by='All518TRAIN source audit;517accepted pairs/39068polygon rows;one whole69row mixed-format file quarantined;no models',
            modifications='Original archive intact;1036verified TRAIN member copies;derived polygonCSV/frameJSON/similarity candidateCSV;unknown-aware diagnostic support PNGs',
            status='TRAIN quality audit completed with quarantine;source-wide development-exposed,not final eligible',
            open_issues='907low-dHash-distance pairs are similarity candidates,not confirmed duplicates;no EXIF capture dates;class-support boundary conflicts unknown;annotation/exhaustiveness unverified;no model training yet')
    with catalog.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    state.update(last_updated_at=now,scheduled_wakeups_completed=40,open_space_train_audit=pointer,prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'All518publisher TRAIN photos audited:517syntactically accepted pairs/39068source polygons(28604occupied/10464vacant). Mixed-format train328line69has5tokens;whole69row file quarantined,originals retained. No valid/test semantic reads. See reports/open_space_train_audit_latest.json and usagev3. Do not repeat identical audits.',
        'Next concrete implementation:prepare bounded occupancy crop/feature manifest from517accepted photos,up to32label-blind evenly spaced source polygon rows per frame. Use original-source polygon geometry and existing gray127masked crop convention;exclude ambiguous opposing-class support from visible input;reject crops with <95percent unambiguous polygon support or <12pixel bbox width/height. These are future frozen crop-quality gates,not measured acceptance yet. Explicitly remap source class0occupied->model label1 and source class1vacant->model label0,retaining original source class. Keep source rows/hashes and excluded records.',
        'Then implement ONE bounded DEVELOPMENT-ONLY source-balanced frozen-ResNet18 head trial:existing PKLot train set plus new accepted source TRAIN crops;start from preserved occupancy-expansion candidate;retain current app model. Source weights PKLot0.75/new0.25,class-balanced within source;seed128,max6epochs,patience2,checkpoint/cache/cancel,at most900seconds per invocation. Freeze config/source/data hashes before training. Validation only original2028PKLot DEVELOPMENT labels,not new-source publisher valid/test or consumed finals. Compare stronger archived development head(12errors/4false-vacant),not only weak original. No source018/night/unseen-lot accuracy claim;new independent final required before promotion. Old training CLI requires now-consumed final closed,so build a separate explicitly development-only route with NO final callback,not a replay/claim waiver.',
        'Whole SRC-DS-018 remains one development-exposed source group:0EXIF capture dates/all518images1280x640;907dHash<=8/256similarity candidates,0exact RGBduplicate groups. Do not call candidates confirmed duplicates or create independent splits from them. Outside/conflicting support is255unknown;no parking/background negative labels exist. Region segmentation training needs separately qualified ROI/background labels.',
        'Counter58;wakeups40;source catalog58;next separate100-run live checkpoint100;no active jobs.233software tests PASS,including6new synthetic coverage/hash tests. Original checkpoints/claims and failed rainy-final retention13/14<95percent remain unchanged;no app promotion or final replay. CNR image rights unqualified and images unopened. Existing424fileoffline package remains dated.',
        'Singapore'+live['checked_at']+':44snapshots,1111new causal persistence matches,37369total,MAE4.859429spaces;1183new forecasts frozen;missing targets unscored. Next sensible collection AFTER'+next_poll+'. No neural/camera live accuracy. Python/Jupyter preserved;physical/manual/browser/student/official university acceptance still separate.'
    ];dump('data/automation_state.json',state)
    note=('All518SRC-DS-018TRAIN photos and1036original member copies verified;72,701,375TRAIN bytes retained. '+
        '517pairs accepted syntactically,39,068source polygons(28,604occupied/10,464vacant);train328contains one5-token box row atline69inside a polygon file,so its ENTIRE69rows are quarantined without repair/partial salvage. '+
        'All518images1280x640,0EXIF capture dates.0exactRGBduplicate groups,907pairs at frozen dHash<=8/256are similarity candidates,not confirmed duplicates or independent split groups. '+
        'New source-support helper assigns known occupied1/vacant0only inside nonconflicting supplied polygons;unannotated or contradictory support255unknown. '+
        'At diagnostic320x160,388accepted frames have some opposing-class raster overlap,74,632pixels out of10,771,213supplied-union pixels;maximum frame fraction1.731percent. Shared raster boundaries can contribute;this is not measured annotation error. '+
        'Actual day/night support PNGs visually inspected. No region/background negative masks inferred. Source-wide group remains development-exposed;zero valid/test pixel/semantic target reads,though compressed archive bytes/headers are scanned for hashing/location. '+
        'All233software tests pass(including6new synthetic coverage/hash tests). Original models/claims/archive untouched;no training/scoring/promotion. One audit57->58,wakeups40;source58,next100-run checkpoint100,no active jobs. '+
        'Latest Singapore44snapshots add1,111causal baseline matches:37,369total,persistenceMAE4.859429spaces;1,183new forecasts frozen;missing targets unscored,not camera/neural accuracy. '+
        'Next:bounded masked occupancy crop preparation and one explicitly DEVELOPMENT-ONLY source-balanced head trial with existing PKLot development labels;no final replay or app replacement. '+
        'Derived CSVs/data locations:reports/open_space_train_audit_latest.json;guide:docs/OPEN_SPACE_DATA_GUIDE.md.')
    for path in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','docs/DATASET_PROVENANCE.md','docs/THIRD_PARTY_SOURCES.md']:append(path,note)
    append('docs/UI_TEST_LOG.md', 'Generated TRAIN-only train001/day and train518/night source-support PNGs visually inspected. These are supplied-label diagnostics with unknown areas gray,not model predictions or app/manual acceptance. Existing app/offline package unchanged.')
    polygon_csv=next(p for p in run['derived_files'] if p.endswith('polygons.csv'))
    append('docs/OPEN_SPACE_DATA_GUIDE.md', 'We checked all518photos in the publisher\u2019s TRAIN folder.517photo/label pairs passed the strict format checks,containing39,068supplied parking-space outlines. '+
        'One file mixes a rectangular-box row into polygon labels;the whole file and its69rows are set aside unchanged. This is like setting aside a worksheet with a different answer format rather than guessing how to mark it. '+
        'All photos are1280x640 and none supplies an EXIF capture date. There are907visually similar hash-pair candidates;these are leads for checking,not907proven duplicates. No exact decoded-photo duplicates were found within TRAIN. '+
        'Gray in the new coverage pictures means unknown:outside labelled spaces or where opposite labels overlap. We do not tell the model that an unlabelled street or bay is empty. These pictures are label diagnostics,not AI answers. '+
        'The actual accepted polygon CSV is `'+polygon_csv+'`;it retains source image,file hashes,row text,class and original polygon coordinates. The frame/quarantine/similarity files beside it preserve rejected files and screening results. '+
        'Exact copied TRAIN originals are under `'+run['original_copies']+'`. Publisher validation/test photos stay unopened semantically;allsource remains development material. '+
        'Next:prepare small masked occupancy crops and test a bounded training idea against existing development data. This audit adds no model accuracy. Current decision:`data/manifests/open_space_usage_qualification_v3.json`.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['DATA-02','DATA-03','QA-02']:
            row['actual_evidence']+='; reports/open_space_train_audit_latest.json; usagev3; tests/test_annotation_quality.py'
            row['test_result']+=';518TRAIN images audited,517accepted/39068polygons,1mixed file quarantined,unknown-aware support,907similarity candidates;233software tests'
            row['open_problems']+=';No source-independent final split or new model accuracy;unannotated backgrounds unknown,near duplicates unverified'
    with req.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    dump(E/'handoff.json',dict(recorded_at=now,run_id=rid,completed_trials=58,wakeups=40,source_records=58,next_live_milestone=100,
        audit_summary=summary,all233software_tests_passed=True,no_active_jobs=True,protected_sources_models_claims_unchanged=True,
        no_new_model_accuracy=True,next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(trials=58,wakeups=40,accepted_pairs=517,polygons=39068,tests=233,snapshots=snapshots),indent=2))


if __name__=='__main__':main()
