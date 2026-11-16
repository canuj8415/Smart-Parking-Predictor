"""Recover the CNR handoff interrupted by the account limit;no rerun of models."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.cnrpark_holdouts import assert_closed
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T224739Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    if (E/'checks.json').exists():raise RuntimeError('Handoff already recorded')
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');run=read('models/cnrpark_metadata_qualification.json');tests=read(E.relative_to(ROOT)/'regression_summary.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==44 and tests['success'] and tests['tests']==191
    assert not state['active_validation_jobs'] and not state['active_training_jobs'] and run['metadata_gate_passed']
    assert all(digest(ROOT/p)==h for p,h in run['source_hashes'].items())
    final=assert_closed(ROOT/'data/manifests/cnrpark_final_dates_v1.json',ROOT,ROOT/'data/cnrpark_holdout_claims');assert final['reserved_rows']==32079
    weights=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json');assert all(digest(ROOT/p)==h for p,h in weights.items())
    receipts=[json.loads(x) for x in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    cnr=[r for r in receipts if r['source_id']=='SRC-DS-002'];assert all(digest(ROOT/r['local_path'])==r['sha256'] for r in cnr)
    write(E.relative_to(ROOT)/'acquisition_receipts.json',dict(receipts=cnr,asset_bytes=467635098,publisher_checksum_provided=False,local_hashes_verified=True))
    path=ROOT/'data/source_manifest.csv'
    with path.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==57
    for row in sources:
        if row['source_id']=='SRC-DS-002':row.update(source_url='http://cnrpark.it/',download_url='Author HTTPS GitHub archive release75867853;assetIDs123488130and76402006;exact URLs in receipts',
            access_date=now,access_time_precision='Exact per-file acquisition receipts;handoff recovery time separate',version='Local immutable CSV/EXTZIP snapshot;publisher release digest null',
            license='Publisher ODbL1.0database declaration;individual image-content scope unqualified',permission='Acquisition/inspection and factual metadata preparation only;no image modelling/public redistribution',
            original_size='467635098bytes/CSV+EXTZIP',local_location='data/raw/cnrpark_official/;data/splits/cnrpark-global-dates-v1/',sha256='Per-file local SHA256 in receipts;no publisher checksum',
            purpose='Independent parking-source qualification and whole-date reservation',used_by=run['run_id']+';metadata mapping only,no images decoded/trained/scored',
            modifications='Raw files unchanged;derived manifest excludes occupancy/occupant_changed fields',attribution='CNRPark research team;Amato,Carrara,Falchi,Gennaro,Meghini,Vairo;official author/site links retained',
            status='Official archive acquired;metadata qualified;image use deferred',open_issues='Image-content terms/pixel quality/label accuracy unqualified;32079rows/5global dates reserved and unconsumed. No CNR accuracy claim.')
    with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(sources)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    inventory['datasets']=[r for r in inventory['datasets'] if r['source_id']!='SRC-DS-002']+[dict(source_id='SRC-DS-002',status='Metadata qualified;images inspection-only',
        raw_metadata='data/raw/cnrpark_official/CNRPark+EXT.csv',raw_archive='data/raw/cnrpark_official/CNR-EXT-Patches-150x150.zip',asset_bytes=467635098,
        full_csv_rows=157549,ext_rows=144965,preliminary_rows_excluded=12584,cameras=9,dates=23,split=run['summary'],used_for_model_training=False,used_for_model_evaluation=False,
        image_members_decompressed=0,usage_qualification='data/manifests/cnrpark_usage_qualification_v1.json')]
    write('data/dataset_inventory.json',inventory)
    state.update(scheduled_wakeups_completed=31,last_updated_at=now,cnrpark_metadata_qualification=dict(run_id=run['run_id'],rows=144965,reserved_final_rows=32079,metadata_gate_passed=True,image_analysis_authorized=False))
    state['next_actions']=[
        'CNRhandoff recovered after usage-limit interruption;44unique completed trials and191tests. Official CSV/EXTZIP retained;144965EXTrecords/9cams/23dates match archive entries.32079records/5dates reserved/unconsumed;no JPEG decoded or model scoring. See docs/CNRPARK_DATA_QUALIFICATION.md.',
        'Next independently inventory unused valid PKLot date groups from existing licensed archive. Exclude all dates mentioned in prior model/manifests/experiment records,then reserve fresh final groups before changed-method evaluation. Missing occupancy attributes remain unknown;never repair invalid dates silently.',
        'CNRdatabase metadata use is qualified but image-content rights are not. Keep images inspection-only under PROJECT_CONSTRAINTS rule5. Source research may continue;do not substitute routine user approval for source rights. No bypass,private access or author contact.',
        'Original images/Birmingham/DAVIS finals remain consumed;old models/packages/reports preserved. Canonical CNRdate guard claims before callback and failures stay consumed. Raw CSV fields were tokenized;targets were not semantically inspected/used for selection.',
        'Next100-run live checkpoint100;no active jobs. Respect account limits;skipped wakeups are not completed work or experiments. Resume public feed at sensible cadence;gap targets without matching later observations stay unscored.'
    ];write('data/automation_state.json',state)
    note='''Official CNRpublisher HTTP page recovered after HTTPS failure;current links point to author HTTPS GitHub release. CSV18,132,695bytes/EXTZIP449,502,403bytes retained with exact receipts/local SHA;publisher digest absent.144,965EXTrecords map exactly to JPEG member names,9cameras/23dates.13/5/5global-date roles contain82,361train/30,525development/32,079reserved records;all cameras on each date stay together. No JPEG decompressed or model trained/scored. CSV fields were tokenized;occupancy values were not semantically used,and omitted from derived manifest. Database ODbLdeclared;individual image-content rights unqualified,soimages remain inspection-only under PROJECT_CONSTRAINTS rule5.7newsynthetic guard/parser tests and full191regressions pass. Temporary fixture permission errors and licence-download403preserved;primary licence read through web tool,no original licence HTML copy claimed. One metadata trial advances43->44;final images remain unopened/unclaimed. Usage-limit auto-review failure interrupted the documentation action before execution;no bypass or credit purchase. Handoff resumed after the known reset. Source catalog57updated in place;original models/packages intact. Next independent work:unused licensed PKLot date inventory and fresh reservations. Guide:docs/CNRPARK_DATA_QUALIFICATION.md.'''
    title='## 26 October 2026 / recovered CNR metadata qualification handoff'
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md']:
        p=ROOT/name;old=p.read_text(encoding='utf-8');assert title not in old;p.write_text(old.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    path=ROOT/'docs/PROJECT_CONSTRAINTS.md';path.write_text(path.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nCNRimages remain inspection-only:individual-content scope unqualified.32079records across5global dates reserved;claim canonical whole dates before any qualified final evaluation. Continue independent licensed PKLot work;existing final groups remain consumed.\n',encoding='utf-8')
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=44,tests=191,source_records=57,metadata_rows=144965,reserved_final_rows=32079,image_members_decompressed=0,original_weights_unchanged=True))
    write(E.relative_to(ROOT)/'interruption_recovery.json',dict(recovered_at=now,reason='Automatic approval review could not complete because account usage limit was reached;action not executed',
        action='Create/run CNR handoff recorder',limit_reset_reported='05:45 Asia/Calcutta',successful_resume_read='2026-10-26T00:18:02Z',
        bypass_or_credit_purchase=False,skipped_triggers_not_counted=['2026-10-25T23:17:39.760Z','2026-10-25T23:47:40.275Z']))
    print(json.dumps(dict(completed_trials=44,tests=191,handoff_saved=True),indent=2))
if __name__=='__main__':main()
