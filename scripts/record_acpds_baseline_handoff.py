"""Preserve cross-source baseline failure and exact continuation, no retuning."""
import csv,json,shutil,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T230905Z'
RAW=ROOT/'data/raw/acpds_official/17da2c8b33055be8019483260f0efbcbdfda0478'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(path,title,body):
    p=ROOT/path;t=p.read_text(encoding='utf-8');assert title not in t;p.write_text(t.rstrip()+'\n\n'+title+'\n\n'+body+'\n',encoding='utf-8')

def main():
    assert not (E/'checks.json').exists();now=datetime.now(timezone.utc).isoformat();s=read(ROOT/'data/automation_state.json');images=read(ROOT/'models/acpds_image_qualification.json');baseline=read(ROOT/'models/acpds_occupancy_baseline.json');review=read(E/'train_overlay_review.json');overall=baseline['overall']
    assert s['completed_recorded_runs_since_schedule']==len(set(s['completed_run_ids']))==91 and not s['active_training_jobs'] and not s['active_validation_jobs']
    assert images['geometry_gate_passed'] and images['images_decoded']==38 and review['passed'] and not baseline['development_reliability_gate_passed']
    assert overall['samples']==1904 and overall['hard_confusion']==[[961,112],[88,743]] and overall['selective']['false_vacant']==62
    frozen=read(ROOT/'experiments/evidence/HEARTBEAT-20261026T223905Z/checks.json')['frozen_hashes_unchanged']
    for p,h in frozen.items():assert digest(ROOT/p)==h,p
    for result in [images,baseline]:
        protocol=ROOT/'experiments/results'/result['run_id']/'protocol.json';p=read(protocol);assert digest(protocol)==result['protocol_sha256']
        for name,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/name)==h,name
    for name,h in review['images'].items():assert digest(ROOT/name)==h,name
    manifest=read(ROOT/images['development_images']);assert digest(ROOT/images['development_images'])==images['development_images_sha256']
    for f in manifest['frames']:
        assert f['role'] in ('train','valid') and digest(ROOT/f['image'])==f['image_sha256'] and digest(ROOT/f['layout'])==f['layout_sha256']
    tests=(E/'unit_tests.txt').read_text(encoding='utf-8-sig');assert 'Ran 404 tests' in tests and tests.rstrip().endswith('OK')
    live=read(ROOT/'data/processed/singapore_prospective/summary.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json');issuance=read(ROOT/'reports/singapore_issuance_latest.json');snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    assert snapshots==64 and health['status']=='healthy' and health['forecasts_logged']==11837 and health['global_origins']==11 and not health['target_json_decoded'] and not health['performance_evaluated']
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];last=next(x for x in reversed(receipts) if x['source_id']=='SRC-LIVE-001');nexttime=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    s['scheduled_wakeups_completed']+=1;s['last_wakeup_completed_at']=now;s['prospective_live_summary']=live;s['acpds_train_overlay_review']=review;s['singapore_issuance_health'].update(metadata_status='healthy',status='healthy',raw_files_hashed_once=health['raw_files_hashed_once'],semantic_context_verified=False,performance_evaluated=False,forecasts_logged=11837,global_origins=11)
    s['next_actions']=[
        'Collect once AFTER '+nexttime+' via scripts/collect_singapore_study.py;then routine check_singapore_issuance_health.py WITHOUT --record-trial. Latest64actual snapshots;11837genuine learnedforecasts/11origins metadatahealthy. Do not backfill missing observations or issue retrospective forecasts.',
        'Highest-impact vision task: acquire remaining228publisherTRAIN images only using bounded ZIP admission/range/ETag/CRC code.38images already qualified (3TRAIN+all35VALID) in '+images['development_images']+'. Add explicit resumable receipt/hash verification before reusing existing raw members;current script refuses overwrite. RemainingTRAIN acquisition is routine data preparation,not one run per image. Disk D had36.4GB free. WholeTEST/alllots/views/aliases and27defaultclosed image names remainclosed.',
        'Then prespecify ONE bounded source-adaptation hypothesis using ACPDSTRAIN only plus appropriate original PKLotTRAIN retention. Original baseline on35VALID/1904spaces is89.4958%hardaccuracy,62/831occupied confidentlyfalsevacant,17imagesbelow90%;three readiness gates failed. Keep existing .5/.25/.75 thresholds. No open-ended crop/threshold grids or replay of consumed PKLot/UVG final data. Use validation early stopping/checkpoint selection;record all failures. FinalTESTneeds tested durable whole-partition claim/frozen gates before any pixels/semantics,not implemented yet.',
        'Image geometry: all38are4000x3000,raw orientation1;publisher x*(W-1),y*(H-1). ThreeTRAINoverlays visually verified Trueoccupied/Falsevacant and supplied ground-space geometry. Elevated cars can project beyond polygons;this is a hypothesis for source shift,not a proven causal error analysis. Original crop_slot and normalization unchanged. Action-camera source is not continuous CCTV or automatic-region segmentation ground truth.',
        'SG final CLOSED until2026-10-27T10:51UTC(16:21IST). No learned interim target/matching/error/coverage decoding,refit/backdating/backfill. Existing once-only scorer/globalclaim atclosure. Rollingpersistence56499outcomes/MAE5.171330466025947spaces is separate and not camera accuracy. Next100completed-run live checkpoint100;counter91/404softwaretests/63sourceIDs/noactivejobs.',
        'SoftwareREADY selected451-file demo and dated7pagePDF preserved;do not repeat identical package tests for counts. Source-baseline failure is preserved,not production replacement. Physicaloffline/newmachine/visiblemanual/studentmastery/university-document acceptance remainsopen.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory.update(inventoried_at=now,acpds_image_qualification=images,acpds_occupancy_baseline=baseline,acpds_train_overlay_review=review)
    for d in inventory['datasets']:
        if d.get('source_id')=='SRC-DS-021':d.update(status='38development images/geometry qualified;unchanged cross-source baseline failed readiness;TESTclosed',acquired_development_images=38,train_images_acquired=3,valid_images_acquired=35,remaining_train_images=228,image_qualification=images,baseline=baseline,train_overlay_review=review,used_for_model_evaluation=True,used_for_model_training=False,final_images_or_semantics_opened=False)
        if d.get('source_id')=='SRC-LIVE-001':d.update(snapshot_count=snapshots,raw_path=last['local_path'],provider_timestamp=last.get('provider_timestamp'),latest_prospective_summary=live,prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'],learned_issuance_metadata=s['singapore_issuance_health'])
    dump(ROOT/'data/dataset_inventory.json',inventory)
    source=ROOT/'data/source_manifest.csv'
    with source.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    assert len(rows)==len({r['source_id'] for r in rows})==63
    for row in rows:
        if row['source_id']=='SRC-DS-021':row.update(used_by=row['used_by']+';'+images['run_id']+';'+baseline['run_id'],modifications=row['modifications']+';38development JPEG members decoded with original bytes retained;pixel layouts mapped x*(W-1),y*(H-1);unchanged classifier DEVELOPMENT predictions',status='Development geometry passed;original classifier cross-source readiness failed;TESTclosed',open_issues='89.4958%hard accuracy;62confidentfalsevacant among831occupied;no adaptation/final/camera/automatic-region claim;228TRAIN images unacquired')
    with source.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    evidence=ROOT/'docs/source_evidence/acpds_image_adapter_20261026';evidence.mkdir(exist_ok=False)
    for name in ['LICENSE','publisher_visualize.py','publisher_transforms.py','publisher_rcnn.py']:shutil.copyfile(RAW/name,evidence/name)
    dump(evidence/'evidence_hashes.json',{p.name:digest(p) for p in evidence.iterdir() if p.is_file()})
    dump(E/'collection_and_health.json',dict(snapshot_receipt=last,snapshots=snapshots,baseline_scores_added=live['scores_added'],baseline_scores_total=live['scores_total'],baseline_mae_spaces=live['baseline_mae_spaces'],study_issuance=issuance['study_issuance'],health=health,next_collection_after=nexttime))
    title='## 27 October 2026 IST / real ACPDS images qualified; unchanged classifier fails source-shift gates'
    body=('Exact selective ZIP ranges acquired 3 seeded TRAIN and all 35 VALID photographs (51,978,829 network bytes); 38 original JPEGs decode at 4000 by 3000 with orientation 1. All supplied polygons validate using the author\'s normalized x*(W-1),y*(H-1) convention. All three TRAIN overlays were visually checked for coordinate/class convention; True marks occupied ground spaces and False vacant. Cars project beyond ground footprints and occlusions are visible; this is a possible source-shift factor, not a proven cause. No complete TEST member was acquired or decoded. Five new synthetic ZIP admission/range/descriptor/CRC/name/budget tests bring the full software suite to 404 passing tests.\n\n'
          'The prespecified unchanged ResNet18 baseline evaluated all 1,904 labelled VALID spaces in 146.537 seconds: 1,704 correct (89.4958%), confusion [[961,112],[88,743]], image-average accuracy 90.6248%. Seventeen of 35 images fell below 90%. At the fixed .25/.75 uncertainty thresholds, 62 of 831 occupied spaces were confidently called vacant (7.461%), and 115 of 1,904 predictions were uncertain (6.040%). Overall accuracy, every-image accuracy and false-vacancy gates failed; the uncertainty gate passed. This is a crop-classifier development result with supplied geometry, not detector fusion, automatic segmentation, continuous camera or final-test accuracy. No weights, thresholds or production behavior changed. Runtime includes concurrent software-test CPU activity and is not a deployment speed benchmark.\n\n'
          'Two distinct completed trials raised the counter from 89 to 91: real-image/geometry qualification (68.812 seconds) and unchanged cross-source baseline. No per-image/test/frame counts. Source IDs remain 63; wakeups completed 60; next separate 100-run live checkpoint is 100; no active jobs remain. The official 23:09 UTC Singapore snapshot is number 64, adding 1,132 rolling persistence outcomes (56,499 total; MAE 5.171330 spaces) and 1,276 baseline forecasts. Another 1,073 genuine learned forecasts were frozen, giving 11,837 forecasts and 11 origins with healthy receipts. Learned matching, coverage and error remain unscored until 27 October 10:51 UTC. Next collection after '+nexttime+'. All frozen methods, original weights, consumed claims and whole ACPDS TEST reservation remain unchanged.\n\n'
          'Next acquire the remaining 228 TRAIN images with explicit resumable receipt verification, then prespecify one bounded TRAIN-only adaptation with PKLot development retention and validation early stopping. Do not adjust thresholds from this baseline or open TEST without a tested durable whole-partition claim. See docs/ACPDS_BASELINE_GUIDE.md. Official documents, student demonstration, visible manual dialogs, physical disconnection and new-machine acceptance remain open.')
    for path in ['docs/AUTONOMOUS_PROGRESS.md','docs/PROJECT_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md']:append(path,title,body)
    append('docs/SOURCE_REGISTRY.md',title,'SRC-DS-021 now includes 38 CRC-verified development JPEGs and an unchanged classifier DEVELOPMENT evaluation. All original bytes, exact UTC/range/ETag/SHA receipts and MIT notice are retained. Saved coordinate/visualization code evidence:docs/source_evidence/acpds_image_adapter_20261026/. The author\'s results are not local results; final pixels/labels remain closed. No new source IDs were added.')
    append('docs/UI_TEST_LOG.md',title,'Visually reviewed all three prespecified TRAIN geometry overlays; no model or TEST overlay was viewed for this format check. This was source-image inspection, not a visible application, browser, manual-dialog, student, new-machine or physical-offline acceptance test.')
    append('docs/ACPDS_QUALIFICATION.md',title,'The follow-on image/geometry qualification and unchanged classifier baseline are recorded in models/acpds_image_qualification.json and models/acpds_occupancy_baseline.json. Geometry passed; readiness failed. The earlier annotation-only result and its repair history remain unchanged. See docs/ACPDS_BASELINE_GUIDE.md for denominators and next steps.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        if row['requirement_id']=='DATA-02':row['actual_evidence']+=';models/acpds_image_qualification.json';row['test_result']+=';38ACPDSdevelopmentJPEGs/geometry qualified,TESTclosed'
        if row['requirement_id']=='CLS-01':row['actual_evidence']+=';models/acpds_occupancy_baseline.json';row['test_result']+=';unchanged ACPDSVALID1904spaces accuracy89.4958percent,62/831confidentfalsevacant,readinessFAIL';row['open_problems']+=';Cross-source readiness failed;requires bounded TRAIN adaptation and independent final protocol'
        if row['requirement_id']=='QA-02':row['test_result']+=';404softwaretests pass including5selectiveZIPfixtures'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(rows)
    dump(E/'checks.json',dict(checked_at=now,counter_before=89,counter_after=91,completed_trials=[images['run_id'],baseline['run_id']],wakeups_completed=60,unique_sources=63,software_tests=404,frozen_hashes_unchanged=frozen,source_geometry_gate=True,source_reliability_gate=False,hard_accuracy=overall['hard']['accuracy_on_covered'],confident_false_vacant=62,actual_occupied=831,whole_test_remains_closed=True,active_jobs=[],next100_run_checkpoint=100,next_collection_after=nexttime,full_project_complete=False))
    print(json.dumps(dict(counter=91,sources=63,tests=404,hard_accuracy=overall['hard']['accuracy_on_covered'],readiness_gate=False,next_collection=nexttime,no_active_jobs=True)))

if __name__=='__main__':main()
