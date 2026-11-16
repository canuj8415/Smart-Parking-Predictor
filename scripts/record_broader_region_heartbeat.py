"""Record completed broader-data validation and the bounded training study."""
import csv,hashlib,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.live import parse_feed
DATA='REGION-DATA-20261025T004308948713Z';TRAIN='REGION-TRANSFER-20261025T004539209450Z'
EVIDENCE=ROOT/'experiments/evidence/HEARTBEAT-20261025T003925Z'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f);return r.fieldnames,list(r)
def table(path,fields,values):
    with (ROOT/path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL if path=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);w.writeheader();w.writerows(values)
def append(path,text):
    title='25October2026 / broader parking-region development'
    p=ROOT/path;old=p.read_text(encoding='utf-8')
    if title not in old:p.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();data=read('experiments/results/'+DATA+'/run.json');trained=read('experiments/results/'+TRAIN+'/run.json')
    assert not trained['final_images_decoded'] and not trained['production_changed']
    tests=(EVIDENCE/'unit_tests_after_training_changes.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 88 tests',tests) and tests.rstrip().endswith('OK')
    write(EVIDENCE.relative_to(ROOT)/'software_checks.json',dict(checked_at=now,tests_passed=88,failures=0,scope='Selector/date/identity guards, failed/tampered-audit training rejection and prior software suite; not camera accuracy'))
    weights=read('experiments/evidence/HEARTBEAT-20261025T000925Z/production_unchanged.json')
    for p,h in weights.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    write(EVIDENCE.relative_to(ROOT)/'production_unchanged.json',weights)
    receipts=[json.loads(x) for x in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
    live_receipts=[x for x in receipts if x['source_id']=='SRC-LIVE-001'];latest=live_receipts[-1]
    live=read('data/processed/singapore_prospective/summary.json');raw=read(latest['local_path']);valid=parse_feed(raw)
    assert len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in valid})==len(valid)
    assert hashlib.sha256((ROOT/latest['local_path']).read_bytes()).hexdigest()==latest['sha256']
    gap=(datetime.fromisoformat(latest['accessed_at'])-datetime.fromisoformat(live_receipts[-2]['accessed_at'])).total_seconds()/60
    write(EVIDENCE.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=latest,previous_collection=live_receipts[-2],collection_gap_minutes=gap,
        gap_cause='Not established; no intervening observations fabricated',accepted_lot_observations=len(valid),car_parks=len({r['car_park_id'] for r in valid}),
        raw_lot_records=sum(len(r['carpark_info']) for r in raw['items'][0]['carpark_data']),duplicate_keys=0,bounds_valid=True,
        scope='Persistence only; no neural/camera/flow live accuracy'))
    wall=(datetime.fromisoformat(trained['finished_at'])-datetime.fromisoformat(trained['started_at'])).total_seconds()
    write(EVIDENCE.relative_to(ROOT)/'timing_note.json',dict(started_at=trained['started_at'],finished_at=trained['finished_at'],reported_duration_seconds=trained['duration_seconds'],wall_timestamp_difference_seconds=wall,
        note='A substantial observed wall-clock/collection gap occurred during this invocation. Cause not established. No CPU-speed comparison or uninterrupted-operation claim.'))
    write('models/region_broader_data_card.json',data)
    fields,registry=rows('experiments/EXPERIMENT_REGISTRY.csv');existing={r['experiment_id'] for r in registry}
    for ident,result in [(DATA,data),(TRAIN,trained)]:
        if ident in existing:continue
        p='experiments/results/'+ident
        value=dict(experiment_id=ident,run_type='Broader selected-development data audit and frozen-model replay; no training' if ident==DATA else 'Bounded35epoch broader-development neural-region training; final closed',
            started_at=result['started_at'],finished_at=result['finished_at'],source_ids='SRC-DS-001;SRC-MOD-003',split_ids='Broader known-camera dates:141train/24validation; shared final6closed',
            configuration=p+'/protocol.json',architecture='Frozen original high-resolution candidate plus train-only geometry' if ident==DATA else result['architecture'],model_version=ident,
            optimizer='' if ident==DATA else result['optimizer'],learning_rate='' if ident==DATA else result['learning_rate'],epochs=0 if ident==DATA else result['epochs_completed'],batch_size='' if ident==DATA else 4,
            random_seed=result['seed'],hardware='CPU4 threads; BLAS1/OMP2/MKL2',execution_environment='Python3.12.10; Torch2.14.0+cpu',training_duration=result['duration_seconds'],
            loss_curves='' if ident==DATA else p+'/curves.json',evaluation_metrics=json.dumps(result['frozen_replay'] if ident==DATA else dict(validation=result['validation'],gate_passed=result['validation_gate_passed'],final_images_decoded=0)),
            logs=p,checkpoints='Existing frozen candidate only' if ident==DATA else p+'/candidate.pt',code_revision_basis='e525294 plus sealed protocol and exact implementation_sources.json',
            implementation_sha256=result['code_sha256']['scripts/audit_broader_regions.py'] if ident==DATA else result['code_sha256'],
            conclusions='165original image/XML pairs validated; no selected/protected exact duplicates; frozen priorIoU0.75852 vs geometry0.76762 on24newdevelopment frames' if ident==DATA else f"New same-cohort IoU{result['validation']['overall']['pixel_iou']:.5f}; gate_passed={result['validation_gate_passed']}; no final decoding/promotion; source clock gap disclosed")
        registry.append({k:value.get(k,'') for k in fields})
    table('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-001':item['broader_region_study']=dict(data_audit_run=DATA,training_run=TRAIN,development_manifest=data['development_manifest'],train_frames=141,validation_frames=24,
            training_dates=18,validation_dates=6,exact_duplicates=0,protected_final_decoded=0,model_promoted=False)
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in valid}),observations=len(valid),raw_lot_records=sum(len(r['carpark_info']) for r in raw['items'][0]['carpark_data']),provider_timestamp=latest['provider_timestamp'],raw_path=latest['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==18
    state.update(scheduled_wakeups_completed=11,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['best_development_region']['scope']='Historical six-frame development study; scores are not comparable directly with the broader cohort'
    state['broader_development_region']=dict(run_id=TRAIN,data_audit_run=DATA,validation_frames=24,validation_dates=6,validation_iou=trained['validation']['overall']['pixel_iou'],
        frozen_prior_same_cohort_iou=data['frozen_replay']['overall']['frozen_candidate']['pixel_iou'],geometry_iou=data['frozen_replay']['overall']['train_geometry']['pixel_iou'],
        gate_passed=trained['validation_gate_passed'],production_promoted=False,final_images_decoded=0)
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;8scored issue cohorts; source matching is not accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        f'Resume official collection for1184forecasts frozen08:25UTC at actual20-45min targets; missed00:40cohort windows remain unscored. Observed{gap:.1f}min collection gap has no established cause. Counter18; next separate100-run milestone100.',
        'Broader training completed; compare only on the same24newdevelopment frames. Shared final6stays closed and production unchanged. Do not compare the new cohort directly with the old six-frame0.79629. Preserve all candidates and failed gates before another prespecified change.',
        'Highest-impact next reliability check: predeclare a frozen occupancy-head evaluation on broader date-separated crops, reporting occupied/vacant confusion, false-vacancy errors and uncertainty; do not tune on reserved final dates. Consider further region geometry/boundary diagnosis using training data.',
        'Forecast candidates still fail per-park gates. Use preserved actual source/target times and appropriate unseen history for a bounded robustness hypothesis; no Birmingham-to-Singapore validation claim.',
        'MetaPKLot remains inspection-only. Gate counting needs labelled positive/negative footage and desktop editor. Presentation/guide are dated ready materials; report compilation, native save, offline/fresh setup, official documents and student rehearsal remain unfinished.'
    ]
    write('data/automation_state.json',state)
    iou=trained['validation']['overall']['pixel_iou'];gate=trained['validation_gate_passed']
    overview=f'''Prepared data/manifests/region_broader_development_v1.json before decoding:
141train images on18unused dates,24validation images on6later unused dates,
three represented cameras. All dates precede the existing per-camera final
boundaries. Previously used/original-test/semantic-test/known-study/reserved-final
dates excluded globally. Up to8train/4validation chronological samples per date.
All165original images/XML validated (camera, dimensions, polygons, nonempty
masks), with no selected exact duplicates or matches to protected image bytes.
Protected JPEGs were hash-only; final XML/images never decoded. Invalid raw date
labels stay rejected. Near-duplicate/perceptual independence remains unverified.

{DATA}: frozen old high-resolution candidate scores0.758518IoU on the new24
development frames, train-majority geometry0.767625. Per-camera frozen scores
0.80975/0.67802/0.75789. This differs from its old six-frame0.79629 cohort.
Training data contains3ufpr04geometries, other cameras1each; validation weather
is12sunny/12cloudy, with no rain validation. These are known-camera development
checks, not a new final or vehicle-mask benchmark.

{TRAIN}: bounded maximum35epochs, seed71, frozen ResNet18 plus unchanged
decoder,384x224input/common192x112selection, balanced coefficient4.574fixed
from prior train-only reference, Adam0.002,batch4,brightness augmentation,
patience12. Encoder caching chunks8frames to bound peak memory. Data/date/sample
count/optimization steps/budget differ from old studies, so no single-factor
causal claim. Best epoch{trained['best_epoch']}/{trained['epochs_completed']}; new common
IoU{iou:.6f} versus frozen0.758518/geometry0.767625 on SAME24frames. Validation
gate passed={gate}. New per-camera IoUs are0.86169/0.66733/0.81611;ufpr04
slightly regresses from frozen0.67802. The overall<0.80and stable-camera
geometry-retention rules fail. No automatic promotion or final decoding, even if a gate
passes. Selected checkpoint/source bytes, protocol hashes, curves, masks and
exact replay evidence retained. All3production checkpoint hashes unchanged.

88software checks pass, including5metadata-selector and2training-audit/budget
guards. New data audit plus real training are2completed recorded trials; counter
18,next100-run checkpoint100. Frames/epochs/tests are not separate runs. No
trainers remain active after completion. Clock/collection timestamps show a long
observed gap during this invocation; its cause is not established and runtime
does not establish uninterrupted training or a CPU-speed improvement.

Official snapshot00:40UTC added1200later matched outcomes/1230frozen forecasts.
After the observed00:40-to08:25gap, one fresh snapshot resumed history and froze
1184new forecasts with0new scores. Total14724issued/9074scored across8scored
issue cohorts, persistenceMAE3.7976637spaces.4466expired missing targets and
1184pending at08:25UTC. Matching9074/13540=67.02%among resolved entries is
not accuracy. Missing readings/scores and the reason for the gap are not invented.
All15raw snapshots/history/URLs/checksums remain; no neural/camera live accuracy.

Presentation/report/guide retain their earlier dated evidence. Official documents,
final report compilation, labelled parking-video, desktop gate editor, native
export-save, physical/fresh offline and unaided student checks remain unfinished.
Exact next actions in data/automation_state.json.'''
    for p in ['docs/AUTONOMOUS_PROGRESS.md','docs/PROJECT_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/TEST_RESULTS.md',f'88software checks pass. Broader data audit validated165selected original frames/XML and exact hash separation. Frozen priorIoU0.758518 and new candidateIoU{iou:.6f} on the SAME24newdevelopment frames; gate_passed={gate}. Full source/protocol/checkpoint replay and figure evidence retained. Shared final6closed,3production hashes unchanged. Clock/collection gap disclosed; no speed/continuous-operation claim.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant implemented metadata-only broader-date selection and fail-closed audit guards, validated165original frames/XML, replayed the frozen candidate, ran one bounded35epoch broader neural trial and88software checks, maintained exact source/checkpoint evidence and live collection. No student independent mastery, new-camera reliability, vehicle-mask accuracy or final-test score implied.')
    fields,sources=rows('data/source_manifest.csv')
    for source in sources:
        if source['source_id']=='SRC-DS-001' and 'broader141train' not in source['used_by']:source['used_by']+='; broader141train/24validation date study, protected final closed'
    table('data/source_manifest.csv',fields,sources)
    fields,requirements=rows('docs/REQUIREMENTS.csv')
    for q in requirements:
        if q['requirement_id']=='DATA-02':q['test_result']='165broader original images/XML validated; exact selected/protected hash checks pass; invalid source dates rejected; no full-archive or perceptual audit claim'
        if q['requirement_id']=='DATA-03':q['actual_evidence']+='; data/manifests/region_broader_development_v1.json';q['test_result']='18train/6later validation dates globally disjoint and before sealed final dates; no exact selected/protected image matches'
        if q['requirement_id']=='SEG-02':q.update(actual_evidence=q['actual_evidence']+'; models/region_broader_candidate.json',test_result=f'Broader same24frame IoU{iou:.6f} vs frozen0.758518/geometry0.767625; gate_passed={gate}; final6closed;88software checks')
    table('docs/REQUIREMENTS.csv',fields,requirements)
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Thirteen authorized public snapshots acquired','Fifteen authorized public snapshots acquired').replace('Seven prospective persistence cohorts scored','Eight prospective persistence cohorts scored').replace('7,874 matched later outcomes, MAE3.203','9,074 matched later outcomes, MAE3.798').replace('81 tests pass; network-disabled-process image check passes','88 tests pass; network-disabled-process image check passes')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md',f'Broader141train/24development candidateIoU{iou:.6f} vs same-cohort frozen0.758518, geometry0.767625. Gate_passed={gate}; no promotion/final decoding.88software checks pass;3production hashes unchanged. Counter18. Observed live gap disclosed;15snapshots/9074matched baseline outcomes, MAE3.79766 and67.02%resolved matching at08:25UTC. Dated slides and older six-frame metrics retain their original scope.')
    print(json.dumps(dict(counter=18,iou=iou,gate_passed=gate,live_scores=live['scores_total'],live_gap_minutes=gap),indent=2))
