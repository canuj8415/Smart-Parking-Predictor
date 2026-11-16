"""Dated report/group-audit handoff;metadata only,no new model/final scoring."""
import csv,json,shutil,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T190901Z'
PROJECT=ROOT/'reports/evidence_addendum_20261027'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,body):
    path=ROOT/p;text=path.read_text(encoding='utf-8');assert title not in text
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+body+'\n',encoding='utf-8')


def main():
    assert not (E/'checks.json').exists();now=datetime.now(timezone.utc).isoformat();s=read(ROOT/'data/automation_state.json')
    assert s['completed_recorded_runs_since_schedule']==len(set(s['completed_run_ids']))==88 and not s['active_training_jobs'] and not s['active_validation_jobs']
    group=read(ROOT/'models/pklot_remaining_group_audit.json');validation=read(E/'pdf_checks.json');build=read(PROJECT/'build.json');pdf=ROOT/build['pdf']
    assert validation['artifact_gate_passed'] and validation['pages']==7 and group['development_exposed']==group['consumed_final']==3 and group['newly_qualified_final_groups']==0
    assert digest(pdf)==build['pdf_sha256']==validation['pdf_sha256'] and digest(PROJECT/'report_inputs.json')==build['input_manifest_sha256']
    assert 'Ran 392 tests' in (E/'unit_tests_final.txt').read_text(encoding='utf-8-sig') and (E/'unit_tests_final.txt').read_text(encoding='utf-8-sig').rstrip().endswith('OK')
    for row in read(PROJECT/'report_inputs.json')['inputs']:assert digest(PROJECT/row['snapshot'])==row['sha256']
    for rid in [group['run_id'],validation['run_id']]:
        p=read(ROOT/'experiments/results'/rid/'protocol.json')
        for name,h in p['source_hashes'].items():assert digest(ROOT/name)==h,name
    frozen=read(ROOT/'experiments/evidence/HEARTBEAT-20261026T170900Z/checks.json')['frozen_hashes_unchanged']
    for name,h in frozen.items():assert digest(ROOT/name)==h,name
    for name,h in read(ROOT/'models/singapore_trend_development.json')['protected_hashes'].items():assert digest(ROOT/name)==h,name
    for name,h in read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')['implementation_hashes'].items():assert digest(ROOT/name)==h,name
    old_report=ROOT/'reports/technical_report_latest.json';shutil.copyfile(old_report,E/'earlier_technical_report_pointer.json')
    pointer=dict(kind='Dated seven-page evidence addendum;not replacement official final report',created_at=build['created_at'],pdf=build['pdf'],pdf_sha256=build['pdf_sha256'],project=build['project'],
        pages=7,source_snapshots=17,source_ids=62,software_tests=392,recorded_trials_at_input_freeze=87,artifact_validation_trial=validation['run_id'],group_audit_trial=group['run_id'],
        authored_content='reports/evidence_addendum_20261027/report_content.json',input_manifest='reports/evidence_addendum_20261027/report_inputs.json',
        artifact_gate_passed=True,all_pages_visually_reviewed=True,standalone_pdf_engine='ReportLab',no_new_model_or_final_evaluation=True,official_compliance_claimed=False,
        older_report_preserved=True,guide='docs/EVIDENCE_ADDENDUM_GUIDE.md')
    dump(ROOT/'reports/evidence_addendum_latest.json',pointer);dump(ROOT/'models/evidence_addendum_validation.json',validation)
    old=read(old_report);old['dated_evidence_addendum']=pointer;dump(old_report,old)
    live=read(ROOT/'data/processed/singapore_prospective/summary.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json')
    assert live['scores_total']==55367 and health['forecasts_logged']==10764 and health['global_origins']==10
    receipts=[json.loads(v) for v in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];raw=Path(live['snapshot_path']).resolve();receipt=next(r for r in reversed(receipts) if (ROOT/r['local_path']).resolve()==raw);assert digest(raw)==receipt['sha256']
    assert len(list((ROOT/'data/raw/singapore_live').glob('*.json')))==62;nexttime=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    s.update(last_updated_at=now,scheduled_wakeups_completed=s['scheduled_wakeups_completed']+1,evidence_addendum=pointer,prospective_live_summary=live,
        last_live_baseline_score=dict(outcomes=55367,mae_spaces=live['baseline_mae_spaces'],scope='Rolling persistence only,not learned/camera accuracy',coverage=live['forecast_coverage']))
    s['singapore_forecast_study'].update(learned_forecast_batches=10,learned_forecasts_logged=10764,learned_global_origins=10,learned_live_performance_evaluated=False)
    s['singapore_issuance_health'].update({k:health[k] for k in ['checked_at','forecasts_logged','batch_receipts','global_origins','unique_series','origins']});s['singapore_issuance_health'].update(metadata_status='healthy',status='healthy',raw_files_hashed_once=12,semantic_context_verified=False,performance_evaluated=False)
    s['next_actions']=[
        'TOP PRIORITY nextwake: collectonce AFTER'+nexttime+' via scripts/collect_singapore_study.py;30minuteplan/minimum1min.19:39wakeis~3.5minEARLY:do usefulindependentpreparationuntilactualdue,noskip/backdate/earlypoll. Then routinehealth WITHOUT --record-trial.62snapshots/10764genuinelearnedforecasts/10originsmetadatahealthy;no learnedtargetscoring.',
        'FrozenSGfinal closeduntil27October10:51UTC(16:21IST). No refit/frozenmethodchanges/backfill/interimtargetdecode. Atclosureexistingonce-onlyscorer/globalclaim. Rollingpersistence55367matches/MAE4.861090541297163spaces isseparate;10loggedoriginsnotmatchedfinalcoverage.',
        'Freshvisionadmissionpriority:earlier6provisionalPKLotgroupsnow3development-exposed/3consumedfinal;newauditestablishes0newqualifiedfinalgroups. ThisdoesNOTproveallpossiblefuturedataexhausted. Seekgenuinelynewlicensedlabelledcamera/session/dategroupsandreservebeforechanged-method evaluation;do notrenameframesfromuseddates. No ORB/crop/thresholdgrids onexposedcohorts. NDISPark/CNRcontentrightsunqualified;HighwayDrivewholefinalunopened.',
        'New7-pagePDFaddendum isverifiedwith17hash-boundinput snapshots and7renderedpages;olderv003PDF/TeX preserved. Itseparatesconditionalregions,failedoccupancy/trafficgates,Birminghamfinal,SGdevelopment/pendingfuture,andsoftwareacceptance. Do notclaimnewmodelaccuracy,officialrubriccompliance,studentmasteryorfullprojectcompletion. Counter88/392softwaretests/62sources/next100-runcheckpoint100;noactivejobs.',
        'Independentnextusefulwork:publisher-backedfreshvisiondataqualification OR updatepresentation/studentexplanationmaterials fromdatedaddendum. Current451-filecopieddemosoftwareREADYwith13faulttests/107versions/actualJupyter;do notrepeatidenticalpackagechecksforcounts. Physicaloffline/newmachine/visiblemanualdialog/student/officialacceptance remainopen.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory.update(inventoried_at=now,pklot_remaining_group_audit=group,evidence_addendum=pointer,singapore_issuance_health=s['singapore_issuance_health'])
    for row in inventory['datasets']:
        if row.get('source_id')=='SRC-DS-001':row['current_provisional_group_role_audit']=group
        if row.get('source_id')=='SRC-LIVE-001':row.update(snapshot_count=62,raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],latest_prospective_summary=live,prospective_baseline_scored_outcomes=55367,prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'],learned_issuance_metadata=s['singapore_issuance_health'])
    dump(ROOT/'data/dataset_inventory.json',inventory)
    title='## 27 October 2026 IST / current group-role audit and seven-page evidence addendum'
    body=('Metadata-onlyauditreconcilesallsixearlierprovisionalPKLotgroups:3development-exposed/3consumedfinal/0unaccounted/0newqualifiedfinalgroups. Claimstatusconsumeswholecamera/dateeveniffailed;frozenunopenedreservationflagsdonotoverrideclaims. No pixels/XMLsemantics/archivebodies/modelcalls. Scopeonlyearlier6groups,notproofnofuturedataexists. Fournewsyntheticgroup-identity/claimtests;full392softwaretestspass. Createdseparate7-pagePDFaddendumwith17hash-boundsource snapshots,62sourceIDs,2saved-metriccharts;all7renderedpagesvisuallyreviewed,0out-of-margincharacters,requiredmetrics/pending/failuretextchecks pass. Itpreservesconditionalregion0.910vsresearchCNN0.803limits,failedrainyPUCPR13/14retention,realtraffic113/153maskadmissionfailure,Birminghamfinal31.72vs39.07MAE,andSGdevelopment6.310vs6.958withprospectiveperformanceunscored. Earlier12-pagev003PDF/TeX unchanged;newdocumentisanaddendum,notofficialsubmission. FirstauthoringattemptlackedmatplotlibinbundledPDFruntime;source/errorretained,chartsdelegatedtoexistingprojectruntimewithoutinstallingpackages. Internalrepairnotadditionaltrial. Two completedtrials86->88:updated-roleauditandfinalartifactQA;notperpage/hash/test/frame. Wakeups58/source62/next100-runcheckpoint100/noactivejobs.62officialSGsnapshots;19:12collectionadds1082rollingpersistenceoutcomes:55367total/MAE4.861091spaces;1091newbaselineforecasts.990newgenuinelearnedforecasts,10764total/10originsmetadatahealthy;nolearnedtargetmatching/error/coverageuntil27Oct10:51UTC. Nextcollectionafter'+nexttime+'. NewPDFfreezes87trialsbeforeitsownQA;currentledger88. Rights/independentfreshvisionlabels andphysical/manual/newmachine/student/universityacceptance remainopen.')
    for doc in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/IMPLEMENTATION_STATUS.md','docs/AI_ASSISTANCE_LOG.md']:append(doc,title,body)
    append('docs/UI_TEST_LOG.md',title,'All7actualPDFpagePNGsreviewed:legibletables/plots,consistentheaders/footers,noclipping/overlap. PDFtextboundschecks pass. No newvisibleapp/browser/native-dialog/student/physicaloffline/newmachineacceptance.')
    source=ROOT/'data/source_manifest.csv'
    with source.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==len({r['source_id'] for r in sources})==62
    for row in sources:
        if row['source_id']=='SRC-DS-001':row['used_by']+=';'+group['run_id']+' metadata-onlygroup-roleaudit';row['permission']='Attributed local academic use under recorded publisher CC BY4.0;earlier No data use yet text was an initial-discovery status placeholder,not a licence restriction'
    with source.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    append('docs/SOURCE_REGISTRY.md',title,'62permanentIDsunchanged. Metadata-onlyreconciliationusesexistingmanifests/durableclaims,noimagecontentornewexternalacquisition. SRC-DS-001masterpermissionfieldcorrectsstaleinitial-discovery No data use yet placeholder;recordedCCBY4.0licence/actualpastuse unchanged. FrozenreportCSVsnapshotremainsexactasatinputfreeze;thismastercleanupislatersourcedmetadata,norewriteofearlierrecords.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        if row['requirement_id']=='DOC-01':row['actual_evidence']+=';reports/evidence_addendum_latest.json;docs/EVIDENCE_ADDENDUM_GUIDE.md';row['test_result']+=';27OctIST7-pageaddendum/17frozeninputs/7renderedpages passes,olderPDF/TeX preserved'
        if row['requirement_id']=='DATA-01':row['actual_evidence']+=';models/pklot_remaining_group_audit.json';row['open_problems']+=';Earlier6provisionalgroupsnow3development/3consumed;nonewqualifiedfinalgroupsfromthisaudit'
        if row['requirement_id']=='QA-02':row['test_result']+=';392softwaretests;4newwhole-groupclaimfixtures andreportartifactQA'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(rows)
    dump(E/'checks.json',dict(checked_at=now,completed_trials=[group['run_id'],validation['run_id']],counter_before=86,counter_after=88,wakeups_completed=58,unique_sources=62,software_tests=392,
        report=pointer,metadata_only_group_roles=dict(development=3,consumed=3,newly_qualified=0),frozen_hashes_unchanged=frozen,old_v003_pointer_preserved=True,
        source_csv_master_placeholder_corrected_after_report_freeze=True,live_snapshots=62,learned_forecasts=10764,learned_origins=10,learned_targets_decoded=False,learned_performance_evaluated=False,
        next_live_collection_not_before=nexttime,next100_run_checkpoint=100,active_jobs=[],official_compliance_claimed=False))
    print(json.dumps(dict(counter=88,sources=62,tests=392,pdf=build['pdf'],next_collection=nexttime)))


if __name__=='__main__':main()
