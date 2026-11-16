"""Record the rejected TRAIN component, immutable evidence and next work."""
import csv,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    e=ROOT/'experiments/evidence/HEARTBEAT-20261027T040910Z';run=read(ROOT/'models/anchor_support_train.json');out=ROOT/'experiments/results'/run['run_id'];protocol=read(out/'protocol.json');assert run['protocol_sha256']==digest(out/'protocol.json')
    for f,h in {**protocol['source_hashes'],**protocol['input_hashes'],**protocol['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    s=read(ROOT/'data/automation_state.json');assert s['completed_recorded_runs_since_schedule']==99==len(set(s['completed_run_ids'])) and s['scheduled_wakeups_completed']==65;assert not s['active_training_jobs'] and not s['active_validation_jobs']
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as f:ids=[r['experiment_id'] for r in csv.DictReader(f)]
    assert all(ids.count(r)==1 for r in s['completed_run_ids'])
    assert not run['train_geometry_gate_passed'] and run['model_calls']==dict(detector=24,classifier=0)
    tests=e/'unit_tests.txt';assert 'Ran 442 tests' in tests.read_text() and '\nOK' in tests.read_text()
    report=read(ROOT/'reports/anchor_train_explanation_latest.json');target=ROOT/report['path'];manifest=read(target/'manifest.json');assert report['manifest_sha256']==digest(target/'manifest.json') and manifest['explanation_sha256']==digest(target/'EXPLANATION.md')
    for example in manifest['examples']:assert example['available'] and digest(target/example['preview'])==example['preview_sha256']
    now=datetime.now(timezone.utc).isoformat()
    review=dict(checked_at=now,manifest_sha256=digest(target/'manifest.json'),images_reviewed=[v['preview'] for v in manifest['examples']],readable_headers=True,polygon_box_and_anchor_visible=True,
        source_labels_unchanged=True,new_model_calls=0,scope='Three fixed-order TRAIN examples,not representative samples,independent truth or causal proof',
        observations=['Vacant support removed:projected vehicle rectangle crosses supplied vacant bay while bottom-center lies outside it.',
                      'Occupied support lost:bottom-center falls outside the oblique supplied occupied polygon despite substantial box overlap.',
                      'Occupied support added:point lands in an occupied-label bay,but physical vehicle association remains unverified and can differ from the apparent neighboring box.'])
    dump(target/'visual_review.json',review)
    live=read(ROOT/'reports/singapore_issuance_latest.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json');assert live['collection']=='acquired' and health['status']=='healthy' and not health['target_json_decoded'] and not health['performance_evaluated'];assert health['forecasts_logged']==17318 and health['global_origins']==16
    assert digest(ROOT/live['study_issuance']['receipt_path'])==live['study_issuance']['receipt_sha256']
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')));assert snapshots==70
    next_collection=(datetime.fromisoformat(live['baseline']['checked_at'])+timedelta(minutes=30)).isoformat()
    s.update(scheduled_wakeups_completed=66,last_wakeup_completed_at=now,last_updated_at=now,prospective_live_summary=live['baseline'],last_live_baseline_score=live['baseline'],singapore_issuance_health=health)
    s['trigger_handling_note']='04:09 trigger was early versus04:09:46due;independent geometry preparation first,source-compliant actual collection04:11:11UTC. One fixed TRAIN study98->99;24photos/6children/3previews/5tests are not separate trials. No final/VALID evaluation.'
    s['anchor_train_explanation']=dict(path=report['path'],manifest_sha256=report['manifest_sha256'],visual_review_sha256=digest(target/'visual_review.json'),new_model_calls=0,student_mastery_assessed=False)
    s['next_actions']=[
      'Collect once AFTER '+next_collection+' through collect_singapore_study.py;routine metadata health WITHOUT --record-trial.70official snapshots/17318learnedforecasts/16origins/16receiptedbatches healthy. Next04:39heartbeat is early versus04:41:11due:do useful independent work first,never poll early/backfill/decode pending learned targets.',
      'Read models/anchor_support_train.json and reports/'+target.name+'/EXPLANATION.md. Reject naive box-bottom-center:24seededTRAINphotos/757bays,357occupied400vacant. Vacant-label support46->61 (worse),occupied-label support269->190;paired originaloccupiedsupport169/269=62.8253% retained,20of24imagesbelow90%.24detector/0classifier calls,112.642sec. No occupancy accuracy or physical vehicle association claim;no VALID/TEST images/labels read. Do not shift anchors/sweep thresholds against these outcomes or install helper.',
      'Highest-impact independent next work: refresh selected offline demonstration to include bounded assignment c004db7. Preserve old451-fileREADY copy and failed attempts. Inspect scripts/build_offline_demo.py (generic fresh builder,includes current src/*.py and safe pre-origin snapshot selector). Run the new build in approved local-loopback context so the existing Jupyter verifier does not hang in managed Windows socketpair.accept. Freeze current inputs/gates and old selected payload hashes before installing;no paid services/new packages/networkfallback. Keep copied source/input/output hash and normal-use audit proofs.',
      'Do not blindly run old postvalidators: scripts/check_combined_offline_demo.py and check_refreshed_offline_demo.py bind26Octdates/evidence folders and old checks; revalidate_copied_notebook.py targets old exact package. Create a new bounded parameterized controller/record for current copy,retaining existing file/DNS/foreign-workspace guards and original failure records. Verify current occupancy_patches import is included,actual hidden app,exports,107locked versions and copied notebook. Software package acceptance is not physicaloffline/newmachine/manual/student acceptance.',
      'Counter99;next genuine completed trial may reach100. At100 perform the separately required official-live checkpoint with immutable raw/normalized/URL/time/hash receipts,source freshness/schema/bounds/duplicate checks and actual app behavior. Respect minimum1minute and sensible history cadence;do not invent model/camera accuracy or open reserved learned targets. Save milestone evidence/last_scheduled_live_checkpoint and next200 explicitly;routine collection alone is not a new experiment. Never add a filler run to hit100.',
      '442softwaretests pass;66actualwakeups/63sourceIDs/noactivejobs. Production originalweights remain72272f0f/UNet2fe3743e/LSTM27dc324e. Research last-block7ea60239 andhead d930f14a preserved,not promoted. Fixed fusion on35reusedVALID alsofailed retention;keep those outputs immutable. Stronger parking-region learning needs appropriate qualified labels;supplied bay polygons are not exhaustive whole-lot/background groundtruth.',
      'SG final remainsCLOSED until2026-10-27T10:51UTC(16:21IST):no interim learnedtarget/matching/error/coverage,refit/backdating. Use once-only scorer/globalclaim only afterclosure.62268rollingpersistenceoutcomes/MAE5.791128669621635spaces are aggregateavailability,notcamera truth. AllACPDS27TEST/lots/views/aliases andHighwayDrive remainclosed. Officialdocs/manualphysicaloffline/newmachine/student acceptance stillopen.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['anchor_support_train']=dict(run_id=run['run_id'],card='models/anchor_support_train.json',card_sha256=digest(ROOT/'models/anchor_support_train.json'),images=24,spaces=757,role='Seeded admitted TRAIN subset;previously used in representation training,not unseen/final',source_id='SRC-DS-021',source_assets_added=0,model_calls=run['model_calls'],component_gate_passed=False,production_promoted=False);inventory['singapore_issuance_health']=health;dump(ROOT/'data/dataset_inventory.json',inventory)
    summary=f'''
## 27 October 2026 IST / reject bottom-center support on TRAIN geometry

Tested one fixed alternative to full-box overlap: floored bottom-center point
inside the original rasterized supplied bay; out-of-image point stays unknown,
with one detector per bay. No clipping, threshold variants, crop or model tuning.
Seed164 sampled24 of228admitted TRAIN photos after excluding3prior TRAIN API
previews. All images/labels participated in earlier representation training;
this is a component TRAIN diagnostic, not independent camera/model accuracy.
No classifier forwards or fitting; actual fixed Faster640/confidence0.5 ran24times.
No VALID/TEST photos or label semantics were read by this trial.

Across757bays (357occupied/400vacant), false support of vacant-label bays WORSENED
46->61, while supported occupied-label bays fell269->190. Only169of269originally
supported occupied bays retained support (62.8253%);100were lost and21new occupied
bays supported.20of24images fall below90%paired retention. Vacant support removed
on29old bays was outweighed by44new false supports. Cohort-size gate passes;
false-support reduction/globalretention/per-imageretention gatesFAIL. No support
never proves vacancy; occupied bay label does not verify physical vehicle identity.
Candidate remains separate research helper,not imported by production VisionEngine.
Do not sweep point shifts/thresholds against this rejection or retune35reusedVALID.

Six isolated4photochildren checkpointed each frame;112.642seconds total, maximum
sampled childRSS1283440640bytes below1.75GiBcap. Five meaningful support/identity/
boundary/denominator tests bring full suite442/OK7.317seconds. Three fixed-order
TRAIN crops and source-bound student explanation created; all3visuallyinspected.
They illustrate a removed warning,a lost occupied support and a new support whose
physical vehicle association is unverified; no relabeling/causalproof. See
reports/{target.name}/EXPLANATION.md and visual_review.json.
One completed experiment98->99,not perphoto/batch/test/preview;wakeups66/sourceIDs63,
noactivejobs. Originalweights/frozenSGmethods/finalreservations unchanged.

OfficialSGsnapshot70 at04:11:11UTC adds1163later rollingpersistence outcomes:
62268total/MAE5.791128669621635spaces and1204newbaselineforecasts.1113genuine
learned forecasts newlyfrozen give17318forecasts/16origins/16receiptedbatches;
metadatahealthy,learnedtargetdecoding/matching/coverage/error remainsclosed until
27Oct10:51UTC. Nextcollection after{next_collection};earlier146mingap notbackfilled.
Next update the outdated offline demonstration at a genuine application milestone,
using safe pre-origin snapshot selection and approved loopback for real copied
Jupyter;old postvalidators have date/package bindings and need a new parameterized
controller. Preserve old451-fileREADY/failures. At actual100completed trials perform
the separate required live checkpoint;pending100 now,no filler trial. Physical
offline/newmachine/manual/student/university acceptance remainsopen.
'''
    for name in ['PROJECT_PROGRESS.md','AUTONOMOUS_PROGRESS.md','TEST_RESULTS.md']:
        with (ROOT/'docs'/name).open('a',encoding='utf-8') as f:f.write(summary)
    with (ROOT/'docs/IMPLEMENTATION_STATUS.md').open('a',encoding='utf-8') as f:f.write('\n## Latest TRAIN geometry diagnostic — 27 October 2026\n\nNaive detector bottom-center support rejected on24TRAINphotos/757bays:vacant-label support46->61 (worse),paired occupied-support retention169/269=62.8253%,20images below90%. No classifier inference/training,VALID/TEST access or production change.442tests/99completedtrials/66wakeups/noactivejobs. Pending separate100-run live checkpoint100. Offline selected451-filecopy still predates bounded assignment;refresh next.70officialSGsnapshots/17318unscoredlearnedforecasts. Detailed card models/anchor_support_train.json and source-bound explanation under reports/anchor_support_ANCHOR-TRAIN-20261027T041309240270Z.\n')
    with (ROOT/'docs/UI_TEST_LOG.md').open('a',encoding='utf-8') as f:f.write('\n## 27 October 2026 — TRAIN geometry examples only\n\nThree source-bound fixed-order PNGs visually reviewed:vacant support removed,occupied support lost,occupied support added. Supplied polygon,detector rectangle and yellow box-bottom proxy are visible with readable headers. New bay support does not verify correct physical vehicle association. Published labels unchanged;no visibleGUI/native-dialog/offline/newmachine/manual/student acceptance.442softwaretests pass;no production geometry change.\n')
    with (ROOT/'docs/AI_ASSISTANCE_LOG.md').open('a',encoding='utf-8') as f:f.write('\n27Oct2026:Codex implemented a research-only point-support helper,5softwaretests and one fixed24TRAIN-photo diagnostic with source-bound illustrative crops. Candidate rejected on frozen gates;original application unchanged. Report/explanations are AI-assisted,not evidence of student independent work/mastery. No validation/final access or source-label relabeling.\n')
    dump(e/'checks.json',dict(checked_at=now,counter_before=98,counter_after=99,wakeups_completed=66,software_tests=442,source_ids=63,completed_trial=run['run_id'],frozen_hashes_unchanged=protocol['protected_hashes'],source_hashes=protocol['source_hashes'],train_component_checks=run['checks'],production_promoted=False,validation_or_final_opened=False,model_calls=run['model_calls'],active_jobs=[],next100_run_checkpoint=100,next_collection_after=next_collection,full_project_complete=False,
        artifacts={f.relative_to(ROOT).as_posix():digest(f) for f in [tests,ROOT/'models/anchor_support_train.json',target/'EXPLANATION.md',target/'manifest.json',target/'visual_review.json']}))
    print(json.dumps(dict(counter=99,wakeups=66,software_tests=442,active_jobs=[],full_project_complete=False,next_collection_after=next_collection)))

if __name__=='__main__':main()
