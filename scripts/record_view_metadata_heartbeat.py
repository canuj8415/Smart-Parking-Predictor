"""Dated once-only registration of real development failure and source integrity."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T170900Z'
VIEW='VIEW-COMPATIBILITY-20261026T172503270481Z'
ND='NDISPARK-METADATA-20261026T172640352090Z'
RAW=ROOT/'data/raw/ndispark_official'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,body):
    path=ROOT/p;text=path.read_text(encoding='utf-8')
    assert title not in text
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+body.strip()+'\n',encoding='utf-8')
def csv_read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);return r.fieldnames,list(r)
def csv_write(path,fields,rows):
    quoting=csv.QUOTE_ALL if Path(path).name=='REQUIREMENTS.csv' else csv.QUOTE_MINIMAL
    with Path(path).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,quoting=quoting);w.writeheader();w.writerows(rows)


def main():
    assert not (E/'checks.json').exists(),'Dated work already registered'
    now=datetime.now(timezone.utc).isoformat();statepath=ROOT/'data/automation_state.json';s=read(statepath)
    assert len(set(s['completed_run_ids']))==s['completed_recorded_runs_since_schedule']==78
    assert not s['active_training_jobs'] and not s['active_validation_jobs']
    logs=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert 'Ran 369 tests' in logs and logs.rstrip().endswith('OK')
    results={i:read(ROOT/'experiments/results'/i/'run.json') for i in [VIEW,ND]}
    for i,r in results.items():
        folder=ROOT/'experiments/results'/i;p=read(folder/'protocol.json');assert digest(folder/'protocol.json')==r['protocol_sha256']
        for f,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        assert r.get('final_images_opened',0)==0 and r.get('final_annotations_opened',0)==0 and not r['production_promoted']
    assert not results[VIEW]['development_gate_passed'] and results[ND]['metadata_validation_passed'] and not results[ND]['image_admission']
    rows=read(ROOT/'experiments/results'/VIEW/'decisions.json')
    same=[r for r in rows if r['kind']=='real_development' and r['actual_camera']==r['requested_camera']]
    wrong=[r for r in rows if r['kind']=='real_development' and r['actual_camera']!=r['requested_camera']]
    synthetic=[r for r in rows if r['kind']=='synthetic_changed_view']
    assert (len(same),sum(r['compatible'] for r in same),len(wrong),sum(r['compatible'] for r in wrong),len(synthetic),sum(r['compatible'] for r in synthetic))==(16,1,32,0,48,0)
    scorer=read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')
    for f,h in scorer['implementation_hashes'].items():assert digest(ROOT/f)==h,f
    frozen={'data/manifests/singapore_forecast_reservation_v1.json':'bd47defbec2e4e73388b4eb4ad8dd8d04528a04df15ae78242427ca93f5afaca',
        'data/manifests/singapore_trend_issuance_v1.json':'b68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625',
        'data/manifests/singapore_trend_scoring_v1.json':'1dc86326f3152ca090572041434e057980e151ee75ea4a2b8292f4385cb3aa1b',
        'models/checkpoints/singapore_trend/SG-LAD-20261026T081112980974Z/model.json':'b11dd08ff444affb92de3841a23ef6de0b63833d270f748df4ff654426e1851f',
        'data/manifests/uvg_source_roles_v1.json':'68599fe2e3f8206acf96626f25777af97bafa2351195a0cc76a613f49d35535e'}
    assert all(digest(ROOT/f)==h for f,h in frozen.items())
    baseline=read(ROOT/'data/processed/singapore_prospective/summary.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json');issuance=read(ROOT/'reports/singapore_issuance_latest.json')
    assert baseline['scores_added']==0 and health['status']=='healthy' and health['forecasts_logged']==6630 and health['global_origins']==6
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    live=next(r for r in reversed(receipts) if r['local_path']=='data/raw/singapore_live/20261026T170956123200Z.json')
    assert digest(ROOT/live['local_path'])==live['sha256']
    assert len(list((ROOT/'data/raw/singapore_live').glob('*.json')))==58
    fields,sources=csv_read(ROOT/'data/source_manifest.csv');assert len(sources)==60 and len({r['source_id'] for r in sources})==60
    assert not {'SRC-DS-020','SRC-DOC-022'}&{r['source_id'] for r in sources}
    regfields,registry=csv_read(ROOT/'experiments/EXPERIMENT_REGISTRY.csv');assert not {VIEW,ND}&{r['experiment_id'] for r in registry}
    # Preflight complete. Register original acquisition times separately from today's receipt registration.
    url='https://zenodo.org/records/6560823/files/ndis_park.zip?download=1';apiurl='https://zenodo.org/api/records/6560823';licurl='https://opendatacommons.org/licenses/by/1-0/'
    events={Path(e['path']).name:e for e in read(RAW/'readme_ranges.json')['events']};probe=read(RAW/'range_probe_metadata.json');lic=read(RAW/'odc_by_primary.acquisition.json')
    localreceipts=[]
    for f in sorted(RAW.iterdir()):
        if not f.is_file():continue
        meta=dict(receipt_registration_at=now,semantic_annotation_bodies_opened=False,image_pixels_decoded=False,whole_archive_checksum_verified=False)
        source='SRC-DS-020';sourceurl=url
        if f.name.startswith('metadata_'):
            sourceurl=apiurl;meta.update(resource_kind='Original API JSON',original_request_started_at='2026-10-26T17:10:01.857724+00:00',original_completion_time_exact=False,original_completed_no_later_than=probe['checked_at'])
        elif f.name=='archive_footer.bin':meta.update(resource_kind='Original HTTP206 tail with opaque compressed noncentral prefix',original_acquisition_completed_at=probe['checked_at'],range_start=118122292,range_end=118187827,noncentral_bytes=39021)
        elif f.name in events:
            event=events[f.name];meta.update(resource_kind='Original exact README range',original_acquisition_completed_at=event['accessed_at'],range_start=event['start'],range_end=event['end'])
        elif f.name=='odc_by_primary.html':
            source='SRC-DOC-022';sourceurl=licurl;meta.update(resource_kind='Original primary licence HTML',original_acquisition_completed_at=lic['completed_at'])
        else:
            if f.name.startswith('odc_'):source='SRC-DOC-022';sourceurl=licurl
            meta.update(resource_kind='Derived slice/inventory/document text or acquisition sidecar',original_source_acquisition_time='See paired original-range/API/licence receipts;derived-file creation time was not independently recorded')
        localreceipts.append(receipt(source,f,sourceurl,'Bounded official metadata/document qualification;no image/semantic-label admission',**meta))
    for sid,kind,resource,creator,sourceurl,local,license_text,size,issue in [
        ('SRC-DS-020','dataset metadata and README only','NDISPark v1.0;DOI10.5281/zenodo.6560823','Luca Ciampi;Carlos Santiago;Joao Paulo Costeira;Claudio Gennaro;Giuseppe Amato','https://zenodo.org/records/6560823',next(RAW.glob('metadata_*.json')),'ODC Attribution 1.0 (odc-by) at record level;individual-content rights unqualified',133685,'No individual-content permission;no image/annotation decoding or benchmark admission;test count CSV is not instance-mask final labels'),
        ('SRC-DOC-022','primary licence documentation','Open Data Commons Attribution License1.0','Open Data Commons / Open Knowledge Foundation',licurl,RAW/'odc_by_primary.html','Primary licence text consultation;database and individual-content rights distinguished',46288,'No separate image content licence inferred')]:
        item=dict(source_id=sid,resource_type=kind,resource=resource,original_creator=creator,source_url=sourceurl,download_url=apiurl if sid=='SRC-DS-020' else licurl,access_date='2026-10-26',access_time_precision='Exact range/licence UTC in sidecars;API request start and bounded completion;receipt registration separately timed',version='1.0',license=license_text,permission='Public metadata/README/licence inspection only;image content not admitted',original_size=size,local_location=local.relative_to(ROOT).as_posix(),sha256=digest(local),purpose='Qualify fresh parking instance segmentation source without semantic data access',used_by=ND,modifications='Original bodies retained;derived directory slice/README/text;opaque tail prefix undecoded;cookie header redacted from sidecar',attribution='See docs/NDISPARK_QUALIFICATION.md and original creator/DOI/URL',status='Metadata integrity passed;image admission false',open_issues=issue)
        sources.append({k:item.get(k,'') for k in fields})
    for source in sources:
        if source['source_id']=='SRC-DS-001':source['used_by']=source['used_by'].rstrip(';')+';'+VIEW
    csv_write(ROOT/'data/source_manifest.csv',fields,sources)
    for i in [VIEW,ND]:
        r=results[i];folder=ROOT/'experiments/results'/i;p=read(folder/'protocol.json')
        record=dict(experiment_id=i,run_type='Stored-layout view compatibility DEVELOPMENT;rejected' if i==VIEW else 'Official metadata integrity and rights qualification;image admission blocked',started_at=r['started_at'],finished_at=r['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='PKLot141TRAIN/24DEVmanifest;6TRAINreferences/24DEVimages;no final' if i==VIEW else 'Metadata+READMEonly;259JPEGnames,zeroimagepixel/semanticlabelaccess',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='ORB/Hamming/RANSAC/2of3references' if i==VIEW else 'BoundedZIPdirectory/READMEDEFLATE+CRC;database-contentlicenceguard',random_seed=p['seed'],hardware='CPU',execution_environment=r.get('environment',{'python':sys.version}),training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(r['metrics'] if i==VIEW else dict(checks=r['checks'],inventory=r['inventory'],image_admission=False)),logs=folder.relative_to(ROOT).as_posix(),checkpoints='No model/production changes',code_revision_basis='2be8a44 plus sealed exact source snapshots',implementation_sha256=p['implementation_hashes']['scripts/validate_view_compatibility.py' if i==VIEW else 'scripts/qualify_ndispark_metadata.py'],conclusions='Only1of16matchingcameraaccepted;wrong0of32;synthetic0of48accepted;usabilityFAIL,noappintegration' if i==VIEW else 'All6metadata gates pass;image-content rights remain unqualified;no semantic source use')
        registry.append({k:record.get(k,'') for k in regfields});s['completed_run_ids'].append(i)
    csv_write(ROOT/'experiments/EXPERIMENT_REGISTRY.csv',regfields,registry)
    viewcard=dict(results[VIEW],report='experiments/results/'+VIEW+'/run.json',guide='docs/VIEW_COMPATIBILITY_STUDY.md',protocol='experiments/results/'+VIEW+'/protocol.json',decision_labels='Publisher camera group IDs;not independent manual pose certification',automatic_stored_layout_gate_qualified=False,software_tests_passed=369)
    ndcard=dict(results[ND],source_ids=['SRC-DS-020','SRC-DOC-022'],report='experiments/results/'+ND+'/run.json',guide='docs/NDISPARK_QUALIFICATION.md',raw_root='data/raw/ndispark_official',receipts=localreceipts,software_tests_passed=369)
    dump(ROOT/'models/view_compatibility_development.json',viewcard);dump(ROOT/'reports/view_compatibility_latest.json',viewcard)
    dump(ROOT/'models/ndispark_metadata_card.json',ndcard);dump(ROOT/'reports/ndispark_qualification_latest.json',ndcard)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['view_compatibility_development']=viewcard;inventory['ndispark_metadata_qualification']=ndcard
    inventory['datasets'].append(dict(source_id='SRC-DS-020',name='NDISPark metadata/README qualification only',inventory=results[ND]['inventory'],image_pixels_decoded=0,semantic_annotations_opened=0,image_admission=False,individual_content_rights_qualified=False,card='models/ndispark_metadata_card.json',used_for_model_training=False,used_for_model_evaluation=False))
    dump(ROOT/'data/dataset_inventory.json',inventory)
    s['scheduled_wakeups_completed']+=1;s['completed_recorded_runs_since_schedule']=len(s['completed_run_ids']);s['last_completed_run']=ND;s['last_updated_at']=now
    s['view_compatibility_development']=viewcard;s['ndispark_metadata_qualification']=dict(report=ndcard['report'],report_sha256=digest(ROOT/ndcard['report']),guide=ndcard['guide'],image_admission=False,software_tests_passed=369)
    s['prospective_live_summary']=baseline;s['last_live_baseline_score']=dict(outcomes=baseline['scores_total'],mae_spaces=baseline['baseline_mae_spaces'],scope='Rolling persistence only;distinct from future learned cohort;no neural/camera accuracy',coverage=baseline['forecast_coverage'])
    s['singapore_issuance_health'].update(checked_at=health['checked_at'],status='healthy',forecasts_logged=6630,global_origins=6)
    s['trigger_handling_note']='Coalesced15:08/15:38/16:08/16:38triggers produced no saved intervening collections/work. This17:09session registers2completed trials,not pertrigger/frame/request/test. Actual14:43->17:09gap remainsmissing;no backfill.'
    s['next_actions']=[
        'TOP PRIORITY nextwake: collectonce AFTER2026-10-26T17:39:57.962120Z with scripts/collect_singapore_study.py;30minuteplan/minimum1min. If wakeearly,do usefulindependentworkuntilactualdue;no earlypoll/backdate. Latest58snapshots;17:09issuer0newbecausepreviouscontextstale. Then routine scripts/check_singapore_issuance_health.py WITHOUT --record-trial. Learned6630/6origins remain outcome-unscored.',
        'Frozen Singapore learnedfinal closeduntil27October10:51UTC. Do not decode targets,refit,repair/backfillpartialbatches,changefrozenmethodsorclaiminterimaccuracy. Atclosure useonce-onlyexisting scorer withglobalclaim;missingoutcomesunscored. Rollingpersistence50985matches/MAE5.137157987643424spaces isseparate.',
        'NDISParkSRC-DS-020metadata/README qualified,butindividualcontentrightsunqualified. Keep image/annotationaccessblocked;originaltail39021noncentralbytesopaque. Seekpublishercontent-rightsevidence beforesemanticuse;do notinferCNRpermissionorautomaticcar-categorycompatibility. No authorcommunication authorized.',
        'ViewcompatibilityDEVstudyREJECTED:1/16matchingcameraaccepts,0/32wrong,48/48syntheticrejects;notusablegate/noappintegration. Stopdescriptor/thresholdgridsonthiscohort. Independentnextwork:TRAIN-onlystaticbackgroundreferencehypothesiswithfreshgroupreservation OR app/export/offlinecorrectnesswithinexistingverifiedscope. No oldfinalreplay;HighwayDrivefinalstillunopened/nofinalcontroller.',
        'Finishappintegration/exports,physicaloffline/newmachine/manualbrowserchecks,report/presentationandstudentexplanationswithinactualacceptancecriteria. Missinguniversitydocumentsblockofficialcomplianceonly. Counter80,62sources,nextseparate100-runlivecheckpoint100;noactivejobs.'
    ]
    dump(statepath,s)
    body='Implemented bounded ZIP metadata and README validation with explicit individual-content admission guard. NDISPark official API declares ODC-BY database licence; individual image/annotation rights remain unqualified. Verified271entries/259JPEGnames(112TRAIN/30validation/117test),READMECRC61306bytes;no wholeZIP/MD5verification,completeJPEGacquisition,pixeldecode orsemanticlabelaccess. Initial65536byte tail includes39021noncentralbytes retainedopaque;notallacquiredbytesaremetadata. Primarylicencescope/READMEtest-count-only limitation documented. Separate offline revalidation0.203s passes6checks afterexplicitpriorresearch exposure;one completed trial. Independent prespecified PKLot TRAIN/DEV viewcheck10.016s uses6TRAINreferences/24DEVimages,zeroXML/final/neuralreads:1/16matchingcamera accepted,0/32wrong-camera accepted,48/48syntheticchangedview rejected. Usability gateFAIL;noapppromotion/thresholdretuning. CameraIDsnotmanualposecertification;syntheticfixturesnotrealrelocationtruth. Saveddiagnostic43/48matchingreferencepairs lackenoughmatches;causenotestablished. All369softwaretestspass(14new);originalZIPcommentfixturefailurepreserved. Originalproductionweights/frozenSGmethods/consumedclaimshashesunchanged. Two distincttrials78->80,wakeups54,62sources,next100-runcheckpoint100,noactivejobs. LatestofficialSGsnapshot58at17:09after146mingap:0newpersistence matches,total50985/MAE5.137158spaces;1327newbaselineforecasts. Learned0new(stalepriorcontext),6630genuineforecasts/6originsmetadatahealthy,unscoreduntil27Oct10:51UTC. Missing15:13/15:43/16:13/16:43observationsnotinvented;nextcollectionafter17:39:57.962120UTC. Guides:NDISPARK_QUALIFICATION.md;VIEW_COMPATIBILITY_STUDY.md. Genuineprojectcompletionstillpending.'
    for doc in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md']:
        append(doc,'## 26 October 2026 / bounded source qualification and failed view compatibility',body)
    append('docs/IMPLEMENTATION_STATUS.md','## 26 October: source access guard and view compatibility',
        '369softwaretests pass. BoundedZIP/README helper implemented;NDISParkmetadata integrity passes butindividualcontentrights remainunqualified,soimages/semanticlabelsblocked. Independentstored-layoutviewcheckfailsusability(1/16matchingcameraaccepted);notintegratedorpromoted. Originalregion/appmodel unchanged. See NDISPARK_QUALIFICATION.md and VIEW_COMPATIBILITY_STUDY.md. Counter80/next100;SGfuturelearnedfinalstillclosed.')
    append('docs/REGION_STABILITY_GUIDE.md','## 26 October: runtime view-check hypothesis rejected',
        'A prespecified TRAIN/DEVORB-homographycheck accepts1/16matching-camera pairs,0/32wrong-camera pairs;rejects48/48syntheticshifts/rotations/flips. Usabilitygatefails;notanapp/stored-geometryauthorizationgate. No finalimages/XMLorneuralcalls. SamecameraIDisnotindependentposecertification. Existingconditionalregionresults/weights unchanged. See VIEW_COMPATIBILITY_STUDY.md and models/view_compatibility_development.json;no repeatedthresholdgrid.')
    append('docs/SOURCE_REGISTRY.md','## Sources SRC-DS-020 and SRC-DOC-022 / 26 October',
        'NDISParkofficialZenodo6560823/version1.0/DOI10.5281/zenodo.6560823:Ciampi,Santiago,Costeira,Gennaro,Amato. MetadataandexactREADMEonly;recordlicenceODC-BY,notCCBY. PrimaryODCAttribution1.0scope distinguishesdatabasefromcontents;individualimage/annotationrightsremainunqualified. See https://zenodo.org/records/6560823 and https://opendatacommons.org/licenses/by/1-0/ . Sourcecatalog62uniqueIDs;receiptregistrationUTCseparatefromoriginalrange/licenceUTC;APIcompletionbounded. Originaltailincludes39021opaque noncentralbytes;wholearchivechecksumunverified. Fullscopeandattribution:NDISPARK_QUALIFICATION.md.')
    reqfields,requirements=csv_read(ROOT/'docs/REQUIREMENTS.csv')
    for req in requirements:
        values=list(req.values())
        if values[0] in ['SEG-02','SRC-01']:
            for key,value in req.items():
                if value and ('models/region_stability_final.json' in value or 'data/source_manifest.csv' in value):req[key]=value+';models/view_compatibility_development.json' if values[0]=='SEG-02' else value+';docs/NDISPARK_QUALIFICATION.md'
            # Append dated evidence without declaring requirement/compliance completion.
            evidencekey=reqfields[-3];req[evidencekey]=req[evidencekey]+(';26OctviewDEV1/16samecameraaccepts,gateFAIL,noappintegration;369softwaretests' if values[0]=='SEG-02' else ';26Oct62uniqueIDs;NDISParkmetadataonly,individualcontentunqualified;receipts/rightsboundariesrecorded')
    csv_write(ROOT/'docs/REQUIREMENTS.csv',reqfields,requirements)
    dump(E/'checks.json',dict(registered_at=now,completed_trials=[VIEW,ND],counter_before=78,counter_after=80,wakeups_completed=54,unique_sources=62,software_tests=369,view_saved_decisions_recomputed=True,metadata_integrity_passed=True,ndispark_image_admission=False,frozen_hashes_unchanged=frozen,production_and_consumed_claims_unchanged=True,learned_target_decoding=False,learned_final_evaluation=False,active_jobs=[],next_live_collection_not_before='2026-10-26T17:39:57.962120+00:00',live_raw_sha256_verified=live['sha256'],live_baseline_summary=baseline,learned_health_summary={k:health[k] for k in ['checked_at','status','forecasts_logged','global_origins']}))
    print(json.dumps(dict(counter=80,wakeups=54,sources=62,tests=369,next_collection='2026-10-26T17:39:57.962120Z')))


if __name__=='__main__':main()
