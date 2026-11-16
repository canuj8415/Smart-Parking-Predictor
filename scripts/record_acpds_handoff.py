"""Save the qualification result and honest collection gap without target reads."""
import csv,json,shutil,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T223905Z'
RAW=ROOT/'data/raw/acpds_official/17da2c8b33055be8019483260f0efbcbdfda0478'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(path,title,body):
    p=ROOT/path;t=p.read_text(encoding='utf-8');assert title not in t;p.write_text(t.rstrip()+'\n\n'+title+'\n\n'+body+'\n',encoding='utf-8')

def main():
    assert not (E/'checks.json').exists();now=datetime.now(timezone.utc).isoformat();s=read(ROOT/'data/automation_state.json');r=read(ROOT/'models/acpds_development_qualification.json');out=ROOT/'experiments/results'/r['run_id']
    assert s['completed_recorded_runs_since_schedule']==len(set(s['completed_run_ids']))==89 and not s['active_training_jobs'] and not s['active_validation_jobs']
    assert r['metadata_gate_passed'] and r['development']['train']['spaces']==7842 and r['development']['valid']['spaces']==1904 and not r['final_json_deserialized'] and r['default_closed_image_names']==27
    assert digest(ROOT/'data/manifests/acpds_source_roles_v1.json')==r['role_manifest_sha256']
    amendment=read(out/'protocol_amendment_02.json');assert digest(out/'protocol_amendment.json')==amendment['previous_amendment_sha256']
    for p,h in amendment['implementation_hashes'].items():assert digest(ROOT/p)==h,p
    dump(out/'amended_implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in amendment['implementation_hashes']})
    frozen=read(ROOT/'experiments/evidence/HEARTBEAT-20261026T190901Z/checks.json')['frozen_hashes_unchanged']
    frozen.update(read(ROOT/'models/singapore_trend_development.json')['protected_hashes']);frozen.update(read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')['implementation_hashes'])
    for p,h in frozen.items():assert digest(ROOT/p)==h,p
    tests=(E/'unit_tests.txt').read_text(encoding='utf-8-sig');assert 'Ran 399 tests' in tests and tests.rstrip().endswith('OK')
    live=read(ROOT/'data/processed/singapore_prospective/summary.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json');issuance=read(ROOT/'reports/singapore_issuance_latest.json')
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];last=next(x for x in reversed(receipts) if x['source_id']=='SRC-LIVE-001')
    assert health['status']=='healthy' and not health['target_json_decoded'] and not health['performance_evaluated']
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')));assert snapshots==63
    nexttime=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    s['scheduled_wakeups_completed']+=1;s['last_wakeup_completed_at']=now;s['prospective_live_summary']=live;s['singapore_issuance_health'].update(metadata_status='healthy',status='healthy',raw_files_hashed_once=health['raw_files_hashed_once'],semantic_context_verified=False,performance_evaluated=False)
    s['next_actions']=[
        'Collect once AFTER '+nexttime+' via scripts/collect_singapore_study.py,then check_singapore_issuance_health.py WITHOUT --record-trial.30minute plan/minimum1min. Latest actual22:39UTC;19:12->22:39gap is missing,not backfilled. No new learned issuance:1193 no-previous/5stale exclusions.10764learnedforecasts/10origins remain healthy/unscored.',
        'Fresh vision source SRC-DS-021 ACPDS now rights-qualified under explicit author MIT dataset grant. FIRST implement bounded exact ZIP member acquisition with ETag/range/CRC and role allowlist,then acquire TRAIN/VALID images only. Roles data/manifests/acpds_source_roles_v1.json sealed BEFORE labels;27 archive-complement names default CLOSED and whole publisherTEST/alllots/views/aliases stayreserved. No final loader/claim yet;do not deserialize mixed annotation JSON wholesale.',
        'Use experiments/results/'+r['run_id']+'/development_annotations.json (231TRAIN/35VALID,7842/1904 explicit spaces) and existing CRC-verified mixed raw only through acpds_admission.development_only. Check acquired-image dimensions,coordinate order,normalized ROI geometry and class convention against author loader before crops/inference. Train/valid disjoint-lot statement is author evidence,not verified geolocation;capture dates/pretraining overlap unknown. Source is action-camera uniqueviews,not real CCTV sequence or automatic parking-region truth.',
        'After image/label geometry qualification:prespecify an unchanged-checkpoint occupancy DEVELOPMENT baseline on publisherVALID before proposing one bounded adaptation with TRAIN-only fitting. ReserveTESTonce-only durable claim and frozen gates BEFORE finalpixels/semantics. No threshold/crop grids on consumed PKLot/UVG data. NDISPark/CNR content rights remainunqualified;HighwayDrive remainsclosed.',
        'SG final CLOSED until2026-10-27T10:51UTC(16:21IST). No interim learned target/matching/error/coverage read,refit/backdating/backfill. Atclosure existing once-only scorer/globalclaim. Rollingpersistence55367outcomes/MAE4.861090541297163spaces is separate;not camera truth. Next100completed-run live checkpoint100;counter89/399softwaretests/63sourceIDs;noactivejobs.',
        'Selected451-file offline demo remains softwareREADY;do not repeat identical checks for counts. Dated7pagePDF preserved. Physicaloffline/newmachine/visiblemanual/studentmastery/university-document acceptance remainopen.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');assert not any(d.get('source_id')=='SRC-DS-021' for d in inventory['datasets'])
    inventory['datasets'].append(dict(source_id='SRC-DS-021',status='Development annotation integrity qualified;images not acquired/decoded;TEST closed',publisher_revision='17da2c8b33055be8019483260f0efbcbdfda0478',archive_bytes=380796292,whole_archive_acquired=False,development=r['development'],default_closed_image_names=27,role_manifest='data/manifests/acpds_source_roles_v1.json',role_manifest_sha256=r['role_manifest_sha256'],evidence=r,rights='Author explicit MIT grant includes dataset;retain notice',limitations=r['limitations']))
    for d in inventory['datasets']:
        if d.get('source_id')=='SRC-LIVE-001':d.update(snapshot_count=snapshots,raw_path=last['local_path'],provider_timestamp=last.get('provider_timestamp'),latest_prospective_summary=live,prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'],learned_issuance_metadata=s['singapore_issuance_health'])
    inventory.update(inventoried_at=now,acpds_development_qualification=r);dump(ROOT/'data/dataset_inventory.json',inventory)
    source=ROOT/'data/source_manifest.csv'
    with source.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    assert len(rows)==len({x['source_id'] for x in rows})==63
    for row in rows:
        if row['source_id']=='SRC-DS-021':row.update(original_size='380796292remote ZIP bytes;295entries/293image names;wholearchive not acquired',sha256='Per-file SHA256/ETag/exact-range receipts;annotation CRCverified;no wholearchive checksum',used_by=r['run_id'],modifications='Originals unchanged;TRAIN/VALID-only JSON reader;explicit boolean labels preserved;TEST branch opaque',status='Development annotation qualification passed;no pixels/model score;whole TEST reserved',open_issues=r['limitations'])
    with source.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    evidence=ROOT/'docs/source_evidence/acpds_20261026';evidence.mkdir(exist_ok=False)
    for name in ['README.md','LICENSE','publisher_loader.py','paper_abstract.html','head.json','directory_inventory.json']:shutil.copyfile(RAW/name,evidence/name)
    dump(evidence/'evidence_hashes.json',{p.name:digest(p) for p in evidence.iterdir() if p.is_file()})
    dump(E/'collection_and_health.json',dict(collection_checked_at=live['checked_at'],snapshot_receipt=last,snapshots=snapshots,baseline_scores_added=live['scores_added'],baseline_mae_spaces=live['baseline_mae_spaces'],study_issuance=issuance['study_issuance'],health=health,next_collection_after=nexttime,missing_interval='2026-10-26T19:12:33.568681Z -> 2026-10-26T22:39:27.851456Z;no invented intermediate observations'))
    title='## 27 October 2026 IST / fresh licensed ACPDS development admitted; TEST remains closed'
    body=('Author source SRC-DS-021 is pinned to repository revision17da2c8b33055be8019483260f0efbcbdfda0478. The paper explicitly grants MIT for dataset/code/models;notice retained. Whole author TEST/all lots/views/aliases was reserved before annotation decoding. Bounded ETag/HTTP206 acquisition verifies annotation ZIP descriptor,CRC and expanded size;380796292-byte wholearchive not downloaded/checksummed. TRAIN231images/7842spaces(3940occupied,3902vacant),VALID35/1904(831occupied,1073vacant),normalized coordinates0..1;no cross-partition duplicate filenames. Archive293image names leaves27 default-closed,not a decodedTESTlist. No pixels,models or TESTsemantics opened. Unique-lot separation is author evidence,not independent geolocation/date audit;no CCTV/automatic-region/generalization claim. Seven new synthetic admission tests;full399softwaretests pass. Two internal adapter-format repairs preserved:header-only ZIPflag8 rejection and integer-only rejection of explicit publisher booleans;original protocol plus chained pre-resumption amendments retained. They are one completed qualification trial88->89,not extra counts. Successful cached revalidation callback1.601seconds excludes earlier acquisition/discovery/repair work. SourceIDs63,wakeup59,next100-runcheckpoint100,noactivejobs. Latest actual Singapore22:39UTCsnapshot63;19:12->22:39gap remains missing.1199newpersistence forecasts/0newmatches;55367pastoutcomes/MAE4.861091spaces unchanged. Learned issuance0(newprevious-observation/staleness exclusions),10764forecasts/10origins metadatahealthy and unscored until27Oct10:51UTC. Nextcollectionafter'+nexttime+'. Next implement bounded TRAIN/VALID image allowlist acquisition and geometry/class-convention audit before occupancy baseline;keep wholeTESTclosed. Originalweights/frozenmethods/claims/reports untouched;official/manual/student/physicaloffline acceptance remainsopen.')
    for path in ['docs/AUTONOMOUS_PROGRESS.md','docs/PROJECT_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md']:append(path,title,body)
    append('docs/SOURCE_REGISTRY.md',title,'SRC-DS-021 Martin Marek,Action-Camera Parking Dataset;official https://github.com/martin-marek/parking-space-occupancy ;author https://arxiv.org/abs/2107.12207 explicitly includes dataset in MIT grant. Saved primary documents/loader/licence/metadata with hashes:docs/source_evidence/acpds_20261026/. Per-range receipts:data/resource_receipts.jsonl. Source roles sealed before semantics. See docs/ACPDS_QUALIFICATION.md. 63unique source IDs. No author-reported 98% score claimed as local accuracy.')
    dump(E/'checks.json',dict(checked_at=now,counter_before=88,counter_after=89,completed_trial=r['run_id'],wakeups_completed=59,unique_sources=63,software_tests=399,frozen_hashes_unchanged=frozen,role_manifest_sha256=r['role_manifest_sha256'],final_semantics_opened=False,image_pixels_opened=False,model_calls=0,active_jobs=[],next100_run_checkpoint=100,next_collection_after=nexttime,full_project_complete=False))
    print(json.dumps(dict(counter=89,sources=63,tests=399,next_collection=nexttime,no_active_jobs=True)))

if __name__=='__main__':main()
