"""Select the verified fresh copy and preserve the required live milestone evidence."""
import csv,json,shutil,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.package_acceptance import verify_payload

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    e=ROOT/'experiments/evidence/HEARTBEAT-20261027T043910Z';pre=read(e/'preflight.json');rid='COMBINED-DEMO-20261027T044747395249Z';r=read(ROOT/'experiments/results'/rid/'run.json');package=ROOT/r['package'];milestone=read(ROOT/'models/live_checkpoint_100.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json')
    s=read(ROOT/'data/automation_state.json');assert s['completed_recorded_runs_since_schedule']==101==len(set(s['completed_run_ids'])) and s['scheduled_wakeups_completed']==66 and s['next_live_checkpoint_at_run']==200;assert not s['active_training_jobs'] and not s['active_validation_jobs']
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:ids=[v['experiment_id'] for v in csv.DictReader(stream)]
    assert all(ids.count(v)==1 for v in s['completed_run_ids'])
    assert r['combined_demo_gate_passed'] and len(r['checks'])==5 and r['payload_files']==468 and r['payload_bytes']==809047000
    assert verify_payload(package,r['payload'])==468
    assert read(package/'READY.json')['report_sha256']==digest(package/'COMBINED_VALIDATION.json')
    protected={**pre['protected_hashes'],**r['protected_hashes']}
    for cardfile in ['models/acpds_balanced_head.json','models/acpds_last_block.json']:
        card=read(ROOT/cardfile);protected[card['candidate_checkpoint']]=card['candidate_checkpoint_sha256']
    for f,h in {**protected,**pre['previous_files'],**r['source_hashes'],**pre['source_hashes']}.items():assert digest(ROOT/f)==h,f
    oldpackage=ROOT/pre['previous_pointer']['path'];assert verify_payload(oldpackage,pre['previous_payload_files'])==451
    assert milestone['checkpoint_gate_passed'] and not milestone['learned_accuracy_evaluated'] and not milestone['camera_accuracy_evaluable']
    d=milestone['details'];assert d['accepted_rows']==2423 and d['invalid_bounds_excluded']==5 and d['accepted_duplicate_rows']==0 and d['csv_roundtrip']
    assert d['app']['status']=='passed' and d['app']['model_calls']==0
    assert health['status']=='healthy' and health['forecasts_logged']==19551 and health['global_origins']==18 and not health['target_json_decoded'] and not health['performance_evaluated']
    for log in ['unit_tests.txt','unit_tests_launcher.txt']:
        text=(e/log).read_text();assert 'Ran 446 tests' in text and '\nOK' in text
    assert digest(ROOT/'data/manifests/copied_package_acceptance_v1.json')==pre['contract_sha256']
    now=datetime.now(timezone.utc).isoformat();history=ROOT/'reports/demo_package_history'/rid;history.mkdir(parents=True,exist_ok=False)
    for name in ['demo_package_latest.json','offline_demo_latest.json']:shutil.copyfile(ROOT/'reports'/name,history/name)
    pointer=dict(run_id=rid,kind='Fresh copied selected demo with bounded assignment and107locked dependencies',path=r['package'],files=468,bytes=809047000,manifest_sha256=digest(package/'BUNDLE_MANIFEST.json'),validation_sha256=digest(package/'COMBINED_VALIDATION.json'),validation_report=(package/'COMBINED_VALIDATION.json').relative_to(ROOT).as_posix(),guide='docs/CURRENT_OFFLINE_PACKAGE.md',python=r['package']+'/.venv/Scripts/python.exe',fresh_package_environment=r['package']+'/.venv',fresh_package_install_verified=True,runtime_reused=False,existing_base_python_reused=True,installer_wheels=107,installer_bytes=257829508,all107versions_verified=True,actual_copied_folder_kernel_verified=True,included_notebooks=r['selected_notebooks'],excluded_notebooks=r['excluded_notebooks'],transactional_export_tests=13,bounded_assignment_included=True,occupancy_patch_sha256=read(ROOT/'data/manifests/copied_package_acceptance_v1.json')['occupancy_patch_sha256'],forecast_methods=['Original LSTM','Group-relative residual LSTM'],cached_live_snapshot=r['cached_live_snapshot'],cached_live_provider_timestamp=r['cached_live_provider_timestamp'],cached_live_sha256=r['cached_live_sha256'],cached_live_selection=r['cached_live_selection'],previous_run=pre['previous_pointer']['run_id'],previous_pointer_archive=(history/'demo_package_latest.json').relative_to(ROOT).as_posix(),physical_network_disconnection_verified=False,new_machine_verified=False,visible_manual_acceptance=False,student_mastery_assessed=False,scientific_accuracy_evaluated=False,model_training_performed=False,execution_context='Approved local-loopback;existing Python external/fallback audit guards retained')
    dump(ROOT/'reports/demo_package_latest.json',pointer);dump(ROOT/'reports/offline_demo_latest.json',pointer);dump(ROOT/'models/current_offline_package.json',pointer)
    baseline=d['rolling_persistence'];issuance=d['frozen_future_issuance'];next_collection=(datetime.fromisoformat(baseline['checked_at'])+timedelta(minutes=30)).isoformat();snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')));assert snapshots==72
    dump(ROOT/'reports/singapore_issuance_latest.json',dict(checked_at=baseline['checked_at'],source_id='SRC-LIVE-001',collection='acquired_by_required100run_checkpoint',learned_final_scoring='Disabled;separate once-only final scorer after closure',baseline=baseline,study_issuance=issuance,milestone_checkpoint=milestone['run_id']))
    s.update(scheduled_wakeups_completed=67,last_wakeup_completed_at=now,last_updated_at=now,combined_offline_demo=pointer,current_offline_refresh=pointer,last_live_baseline_score=baseline,prospective_live_summary=baseline,singapore_issuance_health=health)
    s['trigger_handling_note']='04:39trigger preceded next due04:41:11;independent package work first,actual routinecollection04:42:31. Fresh copy is completed trial100. Separately required milestone100acquisition04:54:19 used existing minimum60second guard after11.8mingap and actual native callback;completed validation trial101,next milestone200. No frame/phase/test/forecast inflated counts.'
    s['next_actions']=[
      'Collect once AFTER '+next_collection+' through collect_singapore_study.py;routine metadata health WITHOUT --record-trial.72official snapshots/19551learnedforecasts/18origins/18receiptedbatches healthy. Milestone collection supersedes old05:12routine due;next05:09heartbeat is early versus05:24:19due. Do independent useful work first,no early polling/backfill/learned matching.',
      'Selected current copy '+r['package']+' is468payload files/809047000bytes,107original wheels/notices,NEW local.venv,actual hidden app bothdetectors and transactional exports,actual notebook08kernel/1PNG,13syntheticfaultcases,107locked versions and scoped fallback/DNS probes allpass. Current occupancy_patches import verified;fixedTRAIN fixture68occupied32vacant0uncertain/100 retained for bothdetectors,not accuracy. Original451-filecopy and failedbuild/acceptance chain unchanged;history pointers preserved. No repeated rebuild/re-inference merely forcounts.',
      'Next scientific priority: expand the earlier six-provisional-group PKLot role audit to ALL original archive camera/date metadata,joining every prior TRAIN/DEV exposure,reservation,consumedclaim and alias. Read scripts/audit_remaining_pklot_groups.py and src/smart_parking/group_role_audit.py first. Earlier six-group audit found0freshgroups only within that list,not global exhaustion. Do not decode new pixels/XML labels until roles/fresh cohorts are reserved. Qualify actual bay-union target semantics separately from exhaustive whole-parking-area masks before any segmentation training.',
      'Alternatively update dated report/presentation/student explanation to current software milestone and preserved failed occupancy/geometry studies. Earlier PDFaddendum is a dated87-counter snapshot,not current101 evidence. Student exercises remainunassessed. Keep Python/Jupyter reusablemodules;run full software tests reproducibly with python scripts/run_project_tests.py (workspace-owned TEMP/import path).446tests pass;do not reuse old hardcoded-date postvalidators on this new copy.',
      'Counter101/67actualwakeups/63sourceIDs/noactivejobs. Required100-run live checkpoint PASSED:2423acceptedrows/2005parks,5invalid-bound records excluded,0acceptedduplicates,43.46sec providerage at acquisition,native table2423rows/filter1/provider/path/status checks. Existing source/receipts/normalizedCSV hashes retained;no additional app poll or modelcalls. next_live_checkpoint_at_run200,last_scheduled_live_checkpoint100. This is software/feed evidence,not camera or learned model accuracy.',
      'SG final remainsCLOSED until2026-10-27T10:51UTC(16:21IST):no interim learnedtarget/matching/error/coverage,refit/backdating. Use once-only scorer/globalclaim only afterclosure.63461rollingpersistenceoutcomes/MAE5.768897433069129spaces are separate aggregateavailability,notcamera truth.19551loggedforecasts/18origins are not final matched coverage. Do not imply BirminghamvalidatedSG.',
      'Original modelweights/frozenSGmethods/consumedclaims/bestverifiedcheckpoints unchanged. Research last-block occupancy and fixedfusion and bottom-center TRAIN support failedgates;do not install or retune thresholds/anchor/crops on exposedcohorts. AllACPDS27TEST/lots/views/aliases andHighwayDrive remainclosed. Physicaloffline/newmachine/visiblemanual/student/university acceptance stillopen;full datasets and10other notebooks absentfromselectedcopy.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory.update(inventoried_at=now,combined_offline_demo=pointer,current_live_milestone=dict(milestone=100,run_id=milestone['run_id'],accepted_rows=2423,gate_passed=True,normalized_csv=d['normalized_csv'],normalized_csv_sha256=d['normalized_csv_sha256']),singapore_issuance_health=health)
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=2005,observations=2423,raw_lot_records=2428,raw_path=d['receipt']['local_path'],provider_timestamp=d['metadata']['provider_timestamp'],snapshot_count=72,prospective_baseline_scored_outcomes=baseline['scores_total'],prospective_baseline_mae_spaces=baseline['baseline_mae_spaces'],forecast_target_coverage=baseline['forecast_coverage'])
    dump(ROOT/'data/dataset_inventory.json',inventory)
    guide=f'''# Current selected offline demonstration

The verified copy is `{r['package']}`. It contains 468 payload files (809,047,000
bytes), including 107 original installer wheels and their notices. A new local
environment was installed from those wheels using hash locks and no index.
Existing Windows, 64-bit Python 3.12 and Tk were reused; they are not distributed.

In PowerShell opened inside that copied folder, launch the already installed app:

```powershell
& '.\\.venv\\Scripts\\python.exe' run_app.py
& '.\\.venv\\Scripts\\python.exe' scripts/start_jupyter.py --offline --notebook '08_image_patterns_and_svd.ipynb'
```

Keep the copy at its verified location. Moving installed environments can break
absolute kernel paths; use the included setup instructions to create a new local
environment rather than overwriting a verified one. Only notebook 08 and selected
demo assets are included; full training datasets and ten other notebooks are absent.

Both actual detector routes retain the fixed TRAIN example counts of 68 occupied,
32 vacant and 0 uncertain out of 100. Those are reproducibility checks, not a new
accuracy score. The bounded assignment helper is included and its import was
verified. The actual copied-folder Jupyter kernel produced one inline PNG.
Thirteen synthetic export fault cases, all 107 locked dependency versions and
separate deliberate fallback/DNS probes passed. Normal audit records have no
denials. Localhost transport was allowed for Jupyter; external/fallback guards
were retained. Python audits do not isolate native extension I/O.

The copy intentionally retains the earlier cached Singapore snapshot
`{r['cached_live_snapshot']}`, before the reserved prospective period. Its age
and provider timestamp remain visible. Current main-project live history is
separate; pending learned forecast targets were not copied into the demo.

The older 451-file accepted copy, its original failed build report and its later
REVALIDATION_ACCEPTANCE chain are unchanged. Earlier selection pointers are in
`reports/demo_package_history/{rid}`. The new authoritative pointer is
`reports/offline_demo_latest.json`; READY.json and COMBINED_VALIDATION.json inside
the copy bind its actual validation. It passed in {r['duration_seconds']:.3f} seconds.

The separate 100-run live checkpoint accepted 2,423 rows from 2,005 car parks,
excluded five invalid bound records, verified duplicates/freshness/CSV integrity,
and exercised the hidden native live table/filter/status callback with actual
fresh rows. It is aggregate feed/software validation, not camera accuracy.
Learned Singapore forecasts remain unscored until their separate final closure.

Physical network disconnection, a different computer, visible manual/browser
rehearsal, student independent explanation and official university acceptance
remain unverified. Local academic use does not authorize external redistribution.
For reproducible project tests, use `python scripts/run_project_tests.py`; it keeps
temporary files and imports inside the workspace. The current full suite passes
446 tests. The initial temporary-folder cleanup failure is retained as evidence.
'''
    (ROOT/'docs/CURRENT_OFFLINE_PACKAGE.md').write_text(guide,encoding='utf-8')
    note=f'''
## 27 October 2026 IST / current copied package accepted and100-run checkpoint passed

New selected copy {r['package']} passes all5stages in299.063seconds:468payloadfiles/
809047000bytes,107original wheels/notices,NEW package-local environment installed
no-index/hash-locked,both actual hidden detector routes/exports/semantic separation/
archived forecast identities/SVD/video,copied notebook08actualkernel/1PNG,13synthetic
transaction fault cases and generic current-copy acceptance. FixedTRAIN sample
counts68occupied32vacant0uncertain/100 remain identical for bothdetectors;not new
accuracy. Current bounded occupancy_patches import/sourcehash verified. All107locked
versions match;existing environment overwrite refused. Normal Python audit denials0;
separate original-workspace/DNS negative controls blocked. Jupyter used approved
local loopback while external/fallback guards remained active;native extensionIO
and physical networking remain outside audit coverage.

Old451-fileacceptedpayload,READY/revalidationacceptance and originalfailed COMBINED
report all remain unchanged;previous pointers archived. Preflight initially assumed
oldpointer referenced COMBINED_VALIDATION;actualREADY explicitly references later
REVALIDATION_ACCEPTANCE,now verified by exact hash. Four new pure acceptance tests
bring suite446;initial Windows temporary-folder cleanup error preserved. Workspace
TEMP launch passes446/6.769sec;new reproducible run_project_tests.py passes446/9.283sec.
These are context repairs and softwarechecks,not extra experiments. New copy retains
safe pre-origin saved SGsnapshot26Oct02:30UTC;no pending learnedtargets packaged.
Onlynotebook08/selectedassets included;full datasets/10other notebooks/baseOS absent.

Fresh copy is completed trial100. Separately required LIVE-MILESTONE-100 checkpoint
is completed validation101:one fresh official acquisition viaexisting immutable raw/
receipt/history mechanism,at least60secs afterpriorpoll.2428rawlotrecords ->2423accepted
rows/2005parks,5invalid bounds excluded,0acceptedduplicates,43.460442sec providerage.
Normalized per-checkpointCSV round-trip/hash passes. ActualhiddenTk table2423rows,
filter1row andprovider/path/age-status checks pass. Backend callback receives those
actualacquiredrows without second poll;no modelcalls or cameraGT. LearnedMAE and
comparison remain unevaluated because finalstudy closed. Lastscheduledmilestone100
passed,next200;not100%accuracy/certification. Counter99->101 fromtwo actualtrials,
not per468files/107wheels/5phases/2423rows/testcase. Wakeups67/sourceIDs63/noactivejobs.

72officialSGsnapshots. Routine04:42acquisition froze1063learnedforecasts;milestone
04:54:19 froze1170more.19551forecasts/18origins/18receiptedbatches metadatahealthy,
no target decoding/matching/coverage/error. Rollingpersistence63461outcomes/MAE
5.768897433069129spaces;milestone added49later matches. Nextcollection after
{next_collection};this supersedes older routine due. Finalclosure27Oct10:51UTC unchanged.
Originalweights,frozenSGmethods,consumedclaims and bestresearchcheckpoints unchanged.
Next expand earlier six-group PKLot role audit to complete archive metadata before
fresh segmentation cohorts/pixel access,or update dated presentation/student materials.
Physicaloffline/newmachine/visiblemanual/student/university acceptance remainsopen.
See CURRENT_OFFLINE_PACKAGE.md;authoritative reports/offline_demo_latest.json.
'''
    for name in ['PROJECT_PROGRESS.md','AUTONOMOUS_PROGRESS.md','TEST_RESULTS.md','IMPLEMENTATION_STATUS.md']:
        with (ROOT/'docs'/name).open('a',encoding='utf-8') as stream:stream.write(note)
    with (ROOT/'docs/UI_TEST_LOG.md').open('a',encoding='utf-8') as stream:stream.write('\n## 27 October 2026 — fresh current copy and milestone native callback\n\nActual hidden app in new468-filecopy runsbothdetectors,transactional PNG/CSV/JSON exports,semantic preview separation,archived forecast method identities,SVD/progress/video and cached pre-origin feed. Mocked dialogs,not visible manual acceptance. Actualcopied Jupyterkernel/1PNG passes with local loopback and unchanged external/fallback guards. Separate milestone100 main-app callback displays2423actual freshlyacquired rows/filter1/provider/path/status,backend patched toavoid duplicatepolling. No camera accuracy/physicaloffline/newmachine/student/official acceptance.446softwaretests pass.\n')
    for name in ['COMBINED_OFFLINE_DEMO_GUIDE.md','AI_ASSISTANCE_LOG.md','LICENSING_RECORD.md']:
        with (ROOT/'docs'/name).open('a',encoding='utf-8') as stream:stream.write('\n27Oct2026:Current selected copy is468files/809047000bytes with107original hash-locked wheels/full notices and actual fresh environment/app/notebook/export checks. Pointer reports/offline_demo_latest.json;guide CURRENT_OFFLINE_PACKAGE.md. Old451-fileaccepted/failed records preserved. Sourcecatalog63 unchanged,no new package acquisition or external publication. Codex-assisted implementation/tests/docs;student mastery not assessed. Physical/manual/newmachine/university gates remainopen.\n')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['ENV-02','QA-02','OFF-01','PKG-01','PY-01']:
            row['actual_evidence']+=';reports/offline_demo_latest.json;docs/CURRENT_OFFLINE_PACKAGE.md;models/live_checkpoint_100.json'
            row['test_result']+=';27Oct current468-filecopy/107locked versions/newvenv/actual copied notebook08kernel/13transaction fixtures pass;446softwaretests;separate100-run live checkpoint passes;physical/newmachine/manual/student/official acceptance remains open'
    with path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    dump(e/'preflight_repairs.json',dict(initial_test_errors=4,initial_error_log='unit_tests_initial_temp_permission_failure.txt',cause='Windows managed default temporary folder cleanup denied;assertions unchanged',qualified_test_environment='Workspace TEMP/TMP/import path',reproducible_launcher='scripts/run_project_tests.py',old_validation_pointer_target='REVALIDATION_ACCEPTANCE.json',old_initial_failed_report_preserved=True,guards_removed=False,extra_experiments_counted=False))
    dump(e/'checks.json',dict(checked_at=now,counter_before=99,counter_after=101,wakeups_completed=67,software_tests=446,source_ids=63,completed_trials=[rid,milestone['run_id']],frozen_hashes_unchanged=protected,previous_payload_files_verified=451,current_payload_files_verified=468,new_install=True,actual_notebook=True,required100_checkpoint_passed=True,next_live_checkpoint_at_run=200,active_jobs=[],next_collection_after=next_collection,full_project_complete=False,
        source_hashes={**r['source_hashes'],**pre['source_hashes'],**read(ROOT/'experiments/results'/milestone['run_id']/'protocol.json')['source_hashes']},
        artifacts={f.relative_to(ROOT).as_posix():digest(f) for f in [e/'unit_tests.txt',e/'unit_tests_launcher.txt',ROOT/'reports/offline_demo_latest.json',ROOT/'models/live_checkpoint_100.json',ROOT/d['normalized_csv'],ROOT/'docs/CURRENT_OFFLINE_PACKAGE.md']}))
    print(json.dumps(dict(counter=101,wakeups=67,software_tests=446,selected_copy=r['package'],required100_checkpoint_passed=True,next_milestone=200,next_collection_after=next_collection,full_project_complete=False)))

if __name__=='__main__':main()
