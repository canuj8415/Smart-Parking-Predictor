"""Record licensed sequence acquisition, indexed tracking and scoped development."""
import csv,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
D='DAVIS-DATA-20261025T112046003173Z';V='DAVIS-FOREGROUND-20261025T112345510431Z'
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T110727Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def table_read(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as s:
        r=csv.DictReader(s);return r.fieldnames,list(r)
def table_write(p,fields,rows):
    with (ROOT/p).open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=fields,quoting=csv.QUOTE_ALL if p=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);w.writeheader();w.writerows(rows)
def append(p,text):
    title='25 October 2026 / licensed labelled sequences and frame-index tracking'
    path=ROOT/p;old=path.read_text(encoding='utf-8')
    if title not in old:path.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    failed_attempt=V
    V=next(i for i in reversed(read('data/automation_state.json')['completed_run_ids']) if i.startswith('DAVIS-FOREGROUND-'))
    now=datetime.now(timezone.utc).isoformat();data=read('experiments/results/'+D+'/run.json');run=read('experiments/results/'+V+'/run.json');metrics=run['metrics'];acq=read('data/raw/davis2017_metadata/subset_acquisition.json')
    assert data['data_gate_passed'] and not run['final_sequence_evaluated']
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 139 tests',tests) and tests.rstrip().endswith('OK')
    for p,h in run['source_hashes'].items():
        if digest(ROOT/p)!=h:
            original=read('experiments/results/'+V+'/implementation_sources.json')[p]['source']
            corrected=original.replace('SRC-DS-011','SRC-DS-012').replace('davis_car_sequences_v1.json','davis_car_sequences_v2.json')
            assert (ROOT/p).read_text(encoding='utf-8')==corrected,'Only documented metadata relabelling may differ'
    production=read('experiments/evidence/HEARTBEAT-20261025T103727Z/production_unchanged.json')
    for p,h in production.items():assert digest(ROOT/p)==h
    write(E.relative_to(ROOT)/'production_unchanged.json',production)
    write('models/davis_foreground_development.json',dict(**{k:v for k,v in run.items() if k!='source_ids'},source_ids=['SRC-DS-012','SRC-MOD-001'],original_recorded_source_ids=run['source_ids'],source_id_correction='data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json'))
    reservation=ROOT/'data/manifests/davis_car_roundabout_final_v2.json'
    correction=read('data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json')
    assert digest(reservation)==correction['corrected_v2_reservation_sha256']
    assert digest(ROOT/'data/manifests/davis_car_roundabout_final_v1.json')==data['reservation_sha256']
    records=read('experiments/results/'+V+'/frame_records.json');assert len(records)==80
    assert all('video_time_seconds' not in e for r in records for e in r['tracking']['events'])
    write(E.relative_to(ROOT)/'checks.json',dict(tests_passed=139,frames_processed=80,reserved_sequence='car-roundabout',reserved_sequence_frames=75,reservation_sha256=digest(reservation),reserved_pixels_decoded=False,reserved_annotation_values_decoded=False,production_weights_unchanged=True,physical_fps_known=False,frame_events_have_no_fabricated_seconds=True,precision_or_exhaustive_accuracy_evaluable=False))
    fields,sources=table_read('data/source_manifest.csv')
    if not any(r['source_id']=='SRC-DS-012' for r in sources):
        values=dict(source_id='SRC-DS-012',resource_type='dataset / original labelled image sequences',resource='DAVIS2017 car-turn and car-roundabout original JPEG frames / publisher foreground masks',original_creator='Jordi Pont-Tuset; Federico Perazzi; Sergi Caelles; Pablo Arbelaez; Alexander Sorkine-Hornung; Luc Van Gool',source_url='https://davischallenge.org/davis2017/code.html',download_url=acq['archive_url'],access_date=acq['acquired_at'],access_time_precision='Actual UTC per-file receipts; metadata review25October2026',version='Official2017TrainVal480p ZIP; ETag'+acq['archive_etag'],license='Dataset aggregate CC BY-NC4.0; README author-owned sequence default; selected2sequences absent from SOURCES.md external exceptions',permission='Local noncommercial academic use with attribution; no accounts/restricted agreement accepted; no commercial deployment/publication performed',original_size='Archive832766765bytes; original subset20197285bytes/310members; full archive NOT acquired',local_location='data/raw/davis2017_subset/; data/raw/davis2017_metadata/; data/raw/davis2017_ranges/',sha256='Per-member/range SHA256 and ZIP CRC in receipts/acquisition manifest; whole archive SHA unknown',purpose='Real foreground detection/tracking and image-plane crossing development; reserved unseen sequence',used_by=D+'; '+V+'; frame-index tracking tests',modifications='Original members unchanged; derived bbox/reference crossings from publisher object1 mask; original fps unestablished',attribution='DAVIS authors; Pont-Tuset et al.2017; Perazzi et al.2016; https://davischallenge.org/ ; CC BY-NC4.0; see source README/SOURCES',status='acquired / development evaluated; car-roundabout reserved unopened',open_issues='Foreground labels are partial traffic ground truth; no exhaustive precision/mAP/parking occupancy; original fps unknown; source/pretrained overlap not audited; final sequence guard/evaluation pending')
        sources.append({k:values.get(k,'') for k in fields})
    table_write('data/source_manifest.csv',fields,sources)
    fields,registry=table_read('experiments/EXPERIMENT_REGISTRY.csv')
    if not any(r['experiment_id']==failed_attempt for r in registry):
        original=read('experiments/results/'+failed_attempt+'/protocol.json')
        failure=dict(experiment_id=failed_attempt,run_type='Interrupted reporting attempt; NOT counted as completed experiment',started_at=original['started_at'],source_ids='SRC-DS-012;SRC-MOD-001',split_ids='car-turn development only',configuration='experiments/results/'+failed_attempt+'/protocol.json',architecture='Frozen Faster R-CNN plus frame-index tracker',epochs=0,evaluation_metrics='No valid metrics saved',logs='experiments/results/'+failed_attempt,implementation_sha256=original['source_hashes']['scripts/evaluate_davis_development.py'],conclusions='80frames processed, then TypeError from duplicate metrics keyword prevented report serialization. Progress/interrupted evidence retained; writer fixed, per-frame journal added before fresh development rerun. No threshold/model tuning or final use.')
        registry.append({k:failure.get(k,'') for k in fields})
    for ident,r in [(D,data),(V,run)]:
        if any(x['experiment_id']==ident for x in registry):continue
        values=dict(experiment_id=ident,run_type='Original-byte/header data-readiness validation' if ident==D else 'Frozen labelled-foreground development evaluation; partial annotation scope',started_at=r['started_at'],finished_at=r['finished_at'],source_ids='SRC-DS-012' if ident==D else 'SRC-DS-012;SRC-MOD-001',split_ids='car-turn development80; car-roundabout reserved75',configuration='experiments/results/'+ident+'/protocol.json',architecture='ZIP range/CRC/header membership checks' if ident==D else 'Frozen Faster R-CNN ResNet50 + frame-index GateCounter',model_version='Data only' if ident==D else r['detector_sha256'],epochs=0,batch_size=1,random_seed=r['seed'],hardware='CPU; Torch4/BLAS1/OMP2/MKL2',execution_environment='Python3.12.10; existing Torch/OpenCV/Pillow',training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(dict(data_gate_passed=True,frames=155,original_files=310)) if ident==D else json.dumps(metrics),logs='experiments/results/'+ident,checkpoints='No new weights',code_revision_basis='b0389db plus sealed exact source snapshots',implementation_sha256=r['source_hashes']['scripts/audit_davis_subset.py' if ident==D else 'scripts/evaluate_davis_development.py'],conclusions='310paired original files verified,155frame pairs; final75pixel/label values unopened; no model accuracy' if ident==D else 'Single annotated car development; recall/crossing recovery only, no exhaustive precision or physical-time/parking-flow accuracy; see run metrics')
        registry.append({k:values.get(k,'') for k in fields})
    table_write('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(s) for s in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()];receipt=[r for r in receipts if r['source_id']=='SRC-LIVE-001'][-1];payload=read(receipt['local_path']);rows=parse_feed(payload)
    assert digest(ROOT/receipt['local_path'])==receipt['sha256'] and len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})==len(rows)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_observations=len(rows),raw_records=raw_count,invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),feed_age_seconds=(datetime.fromisoformat(live['checked_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds(),interpretation='1046previously frozen persistence forecasts newly matched later targets;93old missing targets expired. No neural/camera accuracy.'))
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==29
    assert all(sum(r['experiment_id']==i for r in registry)==1 for i in state['completed_run_ids'])
    state.update(scheduled_wakeups_completed=17,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['davis_sequences']=dict(data_audit_run=D,development_run=V,metrics=metrics,development_diagnostic_gate_passed=run['diagnostic_gate_passed'],source_id='SRC-DS-012',final_sequence='car-roundabout',final_frames=75,final_pixels_unopened=True,physical_fps_known=False,scope='Single labelled foreground car, image-plane crossings; no exhaustive traffic precision/accuracy')
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;14scored issue cohorts; separate from neural/camera studies.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'DAVIS car-roundabout75frames is RESERVED and pixel/annotation values unopened. Implement/test a durable exclusive source/whole-SEQUENCE final claim before any final decoding; failures consume the whole sequence. Freeze a valid reference/partial-label scoring protocol first; no invented physical fps/timestamps. The new tracker has explicit frame units; video-file processing rejects frame configs.',
        'DAVIS car-turn midpoint line had ZERO reference crossings, so event recall is NOT EVALUABLE, despite75/75labelled-car box matches. Tracking only74/75frames and dominant identity53/75 shows fragmentation. Next use saved detections for a predeclared setup-only gate-calibration replay, not another detector run; do not use reserved sequence labels. No full counting-accuracy claim.',
        'All previous image camera/date finals and Birmingham final dates remain CONSUMED. Never reuse those groups for changed-method evaluation/tuning. Preserve new licence/rights snapshots, original ranges/members, receipts and source hashes. Two DAVIS sequences are source-owned defaults, local noncommercial academic use only.',
        'Continue occupancy training-only robustness, labelled flow final protocol, application native/visible/fresh-offline acceptance, report/presentation updates and student explanations. Conditional region routing remains geometry-dependent; no production promotion or unseen-camera claim. MetaPKLot remains inspection-only.',
        'Next official Singapore collection: score frozen11:09forecasts only against actual later fresh same-capacity readings. Current15684scored/4847expired/1291pending at11:09. Counter29; separate100-run live checkpoint at100.'
    ]
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    if not any(r['source_id']=='SRC-DS-012' for r in inventory['datasets']):inventory['datasets'].append(dict(source_id='SRC-DS-012',status='acquired_development_evaluated_final_sequence_reserved',original_files=310,frame_pairs=155,member_bytes=20197285,archive_fully_downloaded=False,full_archive_sha256=None,archive_etag=acq['archive_etag'],used_for_model_training=False,used_for_model_evaluation=True,source_manifest='data/manifests/davis_car_sequences_v2.json',reserved_final_manifest='data/manifests/davis_car_roundabout_final_v2.json',development_run=V,reserved_pixels_decoded=False,licence='DAVIS aggregate CC BY-NC4.0; selected author-owned sequences; original README/SOURCES retained',physical_fps_known=False))
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    summary=f'''Acquired a new real annotated source, DAVIS2017 SRC-DS-012:310original members,
155frame/mask pairs,20,197,285member bytes from the official832,766,765byte archive
using bounded verified ranges (~21.5MB transferred in acquisition, not full ZIP).
ETag, local member/range SHA256 and ZIP CRC retained; full archive SHA unknown.
Official README/SOURCES and website/license snapshots reviewed: dataset CC BY-NC4.0;
car-turn/car-roundabout absent from external footage exceptions. Local noncommercial
academic use with author attribution; code BSD licence is not the dataset licence.

Roles fixed before pixel inspection:car-turn80frames development (first5setup),
car-roundabout75frames reserved final. Headers/pairing/hashes/consecutive names
verified; reserved pixel/annotation values remain unopened. Source fps not established.
Added explicit frame-index tracker mode and frame_index events; no invented physical
seconds. Timestamp-video/Desktop paths reject frame configs. Default-seconds behavior
replays exactly on25archived real street detection frames, without model rerun.
139software checks pass, including6new ZIP/time-unit and3reference-rule tests.

One frozen Faster R-CNN/ResNet50 development trial evaluated the publisher-labelled
foreground car only. Same fixed middle-image gate; known mask ID1 reference crosses
without predicted association. No parameter fitting. Actual metrics:{json.dumps(metrics)}.
Diagnostic gate={run['diagnostic_gate_passed']}. These are correlated frames of ONEcar,
not independent vehicles or exhaustive traffic labels. Extra predicted events cannot
establish precision/mAP/overall flow accuracy. Image-plane line is not a parking
entrance; camera motion and unknown fps preclude physical-time/speed claims. No
project training on DAVIS; upstream pretrained-data overlap not audited.

Initial80frame inference finished but reporting failed on a duplicate metrics keyword;
no valid scores were saved or counted. Failure/protocol/progress retained. Writer
fixed and append-only per-frame journal added before a frozen-parameter development
rerun. No final data or threshold/model tuning used to correct the software error.
Two completed trials advance counter29; no active jobs. Final sequence still needs
a durable whole-sequence claim and frozen protocol before decoding. All old image/
forecast final groups remain consumed.3production hashes unchanged. Source receipts,
split/weights/code/config hashes and original data preserved. New beginner guide:
docs/LABELLED_SEQUENCE_GUIDE.md. Other model/runtime/offline/report/student limits remain.

Official11:09snapshot21:1046earlier frozen persistence forecasts newly matched,
15684scored total,MAE4.330528spaces;4847expired/1291pending,76.39%resolved matching.
1249new forecasts frozen. This separate Singapore study is not neural/camera accuracy.'''
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,summary)
    append('docs/TEST_RESULTS.md','139software tests pass. New mode uses real frame indices and omits physical-time fields;25archived default-seconds tracker outputs match frozen implementation exactly. Original310DAVIS entries pass CRC/hash/header/pairing checks. Scoped foreground development metrics saved in '+V+'; no final-sequence evaluation or exhaustive traffic accuracy.3production hashes unchanged. Initial80frame attempt failed at report serialization, had no saved valid metrics and is not counted. Failure retained; fixed writer/per-frame journal before frozen-parameter rerun.')
    append('docs/PROJECT_CONSTRAINTS.md','DAVIS car-roundabout is reserved as an entire sequence:75frames, pixels and annotation values unopened. Use a tested durable source/whole-sequence claim before final decoding; failure consumes it. Unknown source fps must remain unknown; frame-index mode does not create physical timestamps. Publisher foreground masks are partial traffic ground truth; no exhaustive precision/mAP/occupancy or parking entrance accuracy claim. Dataset aggregate CC BY-NC4.0, local noncommercial academic use with attribution; selected sequences absent from external-source exceptions.')
    for p in ['docs/RESEARCH_LOG.md','docs/THIRD_PARTY_SOURCES.md']:append(p,'Primary DAVIS download page https://davischallenge.org/davis2017/code.html and official website licence schema reviewed25October2026. Official archive README/SOURCES preserved: aggregate CC BY-NC4.0, authors own sequences unless listed; car-turn/car-roundabout not external exceptions. Code repository BSD licence was not used as data permission. No third-party DAVIS code installed/copied; project-built bounded range decoder uses stdlibZIP/CRC. Exact URLs/times/ETag/ranges/member hashes in receipts;20MBoriginal subset, not full832MBarchive. Papers: Pont-Tuset et al.2017; Perazzi et al.2016. Foreground/reference and physical-fps limitations remain explicit.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant researched official source/rights, acquired original DAVIS subset with CRC/range provenance, reserved an unopened sequence, added frame-index tracking, derived rule-specific reference events from publisher masks and evaluated frozen detector development. Object1 visually reviewed as a car in setupframe0; no new human/student annotation claim. No weights trained or final sequence decoded. Foreground recall is not full traffic accuracy.')
    append('docs/LABELLED_SEQUENCE_GUIDE.md',f'''Completed scored run: `experiments/results/{V}/`.

| Development observation | Actual result |
|---|---:|
| Labelled car box matched | {metrics['annotated_car_detected_frames']}/{metrics['scored_visible_car_frames']} scored frames |
| Matched tracker identity present | {metrics['matched_tracking_frames']}/{metrics['scored_visible_car_frames']} frames |
| Dominant predicted identity share | {metrics['dominant_track_fraction']:.1%} |
| Label-derived crossings of the fixed midpoint line | {metrics['reference_events']} |
| Crossing recall | Not evaluable: no reference crossing |
| Exhaustive traffic precision | Not evaluable: foreground labels only |

This is one car seen repeatedly. Tracking fragments across a gap; zero consecutive
matched-ID switches does not prove uninterrupted identity. No crossing took place
under this particular gate rule, so its zero predicted count is not a positive
counting-accuracy test. Next, a setup-only gate placement can be tested using the
saved detections, without rerunning the neural detector or opening reserved data.
`recorded_at` in detector records is the processing time, not the filming time.''')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Twenty authorized public snapshots acquired','Twenty-one authorized public snapshots acquired').replace('Thirteen prospective persistence cohorts scored','Fourteen prospective persistence cohorts scored').replace('14,638 matched later outcomes, MAE4.250','15,684 matched later outcomes, MAE4.331').replace('130 tests pass; network-disabled-process image check passes','139 tests pass; network-disabled-process image check passes');p.write_text(s,encoding='utf-8')
    append('docs/IMPLEMENTATION_STATUS.md','New DAVIS foreground-labelled development evidence and frame-index tracker mode implemented.139tests; counter29. Separate75frame sequence reserved/unopened; unknown physical fps; no exhaustive traffic/parking-count accuracy. New guide docs/LABELLED_SEQUENCE_GUIDE.md. Latest live21snapshots/15684matched persistence outcomes,MAE4.330528; no neural live transfer.')
    fields,requirements=table_read('docs/REQUIREMENTS.csv')
    for item in requirements:
        if item['requirement_id'] in ['FLOW-01','VID-01']:
            item['actual_evidence']=item['actual_evidence'].replace('davis_car_sequences_v1.json','davis_car_sequences_v2.json')
            if 'models/davis_foreground_development.json' not in item['actual_evidence']:item['actual_evidence']+='; models/davis_foreground_development.json; data/manifests/davis_car_sequences_v2.json'
            item.update(test_result='139software tests; frozen foreground development:'+json.dumps(metrics),open_problems='One selected foreground car; image-plane crossing only; unknown fps; no exhaustive precision or parking entrance accuracy; reserved sequence final guard/evaluation pending')
    table_write('docs/REQUIREMENTS.csv',fields,requirements)
    write(E.relative_to(ROOT)/'research_review.json',dict(primary_download_page='https://davischallenge.org/davis2017/code.html',primary_dataset_licence_schema='https://davischallenge.org/',licence='https://creativecommons.org/licenses/by-nc/4.0/',selected_sequences_external_exceptions=False,rights_metadata_originals='data/raw/davis2017_metadata/README.md and SOURCES.md',code_licence_not_used_as_data_permission=True,source_id='SRC-DS-012'))
    print(json.dumps(dict(counter=29,tests=139,source_count=len(sources),metrics=metrics,final_sequence_unopened=True),indent=2))
