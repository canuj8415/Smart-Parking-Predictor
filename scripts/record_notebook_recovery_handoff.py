"""Record composite copied-demo acceptance without rewriting failed experiments."""
import csv,json,shutil,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T183901Z'
DIAG='NOTEBOOK-DIAGNOSTIC-20261026T184229200431Z'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,body):
    path=ROOT/p;text=path.read_text(encoding='utf-8');assert title not in text
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+body+'\n',encoding='utf-8')


def main():
    assert not (E/'checks.json').exists();now=datetime.now(timezone.utc).isoformat();s=read(ROOT/'data/automation_state.json')
    pointer=read(E/'acceptance_run_pointer.json');rid=pointer['run_id'];r=read(ROOT/pointer['report']);diag=read(ROOT/'experiments/results'/DIAG/'run.json')
    assert s['completed_recorded_runs_since_schedule']==len(set(s['completed_run_ids']))==86 and not s['active_validation_jobs'] and not s['active_training_jobs']
    assert r['composite_software_gate_passed'] and r['corrected_context_notebook_gate_passed'] and not r['remaining_owned_pids']
    protocol=read(ROOT/'experiments/results'/rid/'protocol.json');package=ROOT/protocol['package'];manifest=read(package/'BUNDLE_MANIFEST.json')
    assert all(digest(package/f['path'])==f['sha256'] for f in manifest['files'])
    for f,h in {**protocol['input_hashes'],**protocol['source_hashes'],**protocol['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    frozen=read(ROOT/'experiments/evidence/HEARTBEAT-20261026T170900Z/checks.json')['frozen_hashes_unchanged']
    for f,h in frozen.items():assert digest(ROOT/f)==h,f
    for f,h in read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')['implementation_hashes'].items():assert digest(ROOT/f)==h,f
    previous=read(ROOT/'reports/offline_demo_latest.json');assert previous['run_id']=='COMBINED-DEMO-20261026T025712811956Z'
    assert digest(ROOT/previous['path']/'BUNDLE_MANIFEST.json')==previous['manifest_sha256']
    old=read(ROOT/r['prior_failed_report']);component=read(ROOT/r['prior_component']);assert not old['combined_demo_gate_passed'] and component['component_gate_passed']
    tests=(ROOT/'experiments/evidence/HEARTBEAT-20261026T180901Z/unit_tests_final.txt').read_text(encoding='utf-8-sig');assert 'Ran 388 tests' in tests and tests.rstrip().endswith('OK')
    assert read(E/'diagnostic_cleanup.json')['matching_count']==0
    audit=read(package/'outputs/notebook_check/controller_audit.json');kernel=r['notebook_validation']['kernel_audit'];assert not audit['denied'] and not kernel['denied']
    # Keep the failed build and its reports immutable;the acceptance chain is new.
    acceptance=dict(schema_version=1,accepted_at=now,run_id=rid,gate_passed=True,package=protocol['package'],payload_manifest_sha256=digest(package/'BUNDLE_MANIFEST.json'),
        frozen_payload_unchanged=True,original_failed_build=old['run_id'],original_failed_report_sha256=digest(ROOT/r['prior_failed_report']),
        component_report=r['prior_component'],component_report_sha256=digest(ROOT/r['prior_component']),corrected_notebook_report=pointer['report'],corrected_notebook_report_sha256=digest(ROOT/pointer['report']),
        checks=dict(fresh107_package_install=old['checks']['install']['returncode']==0,actual_hidden_app=old['checks']['app']['returncode']==0,
            synthetic_transaction_cases=13,all107versions_verified=component['checks']['versions']['all107versions_match'],actual_copied_notebook_kernel=True,inline_png_outputs=r['notebook_validation']['inline_png_outputs'],
            normal_python_guard_denials=0,original_source_notebook_unchanged=True),
        execution_context='Jupyter requires approved localhost sockets in the managed automation context;Python nonloopback/workspace-fallback guards retained',
        new_install_during_revalidation=False,model_calls_during_revalidation=0,scientific_accuracy_evaluated=False,
        scope='Selected software demonstration;existing Windows/base Python/Tk reused;not physical offline,new-machine,manual/student or official acceptance')
    assert not (package/'REVALIDATION_ACCEPTANCE.json').exists() and not (package/'READY.json').exists()
    dump(package/'REVALIDATION_ACCEPTANCE.json',acceptance);dump(E/'REVALIDATION_ACCEPTANCE.json',acceptance)
    original_marker=package/'INCOMPLETE';retained_marker=package/'INCOMPLETE.initial_failed_build'
    assert original_marker.resolve().is_relative_to(package.resolve()) and retained_marker.resolve().is_relative_to(package.resolve()) and not retained_marker.exists()
    original_marker.rename(retained_marker)
    shutil.copyfile(package/'START_HERE.md',package/'START_HERE.initial_build.md')
    with (package/'START_HERE.md').open('a',encoding='utf-8') as stream:stream.write('\n## Corrected execution-context acceptance\n\nThe initial COMBINED_VALIDATION.json remains a failed historical attempt. READY.json now references REVALIDATION_ACCEPTANCE.json, combining the existing verified install/app/transaction/version checks with a successful unchanged copied notebook verifier in an approved localhost context. Original payload files and failed outputs are preserved. No second install or detector replay was needed. Physical disconnection,manual/new-machine/student/official acceptance remain separate.\n')
    ready=dict(run_id=rid,gate_passed=True,report='REVALIDATION_ACCEPTANCE.json',report_sha256=digest(package/'REVALIDATION_ACCEPTANCE.json'),scope=acceptance['scope'])
    dump(package/'READY.json',ready)
    backup=E/'previous_latest';backup.mkdir(exist_ok=False)
    for p in ['reports/demo_package_latest.json','reports/offline_demo_latest.json','models/combined_offline_demo_package.json']:
        target=backup/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target)
    latest=dict(previous,run_id=rid,kind='Selected copied demo accepted by immutable component evidence plus approved-loopback notebook revalidation',path=protocol['package'],files=len(manifest['files']),bytes=sum(x['bytes'] for x in manifest['files']),
        manifest_sha256=digest(package/'BUNDLE_MANIFEST.json'),validation_report='REVALIDATION_ACCEPTANCE.json',validation_sha256=digest(package/'REVALIDATION_ACCEPTANCE.json'),
        fresh_package_environment=protocol['package']+'/.venv',python=protocol['package']+'/.venv/Scripts/python.exe',fresh_package_install_verified=True,runtime_reused_for_notebook_revalidation=True,
        all107versions_verified=True,actual_copied_folder_kernel_verified=True,transactional_export_tests=13,original_failed_build=old['run_id'],previous_run=previous['run_id'],
        previous_pointer_archive=(backup/'reports/offline_demo_latest.json').relative_to(ROOT).as_posix(),cached_live_snapshot=old['cached_live_snapshot'],cached_live_sha256=old['cached_live_sha256'],cached_live_provider_timestamp=old['cached_live_provider_timestamp'],
        cached_live_selection=old['cached_live_selection'],included_notebooks=old['selected_notebooks'],excluded_notebooks=old['excluded_notebooks'],execution_context=acceptance['execution_context'])
    for p in ['reports/offline_demo_latest.json','reports/demo_package_latest.json']:dump(ROOT/p,latest)
    dump(ROOT/'models/combined_offline_demo_package.json',dict(acceptance,latest_pointer=latest));dump(ROOT/'reports/offline_refresh_recovery_latest.json',acceptance)
    # Archive actual generated kernel artifacts;do not copy connection/HMAC files.
    shutil.copyfile(package/'outputs/notebook_check/08_executed.ipynb',E/'08_executed.ipynb');shutil.copyfile(package/'outputs/notebook_check/controller_audit.json',E/'controller_audit.json');shutil.copyfile(package/'outputs/notebook_check/kernel_audit.json',E/'kernel_audit.json')
    import base64
    book=read(E/'08_executed.ipynb');pngs=[o['data']['image/png'] for c in book['cells'] if c['cell_type']=='code' for o in c.get('outputs',[]) if 'image/png' in o.get('data',{})]
    assert len(pngs)==1;(E/'notebook_preview.png').write_bytes(base64.b64decode(pngs[0]))
    live=read(ROOT/'data/processed/singapore_prospective/summary.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json')
    assert live['scores_total']==54285 and health['forecasts_logged']==9774 and health['global_origins']==9
    receipts=[json.loads(v) for v in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];raw=Path(live['snapshot_path']).resolve();receipt=next(v for v in reversed(receipts) if (ROOT/v['local_path']).resolve()==raw);assert digest(raw)==receipt['sha256']
    assert len(list((ROOT/'data/raw/singapore_live').glob('*.json')))==61;nexttime=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    s.update(last_updated_at=now,scheduled_wakeups_completed=s['scheduled_wakeups_completed']+1,combined_offline_demo=latest,offline_refresh_recovery=acceptance,prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=54285,mae_spaces=live['baseline_mae_spaces'],scope='Rolling persistence only;not learned/camera accuracy',coverage=live['forecast_coverage']))
    s['singapore_forecast_study'].update(learned_forecast_batches=9,learned_forecasts_logged=9774,learned_global_origins=9,learned_live_performance_evaluated=False)
    s['singapore_issuance_health'].update({k:health[k] for k in ['checked_at','forecasts_logged','batch_receipts','global_origins','unique_series','origins']});s['singapore_issuance_health'].update(metadata_status='healthy',status='healthy',raw_files_hashed_once=11,semantic_context_verified=False,performance_evaluated=False)
    s['offline_refresh_attempts']['status']='Original failed trials preserved;later corrected-context composite acceptance separately recorded';s['offline_refresh_attempts']['later_acceptance_report']='reports/offline_refresh_recovery_latest.json'
    s['next_actions']=[
        'TOP PRIORITY nextwake: collectonce AFTER'+nexttime+' using scripts/collect_singapore_study.py;30minuteplan/minimum1min. Ifearlydoindependentworkuntildue. Routinehealth WITHOUT --record-trial.61snapshots/9774genuinelearnedforecasts/9originsmetadatahealthy;no learnedtargetscores.',
        'FrozenSGfinal closeduntil27October10:51UTC(16:21IST). No refit/frozenmethodchanges/backfill/interimtargetdecoding. Atclosureexistingonce-onlyscorer/globalclaim. Rollingpersistence54285matches/MAE4.911725154278345spaces isseparate;missingtargets unscored.',
        'Offline451-filecopy nowREADY undernewcomposite '+rid+';originalfailedCOMBINED_VALIDATION.json remainsfailed. Local-loopbackpermission resolved managed asyncio socketpair stall;unchangedverifier realkernel/1PNG passes18.187s,external/fallbackauditdenials0. No reinstall/detectorreplay. Priorinstall/app/13faultcases/107versions linkedbyhash. Do not repeat identical rebuilds/checks merely forcounts;physical/manual/newmachine/studentacceptance remainsopen.',
        'Highestindependentnextpriority:distinctTRAIN-onlystaticbackgroundregionhypothesis withfixedDEVgates/freshfinalgroups OR genuinelyqualifiedfreshcamera/negative/regiondata. No ORB/crop/thresholdgridsonexposedcohorts;NDISPark/CNRindividualcontentrights remainunqualified;HighwayDrivewholefinalunopened. Missinguniversitydocsblockofficialcomplianceonly.',
        'Refreshdatedreport/presentation/studentexplanationswithhonestmodel failures andnewsoftwareacceptance. LongvalidationcontrollersmustrecordknownPIDs,checklocal-loopbackcontext up front,andretainactivejobstateuntilcleanupconfirmed. Counter86/62sources/next100-runcheckpoint100;388softwaretests;noactivejobs.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory.update(inventoried_at=now,combined_offline_demo=latest,offline_refresh_recovery=acceptance,singapore_issuance_health=s['singapore_issuance_health'])
    for row in inventory['datasets']:
        if row.get('source_id')=='SRC-LIVE-001':row.update(snapshot_count=61,raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],latest_prospective_summary=live,prospective_baseline_scored_outcomes=54285,prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'],learned_issuance_metadata=s['singapore_issuance_health'])
    dump(ROOT/'data/dataset_inventory.json',inventory)
    title='## 26 October 2026 UTC / copied notebook recovered with approved local loopback'
    body=('Instrumented120-second diagnosticpreservesstack/phase/PIDevidence:importsfinish,butexecutionstallsbeforekernelstartinWindowsasyncio_fallback_socketpair.accept. Automaticdeadlineendeddiagnostic;CANCELmarkerwaswrittenAFTERitsfinishedtimestampanddidnotcausestop. ConservativependingPIDstatewasretained;latercase-insensitiveauthorizedCIMcheckfound0ownedprocesses. Separateprespecifiedapproved-local-loopbacktrial runsUNCHANGEDfrozencopiedverifier successfullyin18.187seconds:realcopiedkernel,5codecellsincluding1diagnostic,1inlinePNG,0savederrors;sourcecells/notebook/payloadunchanged. Controller/kernelPythonfallback/nonloopbackguarddenials0;localRPCallowed. No install/modelinference/fitting/finalorprospective-targetread inrevalidation. NewREVALIDATION_ACCEPTANCE linksprior107install/app/13faultcases/107versionproofsbyhash;initialfailedreportsremainfailedandINCOMPLETEmarkerretainedundernewname. NewREADY/latestpointerselect451-filecopywithtransactionalexports;olderpackages/pointers preserved. Notphysicaloffline,newmachine,visible/manual/student/officialacceptance.388softwaretestsremainpassed;two distincttrials84->86,notperphase/cell. Wakeups57/source62/next100-runcheckpoint100/noactivejobs. Sourcecompliant18:41officialsnapshot61adds1040rollingpersistenceoutcomes:54285total/MAE4.911725spaces;1262newbaselineforecasts.1030newgenuinelearnedforecasts,9774total/9originsmetadatahealthy,unscoreduntil27Oct10:51UTC;loggedoriginsnotmatchedfinalcoverage. Nextcollectionafter'+nexttime+'. Resumeindependentvision/data/reportwork;do notrepeatready-packettestsforcounts.')
    for doc in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/IMPLEMENTATION_STATUS.md','docs/AI_ASSISTANCE_LOG.md']:append(doc,title,body)
    append('docs/UI_TEST_LOG.md',title,'ActualcopiedJupyterkernelexecutesunchangednotebook08plusdiagnosticcelland1PNGunderapprovedlocal-loopbackcontext. Copiedapp/failurecaseswereverifiedpreviouslyandnotreplayedhere. No visiblebrowser/manualdialog/student/newmachine/physicalofflineacceptance.')
    append('docs/COMBINED_OFFLINE_DEMO_GUIDE.md',title,'Latestpointer nowselects451-filecopywithnewREVALIDATION_ACCEPTANCE.json/READY.json. InitialCOMBINED_VALIDATION.jsonremainsfailedhistory;itsINCOMPLETEmarkerretainedasINCOMPLETE.initial_failed_build. Managedautomationmustpermitlocal-loopbacksocketsforJupyter;Pythonexternal/fallbackguardsstayactive. No newinstall/detectorreplay. Onlynotebook08included;10others/fulltrainingdata/basePythonabsent. Physical/manual/newmachine/student/officialacceptance remainopen.')
    append('docs/RESULT_EXPORTS_GUIDE.md',title,'New451-filecopiedpackageincludingtransactionalexports isnowsoftware-acceptedbyhash-linkedcomponentproofsandsuccessfulcorrected-contextJupytercheck. Previousfailuregatesremainhistoricalfailures;see reports/offline_refresh_recovery_latest.json. No power-loss/physical/manual/newmachineacceptance added.')
    append('docs/OFFLINE_REFRESH_EXPLAINED.md',title,'The laterdiagnosticlocalizedthestalltoWindowslocalasyncio socketcreationbeforekernelstart. Withauthorizedloopbackpermission,theunchangedcopiedverifierfinishedin18secondswith1plot;no dependencyreinstall/modelreplaywasneeded. Thelateracceptancerecordlinkstheearlierpassedcomponentsandpreservesoriginalfailures. Thisillustratesanexecution-contextissue,notimprovedmodelaccuracyorstudentmastery.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        if row['requirement_id'] in ['OFF-01','PKG-01']:
            row['actual_evidence']+=';reports/offline_refresh_recovery_latest.json';row['test_result']+=';correctedlocal-loopbackcontext:unchangedcopiedkernel/1PNG passes18.187s;451-filecopycompositeREADY,initialfailurespreserved'
            row['open_problems']='Selectedsoftwaredemo only;10othernotebooks/fulltrainingdata/basePythonabsent;physicaloffline/newmachine/visible/manual/student/officialacceptance pending'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(rows)
    dump(E/'checks.json',dict(checked_at=now,completed_trials=[DIAG,rid],counter_before=84,counter_after=86,wakeups_completed=57,unique_sources=62,software_tests=388,
        new_composite_READY=True,original_failures_preserved=True,payload_files=len(manifest['files']),payload_bytes=latest['bytes'],frozen_hashes_unchanged=frozen,
        actual_copied_kernel=True,inline_png_outputs=1,normal_python_guard_denials=0,execution_context=acceptance['execution_context'],live_snapshots=61,learned_forecasts=9774,learned_origins=9,
        learned_targets_decoded=False,learned_performance_evaluated=False,next_live_collection_not_before=nexttime,next100_run_checkpoint=100,active_jobs=[],physical_manual_newmachine_acceptance=False))
    print(json.dumps(dict(counter=86,sources=62,tests=388,copy_READY=True,package=latest['path'],next_collection=nexttime)))


if __name__=='__main__':main()
