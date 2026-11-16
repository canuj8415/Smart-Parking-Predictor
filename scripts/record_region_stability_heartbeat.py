"""Save failed/passed regional studies, consumed image groups and next actions."""
import csv,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import torch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.region_consensus import compose_mask
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.live import parse_feed
from train_region_transfer import scores
A='REGION-CONSENSUS-20261025T104301553632Z';B='REGION-STABILITY-20261025T104606763875Z';F='REGION-STABILITY-FINAL-20261025T105044848266Z'
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T103727Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def table_read(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as s:
        r=csv.DictReader(s);return r.fieldnames,list(r)
def table_write(p,fields,rows):
    with (ROOT/p).open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=fields,quoting=csv.QUOTE_ALL if p=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);w.writeheader();w.writerows(rows)
def append(p,text):
    title='25 October 2026 / conditional known-camera region stability'
    path=ROOT/p;old=path.read_text(encoding='utf-8')
    if title not in old:path.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();a=read('experiments/results/'+A+'/run.json');b=read('experiments/results/'+B+'/run.json');f=read('experiments/results/'+F+'/run.json');final=f['final_evaluation']
    assert not a['validation_gate_passed'] and b['validation_gate_passed'] and final['final_gate_passed']
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 130 tests',tests) and tests.rstrip().endswith('OK')
    for p,h in f['source_hashes'].items():assert digest(ROOT/p)==h,p
    # The first failed policy remains exactly reproducible with the default branch.
    bundle=torch.load(ROOT/'experiments/results'/A/'candidate.pt',map_location='cpu',weights_only=True)
    priors={c:{k:v.numpy() if isinstance(v,torch.Tensor) else v for k,v in prior.items()} for c,prior in bundle['priors'].items()}
    rows=read('data/manifests/region_broader_development_v1.json')['frames'];rows=[r for r in rows if r['split']=='validation']
    for i,r in enumerate(rows):
        neural=(np.asarray(Image.open(ROOT/'experiments/results'/A/f'validation_neural_{i:02d}.png'))>0)[None]
        expected=np.asarray(Image.open(ROOT/'experiments/results'/A/f'validation_hybrid_{i:02d}.png'))>0
        assert np.array_equal(compose_mask(neural,r['camera_id'],priors)[0],expected)
    arrays={name:np.stack([(np.asarray(Image.open(ROOT/'experiments/results'/F/f'final_{name}_{i:02d}.png'))>0)[None] for i in range(6)]) for name in ['hybrid','neural','majority','truth']}
    for name,key in [('hybrid','hybrid'),('neural','frozen_neural'),('majority','train_majority')]:assert scores(arrays[name],arrays['truth'],final['frames'])==final[key]
    production=read('experiments/evidence/HEARTBEAT-20261025T100726Z/production_unchanged.json')
    for p,h in production.items():assert digest(ROOT/p)==h
    write(E.relative_to(ROOT)/'production_unchanged.json',production)
    manifest=ROOT/'data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json'
    assert digest(manifest)==f['holdout_manifest_sha256']
    try:assert_holdout_closed(manifest)
    except ValueError as error:assert 'overlaps' in str(error)
    else:raise AssertionError('Final image groups must be consumed')
    claims=list((ROOT/'data/holdout_claims').glob('*.claim.json'));owned=[p for p in claims if read(p.relative_to(ROOT))['run_id']==F];assert len(owned)==1
    claim=read(owned[0].relative_to(ROOT));outcome=read(owned[0].with_suffix('.outcome.json').relative_to(ROOT));assert outcome['status']=='completed; holdout consumed' and len(claim['source_groups'])==3
    write(E.relative_to(ROOT)/'output_checks.json',dict(tests_passed=130,failed_policy_saved_mask_replay_exact=True,final_mask_metrics_exact_from_saved_pngs=True,raw_final_images_reopened_for_checks=False,model_inference_repeated_for_checks=False,
        consumed_image_frames=6,consumed_camera_date_groups=claim['source_groups'],claim_sha256=digest(owned[0]),outcome=outcome,figure_visually_reviewed=True,figure_sha256=digest(ROOT/'experiments/results'/F/'mask_comparison.png'),
        architecture_note='No new neural gradient training. Two cameras use stored geometry only; UFPR04 uses CNN only. Image-only limits remain.'))
    for name,result in [('region_consensus_failed.json',a),('region_stability_candidate.json',b),('region_stability_final.json',f)]:write('models/'+name,result)
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()];receipt=[r for r in receipts if r['source_id']=='SRC-LIVE-001'][-1]
    payload=read(receipt['local_path']);observations=parse_feed(payload);raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert digest(ROOT/receipt['local_path'])==receipt['sha256'] and len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in observations})==len(observations)
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_observations=len(observations),raw_records=raw_count,invalid_capacity_excluded=raw_count-len(observations),duplicates=0,
        bounds_valid=all(0<=r['available']<=r['capacity'] for r in observations),feed_age_seconds=(datetime.fromisoformat(live['checked_at'])-datetime.fromisoformat(receipt['provider_timestamp'])).total_seconds(),
        interpretation='1137 earlier frozen persistence forecasts newly matched later readings;58old missing targets expired. No neural/camera/region accuracy inferred from this feed.'))
    fields,registry=table_read('experiments/EXPERIMENT_REGISTRY.csv')
    for ident,r in [(A,a),(B,b),(F,f)]:
        if any(row['experiment_id']==ident for row in registry):continue
        metrics=r['validation'] if ident!=F else r['final_evaluation']['hybrid']
        record=dict(experiment_id=ident,run_type='Training-geometry fitting plus frozen known-camera development evaluation' if ident!=F else 'One-time guarded known-camera regional-mask final evaluation',started_at=r['started_at'],finished_at=r['finished_at'],source_ids='SRC-DS-001;SRC-MOD-003',split_ids='Broader141train/24development; final closed' if ident!=F else 'Sealed6images/3camera-date groups, now consumed',configuration='experiments/results/'+ident+'/protocol.json',architecture=r['method'],model_version=r['checkpoint_sha256'],epochs=0,batch_size=4,random_seed=r['seed'],hardware='CPU; Torch4/BLAS1/OMP2/MKL2',execution_environment='Python3.12.10; existing Torch2.14.0+cpu',training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(metrics),logs='experiments/results/'+ident,checkpoints='experiments/results/'+(ident if ident!=F else B)+'/candidate.pt',code_revision_basis=r['code_revision_basis'],implementation_sha256=r['source_hashes']['scripts/evaluate_region_consensus.py' if ident!=F else 'scripts/evaluate_region_stability_final.py'],conclusions='Rejected:overallIoU0.840 but changing camera0.448 fails; failure retained' if ident==A else 'Known-camera router development0.911, quality/added-value gates pass; stable cams geometry-only' if ident==B else 'Six-image final routerIoU0.910, gate passes; UFPR04CNN0.662; two other cams geometry-only, not new neural accuracy; small known-camera scope')
        registry.append({k:record.get(k,'') for k in fields})
    table_write('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==27
    assert all(sum(r['experiment_id']==ident for r in registry)==1 for ident in state['completed_run_ids'])
    state.update(scheduled_wakeups_completed=16,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['region_stability']=dict(failed_policy_run=A,development_run=B,final_run=F,conditional_final_gate_passed=True,final_iou=final['hybrid']['overall']['pixel_iou'],image_only_cnn_iou=final['frozen_neural']['overall']['pixel_iou'],geometry_iou=final['train_majority']['overall']['pixel_iou'],effective_cnn_controlled_fraction=final['effective_cnn_controlled_fraction'],final_image_groups_consumed=True,production_promoted=False,scope='Six known-camera images; stored geometry for2cams, CNN for1; no automatic layout/slot-ID or unseen-view claim')
    state['best_development_region']['final_reservation_consumed']=True
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;13scored issue cohorts; separate Singapore source, not neural or camera accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Image final6 and all three camera/date groups are CONSUMED. Forecast Dec8–11 and Dec12–19 also consumed. Never tune on or evaluate changed methods on those groups, including different images on the same capture date. Preserve claims/outcomes and every failed experiment; reserve genuinely fresh groups before further model changes/evaluation.',
        'Known-camera stability router passes its conditional six-image final gate, but two views are geometry-only and changing-cameraCNNIoU0.662 is weak. Original image-only models and production preview remain unchanged. Any runtime use needs explicit view/camera provenance and regression/visible checks; same dimensions are insufficient. Do not claim automatic slots/unseen-camera discovery.',
        'Prioritize occupancy training-only robustness (one observed false vacancy remains), legitimately licensed independently labelled flow evaluation, application visible/native-save and physical/fresh offline acceptance. Further image-only mask improvements require fresh final groups; no final-label tuning. MetaPKLot remains inspection-only until scope verified.',
        'Next Singapore collection: match frozen10:38 forecasts only to actual later fresh same-capacity observations. Current14638scored/4754expired/1181pending at10:38. Counter27; separate100-run live checkpoint at100.',
        'Update report/presentation as new dated versions from verified forecast and conditional mask results; do not rewrite historical snapshots. Report compilation, university documents and independent student rehearsal remain outstanding. New explanation:docs/REGION_STABILITY_GUIDE.md.'
    ]
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-001':item['conditional_region_final']=state['region_stability']
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in observations}),observations=len(observations),raw_lot_records=raw_count,provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    overview='''Three bounded regional-mask trials completed without new neural gradient training.
First unanimity-pixel hybrid:developmentIoU0.840285 vs frozenCNN0.797653 and
train-majority0.767625, but UFPR04drops0.667330->0.448052, so gate FAILS. It
locks old background on a changing view. Failure, exact old code/bundle/masks and
replay retained. Revised rule uses stored geometry only if ALL training masks for
a camera are identical; ANY variation routes the WHOLE view to frozenCNN. This
rule uses training geometry, not camera names or final labels. Reused-development
score0.910914, UFPR04unchanged0.667330; quality and added-value gates pass.

One guarded final test decoded the sealed6later-date images only after a flushed
exclusive claim. RouterIoU0.910393/Dice0.953095 vs frozenCNN0.802893 and
train-majority0.767625. Quality/added-value gates PASS. UFPR04isCNN-onlyIoU0.662114;
PUCPR/UFPR05areGEOMETRY-ONLYIoU1.0on2images each. Those perfect stored-geometry
scores are NOT neural image inference evidence. Six known-camera samples/3dates,
no automatic slot IDs/new-camera discovery or reliable moved-camera handling.
Production models/preview unchanged. Original pure-image quality limitations remain.

Image holdout guard now claims camera/date groups as well as exact frames. It
requires group metadata; same-day different-frame reservations are blocked.130tests
pass (5new composition tests plus2date-guard checks). All6finalimages and3camera/date
groups are CONSUMED; no changed-method re-evaluation/tuning, including other frames
on the same dates. Forecast final groups also remain consumed. Original reservation
bytes unchanged; durable claims/outcomes tracked.3production hashes unchanged.

Saved final mask metric arithmetic and first failed-policy masks replay exactly;
no raw final image/XML reopened or model inference repeated for those checks.
Credited comparison figure built only from saved final PNGs, visually reviewed.
New explanation/data locations:docs/REGION_STABILITY_GUIDE.md. Three real trials
advance counter27; no active jobs; next separate100-run live checkpoint100. Future
model changes need genuinely fresh final groups. Occupancy false-vacancy, labelled
flow, camera/view provenance, UI/offline, report/university/student limits persist.

Official10:38 snapshot20 saved rawJSON/normalizedCSV/receipt/URL/SHA.1137prior
frozen persistence forecasts newly matched later observations:14638scored total,
MAE4.249898spaces;4754expired/1181pending;75.48%resolved matching, not accuracy.
1088new forecasts frozen. No camera/region/neural live score inferred from Singapore.'''
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/TEST_RESULTS.md','130software tests pass. Failed unanimity study retained; stable-camera route development and one-time six-image final pass their conditional gates. Final routerIoU0.910393 with two geometry-only views; UFPR04CNN-only0.662114. Stored mask metric and failed-policy replay checks exact; no extra final inference.3production hashes unchanged. Image/date claims consumed; source groups prevent same-day new-frame reuse. Evidence:HEARTBEAT-20261025T103727Z.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant designed two training-geometry routing hypotheses, retained the failed rule, ran the fixed revised rule and one claimed final test, strengthened image holdout grouping, tested five mask/two group-guard cases, plotted saved masks and wrote the student guide. No new neural weight improvement, automatic slot discovery, production promotion, student mastery or live-neural accuracy is claimed.')
    append('docs/PROJECT_CONSTRAINTS.md','The six image-final frames and all3camera/date groups are now CONSUMED under data/holdout_claims. Image guard requires explicit group metadata and rejects same-day alternative frames. Do not tune on or evaluate changed vision methods on these groups. Use genuinely fresh groups for future changes. Conditional known-camera router passed; two cameras use stored geometry only, not image-based neural segmentation. Original production preview unchanged.')
    append('docs/RESEARCH_LOG.md','Reused PKLot SRC-DS-001/UFPR/Almeida and colleagues under recorded CC BY4.0 plus existing ImageNet ResNet18 weights SRC-MOD-003. Project-designed stability routing; no externally attributed algorithm invented. Fitted camera geometry from141training masks/18dates; no final masks used for fitting/selection. Credited figure shows saved derived final images/masks only. Singapore source remains distinct.')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Nineteen authorized public snapshots acquired','Twenty authorized public snapshots acquired').replace('Twelve prospective persistence cohorts scored','Thirteen prospective persistence cohorts scored').replace('13,501 matched later outcomes, MAE4.191','14,638 matched later outcomes, MAE4.250').replace('123 tests pass; network-disabled-process image check passes','130 tests pass; network-disabled-process image check passes')
    s=s.replace('| Learned semantic spaces | Original experimental model plus separately saved candidates | Original finalIoU0.252; prior fresh-final candidate0.481; higher-resolution common-grid development0.796 vs reference0.771/geometry0.768, gate failed, new final closed; no promotion or slot-ID claim |','| Parking-region masks | Image-only models plus conditional known-camera router | Conditional six-image finalIoU0.910 passes; two views geometry-only, one CNN0.662. Image-only limitations remain; final groups consumed, original preview unchanged; no automatic slot-ID claim |')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','Conditional known-camera region route finalIoU0.910 on6images passes;2camsgeometry-only, UFPR04CNN0.662. Pure-image limitations unchanged; no production promotion. Initial hybrid failed and remains saved. All image-final camera/date groups now consumed.130tests; counter27. Live20snapshots/14638matched persistence outcomes,MAE4.249898. See docs/REGION_STABILITY_GUIDE.md; remaining operational/academic limits above persist.')
    fields,requirements=table_read('docs/REQUIREMENTS.csv')
    for item in requirements:
        if item['requirement_id']=='SEG-02':item.update(actual_evidence=item['actual_evidence']+'; models/region_consensus_failed.json; models/region_stability_final.json; REGION-STABILITY-FINAL-20261025T105044848266Z',test_result='Conditional known-camera finalIoU0.910;2geometry-only views,1CNNview0.662;130software tests. Failed0.840unanimity rule preserved.',open_problems='Not pure-image segmentation improvement or automatic slot IDs;6known-camera images only; geometry/camera identity/view must match; final groups consumed; original app preview unchanged',next_action='Source/view provenance and runtime integration only within tested scope; pure-image changes require genuinely fresh final groups; preserve all failures')
    table_write('docs/REQUIREMENTS.csv',fields,requirements)
    fields,sources=table_read('data/source_manifest.csv')
    for item in sources:
        if item['source_id']=='SRC-DS-001' and F not in item['used_by']:item['used_by']+='; '+A+'; '+B+'; '+F+' (camera/date groups consumed; geometry-dependent router); credited figure'
    table_write('data/source_manifest.csv',fields,sources)
    print(json.dumps(dict(counter=27,tests=130,conditional_final_iou=final['hybrid']['overall']['pixel_iou'],camera_date_groups_consumed=3,production_changed=False),indent=2))
