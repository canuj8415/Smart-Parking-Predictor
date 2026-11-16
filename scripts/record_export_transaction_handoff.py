"""Save the once-only handoff for transactional export validation and live cadence."""
import csv,json,shutil,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T173900Z'
RUN='FORECAST-DISPLAY-EXPORT-20261026T174434533261Z'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,body):
    path=ROOT/p;text=path.read_text(encoding='utf-8');assert title not in text
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+body+'\n',encoding='utf-8')


def main():
    assert not (E/'checks.json').exists(),'Dated work already registered'
    now=datetime.now(timezone.utc).isoformat();s=read(ROOT/'data/automation_state.json');r=read(ROOT/'experiments/results'/RUN/'run.json')
    assert s['completed_recorded_runs_since_schedule']==len(set(s['completed_run_ids']))==81 and s['completed_run_ids'][-1]==RUN
    assert not s['active_training_jobs'] and not s['active_validation_jobs']
    assert r['transactional_export_gate_passed'] and r['synthetic_transaction_tests']==13 and r['normal_forbidden_attempts']==0
    assert len(r['negative_control'])==1 and len(r['reports'])==2
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert 'Ran 382 tests' in tests and tests.rstrip().endswith('OK')
    for f,h in {**r['source_hashes'],**r['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    trend=read(ROOT/'models/singapore_trend_development.json')
    for f,h in trend['protected_hashes'].items():assert digest(ROOT/f)==h,f
    scoring=read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')
    for f,h in scoring['implementation_hashes'].items():assert digest(ROOT/f)==h,f
    frozen=read(ROOT/'experiments/evidence/HEARTBEAT-20261026T170900Z/checks.json')['frozen_hashes_unchanged']
    for f,h in frozen.items():assert digest(ROOT/f)==h,f
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    summary=read(ROOT/'data/processed/singapore_prospective/summary.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json');issuance=read(ROOT/'reports/singapore_issuance_latest.json')
    assert health['status']=='healthy' and health['forecasts_logged']==7743 and health['global_origins']==7 and issuance['study_issuance']['issued']==1113
    assert summary['scores_added']==1178 and summary['scores_total']==52163
    snapshot=Path(summary['snapshot_path']).resolve();receipt=next(row for row in reversed(receipts) if ROOT/row['local_path']==snapshot)
    assert digest(snapshot)==receipt['sha256'];assert len(list((ROOT/'data/raw/singapore_live').glob('*.json')))==59
    # Read only acquired batch/receipt metadata via the established health report;
    # no semantic origin/target JSON is opened in this handoff.
    nexttime=(datetime.fromisoformat(summary['checked_at'])+timedelta(minutes=30)).isoformat()
    copied=[]
    for report in r['reports']:
        source=(ROOT/report['export']).resolve();assert source.is_relative_to((ROOT/'outputs/forecast_display_checks'/RUN).resolve())
        target=E/'native_exports'/source.name;assert not target.exists()
        shutil.copytree(source,target)
        manifest=read(target/'export_metadata.json');assert manifest['complete'] and all(digest(target/p)==h for p,h in manifest['files'].items())
        for path in target.iterdir():assert digest(path)==digest(source/path.name)
        copied.append(dict(folder=target.relative_to(ROOT).as_posix(),files={p.name:digest(p) for p in target.iterdir()},selected_windows=report['selected_windows'],method=report['method']))
    card=dict(run_id=RUN,report='experiments/results/'+RUN+'/run.json',report_sha256=digest(ROOT/'experiments/results'/RUN/'run.json'),
        guide='docs/RESULT_EXPORTS_GUIDE.md',integration_gate_passed=True,synthetic_transaction_tests=13,software_tests_passed=382,
        archived_real_reports=2,selected_windows=[8,75],normal_forbidden_attempts=0,negative_raw_probe_blocked=True,
        automatic_analysis_or_forecast_recomputation=False,accuracy_evaluated=False,original_models_and_consumed_claims_unchanged=True,
        old_offline_packages_updated=False,physical_offline_or_manual_UI=False,power_loss_recovery_validated=False,exports=copied)
    dump(ROOT/'models/export_transaction_validation.json',card);dump(ROOT/'reports/export_transactions_latest.json',card)
    s['scheduled_wakeups_completed']+=1;s['last_updated_at']=now;s['export_transaction_validation']=card
    s['forecast_display_exports']=dict(run_id=RUN,integration_gate_passed=True,scientific_accuracy_evaluated=False,report=card['report'],guide=card['guide'],visible_or_manual_UI_validated=False)
    s['prospective_live_summary']=summary;s['last_live_baseline_score']=dict(outcomes=summary['scores_total'],mae_spaces=summary['baseline_mae_spaces'],scope='Rolling persistence only;distinct from future learned study;no camera/neural accuracy',coverage=summary['forecast_coverage'])
    s['singapore_forecast_study'].update(learned_forecast_batches=7,learned_forecasts_logged=7743,learned_global_origins=7,learned_live_performance_evaluated=False)
    s['singapore_issuance_health'].update({k:health[k] for k in ['checked_at','forecasts_logged','batch_receipts','global_origins','unique_series','origins']})
    s['singapore_issuance_health'].update(metadata_status='healthy',status='healthy',raw_files_hashed_once=9,semantic_context_verified=False,performance_evaluated=False)
    s['trigger_handling_note']='17:39trigger arrived before30minutehistorydue;independent export review first,actualcollection17:40:12UTC. One completed softwareintegrationtrial80->81,not perunitcase/report/window/forecast. Earlier14:43->17:09gap remainsmissing.'
    s['next_actions']=[
        'TOP PRIORITY nextwake: collectonce AFTER'+nexttime+' via scripts/collect_singapore_study.py;30minuteplan/minimum1min. Ifearly,doindependentworkuntildue. Latest59officialsnapshots;7743genuinelearnedforecasts/7origins metadatahealthy,1113newat17:40. Then routinecheck_singapore_issuance_health.py WITHOUT --record-trial. No learnedtargetscoring.',
        'FrozenSGlearnedfinal closeduntil27October10:51UTC(16:21IST). No refit/frozenmethodchanges/backdatedissuance/partialbatchrepair/interimtargetdecode. Atclosureexistingonce-onlyscorerandglobalclaim;missingtargets unscored. Rollingbaseline52163matches/MAE5.055690815328873spaces isseparate.',
        'Transactionalexportfixverifiedinworkingsource:13syntheticfault/integritytests plusactualhiddenTk2archivedforecastviews pass;382fullsoftwaretests. PriorofflinepackagesareimmutableDATEDsnapshotsandDO NOT containthispatch. Nextindependentstep:buildNEWversionedofflinepayloadfromcurrentqualifiedsource andrunhash/no-index/guardedarchived-exportvalidation;neveroverwriteoldpackageoropenconsumedrawholdoutsforofflineclaims.',
        'Visionstillunfinished:failedORBviewcheck1/16matchingaccepts,failedtrafficmaskadmission andsource018headtransferpreserved. No threshold/crop/descriptorgrids onreused cohorts. NDISPark/CNRindividualcontentsrights unqualified;noimage/annotationuse. HighwayDrivewholefinalunopened/nofinalcontroller. DistinctTRAIN-onlystaticbackgroundhypothesisrequiresprespecifiedgates/freshfinalgroups.',
        'Nativevisible/manualdialog/newmachine/physicalofflinerehearsal andstudentexplanations/reportrefresh remainopen;missinguniversitydocsblockofficialcomplianceonly. Counter81,62sources,nextseparate100-runlivecheckpoint100;noactivejobs.'
    ]
    dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['export_transaction_validation']=card;inventory['singapore_issuance_health']=s['singapore_issuance_health']
    for dataset in inventory['datasets']:
        if dataset.get('source_id')=='SRC-LIVE-001':
            dataset['prior_snapshot_counts']={k:dataset.get(k) for k in ['raw_path','provider_timestamp','car_parks','observations','raw_lot_records']}
            dataset.update(snapshot_count=59,prospective_summary='data/processed/singapore_prospective/summary.json',latest_prospective_summary=summary,
                prospective_baseline_scored_outcomes=52163,prospective_baseline_mae_spaces=summary['baseline_mae_spaces'],forecast_target_coverage=summary['forecast_coverage'],
                learned_issuance_metadata=s['singapore_issuance_health'],raw_path=receipt['local_path'],provider_timestamp=receipt.get('provider_timestamp'),
                car_parks=None,observations=None,raw_lot_records=None,latest_counts_reaudited_in_handoff=False,
                count_scope='Current feed validated by existing collector;exact current row/carpark counts not re-decoded during metadata-only handoff. Prior dated inventory counts retained separately.')
    dump(ROOT/'data/dataset_inventory.json',inventory)
    body='Fixed concretepartial-exportbugs:injectedimageinterruptionleftpartialoverlay,unsupportedJSONleftorphanPNG,andNaNwaspreviouslypublished. Originalsource/reproductionretained. Imageandarchivedforecast exports nowpreflightstrictfiniteJSON/vector-countagreement,writeownsame-parentstaging,verifyPNGandpayloadhashes,publishcompletedirectorybyrename,andcleanonlyownedfilesonhandledfailure/cancellation. Existingexportsneverreplaced;previewhasseparatehash. Thirteensyntheticfault/integritycases pass;actualhiddenTkexports8original/75later-datearchivedwindows retainmethod/CSV/JSON/plot/provenance. Zeroforbiddennormalraw/processed/split/networkattempts;oneexplicitrawprobe denied. Actuallater-datePNGvisuallyreviewed. One10.070secondcompletedintegrationtrial80->81;notperfixture/window/test. Full382softwaretestspass. No model/accuracy/finalrescore/rawholdoutaccess,originalweights/frozenSGmethods/consumedclaims unchanged. Oldofflinepackagespreserveddonotcontainpatch;no power-loss/manualUI/newmachine/physicalofflineclaim. Wakeups55/source62/next100-runcheckpoint100/noactivejobs. Source-compliant17:40UTCofficialsnapshot59adds1178previouslyfrozenpersistenceoutcomes:52163total/MAE5.055691spaces;1219newbaselineforecasts. Learned1113newgenuinepre-targetforecasts,7743total/7originsmetadatahealthy;unscoreduntil27Oct10:51UTC. Nextcollectionafter'+nexttime+'. Earliergapsremainmissing. Guide:RESULT_EXPORTS_GUIDE.md;exactprotocol:'+RUN+'.'
    for path in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md']:append(path,'## 26 October 2026 / complete export transactions and resumed issuance',body)
    append('docs/IMPLEMENTATION_STATUS.md','## 26 October: transactional result saving',
        'Workingsourcefixverified:handledsavefailuresdonotpublishincompleteanalysis/forecastfolders;priorresultspreserved,strictJSON/countvalidationandcompletepayloadhashes.13syntheticfaultcasesand2actualhiddenTkarchivedforecastreportexports pass;382softwaretests. No newmodelaccuracy/manualUI/physicaloffline/power-lossclaim. Existingofflinepackagesremainolderdatedsnapshots;newpayloadvalidationnext. See RESULT_EXPORTS_GUIDE.md and models/export_transaction_validation.json.')
    append('docs/UI_TEST_LOG.md','## 26 October 2026 / hidden app export transaction regression',
        'ActualhiddenTkappdisplaysandsavesbotharchivedforecastmethods(8and75selectedwindows);legends/text/CSV/JSON/checksums andstale-selectionclearingpass. Controlleddirectorydialogpatchused,novisiblemanualdialogcontrol. Actualexportedlater-datePNGvisuallyinspected:title/axes/legendlegible.13syntheticfailure/cancellation/integritycasesseparatefromrealarchiveddisplay. No manualbrowser/student/newmachine/physicalofflineacceptance.')
    append('docs/COMBINED_OFFLINE_DEMO_GUIDE.md','## 26 October: newer working-source export fix',
        'Thetransactionalexportfixand382-testregressionaredatedAFTERthisoldercombinedpackage. Its424payloadfilesandoriginalbytesremainunchanged;itdoesnotyetcontainthenewsourcepatch. Buildaseparatenewversionedpayloadandvalidatebeforeclaimingupdatedofflinecoverage. Neverreopenconsumedrawholdoutsforsmokechecks;usearchivedoutputs/syntheticfixtures. See RESULT_EXPORTS_GUIDE.md.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id']=='QA-02':row['actual_evidence']+=';models/export_transaction_validation.json;docs/RESULT_EXPORTS_GUIDE.md';row['test_result']+=';26Oct382softwaretests;13syntheticexportfault/integritycases plus2actualhiddenTkarchivedexports pass'
        if row['requirement_id'] in ['OFF-01','PKG-01']:row['open_problems']+=';26Octtransactionalexportpatchonlyinworkingsource;olderofflinepayloadnotyetrefreshed'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    sourcefile=ROOT/'data/source_manifest.csv'
    with sourcefile.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);sourcefields=reader.fieldnames;sources=list(reader)
    assert len(sources)==len({row['source_id'] for row in sources})==62
    for source in sources:
        if source['source_id']=='SRC-DS-003':source['used_by']+=';'+RUN+' archived display/export only,no raw data reads or rescoring'
    with sourcefile.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=sourcefields);writer.writeheader();writer.writerows(sources)
    dump(E/'checks.json',dict(checked_at=now,run_id=RUN,counter_before=80,counter_after=81,wakeups_completed=55,unique_sources=62,full_software_tests=382,synthetic_transaction_cases=13,actual_hidden_Tk_archived_exports=2,archived_windows=[8,75],normal_forbidden_attempts=0,negative_raw_probe_blocked=True,production_models_frozen_methods_consumed_claims_unchanged=True,live_snapshot_count=59,live_raw_sha256_verified=receipt['sha256'],rolling_persistence_outcomes=52163,rolling_persistence_mae_spaces=summary['baseline_mae_spaces'],learned_forecasts=7743,learned_origins=7,learned_target_semantics_decoded=False,learned_performance_evaluated=False,next_live_collection_not_before=nexttime,next100_run_live_checkpoint=100,active_jobs=[],old_offline_payload_updated=False,manual_or_physical_offline_acceptance=False,power_loss_recovery_tested=False,exports=copied))
    print(json.dumps(dict(counter=81,wakeups=55,tests=382,learned_forecasts=7743,learned_origins=7,next_collection=nexttime)))


if __name__=='__main__':main()
