"""Finish one real development study; skipped heartbeat triggers are not trials."""
import csv,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    e=ROOT/'experiments/evidence/HEARTBEAT-20261027T013907Z';run=read(ROOT/'models/acpds_frozen_fusion.json');out=ROOT/'experiments/results'/run['run_id'];protocol=read(out/'protocol.json');assert run['protocol_sha256']==digest(out/'protocol.json')
    for f,h in {**protocol['input_hashes'],**protocol['source_hashes'],**protocol['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    s=read(ROOT/'data/automation_state.json');assert s['completed_recorded_runs_since_schedule']==98==len(set(s['completed_run_ids'])) and s['scheduled_wakeups_completed']==64;assert not s['active_training_jobs'] and not s['active_validation_jobs']
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as f:ids=[r['experiment_id'] for r in csv.DictReader(f)]
    assert all(ids.count(r)==1 for r in s['completed_run_ids'])
    assert all(not value['development_gate_passed'] for value in run['methods'].values())
    assert run['methods']['original']['metrics']['classifier']['false_vacant']==62 and run['methods']['last_block']['metrics']['classifier']['false_vacant']==14
    tests=e/'unit_tests.txt';assert 'Ran 437 tests' in tests.read_text() and '\nOK' in tests.read_text()
    report=read(ROOT/'reports/acpds_fusion_explanation_latest.json');target=ROOT/report['path'];manifest=read(target/'manifest.json');assert digest(target/'manifest.json')==report['manifest_sha256']
    for example in manifest['examples']:
        assert example['available'] and digest(target/example['preview'])==example['preview_sha256']
    review=dict(checked_at=datetime.now(timezone.utc).isoformat(),report_manifest_sha256=digest(target/'manifest.json'),images_reviewed=[r['preview'] for r in manifest['examples']],
        readable_headers=True,geometry_and_detection_drawn=True,source_images_unchanged=True,new_model_calls=0,
        observations=['First original unsafe vacancy warned:very oblique supplied polygon crosses vehicle appearances;detector supports warning.',
                      'First original remaining unsafe vacancy:tree occlusion/projected appearance visible;cause not proven and publisher label retained.',
                      'First research correct vacancy sent to review:published vacant ground polygon overlaps a projected neighboring vehicle box;no relabeling or causal certainty.'],
        scope='Visual rendering review of3fixed-order development examples,not independent labels/representative accuracy/final/GUI acceptance')
    dump(target/'visual_review.json',review)
    live=read(ROOT/'reports/singapore_issuance_latest.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json');assert live['collection']=='acquired' and health['status']=='healthy' and not health['performance_evaluated'] and not health['target_json_decoded'];assert health['forecasts_logged']==16205 and health['global_origins']==15
    now=datetime.now(timezone.utc).isoformat();next_collection=(datetime.fromisoformat(live['baseline']['checked_at'])+timedelta(minutes=30)).isoformat();snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    assert snapshots==69
    previous='2026-10-27T01:13:37.918904+00:00';gap_minutes=(datetime.fromisoformat(live['baseline']['checked_at'])-datetime.fromisoformat(previous)).total_seconds()/60
    s.update(scheduled_wakeups_completed=65,last_updated_at=now,last_wakeup_completed_at=now,prospective_live_summary=live['baseline'],last_live_baseline_score=live['baseline'],singapore_issuance_health=health)
    s['last_collection_gap']=dict(previous_collection=previous,resumed_collection=live['baseline']['checked_at'],gap_minutes=gap_minutes,missing_observations_backfilled=False,score_targets_invented=False,learned_forecasts_added=0,reason='No eligible previous observation after execution gap;stale context excluded by existing frozen method')
    s['trigger_handling_note']='Prepared fixed fusion protocol01:42UTC;437tests completed7sec. No detector ran during later queued heartbeat gap. Actual35photo study ran03:39UTC in183.217sec. One completed trial97->98;intermediate heartbeat triggers are not fabricated completed work. Source collection resumes03:39:46UTC after146mingap.'
    s['acpds_fusion_explanation']=dict(path=report['path'],manifest_sha256=report['manifest_sha256'],visual_review_sha256=digest(target/'visual_review.json'),new_model_calls=0,student_mastery_assessed=False)
    s['next_actions']=[
      'Collect once AFTER '+next_collection+' with existing collect_singapore_study.py;routine metadata health WITHOUT --record-trial.69snapshots/16205learnedforecasts/15origins.03:39collection had0newtargetmatches and0eligible learnedissuances after146mingap;1299baselineforecasts frozen;do not backfill gaps or decode pending learnedtargets.',
      'Read models/acpds_frozen_fusion.json and reports/'+target.name+'/EXPLANATION.md. Original fixed fusion62->33unsafevacants but38correctvacancies senttoreview;research last-block14->3unsafevacants but57correctvacancies lost,967/1024=94.4336%retention below95%;8images below90%for each method. Both readiness gatesFAIL;no installation/threshold tuning.3newdiagnosticPNGs visuallyreviewed,publisherlabels unchanged.',
      'Next distinct geometry hypothesis should be developed using admitted TRAIN photos only,not more tuning of35reusedVALID. Consider prespecified ground-contact/box-bottom support versus full-box overlap,with source geometry/occlusion limits and no causal claims. Freeze one recipe/gates before TRAINanalysis;keep current detector/probability outputs immutable. No threshold/crop/optimizer grid. Any subsequent final assessment needs a separately frozen qualified fresh cohort and once-only claim;allACPDS27TEST/lots/views/aliases andHighwayDrive remainclosed.',
      'Alternative high-impact independent work: qualify exhaustive parking-region labels and source rights,or refresh the selected451-fileofflinepackage to include the bounded assignment at the next application integration milestone. Use existing safe pre-originSGsnapshot selector and approved local-loopback Jupyter context;preserve earlierREADY/failure evidence. Do not copy/decode prospective targets.',
      '437softwaretests pass. Counter98/nextseparate100-runlivecheckpoint100;noactivejobs. One trial,not per35photos/2methods/7batches/3previews. SourceIDs63. Working occupancyweights72272f0f anddetector unchanged;researchlast-block7ea60239 andhead d930f14a retained,notpromoted. Memorypatch c004db7 remainsworking;MaskRCNNdense-outputmemory separateunresolved.',
      'SG final remainsCLOSED until2026-10-27T10:51UTC(16:21IST):no interim learnedtarget/matching/error/coverage,refit/backdating. Use once-only scorer/globalclaim only afterclosure.61105rollingpersistenceoutcomes/MAE5.802520252025203spaces remainseparate aggregateavailability,notcamera truth. Missingofficialdocs/manualphysicaloffline/newmachine/student acceptance remainopen.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['acpds_frozen_fusion']=dict(run_id=run['run_id'],card='models/acpds_frozen_fusion.json',card_sha256=digest(ROOT/'models/acpds_frozen_fusion.json'),images=35,spaces=1904,role='Previously exposed publisherVALID development;not final',model_calls=run['model_calls'],gate_passed=False,source_id='SRC-DS-021',source_assets_added=0,production_promoted=False);inventory['occupancy_patch_validation']=s['occupancy_patch_validation'];inventory['assignment_api_validation']=s['assignment_api_validation'];inventory['singapore_issuance_health']=health;dump(ROOT/'data/dataset_inventory.json',inventory)
    summary=f'''
## 27 October 2026 IST / fixed-method detector fusion exposes review costs

One sealed development diagnostic processed all35already-exposed ACPDS VALID
photos/1904spaces (831occupied/1073vacant). Original and last-block classifier
scores were replayed from hash-bound earlier predictions,with exact supplied
slot geometry equality verified. No classifier forward/fitting. Actual unchanged
FasterRCNN640/confidence0.5 ran35times;application0.12overlap/0.25/0.75states stayed
fixed. Both methods reported independently,no winner/threshold chosen.

Original fusion reduced confident unsafe vacancy62->33 by sending29occupied
spaces to review,butalso38previouslycorrect vacantanswers to review. Uncertainty
182/1904=9.5588%;correctvacancyretention901/939=95.9531%,yet8imagesbelow90%.
The remaining33/831=3.9711%unsafevacancies exceed1%;readinessFAIL.
Research last-block fusion reduced unsafe vacancy14->3 (0.3610%of831) and
uncertainty155/1904=8.1408%,passing those absolute limits. However,57correct
vacancies were also sent to review:967/1024=94.4336%retention below95%,with
8imagesbelow90%;readinessFAIL. Warningsareuncertain,notcorrectoccupiedanswers.
Bothfailed results are preserved;no model/threshold/production promotion.

Seven sequential5photochildren checkpointed every frame;total183.217seconds,
maximum sampled workerRSS1297002496bytes below1.75GiBcap.35detector/0classifier
calls constitute one trial97->98,not perframe/method/batch. Five added meaningful
denominator/state/identity fixtures bring fullsuite437/OK7.000sec. Initial test
launcher omitted src importpath;error preserved,corrected launch passes without
changing sealed study code. Protocol prepared01:42UTC;actual inference started
03:39UTC after executiongap. Intermediate heartbeat triggers are not experiments.

Generated source-bound student explanation and3deterministic first-qualifying
diagnostic PNGs;all3visuallyinspected. Remainingunsafe example shows occlusion;
vacant-label example shows projected neighboring box overlapping supplied ground
polygon. These are observations,not independently verified labels or causalproof.
Labels retained. No final/video/exhaustivedetector/learnedregion/GUI/newmachine/
physicaloffline/studentmastery claim. See reports/{target.name}/EXPLANATION.md,
models/acpds_frozen_fusion.json and visual_review.json. Originalweights/frozenSG
methods/TESTreservations unchanged. Next geometry hypothesis should use admitted
TRAIN only;do not retune overlap/crop/model gates on35reusedVALID. Existing451file
offlineREADYcopy still predates memorypatch c004db7.

Source-compliant officialSGsnapshot69 at03:39:46UTC follows146.148minute gap;
no backfill.0newmatchedpersistenceoutcomes,61105total/MAE5.802520252025203spaces;
1299newbaselineforecasts.0newlearnedforecasts because prior context unavailable
or stale;16205forecasts/15origins/15receiptedbatches metadatahealthy. Learnedtarget
decoding/matching/coverage/error staysclosed until27Oct10:51UTC. Nextcollection
after{next_collection}. Wakeups65/sourceIDs63/nextseparate100runlivecheckpoint100,
noactivejobs. Projectofficial/manual/physical/newmachine/student acceptance open.
'''
    for name in ['PROJECT_PROGRESS.md','AUTONOMOUS_PROGRESS.md','TEST_RESULTS.md']:
        with (ROOT/'docs'/name).open('a',encoding='utf-8') as f:f.write(summary)
    with (ROOT/'docs/IMPLEMENTATION_STATUS.md').open('a',encoding='utf-8') as f:f.write('\n## Latest fixed fusion development — 27 October 2026\n\n35photos/1904spaces fixed Faster640 detector study completed. Original unsafevacants62->33 with38correctvacancies senttoreview;research14->3 with57correctvacancies lost and94.4336%retention<95%. Both gatesFAIL;no promotion.437tests/98completedtrials/65actualwakeups/noactivejobs. Frozen scores reused,35detector/0classifier forwards,not new final or end-to-end API accuracy. Detailed modelcard acpds_frozen_fusion.json and student explanation under reports/acpds_fusion_ACPDS-FROZEN-FUSION-20261027T014230468943Z.69SGsnapshots,learned performance closed.\n')
    with (ROOT/'docs/UI_TEST_LOG.md').open('a',encoding='utf-8') as f:f.write('\n## 27 October 2026 — scientific fusion examples, no desktop control\n\nThree fixed-order diagnostic PNGs rendered and visually inspected:original unsafevacant warned,original unsafevacant remaining,research correctvacant senttoreview. Hashes,source/crop bounds,published labels,method states and supporting boxes retained in report manifest/visual_review.json. Observed occlusion/projection differences are not causal proof. No visible GUI/native-dialog/offline/newmachine/manual/student acceptance;software437/OK.\n')
    with (ROOT/'docs/AI_ASSISTANCE_LOG.md').open('a',encoding='utf-8') as f:f.write('\n27Oct2026:Codex implemented and ran a fixed-method ACPDS development fusion diagnostic,5softwaretests and3source-bound illustrative crops. Actual detector inference is distinguished from replayed classifier scores;all failed gates/source labels preserved. Report explanation is AI-assisted;student independent contribution/mastery not assessed. No final access/model promotion.\n')
    dump(e/'checks.json',dict(checked_at=now,counter_before=97,counter_after=98,wakeups_completed=65,software_tests=437,source_ids=63,completed_trial=run['run_id'],frozen_hashes_unchanged=protocol['protected_hashes'],source_hashes=protocol['source_hashes'],development_gates={k:v['checks'] for k,v in run['methods'].items()},production_promoted=False,final_opened=False,model_calls=run['model_calls'],active_jobs=[],next100_run_checkpoint=100,next_collection_after=next_collection,full_project_complete=False,
        artifacts={p.relative_to(ROOT).as_posix():digest(p) for p in [tests,ROOT/'models/acpds_frozen_fusion.json',target/'EXPLANATION.md',target/'manifest.json',target/'visual_review.json']}))
    print(json.dumps(dict(counter=98,wakeups=65,software_tests=437,project_complete=False,active_jobs=[],next_collection_after=next_collection)))

if __name__=='__main__':main()
