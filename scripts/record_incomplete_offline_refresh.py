"""Record partial offline acceptance honestly;never replace the last READY copy."""
import csv,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T180901Z'
FIRST='COMBINED-DEMO-20261026T181231761064Z';SECOND='COMBINED-DEMO-20261026T181455268229Z'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,body):
    path=ROOT/p;text=path.read_text(encoding='utf-8');assert title not in text
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+body+'\n',encoding='utf-8')


def main():
    assert not (E/'checks.json').exists()
    now=datetime.now(timezone.utc).isoformat();s=read(ROOT/'data/automation_state.json');component_pointer=read(E/'component_run_pointer.json');component=component_pointer['run_id']
    assert s['completed_recorded_runs_since_schedule']==len(set(s['completed_run_ids']))==84 and s['completed_run_ids'][-3:]==[FIRST,SECOND,component]
    assert not s['active_training_jobs'] and not s['active_validation_jobs']
    first=read(ROOT/'experiments/results'/FIRST/'run.json');second=read(ROOT/'experiments/results'/SECOND/'run.json');last=read(ROOT/'experiments/results'/component/'run.json')
    assert not first['combined_demo_gate_passed'] and not second['combined_demo_gate_passed'] and last['component_gate_passed'] and not last['whole_package_ready']
    assert second['checks']==dict(install=dict(returncode=0),app=dict(returncode=0)) and last['checks']['copied_transaction_tests']['synthetic_transaction_tests']==13
    package=ROOT/second['package'];assert (package/'INCOMPLETE').exists() and not (package/'READY.json').exists()
    assert (ROOT/first['package']/'INCOMPLETE').exists() and not (ROOT/first['package']/'READY.json').exists()
    assert all(digest(package/p['path'])==p['sha256'] for p in second['payload'])
    for f,h in {**second['source_hashes'],**second['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert 'Ran 388 tests' in tests and tests.rstrip().endswith('OK')
    process_audit=read(E/'owned_processes_after_timeout.json');assert process_audit['matching_count']==0
    frozen=read(ROOT/'experiments/evidence/HEARTBEAT-20261026T170900Z/checks.json')['frozen_hashes_unchanged']
    for f,h in frozen.items():assert digest(ROOT/f)==h,f
    for f,h in read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')['implementation_hashes'].items():assert digest(ROOT/f)==h,f
    previous=read(ROOT/'reports/demo_package_latest.json');assert previous['run_id']==second['previous_demo']
    assert read(ROOT/'reports/offline_demo_latest.json')['run_id']==previous['run_id']
    assert digest(ROOT/previous['path']/'BUNDLE_MANIFEST.json')==previous['manifest_sha256']
    dump(E/'retained_latest_pointer.json',previous)
    card=dict(status='INCOMPLETE;do not promote',run_ids=[FIRST,SECOND,component],package=second['package'],payload_files=second['payload_files'],payload_bytes=second['payload_bytes'],
        reports={rid:'experiments/results/'+rid+'/run.json' for rid in [FIRST,SECOND,component]},initial_bootstrap_failed=True,initial_bootstrap_cause_confirmed=False,
        revised_bootstrap_passed=True,new_local107versions_verified=True,app_check_passed=True,synthetic_transaction_tests_passed=13,
        jupyter_check_completed=False,jupyter_failure=second['failure'],whole_package_ready=False,latest_verified_package_retained=previous['run_id'],
        failed_copies_preserved=True,owned_process_inventory=process_audit,software_tests_passed=388,cached_snapshot_selection=second['cached_live_selection'],
        learned_target_json_decoded=False,physical_newmachine_manual_acceptance=False,student_explanation_guide='docs/OFFLINE_REFRESH_EXPLAINED.md')
    dump(ROOT/'models/offline_refresh_incomplete.json',card);dump(ROOT/'reports/offline_refresh_latest_attempt.json',card)
    live=read(ROOT/'data/processed/singapore_prospective/summary.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json')
    assert live['scores_total']==53245 and health['forecasts_logged']==8744 and health['global_origins']==8
    receipts=[json.loads(v) for v in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];raw=Path(live['snapshot_path']).resolve()
    receipt=next(r for r in reversed(receipts) if (ROOT/r['local_path']).resolve()==raw);assert digest(raw)==receipt['sha256'];assert len(list((ROOT/'data/raw/singapore_live').glob('*.json')))==60
    nexttime=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    s.update(last_updated_at=now,scheduled_wakeups_completed=s['scheduled_wakeups_completed']+1,offline_refresh_attempts=card,prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=53245,mae_spaces=live['baseline_mae_spaces'],scope='Rolling persistence only;not learned/camera accuracy',coverage=live['forecast_coverage']))
    s['singapore_forecast_study'].update(learned_forecast_batches=8,learned_forecasts_logged=8744,learned_global_origins=8,learned_live_performance_evaluated=False)
    s['singapore_issuance_health'].update({k:health[k] for k in ['checked_at','forecasts_logged','batch_receipts','global_origins','unique_series','origins']});s['singapore_issuance_health'].update(metadata_status='healthy',status='healthy',raw_files_hashed_once=10,semantic_context_verified=False,performance_evaluated=False)
    s['next_actions']=[
        'TOP PRIORITY nextwake: collectonce AFTER'+nexttime+' using scripts/collect_singapore_study.py;30minuteplan/minimum1min. Ifearlydoindependentworkuntildue. Then routinehealth WITHOUT --record-trial.60snapshots/8744genuinelearnedforecasts/8originsmetadatahealthy;no learnedtargetscoring.8loggedoriginsisnotmatchedfinalcoverage.',
        'FrozenSGfinal closeduntil27October10:51UTC(16:21IST). No refit/frozenmethodchanges/backfill/interimtargetdecode. Atclosureexistingonce-onlyscorer/globalclaim. Rollingpersistence53245matches/MAE4.983566532068739spaces isseparate;missingtargets unscored.',
        'Offline refresh remainsINCOMPLETE in '+SECOND+' despitefresh107install/app/13faultcases/versionchecks passing. Jupytertimedout;timeoutcleanupwaitalsoexpired. Case-insensitiveCIMinventory18:29UTCfound0matchingownedprocesses;noneforciblyterminated. Keepoldverified '+previous['run_id']+' selected;no READYpromotion. Bothfailedcopies/rawlogs preserved.',
        'Nextindependentstep:diagnoseJupyterusingEXISTINGfreshcopyvenv,no reinstall/detectorreplay. Preserve451payload/manifest/failedoutputs. CreateNEWbounded diagnosticcontroller/output undercopy outputs withphase markers/faulthandler,explicitlocalTEMP/Jupyterpaths andnewprotocol. RecordexactchildPIDs/cleanupresults;neverclearactivejobsuntilownedchildrenconfirmedended. No pendingSGraworconsumedimage/finaldata;old02:30UTCcachedfeedonly. Do notrepeatblindfullbuilds.',
        'Then resume genuinely distinctTRAIN-onlyregion/background hypothesis orqualifiedfreshpubliccamera/negative/regionlabels;no ORB/threshold/cropgrids onexposedcohorts. NDISPark/CNRcontentrights unqualified;HighwayDrivewholefinalunopened. Refreshreport/presentation/studentexplanations withoutclaimingmastery. Counter84/62sources/next100-runcheckpoint100;388softwaretests;noactivejobs.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory.update(inventoried_at=now,offline_refresh_attempts=card,singapore_issuance_health=s['singapore_issuance_health'])
    for row in inventory['datasets']:
        if row.get('source_id')=='SRC-LIVE-001':row.update(snapshot_count=60,raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],latest_prospective_summary=live,prospective_baseline_scored_outcomes=53245,prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'],learned_issuance_metadata=s['singapore_issuance_health'])
    dump(ROOT/'data/dataset_inventory.json',inventory)
    title='## 26 October 2026 UTC / offline refresh remains incomplete after isolated bootstrap repair'
    body=('A new451-file selected payload preserves an exact prior02:30UTCofficial snapshot whose receipt/provider predate reserved10:00UTCforecast origins;selector hashes opaque bytes,does not decode pendingtargets. Initialfreshcopyfailedensurepipbootstrap;originalchilddetailswerenotcaptured,causeunconfirmed. Revisedinstallerusesexplicitisolatedbootstrap,localTEMP/TMP,capturedlogs,no pipcache andexistingno-index/hashlock. Secondcopyfreshinstallandactualhiddenappchecks pass;Jupyterchecktimesout,andcleanupwaitalsoexpires. No completedkernel/notebookacceptance;INCOMPLETE remains,READYabsent. Independentdeferredcomponent5.094seconds passes13synthetictransactioncases,107exactversion/localdistributionchecks andexisting-venvoverwrite refusal. These fixtures/metadata are not model accuracy. CurrentpackageNOTpromoted;earlierverifiedpointer unchanged. Scopedcase-insensitiveCIMinventoryfound0matchingpackageprocessesat18:29UTC;noneforciblyterminated. DefaultCIMreadwasOS-denied;authorizedscoped elevatedverification succeeded,noapproval-review rejection. All388softwaretestspass(sixnewselector/environmentfixtures). Three completedtrials81->84:bootstrapfailure,partialbuild/Jupyterfailure,distinctdeferredcomponent;notperwheel/test/frame. Wakeups56/source62/next100-runcheckpoint100/noactivejobs. Originalweights/claims/frozenSGmethods unchanged;no finalreplay.60officialSGsnapshots;1082newrollingpersistenceoutcomes,53245total/MAE4.983567spaces;1141newbaselineforecasts.1001newgenuinelearnedforecasts,8744total/8originsmetadatahealthy,unscoreduntil27Oct10:51UTC;8loggedoriginsnotfinalmatchedcoverage. Nextcollectionafter'+nexttime+'. Nextdiagnosekernelinexistingfreshenvwithnewboundedcontroller/phase+PIDevidence;do not reinstall/repeatdetectors. Studentguide:OFFLINE_REFRESH_EXPLAINED.md;mastery/physical/newmachine/manual/officialacceptance remainunassessed.')
    for doc in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/IMPLEMENTATION_STATUS.md','docs/AI_ASSISTANCE_LOG.md']:append(doc,title,body)
    append('docs/UI_TEST_LOG.md',title,'Secondfreshcopiedhiddenappcheckpassesexistingdetector/analysis-preview/archivedforecastexport/cachedlive/SVD/progress/video softwareflows. Newcopiedkernelcheckdidnotfinish;no notebookbrowser/manual/student/physical/newmachineacceptance.13deferredsynthetictransactionchecks passseparately. OlderREADYpackage remainsselected.')
    append('docs/COMBINED_OFFLINE_DEMO_GUIDE.md',title,'Currentlatestpointerintentionally remainsoldverifiedpackage. New451-file refreshedcopyinstall/app/exportfaultchecks pass,butJupytertimeoutleavesitINCOMPLETE;do not useasREADYreplacement. See reports/offline_refresh_latest_attempt.json. Preservefailedoutputsanddiagnoseexistingfreshvenvwithoutreinstall. Tenothernotebooks/fulltrainingdata/basePythonareabsentfromnewselectedpayload;physical/manual/newmachine/studentacceptance stillopen.')
    append('docs/RESULT_EXPORTS_GUIDE.md',title,'Exportfixpasses13syntheticfailure/integritychecksinsideanew107-packagecopy,andactualcopiedappflows pass. ThewholeofflinecopyisNOTREADYbecauseitsJupyterchecktimedout;earlierverifiedpackage remainsselected. Do not claimthatolderpackagecontainsnewpatch. See reports/offline_refresh_latest_attempt.json.')
    source=ROOT/'data/source_manifest.csv'
    with source.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==len({x['source_id'] for x in sources})==62
    for row in sources:
        if row['source_id'] in second['source_ids']:row['used_by']+=';'+SECOND+' localpartialsoftwarecopy,notnewaccuracy'
    with source.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        if row['requirement_id'] in ['OFF-01','PKG-01']:
            row['actual_evidence']+=';reports/offline_refresh_latest_attempt.json';row['test_result']+=';26Octnew451-filecopy107install/app/13exportfaultcases pass,butJupytertimeout leavesINCOMPLETE;oldREADYretained'
            row['open_problems']+=';Diagnosecopiedkernelwithoutreinstall;newrefreshNOTREADY;physical/manual/newmachine/studentacceptance open'
        if row['requirement_id']=='QA-02':row['test_result']+=';26Oct388softwaretests;protected-snapshot/bootstrapfixtures andpartialfresh-runtimeevidence'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(rows)
    dump(E/'checks.json',dict(checked_at=now,completed_trials=[FIRST,SECOND,component],counter_before=81,counter_after=84,wakeups_completed=56,unique_sources=62,software_tests=388,
        refreshed_package_ready=False,old_verified_pointer_retained=previous,failed_copies_preserved=True,component_gate_passed=True,owned_processes_remaining=0,
        frozen_hashes_unchanged=frozen,live_snapshots=60,learned_forecasts=8744,learned_origins=8,learned_targets_decoded=False,learned_performance_evaluated=False,
        next_live_collection_not_before=nexttime,next100_run_checkpoint=100,active_jobs=[],manual_newmachine_physicaloffline_acceptance=False))
    print(json.dumps(dict(counter=84,sources=62,tests=388,refreshed_package_ready=False,old_verified_package=previous['run_id'],next_collection=nexttime)))


if __name__=='__main__':main()
