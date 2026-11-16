"""Save the completed allocation integration and exact resumable state."""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

e=ROOT/'experiments/evidence/HEARTBEAT-20261027T010907Z'
s=read(ROOT/'data/automation_state.json')
assert s['completed_recorded_runs_since_schedule']==97==len(set(s['completed_run_ids']))
assert not s['active_training_jobs'] and not s['active_validation_jobs']
with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as f:
    ids=[r['experiment_id'] for r in csv.DictReader(f)]
assert all(ids.count(r)==1 for r in s['completed_run_ids'])
protected=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T003907Z/checks.json')['frozen_hashes_unchanged']
for f,h in protected.items():assert digest(ROOT/f)==h,f
api=read(ROOT/'models/assignment_api_validation.json')
assert api['integration_gate_passed'] and not api['recovery']['inference_repeated']
assert 'Ran 432 tests' in (e/'unit_tests_integrated.txt').read_text() and '\nOK' in (e/'unit_tests_integrated.txt').read_text()
live=read(ROOT/'reports/singapore_issuance_latest.json')
assert digest(ROOT/live['study_issuance']['receipt_path'])==live['study_issuance']['receipt_sha256']
assert s['scheduled_wakeups_completed']==63
s['scheduled_wakeups_completed']=64
now=datetime.now(timezone.utc).isoformat()
s['last_wakeup_completed_at']=now;s['last_updated_at']=now
s['prospective_live_summary']=live['baseline'];s['last_live_baseline_score']=live['baseline']
s['trigger_handling_note']='01:09 wake continued independent memory work until source-compliant collection at01:13:37UTC. No backfill; next source collection after01:43:37UTC. Reporting-only failure recovered without repeating completed API inference.'
s['next_actions']=[
 'Collect once AFTER 2026-10-27T01:43:37.918904+00:00 using existing collect_singapore_study.py; routine metadata health WITHOUT --record-trial.68official snapshots/16205learned forecasts/15origins/15receipted batches;performance closed. Do not backfill gaps or decode pending learned targets.',
 'Working application uses qualified bounded slot patches. Read docs/OCCUPANCY_MEMORY_GUIDE.md and models/assignment_api_validation.json.432softwaretests;two distinct trials95->97;no active jobs;63source IDs. Keep original dense reference for replay. The original API reporting TypeError remains archived; repaired future runner and one-time recovery are separate. No repeated inference/count inflation.',
 'Next highest-impact bounded study: preregister fixed-threshold FasterRCNN640 plus original classifier fusion on35admitted ACPDSdevelopment photos, with exact source/input/config hashes and false-vacancy/uncertainty/per-image gates BEFORE analysis. This is reused development,not final. Isolate cancellable worker with capped RSS/time;run sequential batches/checkpoint results. Avoid MaskRCNN4K producer until its separate dense-output memory risk is bounded. Do not overlap trainers.',
 'Preserve best last-block checkpoint7ea60239e81e83b4ba397c39498bb4c10861564bd63a6bf44d1eb75cedd85b2f and head d930f14a74fd11647227814c058eba7496846f6653e0488d4c08a9d67cd5c696. Source95.8508%hardaccuracy/14confidentfalsevacants fails1%gate;twoimagesbelow90%;oldfalsevacants2->5. Neither research model replaces original72272f0f checkpoint. No optimizer/crop/threshold grid on same35VALID.',
 'The selected451file softwareREADYofflinecopy predates the memory patch. Refresh/revalidate it at the next integration milestone using existing safe pre-origin snapshot selector and approved local-loopback context for Jupyter;preserve oldREADY/failed evidence. Do not copy/decode reserved SG targets. Physicaloffline/newmachine/visiblemanual/student/university acceptance remainsopen.',
 'SG final remains CLOSED until2026-10-27T10:51UTC(16:21IST):no interim learned matching/error/coverage/targets,refit/backdating. Use once-only scorer/globalclaim only afterclosure. Rollingpersistence61105outcomes/MAE5.802520252025203spaces is separate aggregate availability,not camera groundtruth. Next separate100-runlivecheckpoint at100;97completed now.',
 'Keep allACPDS27TESTimages/alllots/views/aliases andwholeHighwayDrive FINALclosed;consumedPKLotfinals excluded. Sourcecontentrights stillunqualified forNDIS/CNR;no imageuse. Product work continues independently of missing university documents.'
]
# Health reads only receipt/issuance metadata, never target values. Preserve older
# health record but mark its stale nested summary rather than pretending refreshed.
s['singapore_issuance_health']['latest_handoff_note']='Detailed nested health snapshot predates latest collection; current metadata-only health report is reports/singapore_issuance_health_latest.json when present. Wake summary verified16205forecasts/15origins/15receipted batches;no target evaluation.'
dump(ROOT/'data/automation_state.json',s)
summary='''
## 27 October 2026 IST / bounded occupancy assignment integrated

Qualified original-raster bounded slot bitmaps against independent dense reference:
2,000 generated cases, three TRAIN geometry cases with generated detector inputs,
and an isolated fixed 1920x1080/96-slot/24-box fixture all preserve exact output
dictionaries. Additional sampled peak RSS fell207,122,432->9,101,312bytes (95.6%)
on that fixture; retained slot bitmaps199,065,600->1,855,488bytes; assignment
8.351->0.165seconds. These are software fixtures, not camera accuracy or bounds
on model/MaskRCNN output memory. Qualification is frozen at145bdc7.

Working VisionEngine now delegates assignment to this qualified helper; original
dense reference remains. Six added contract tests bring the full suite to432/OK.
Actual FasterRCNN640+original classifier then processed three already exposed
4000x3000TRAIN photos/83spaces: identities, counts, ordered IDs, uncertainty rules,
unique vehicle support, unchanged model hashes and full-size RGB overlays pass.
Three detector and three classifier calls,15.814second worker duration, sampled
peak1,275,285,504bytes below1.5GiB cap. All three previews visually inspected.
No label accuracy, visibleGUI/native-dialog/newmachine/physicaloffline acceptance.

Parent reporting failed after successful inference on a duplicate duration field.
Original code/protocol/stdout/error/worker outputs remain immutable; separate
hash-checked recovery registers this same trial once with NO repeated inference.
Wall timestamps are explicitly derived from worker-file metadata and measured
duration; unavailable parent duration is not invented. Future runner repaired.
Two distinct trials95->97, not per case/frame/test/modelcall. Wakeups64/sourceIDs63,
next separate100-run live checkpoint100,noactivejobs. Original production weights,
frozenSGmethods and finalreservations unchanged. Last-block classifier remains
research only:source95.8508% hardaccuracy but14confidentfalsevacants>1%limit,
twoimagesbelow90%,oldfalsevacants2->5. No model promotion or new final access.

OfficialSGsnapshot68 at01:13:37UTC adds1,178rollingpersistenceoutcomes:
61,105total/MAE5.802520252025203spaces and1,140baselineforecasts. Another1,025
genuine learned forecasts give16,205forecasts/15origins/15receiptedbatches;no
learned target decoding/matching/coverage/error until27October10:51UTC. Next
collection after2026-10-27T01:43:37.918904+00:00; earlier gaps remainmissing.
Next preregister one fixed-threshold Faster/classifier DEVELOPMENT fusion study,
with memory/time caps and false-vacancy/uncertainty gates;avoid further optimizer
or threshold grids on35reusedVALID. Existing451-fileREADYofflinecopy predates
this patch;refresh at a new integration milestone. Guide:OCCUPANCY_MEMORY_GUIDE.md.
Official documents/manual/student/physicaloffline/newmachine acceptance open.
'''
for name in ['PROJECT_PROGRESS.md','AUTONOMOUS_PROGRESS.md','TEST_RESULTS.md']:
    with (ROOT/'docs'/name).open('a',encoding='utf-8') as f:f.write(summary)
with (ROOT/'docs/IMPLEMENTATION_STATUS.md').open('a',encoding='utf-8') as f:
    f.write('\n## Latest application resource integration — 27 October 2026\n\nWorking assignment uses bounded slot patches;432tests and three actual TRAIN-photo API cases pass.97completed trials/64wakeups. Fixed fixture additional RSS falls95.6%;no neural accuracy gain or universal memory bound. Original classifier remains active;research last-block gate still fails. Offline selected copy predates this patch. See OCCUPANCY_MEMORY_GUIDE.md and current automation_state.json for exact evidence/next actions. SG68snapshots/16205learned forecasts remain unscored until10:51UTC.\n')
with (ROOT/'docs/UI_TEST_LOG.md').open('a',encoding='utf-8') as f:
    f.write('\n## 27 October 2026 — API integration and rendered previews only\n\nASSIGNMENT-API-20261027T012959957197Z ran real FasterRCNN640 and original classifier on3previously exposed4KTRAIN photos,83spaces. API identity/count/state/modelhash/overlay contracts pass. All3downscaled PNG overlays visually inspected for intact rendering;this is not occupancy accuracy certification. No desktop control,visible native dialogs,physicaloffline,newmachine or student acceptance executed. Worker reporting error recovered once without rerunning inference. Software432/OK;full allocation guide OCCUPANCY_MEMORY_GUIDE.md.\n')
dump(e/'checks.json',dict(checked_at=now,counter_before=95,counter_after=97,wakeups_completed=64,source_ids=63,software_tests=432,
    completed_trials=[s['occupancy_patch_validation']['run_id'],api['run_id']],frozen_hashes_unchanged=protected,
    api_integration_gate=True,worker_reporting_recovered_without_inference=True,real_camera_accuracy_evaluated=False,
    final_opened=False,model_weights_changed=False,assignment_allocation_integrated=True,active_jobs=[],
    next100_run_checkpoint=100,next_collection_after='2026-10-27T01:43:37.918904+00:00',full_project_complete=False,
    artifacts={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in [e/'unit_tests_integrated.txt',ROOT/'models/occupancy_patch_validation.json',ROOT/'models/assignment_api_validation.json']}))
print(json.dumps(dict(counter=97,wakeups=64,software_tests=432,protected_files=len(protected),active_jobs=[],full_project_complete=False)))
