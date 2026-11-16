"""Persist recovered source qualification,provisional fresh dates and actual live gap."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
from smart_parking.cnrpark_holdouts import assert_closed
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T001740Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    path=ROOT/p;old=path.read_text(encoding='utf-8');assert title not in old
    path.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')
def main():
    if (E/'checks.json').exists():raise RuntimeError('Handoff already recorded')
    state=read('data/automation_state.json');run=read('models/pklot_unused_date_inventory.json');s=run['summary'];plan=read('data/manifests/pklot_fresh_group_plan_v1.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==45 and state['scheduled_wakeups_completed']==31
    assert not state['active_validation_jobs'] and not state['active_training_jobs']
    assert s['provisional_unused_frames']==205 and len(plan['frames'])==6 and plan['whole_reserved_group_frames']==171
    assert all(digest(ROOT/p)==h for p,h in run['source_hashes'].items())
    assert digest(ROOT/s['manifest'])==s['manifest_sha256'] and not plan['pixels_decoded'] and not plan['xml_labels_parsed']
    assert not ({r['date'] for r in plan['frames']} & set(run['excluded_dates']))
    cnr=assert_closed(ROOT/'data/manifests/cnrpark_final_dates_v1.json',ROOT,ROOT/'data/cnrpark_holdout_claims');assert cnr['reserved_rows']==32079
    weights=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json');assert all(digest(ROOT/p)==h for p,h in weights.items())
    now=datetime.now(timezone.utc).isoformat();live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(x) for x in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()];receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001')
    assert digest(ROOT/receipt['local_path'])==receipt['sha256'];payload=read(receipt['local_path']);rows=parse_feed(payload)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in rows) and len(rows)==len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),bounds_valid=True,duplicate_rows=0,not_a100_run_checkpoint=True,
        gap_interpretation='No observations during usage-limit gap;missed target windows remain unscored. This snapshot adds0scores;no invented retrospective target.',scope='Persistence only;no neural/camera accuracy'))
    pointer=dict(run_id=run['run_id'],inventory='models/pklot_unused_date_inventory.json',metadata_manifest=s['manifest'],metadata_manifest_sha256=s['manifest_sha256'],
        group_plan='data/manifests/pklot_fresh_group_plan_v1.json',group_plan_sha256=digest(ROOT/'data/manifests/pklot_fresh_group_plan_v1.json'),
        candidate_frames=205,candidate_date_groups=6,whole_reserved_group_frames=171,preselected_final_frames=6,
        selected_pixel_duplicate_and_annotation_audit_passed=False,images_materialized=False,model_training_or_scoring=False)
    write('reports/fresh_pklot_data_latest.json',pointer)
    inventory=read('data/dataset_inventory.json');inventory.update(inventoried_at=now,fresh_pklot_metadata=pointer)
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-001':item['unused_date_inventory']=pointer
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=snapshots,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state.update(scheduled_wakeups_completed=32,last_updated_at=now,fresh_pklot_metadata=pointer,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;no neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Next execute a bounded PKLot selected-group provenance/byte-duplicate and annotation-support audit using data/manifests/pklot_fresh_group_plan_v1.json. Materialize raw selected members WITHOUT JPEG decode;hash against prior inputs/checkpoints/known protected frames. Parse only development XML first;final pixels/labels remain closed. Keep missing occupancy attributes unknown.',
        'Fresh metadata candidates205frames/6whole dates:developmentPUCPR2012-10-05andUFPR052013-02-28/03-01;finalgroupsPUCPR2012-10-23,UFPR042012-12-24,UFPR052013-04-08reserved in full171frames,6first/last frames preselected. Known cameras/new dates,not new-carpark evidence. No fresh images/labels decoded or model use yet.',
        'After provenance/annotation qualification,freeze a bounded reliability/segmentation hypothesis with old permitted development plus fresh development groups. Existing holdouts.evaluate_final_once must durably claim qualified frozen final6before pixels/labels;never replay prior consumed image/Birmingham/DAVIS groups. Use validation gates/no final tuning,no unsupported100%claims.',
        'CNRofficial archive/CSVnow catalogued:144965EXTrecords/9cams/23dates;32079records over5dates remain reserved/unclaimed. Image-content scope unqualified under project rule5;keep images inspection-only while doing independent licensed PKLot work. Database facts and image permissions remain distinct.',
        'Current counter45;next separate100-run live checkpoint100. Full191tests passed before metadata scan;no original model/production changes. Combined419-file offline demo and older reports remain dated/preserved. Usage-limit interruption recovered after reset;no bypass/purchase;no active jobs.',
        'Latest Singapore '+receipt['accessed_at']+':'+str(snapshots)+'snapshots,30614matched baseline outcomes/MAE4.391684;this snapshot adds0scores because previous targets expired during collection gap. New1191forecasts frozen. Continue sensible half-hour polling;missing outcomes stay unscored. Manual/physical/browser/student/official acceptance remains.'
    ];write('data/automation_state.json',state)
    title='## 26 October 2026 / licensed archive fresh-date metadata inventory'
    note='''After the account reset,the missing CNRhandoff was recovered without repeating its model-free audit. A new bounded scan read only original PKLot tar headers:gzip decompression occurred to reach headers,but no JPEG pixels or XML labels were decoded/parsed.12,218valid paired frames/98camera-date groups,396invalid or inconsistent member metadata entries quarantined,no duplicate member names. Conservative prior model/manifest/layout/experiment-date exclusion leaves205provisional frames over6dates. Whole latest date/camera groups selected by metadata:PUCPR2012-10-23,UFPR042012-12-24,UFPR052013-04-08reserved in full171frames;first/last frames per group preselected for later6-frame final. Other3dates development-only. This is a metadata plan,not a qualified final evaluation:byte-duplicate/source/annotation audit still needed before modelling. All original weights and CNR32,079reserved images remain unchanged/unopened. No training or new accuracy. One inventory trial advances44->45;no counts per header/frame.191software tests retain prior executed scope. Latest actual Singapore snapshot resumed after gap:0new scores,30,614total,MAE4.391684spaces;missed targets remain unscored,new1191forecasts frozen. No camera/neural live accuracy. Next:bounded selected-member audit and frozen development hypothesis. See reports/fresh_pklot_data_latest.json;source catalog57unchanged. Full project/manual/physical/student/official completion unclaimed.'''
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md']:append(p,title,note)
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;requirements=list(r)
    for row in requirements:
        if row['requirement_id']=='DATA-02':row['actual_evidence']+='; models/cnrpark_metadata_qualification.json; reports/fresh_pklot_data_latest.json';row['test_result']+=';CNR144965metadata entries map to archive,images unopened;PKLot12218paired headers/205provisional fresh-date frames';row['open_problems']+=';CNRimage-content use unqualified;fresh PKLot duplicate/annotation audit pending'
        if row['requirement_id']=='SRC-01':row['test_result']='57unique sources;CNRofficial files/metadata/local hashes and usage review recovered;PKLot existing-archive metadata lineage retained'
    with path.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(requirements)
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=45,source_records=57,software_tests=191,valid_paired_metadata=12218,provisional_frames=205,provisional_groups=6,
        whole_final_group_frames=171,preselected_final_frames=6,pixels_decoded=0,labels_parsed=0,original_weights_unchanged=True,cnr_reserved_unconsumed=32079,
        actual_live_snapshots=snapshots,live_scores_added=0,live_scores_total=30614,no_active_jobs=True,next_live_checkpoint=100))
    print(json.dumps(dict(completed_trials=45,candidate_frames=205,live_snapshots=snapshots,live_scores_added=0),indent=2))
if __name__=='__main__':main()
