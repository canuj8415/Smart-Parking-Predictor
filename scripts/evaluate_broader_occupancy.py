"""Frozen occupancy-head diagnostics on the broader development dates.

Classifier-only crop results cannot establish detector fusion or camera counts.
All thresholds and the diagnostic gate are fixed before inference.
"""
import csv,hashlib,json,os,sys,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import torch
from torchvision.models import resnet18
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.occupancy_evaluation import occupancy_metrics
from smart_parking.layout import read_pklot_xml,crop_slot
from smart_parking.vision import normalize_crop
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed

def evaluate():
    torch.set_num_threads(4);started=datetime.now(timezone.utc);clock=time.perf_counter()
    run='OCCUPANCY-BROADER-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state.get('active_training_jobs') or state.get('active_validation_jobs'):raise ValueError('Another recorded experiment is active')
    manifest=ROOT/'data/manifests/region_broader_development_v1.json';reserved=json.loads(manifest.read_text())
    audit=json.loads((ROOT/'experiments/results'/reserved['run_id']/'run.json').read_text())
    if not audit['data_gate_passed'] or digest(manifest)!=audit['development_manifest_sha256']:raise ValueError('Development data audit changed')
    validation=[r for r in reserved['frames'] if r['split']=='validation'];assert len(validation)==24
    shared=ROOT/reserved['shared_final_manifest'];finals=assert_holdout_closed(shared)
    with (ROOT/'data/manifests/pklot_frames.csv').open(newline='',encoding='utf-8') as stream:original=list(csv.DictReader(stream))
    if {r['date'] for r in validation}&{r['date'] for r in original+finals}:raise ValueError('Broader classifier dates overlap original/reserved dates')
    checkpoint=ROOT/'models/checkpoints/occupancy_resnet18.pt';card=json.loads((ROOT/'models/vision_model_card.json').read_text())
    if digest(checkpoint)!=card['checkpoint_sha256']:raise ValueError('Frozen classifier checkpoint changed')
    validated=json.loads((ROOT/'experiments/results'/reserved['run_id']/'validated_frames.json').read_text());lookup={r['image']:r for r in validated}
    paths=['scripts/evaluate_broader_occupancy.py','src/smart_parking/occupancy_evaluation.py','src/smart_parking/layout.py','src/smart_parking/vision.py']
    protocol=dict(run_id=run,started_at=started.isoformat(),source_ids=['SRC-DS-001','SRC-MOD-003'],seed='Deterministic frozen inference; no randomized fitting',
        hypothesis='Broader date-separated development crops reveal occupied-to-vacant errors and the coverage cost of existing uncertainty bands that the small original crop test may miss',
        scope='Classifier-only original slot crops on24known-camera development frames/6dates; not a final holdout or full pipeline test',
        source_manifest=str(manifest.relative_to(ROOT)),source_manifest_sha256=digest(manifest),checkpoint_sha256=digest(checkpoint),classifier_run_id=card['run_id'],
        hard_threshold=.5,uncertainty_thresholds=[.25,.75],batch_size=64,device='cpu',threads=4,
        preprocessing='Existing crop_slot: polygon mask on gray background, bounding crop resized96x96; existing ImageNet RGB normalization; probability=softmax class1 occupied',
        diagnostic_gate='Selective vacancy false-discovery<=1%, coverage>=80%, >=20vacant decisions; each camera with>=20vacant decisions must have<=2%false vacancy. Diagnostic only, never automatic promotion.',
        calibration='Brier score and10fixed equal-width occupied-probability bins; no fitting, threshold search or calibration training',
        error_example_policy='At most8lowest-score hard false-vacant crops, with selective decision displayed; diagnostic examples only, no tuning',
        missing_label_policy='Skip unlabelled slots with an explicit count; no fabricated ground truth',
        shared_final_manifest=str(shared.relative_to(ROOT)),shared_final_manifest_sha256=digest(shared),
        original_training_test_manifest_sha256=digest(ROOT/'data/manifests/pklot_frames.csv'),
        code_sha256={p:digest(ROOT/p) for p in paths},
        limitations=['Only6dates/3known cameras; crops within frames/dates are correlated','Classification thresholds are not calibrated safety guarantees','No detector inference/fusion, slot-layout discovery or full camera availability accuracy','Old360crop test and new development cohort differ','No new training or production changes; final data remains closed'])
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    (folder/'implementation_sources.json').write_text(json.dumps({p:dict(sha256=digest(ROOT/p),source=(ROOT/p).read_text(encoding='utf-8')) for p in paths},indent=2),encoding='utf-8')
    state['active_validation_jobs']=[dict(run_id=run,pid=os.getpid(),kind='frozen broader crop occupancy diagnostics')];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    try:
        bundle=torch.load(checkpoint,map_location='cpu',weights_only=True);model=resnet18(weights=None);model.fc=torch.nn.Linear(512,2)
        model.load_state_dict(bundle['state_dict']);model.eval();model.requires_grad_(False)
        before={key:value.clone() for key,value in model.state_dict().items()};records=[];missing=0;frame_checks=[]
        for index,row in enumerate(validation):
            source=ROOT/row['image'];annotation=ROOT/row['annotation']
            assert digest(source)==lookup[row['image']]['image_sha256'];assert digest(annotation)==lookup[row['image']]['annotation_sha256']
            with Image.open(source) as image:
                image=image.convert('RGB');layout=read_pklot_xml(annotation,image.size)
                if layout['camera_id']!=row['camera_id']:raise ValueError('Source camera mismatch')
                labelled=[s for s in layout['slots'] if s['ground_truth_occupied'] is not None];missing+=len(layout['slots'])-len(labelled)
                crops=[crop_slot(image,slot) for slot in labelled];tensor=torch.stack([normalize_crop(crop) for crop in crops])
                with torch.inference_mode():probabilities=torch.cat([model(batch).softmax(dim=1)[:,1] for batch in tensor.split(64)]).tolist()
                for slot,crop,p in zip(labelled,crops,probabilities):
                    records.append(dict(source_id='SRC-DS-001',source_frame=row['image'],annotation=row['annotation'],date=row['date'],camera_id=row['camera_id'],slot_id=slot['id'],
                        label=slot['ground_truth_occupied'],occupied_score=p,hard_prediction=int(p>=.5),selective_state='vacant' if p<=.25 else 'occupied' if p>=.75 else 'uncertain',
                        crop_rgb_sha256=hashlib.sha256(b'RGB:96x96\0'+crop.tobytes()).hexdigest()))
            frame_checks.append(dict(image=row['image'],image_sha256=digest(source),annotation_sha256=digest(annotation),labelled_slots=len(labelled)))
            if (index+1)%6==0:print(f'{run}: {index+1}/24frames;{len(records)}labelled crops',flush=True)
        assert all(torch.equal(before[k],v) for k,v in model.state_dict().items());assert digest(checkpoint)==protocol['checkpoint_sha256']
        def score(rows):return occupancy_metrics([r['label'] for r in rows],[r['occupied_score'] for r in rows])
        overall=score(records);per_camera={c:score([r for r in records if r['camera_id']==c]) for c in sorted({r['camera_id'] for r in records})}
        per_date={f'{c}/{d}':score([r for r in records if r['camera_id']==c and r['date']==d]) for c,d in sorted({(r['camera_id'],r['date']) for r in records})}
        selected=overall['selective'];risk=selected['false_vacancy_fraction_of_vacant_predictions']
        passed=selected['predicted_vacant']>=20 and risk is not None and risk<=.01 and selected['coverage']>=.8 and all(v['selective']['false_vacancy_fraction_of_vacant_predictions']<=.02 for v in per_camera.values() if v['selective']['predicted_vacant']>=20)
        errors=sorted([r for r in records if r['label']==1 and r['hard_prediction']==0],key=lambda r:(r['occupied_score'],r['source_frame'],r['slot_id']))[:8]
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
            frames=24,capture_date_groups=len(per_date),missing_labels=missing,metrics=overall,per_camera=per_camera,per_date=per_date,diagnostic_gate_passed=passed,
            state_dict_unchanged=True,checkpoint_file_unchanged=True,final_images_decoded=0,final_annotations_decoded=0,production_changed=False,model_training_performed=False)
        for name,value in [('run.json',report),('crop_predictions.json',records),('source_frame_checks.json',frame_checks),('error_examples.json',errors)]:
            (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
        with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
        (folder/'source_attribution.json').write_text(json.dumps(dict(source_id='SRC-DS-001',creator='Almeida et al.; UFPR',source_url='https://web.inf.ufpr.br/vri/databases/parking-lot-database/',license='CC BY4.0',license_url='https://creativecommons.org/licenses/by/4.0/',changes='Original photos/XML retained; polygon-masked96x96slot crops and predicted scores are derived diagnostics'),indent=2),encoding='utf-8')
        assert digest(shared)==protocol['shared_final_manifest_sha256'];assert_holdout_closed(shared)
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,crops=overall['samples'],hard=overall['hard'],selective=overall['selective'],diagnostic_gate_passed=passed),indent=2),flush=True)
    except BaseException as error:
        (folder/'failure.json').write_text(json.dumps(dict(error=str(error),completed_run_counted=False),indent=2),encoding='utf-8');state=json.loads(state_path.read_text());raise
    finally:state['active_validation_jobs']=[];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')

if __name__=='__main__':
    lock=ROOT/'.cache/broader_occupancy.lock';lock.parent.mkdir(exist_ok=True);fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:evaluate()
    finally:lock.unlink(missing_ok=True)
