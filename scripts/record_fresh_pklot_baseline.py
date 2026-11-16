"""Persist fresh-development baseline without promoting it to final/live accuracy."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
from smart_parking.holdouts import assert_holdout_closed
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T001740Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    path=ROOT/p;old=path.read_text(encoding='utf-8');assert title not in old
    path.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')
def main():
    if (E/'baseline_checks.json').exists():raise RuntimeError('Baseline handoff already saved')
    state=read('data/automation_state.json');baseline=read('models/pklot_fresh_classifier_baseline.json');members=read('models/pklot_fresh_member_qualification.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==47 and state['scheduled_wakeups_completed']==32
    assert not state['active_validation_jobs'] and not state['active_training_jobs']
    assert baseline['overall']['samples']==720 and baseline['overall']['hard_errors']==17 and baseline['overall']['confident_false_vacant']==2
    assert baseline['final_images_or_labels_read']==0 and members['summary']['final_pixels_decoded']==0 and members['summary']['final_xml_parsed']==0
    assert all(digest(ROOT/p)==h for p,h in baseline['source_hashes'].items()) and all(digest(ROOT/p)==h for p,h in members['source_hashes'].items())
    final=ROOT/'data/manifests/pklot_fresh_final_v2.json';assert_holdout_closed(final,root=ROOT)
    frames=read('data/manifests/pklot_fresh_development_v1.json')['frames']+read(final)['frames'];copied=[]
    for frame in frames:
        for kind in ['image','annotation']:
            p=ROOT/frame[kind];assert digest(p)==frame[kind+'_sha256']
            copied.append(receipt('SRC-DS-001',p,'https://www.inf.ufpr.br/lesoliveira/download/PKLot.tar.gz',
                'Existing official local archive member materialized for fresh-development/final reservation;no network transfer',
                acquisition_kind='local_archive_member_copy',archive_member=frame[kind+'_archive_member'],parent_archive='data/raw/pklot_subset/PKLot.tar.gz',
                parent_archive_sha256=read('data/manifests/pklot_fresh_group_plan_v1.json')['archive_sha256'],qualification_run=members['run_id'],
                role=frame['role'],exact_per_file_copy_time_captured=False,copy_time_bounds=[members['started_at'],members['finished_at']],
                final_pixels_or_labels_read=False if frame['role']!='development' else None))
    write(E.relative_to(ROOT)/'fresh_member_receipts.json',dict(receipts=copied,network_bytes=0,copy_times_bounded_by_recorded_run=True,receipt_record_times_exact=True))
    rows=read('experiments/results/'+baseline['run_id']+'/development_predictions.json');errors=[r for r in rows if r['label']==1 and r['probability_occupied']<.25]
    assert len(errors)==2 and {r['slot_id'] for r in errors}=={'37'}
    write(E.relative_to(ROOT)/'confident_false_vacant_development_examples.json',dict(rows=errors,scope='Same slot37/twoframes;source ground truth,not independently re-annotated;development only'))
    pointer=dict(run_id=baseline['run_id'],member_qualification_run=members['run_id'],development_frames=12,development_dates=3,development_cameras=2,
        labelled_slots=720,hard_accuracy=baseline['overall']['hard_accuracy'],hard_errors=17,confident_false_vacant=2,uncertain=14,
        development_gate_passed=baseline['development_reliability_gate_passed'],production_promoted=False,checkpoint_unchanged=True,
        final_manifest='data/manifests/pklot_fresh_final_v2.json',final_manifest_sha256=digest(final),final_frames=6,final_groups=3,final_pixels_decoded=0,final_labels_parsed=0,
        guide='docs/FRESH_PARKING_DATA_GUIDE.md',limitations='Development crop-only metric,not final/live/fused-pipeline accuracy;2of4confidentvacant predictions wrong onUFPR052013-02-28despite aggregate gate pass')
    write('reports/fresh_parking_baseline_latest.json',pointer)
    inv=read('data/dataset_inventory.json');inv['inventoried_at']=datetime.now(timezone.utc).isoformat();inv['fresh_pklot_member_qualification']=members['summary'];inv['fresh_pklot_classifier_baseline']=pointer
    for row in inv['datasets']:
        if row['source_id']=='SRC-DS-001':row.update(fresh_development=pointer,fresh_member_qualification=members['summary'])
    write('data/dataset_inventory.json',inv)
    state.update(last_updated_at=datetime.now(timezone.utc).isoformat(),fresh_pklot_member_qualification=members['summary'],fresh_pklot_classifier_baseline=pointer)
    state['next_actions']=[
        'Next prespecify and run the UNCHANGED actual detector+classifier occupancy-fusion pipeline on the12fresh development frames,compare with crop-only baseline720labels. Test whether vehicle evidence catches the2confident false-vacants onUFPR05slot37at17:55/18:10Feb28. Report per-date vacancy precision,uncertainty/coverage and errors;do not change weights/thresholds or claim improvement until measured.',
        'Frozen crop-only baseline fresh development:703/720correct(97.6389%),17harderrors,2confident false-vacants/90confidentvacant predictions,14uncertain. Gate passes coarse preset overall/date bounds,but onFeb28only4confidentvacants with2wrong;not safe-vacancy guarantee. No production promotion or final/live score.',
        'Fresh licensed member qualification passed:12development frames/3dates/2cameras,720explicit labels;6final frames/3camera-date groups raw-copied/hashed but final JPEG pixels/XML labels remain unopened/unparsed. New final manifest data/manifests/pklot_fresh_final_v2.json stays closed. Byte duplicate check passed against receipt fingerprints;perceptual duplicates not ruled out.',
        'Only after a suitably qualified frozen candidate and protocol,claim the6newfinal frames once with holdouts.evaluate_final_once before pixels/labels. Reserve the scarce final for a prespecified paired original/candidate evaluation,not repeated tuning. Earlier image/Birmingham/DAVIS finals remain consumed. Known cameras/new dates,not new-carpark generalization.',
        'CNR144965metadata rows qualified and32079final records remain unopened;image-content rights unqualified,keep images inspection-only.191software regressions pass;current combined419-file package remains an older verified snapshot,do not rebuild for each counter. Student/manual/physical/browser/official acceptance still incomplete.',
        'Counter47,next100-run live checkpoint100,no active jobs. Last actualSingapore00:23UTC37snapshots,30614matched baseline outcomes/MAE4.391684;0new scores after account gap,new1191forecasts frozen. Next sensible collection after00:53UTC;missed targets unscored. Source57and exact local-copy/acquisition lineage retained.'
    ];write('data/automation_state.json',state)
    title='## 26 October 2026 / fresh development members and frozen classifier baseline'
    note='''New licensed raw members qualified:36JPEG/XMLfiles copied unchanged from the existing archive,not newly downloaded. Cross-identity byte hashes checked against source receipts and selected members;no collision.12fixed development frames over3dates/2known cameras contain720explicit occupancy labels,no unknowns.6final frames over3whole camera/date groups are materialized only as raw byte copies/hashes;JPEG pixels not opened and XML labels not parsed. Final reservationv2 remains unclaimed/closed. Perceptual duplication not audited. Frozen original ResNet18crop classifier scores703/720correct(97.6389%)on DEVELOPMENT,17harderrors,2confident false-vacants,14uncertain at unchanged0.25/0.75bands. Per-date hard accuracies1.000/0.9625/0.93125. Coarse preset gate passes,but2of4confidentvacant predictions onUFPR052013-02-28are wrong,bothslot37at17:55/18:10;aggregate accuracy is not vacancy-safe precision. No new training,settings change,production promotion,final/live or end-to-end fused-pipeline accuracy. Two distinct recorded trials:member qualification46and fresh baseline47;not per-frame/crop counts.191software tests remain the prior regression evidence. Actual local-copy receipt times are logging times;copy-event times bounded by run start/end,not fabricated exact network downloads. Next:measure unchanged detector/classifier fusion on these development frames with per-date vacancy/error/uncertainty gates. Final6kept for a frozen qualified paired comparison. Guide:docs/FRESH_PARKING_DATA_GUIDE.md;pointer:reports/fresh_parking_baseline_latest.json.'''
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md']:append(p,title,note)
    append('docs/DATASET_PROVENANCE.md',title,'Raw selected PKLot members are copied/hashed with archive/source/member lineage. Twelve development images decoded/annotations parsed;all720labels explicit. Six final raw JPEG/XMLfiles copied but pixels/labels unviewed/unparsed,whole3date groups closed. No new network acquisition. Source receipt hashes rule out only encoded-byte duplicates,not perceptual duplicates.')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;requirements=list(r)
    for row in requirements:
        if row['requirement_id']=='DATA-02':row['actual_evidence']+='; models/pklot_fresh_member_qualification.json';row['test_result']+=';36fresh raw members hash-qualified,12development frames/720explicit labels,final6pixels/labelsclosed';row['open_problems']+=';perceptual duplicates not audited'
        if row['requirement_id']=='CLS-03':row['actual_evidence']+='; models/pklot_fresh_classifier_baseline.json';row['test_result']+=';fresh DEVELOPMENTcrop-only703/720correct,2confidentfalsevacants/14uncertain;not final/live/fusion accuracy';row['open_problems']+=';Feb28vacancy precision2/4in tiny subgroup;unchanged full-fusion evaluation next'
    with path.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(requirements)
    write(E.relative_to(ROOT)/'baseline_checks.json',dict(completed_trials=47,source_records=57,software_regressions=191,development_labelled_slots=720,hard_correct=703,
        confident_false_vacants=2,uncertain=14,final_pixels_or_labels_read=0,original_classifier_unchanged=True,production_promoted=False,
        next_live_milestone=100,no_active_jobs=True,new_neural_training=False))
    print(json.dumps(dict(completed_trials=47,development_correct=703,development_slots=720,confident_false_vacant=2,final_test_closed=True),indent=2))
if __name__=='__main__':main()
