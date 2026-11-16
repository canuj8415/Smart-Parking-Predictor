"""Save conservative full-archive roles and retrospective protection evidence."""
import csv,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    e=ROOT/'experiments/evidence/HEARTBEAT-20261027T050911Z';r=read(ROOT/'models/pklot_full_role_ledger.json');out=ROOT/'experiments/results'/r['run_id'];p=read(out/'protocol.json');supp=read(out/'historical_consumption_supplement.json');current=supp['current_ledger']
    assert r['metadata_gate_passed'] and r['paired_frames']==12218 and r['camera_date_groups']==98
    for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    assert digest(out/'run.json')==supp['original_completed_run_json_unchanged_sha256'] and supp['completed_experiment_count_added']==0 and supp['protection_records_not_backdated']
    assert digest(ROOT/'scripts/close_historical_pklot_tests.py')==supp['supplement_source_sha256']
    for record in supp['records']:assert digest(ROOT/record['path'])==record['sha256']
    s=read(ROOT/'data/automation_state.json');assert s['completed_recorded_runs_since_schedule']==102==len(set(s['completed_run_ids'])) and s['scheduled_wakeups_completed']==67;assert not s['active_training_jobs'] and not s['active_validation_jobs'];assert s['next_live_checkpoint_at_run']==200
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:ids=[v['experiment_id'] for v in csv.DictReader(stream)]
    assert all(ids.count(v)==1 for v in s['completed_run_ids'])
    tests=e/'unit_tests.txt';assert 'Ran 451 tests' in tests.read_text() and '\nOK' in tests.read_text()
    assert current['status_counts']==dict(training_exposed=50,consumed_durable_final=17,historical_metadata_excluded=16,development_exposed=15) and current['protected_role_overlap_groups']==0
    table=out/'current_group_roles.csv'
    fields=['camera_id','capture_date','paired_frames','status','historical_roles','durable_claim_runs','role_overlap_with_protected','byte_alias_to_protected','new_training_admitted','new_final_admitted']
    with table.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in current['groups']:writer.writerow({k:(';'.join(row[k]) if isinstance(row[k],list) else row[k]) for k in fields})
    live=read(ROOT/'reports/singapore_issuance_latest.json');health=read(ROOT/'reports/singapore_issuance_health_latest.json');assert live['collection']=='acquired' and health['status']=='healthy' and not health['target_json_decoded'] and not health['performance_evaluated'];assert health['forecasts_logged']==20714 and health['global_origins']==19
    assert digest(ROOT/live['study_issuance']['receipt_path'])==live['study_issuance']['receipt_sha256'];snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')));assert snapshots==73
    now=datetime.now(timezone.utc).isoformat();next_collection=(datetime.fromisoformat(live['baseline']['checked_at'])+timedelta(minutes=30)).isoformat()
    s.update(scheduled_wakeups_completed=68,last_wakeup_completed_at=now,last_updated_at=now,singapore_issuance_health=health,prospective_live_summary=live['baseline'],last_live_baseline_score=live['baseline'])
    s['trigger_handling_note']='05:09wake expanded fullPKLot metadata roles. Initial05:22collection check correctly skipped before05:24:19due;actualacquisition05:25:56UTC. One completed fullroleaudit101->102;pre-run alias-flag source correction was not executed/counted. Retrospective consumption repair/probes are part of this audit,not extra experiments. No image/XML/neural evaluation.'
    s['next_actions']=[
      'Collect once AFTER '+next_collection+' via collect_singapore_study.py;routine metadata health WITHOUT --record-trial.73official snapshots/20714learnedforecasts/19origins/19receiptedbatches healthy,not evaluated.05:39heartbeat is early versus05:55:56due:do independent work first;no polling early/backfill/learned target matching.',
      'FullPKLot roles now documented:all12218validatedpairs/98groups,sourcearchive3860376865bytes SHA df182f46 unchanged. Current ledger50historicallyTRAIN,15DEV,17durablyrecordedconsumedfinal,16conservativelymetadataexcluded. Read docs/PKLOT_ROLE_LEDGER_GUIDE.md,models/pklot_current_role_ledger.json and experiments/results/'+r['run_id']+'/current_group_roles.csv. No newTRAIN/final groups admitted;unknownmetadata is not freshness. Legacy eligible_date flags are stale and must not override ledger/claims.',
      'Possible next stronger-region experiment:prepare a bounded image-only bay-union segmentation dataset from EXISTING50TRAIN groups,with explicit role/manifests first and a fixed development cohort from15DEV groups. All17consumeddategroups and known aliases excluded. Compare selected TRAIN JPEG byte hashes against protected metadata/member bytes BEFORE any new pixel/XML decode,without opening protected labels. Quarantine byte aliases. Expanding frames within existing TRAIN dates is not fresh final evidence. Define annotated bay-footprint target carefully;not exhaustive whole-parking-area/background truth.',
      'Alternatively resolve historical usage evidence for16remainingmetadata-excluded groups using code/manifests only,or research a genuinely new rights-qualified labelled source. Do not rename them as fresh final or materialize unknown groups casually. Full group ledger did not establish global data exhaustion. Do not run legacy scripts/train_segmentation.py:its main overwrites original parking_unet.pt. New trainers must save separate candidates,checkpoint/cancel/early-stop,freezegates before learning and keep finalsource closed.',
      'Three historical-consumption records were written NOW,explicitly retrospective/not prior preregistrations. OriginalweightedUNet5testdates,originalvision3testdates andknown-camera3testdates now covered alongside6newerconsumedgroups. Existing guard blocks22newcanonical/folder-alias probes;unrelated TRAINcontrol remains allowed. No metric scores/pixels/XML were re-evaluated. Vision currentcode/manifest hashes differ from oldercard and are disclosed,not silentlytreated as matching;explicit old split_dates/completed360test-sample record provide conservative group protection. Preserve all old claims/cards/checkpoints.',
      'Selected468-file/107wheelcurrentcopy86ceecb remains accepted;no app behavior or weights changed by metadatawork.451softwaretests pass. Counter102/68actualwakeups/63sourceIDs/noactivejobs;required100-runcheckpoint passed,next200. Retrospectiveclaims/syntheticguard probes/memberrows/hashchunks are not separate runs. Dated PDF/presentation remain older snapshots;student explanations/mastery and physicaloffline/newmachine/visiblemanual/university acceptance remainopen.',
      'SG final CLOSED until2026-10-27T10:51UTC(16:21IST). No interim learned target/matching/error/coverage or refit/backdating. Atclosure use existingonce-only scorer/globalclaim.65734rollingpersistenceoutcomes/MAE5.810965406030364spaces remain separate aggregate availability,not cameraGT orBirminghamvalidationinSingapore.20714loggedforecasts/19origins are not final matched coverage.'
    ];dump(ROOT/'data/automation_state.json',s)
    inventory=read(ROOT/'data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['pklot_full_role_ledger']=dict(run_id=r['run_id'],initial_report='models/pklot_full_role_ledger.json',current_supplement='models/pklot_current_role_ledger.json',paired_frames=12218,groups=98,current_status_counts=current['status_counts'],new_groups_admitted=0,retrospective_consumption_records=3,images_or_XML_parsed=0,model_calls=0);inventory['singapore_issuance_health']=health;dump(ROOT/'data/dataset_inventory.json',inventory)
    guide='''# Whole-archive PKLot roles and historical test protection

This metadata audit accounts for all 12,218 paired files in the previously
validated archive index, spanning 98 camera/date groups. It re-hashed the original
3,860,376,865 compressed bytes and verified the existing index checksum. It did
not decompress image formats, parse XML labels, run a model or change weights.
The initial audit took 4.741 seconds. Old rejected member metadata stays rejected.

| Current conservative status | Groups |
|---|---:|
| Training exposure already recorded | 50 |
| Development exposure already recorded | 15 |
| Historical final consumption now durably recorded | 17 |
| Earlier conservative metadata exclusions, still quarantined | 16 |

No new training or final groups were admitted. The earlier inventory's boolean
eligible_date is historical: its six provisional groups later became three
development groups and three consumed final groups. A missing newer claim is
not evidence that an older test was never used. The immutable initial audit
retains its pre-repair counts; the separate consumption supplement gives the
current table. See current_group_roles.csv in the completed audit folder.

The follow-up found five original weighted-segmentation test dates among the
metadata exclusions. Completed original vision and known-camera segmentation
tests also predated newer durable claim handling. Three consumption attestations
were therefore recorded at the actual current time, explicitly retrospective.
They are not presented as preregistrations made before those old evaluations.
All original artifacts and earlier claim files remain unchanged. Existing guard
checks reject 22 canonical/archive-folder alias probes, with a separate unrelated
training-group control allowed. Those probes use labelled synthetic guard
manifests and never open an image. No new experiment count is assigned to them.

For the original vision record, the current code and manifest byte hashes differ
from those recorded historically. This mismatch is retained explicitly; it was
not repaired by inventing an old matching version. The historical card's explicit
test-date map, completed 360-test-sample record and preserved checkpoint justify
conservative whole-date protection. Weighted-segmentation and known-camera
evaluation code hashes match their records. Only metadata and field presence,
not metric score values, were inspected for this consumption repair.

Known image-hash metadata produced no cross-group byte aliases, but most archive
images were not newly hashed individually. This is not proof of no duplicate
images throughout the archive. Future selected TRAIN data need a byte-alias
qualification before decoding; unknown groups remain quarantined. Camera aliases
parking2/pucpr, parking1a/ufpr04 and parking1b/ufpr05 are canonicalized. A consumed
or historical test role overrides later role labels, including failed evaluations.

Five synthetic role/alias/path tests bring the software suite to 451 passing tests.
One planned protocol was replaced before execution to separate an actual hash
alias from a merely protected seed group. Its source/protocol remain preserved,
and it contributes zero trial count. The completed audit is one recorded trial;
the archive frames, checksum chunks and synthetic probes are not separate runs.

A student should explain why an image filename, folder alias or absent claim
cannot make old test data fresh. Explain the difference between prior training
exposure, development decisions, consumed final evaluation and uncertain metadata.
Student independent understanding has not been assessed. Supplied bay polygons
are not automatically exhaustive whole-facility segmentation ground truth.
'''
    gp=ROOT/'docs/PKLOT_ROLE_LEDGER_GUIDE.md';gp.write_text(guide,encoding='utf-8')
    note=f'''
## 27 October 2026 IST / full PKLot roles and retrospective consumption repair

Completed one metadata integrity audit over12218validatedpairs/98canonicalgroups.
Original3860376865compressedbytes/indexchecksum match;4.741seconds. No image
decoding/XMLsemanticlabels/modelcalls/network in normal audit;image/socket negative
controls blocked. Initial roles50TRAIN/15DEV/6durableconsumed/6historicaltestprotected/
21metadataexcluded are preserved in immutable run.json. Follow-up explicit modelcard
test-date evidence identified5originalsegmentationtestdates plus older vision and
known-camera completed tests lacking newer claims. Three records added NOW,
explicitlyretrospective andnot priorpreregistration. Current groupstatuses50TRAIN/
15DEV/17consumed/16metadataexcluded;no automaticnewTRAIN/final admission. Existing
guard blocks22newcanonical/folderalias probes;unrelatedTRAINcontrol allowed. Prior
claims untouched,no scoredtest/pixel/XML replay. Visioncurrentcode/manifesthashes
differ fromoldcard andremain disclosed;oldexplicitdates/completed360test-sample
record/preservedcheckpoint supportconservativeprotection. No metric score values
inspected;othermatched historicalevalcode/checkpointmetadata corroborateconsumption.

Zero known cross-group image-hash aliases in inspectedmetadata,not proofnoneexist
in wholearchive;no exhaustive new per-image hashing. Zero protected-role overlaps
in inspectedrolemanifests. Historical eligible_date flags never override current
closure.16remaininggroups stayquarantined;this is not globaldataexhaustion orfresh
final qualification. Five meaningfulsynthetictests bring fullsuite451/OK6.719sec.
Pre-run aliasflag correction preserved one unexecutedprotocol;0extra runs. Follow-up
protectionrecords/probes are part of this audit,0extra experimentcount. Counter101->102,
wakeups68/sourceIDs63/next100-runmilestone200/noactivejobs. Selected468-fileofflinecopy
and original/bestcheckpoints unchanged. Guide:PKLOT_ROLE_LEDGER_GUIDE.md;currentledger
models/pklot_current_role_ledger.json;immutableauditmodels/pklot_full_role_ledger.json.

73officialSGsnapshots.05:22checkwasnotdue anddidnotpoll;actual05:25:56UTCcollection
adds2273later rollingpersistenceoutcomes:65734total/MAE5.810965406030364spaces and1248
baselineforecasts.1163genuinelearnedforecasts newlyfrozen give20714forecasts/19origins/
19receiptedbatches metadatahealthy. Learnedtargetdecoding/matching/error/coverage stays
closed until27Oct10:51UTC. Nextcollection after{next_collection}. Source licensedaggregate
availability,notcameraGT/BirminghamSGvalidation. Next prepare strongerregiondata using
existingTRAIN groups with explicit target semantics/byte-alias checks,or resolve
quarantined source roles/new rights-qualified data. No legacytrainer overwrite,
oldfinal reuse orautomaticadmission. Physical/manual/newmachine/student/official
acceptance remainsopen;datedPDF/presentation stillolder snapshots.
'''
    for name in ['PROJECT_PROGRESS.md','AUTONOMOUS_PROGRESS.md','TEST_RESULTS.md','IMPLEMENTATION_STATUS.md']:
        with (ROOT/'docs'/name).open('a',encoding='utf-8') as stream:stream.write(note)
    with (ROOT/'docs/UI_TEST_LOG.md').open('a',encoding='utf-8') as stream:stream.write('\n27Oct2026 full-role audit:metadata/softwareguard work only;no nativeUI orimagepreview/newcamera/modelaccuracy acceptance. Existing468-filecopy acceptance remains separate.451softwaretests pass.\n')
    with (ROOT/'docs/AI_ASSISTANCE_LOG.md').open('a',encoding='utf-8') as stream:stream.write('\n27Oct2026:Codex implemented conservative fullPKLot role/knownhashalias audit and5synthetictests,thenretrospectively recorded provenhistoricaltestconsumption with22syntheticguardprobes. Originalclaims/cards/weights and metricvalues unchanged. No pixels/XML ormodels rescored;no student work/mastery invented.\n')
    protected={**p['protected_hashes'],**{record['path']:record['sha256'] for record in supp['records']}}
    for f,h in protected.items():assert digest(ROOT/f)==h,f
    dump(e/'checks.json',dict(checked_at=now,counter_before=101,counter_after=102,wakeups_completed=68,software_tests=451,source_ids=63,completed_trial=r['run_id'],frozen_hashes_unchanged=protected,source_hashes={**p['source_hashes'],'scripts/close_historical_pklot_tests.py':supp['supplement_source_sha256'],'scripts/record_full_roles_handoff.py':digest(__file__)},normal_image_XML_network_accesses=0,new_groups_admitted=0,new_retrospective_records=3,records_not_backdated=True,guard_probes=22,repair_extra_count=0,next_live_checkpoint_at_run=200,active_jobs=[],next_collection_after=next_collection,full_project_complete=False,
        artifacts={f.relative_to(ROOT).as_posix():digest(f) for f in [tests,ROOT/'models/pklot_full_role_ledger.json',ROOT/'models/pklot_current_role_ledger.json',out/'historical_consumption_supplement.json',table,gp]}))
    print(json.dumps(dict(counter=102,wakeups=68,software_tests=451,closed_groups=17,remaining_metadata_quarantine=16,new_groups_admitted=0,next_collection_after=next_collection,full_project_complete=False)))

if __name__=='__main__':main()
