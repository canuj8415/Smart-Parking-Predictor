"""Frozen classifier baseline on fresh DEVELOPMENT dates;never final data."""
import csv,json,math,sys,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def metrics(rows):
    n=len(rows);correct=sum(r['hard_prediction']==r['label'] for r in rows);occupied=sum(r['label']==1 for r in rows)
    vacant=[r for r in rows if r['probability_occupied']<.25];uncertain=sum(.25<=r['probability_occupied']<=.75 for r in rows)
    return dict(samples=n,hard_accuracy=correct/n,hard_errors=n-correct,occupied_labels=occupied,
        confident_vacant_predictions=len(vacant),confident_false_vacant=sum(r['label']==1 for r in vacant),uncertain=uncertain,uncertain_fraction=uncertain/n,
        confusion_matrix=[[sum(r['label']==y and r['hard_prediction']==p for r in rows) for p in [0,1]] for y in [0,1]])
def main():
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_validation_jobs'] and not state['active_training_jobs']
    started=datetime.now(timezone.utc);rid='PKLOT-FRESH-BASELINE-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    dev_path=ROOT/'data/manifests/pklot_fresh_development_v1.json';final_path=ROOT/'data/manifests/pklot_fresh_final_v2.json';assert_holdout_closed(final_path,root=ROOT)
    dev=read(dev_path);assert len(dev['frames'])==12 and all(r['role']=='development' for r in dev['frames'])
    checkpoint=ROOT/'models/checkpoints/occupancy_resnet18.pt';paths=['scripts/evaluate_fresh_pklot_classifier.py','src/smart_parking/vision.py','src/smart_parking/layout.py'];hashes={p:digest(ROOT/p) for p in paths}
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=127,source_ids=['SRC-DS-001','SRC-MOD-003'],source_hashes=hashes,
        development_manifest_sha256=digest(dev_path),closed_final_manifest_sha256=digest(final_path),checkpoint_sha256=digest(checkpoint),
        hypothesis='Unchanged original ResNet18crop classifier retains useful reliability on12metadata-selected fresh DEVELOPMENT images/3dates,without retuning or using final images.',
        preset_gates=dict(overall_hard_accuracy_min=.95,date_hard_accuracy_min=.90,confident_false_vacant_max_fraction_of_occupied=.01,uncertain_fraction_max=.10),
        thresholds=dict(hard=.5,vacant_below=.25,occupied_above=.75),transform='Existing crop_slot grey polygon mask+96x96bilinear and existing normalize_crop',
        limitations=['Development diagnostic,not independent final score','Only2known cameras/3new dates','Crop classifier only,no detector/fusion/end-to-end camera accuracy','No new training or parameter/threshold changes'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        import torch
        from PIL import Image
        from torchvision.models import resnet18
        from smart_parking.layout import read_pklot_xml,crop_slot
        from smart_parking.vision import normalize_crop
        torch.manual_seed(127);torch.set_num_threads(4);model=resnet18(weights=None);model.fc=torch.nn.Linear(512,2)
        model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['state_dict']);model.eval();rows=[]
        for frame in dev['frames']:
            if (folder/'CANCEL').exists() or time.perf_counter()-clock>300:raise InterruptedError('Baseline cancellation/deadline')
            assert digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['annotation'])==frame['annotation_sha256']
            with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
            layout=read_pklot_xml(ROOT/frame['annotation'],image.size);assert layout['camera_id']==frame['camera_id']
            labelled=[s for s in layout['slots'] if s['ground_truth_occupied'] is not None]
            for offset in range(0,len(labelled),32):
                batch=labelled[offset:offset+32];tensor=torch.stack([normalize_crop(crop_slot(image,s)) for s in batch])
                with torch.inference_mode():probabilities=torch.softmax(model(tensor),dim=1)[:,1].tolist()
                rows.extend(dict(frame=frame['image'],image_sha256=frame['image_sha256'],camera_id=frame['camera_id'],date=frame['date'],slot_id=s['id'],label=s['ground_truth_occupied'],probability_occupied=p,hard_prediction=int(p>=.5)) for s,p in zip(batch,probabilities))
            dump(folder/'progress.json',dict(frames_completed=len({r['frame'] for r in rows}),labelled_samples=len(rows)))
        assert len(rows)==720;overall=metrics(rows);groups=defaultdict(list)
        for row in rows:groups[(row['camera_id'],row['date'])].append(row)
        per_date=[dict(camera_id=c,date=d,**metrics(group)) for (c,d),group in sorted(groups.items())]
        accepted=overall['hard_accuracy']>=.95 and all(r['hard_accuracy']>=.90 for r in per_date) and overall['confident_false_vacant']<=math.floor(.01*overall['occupied_labels']) and overall['uncertain_fraction']<=.10
        assert digest(checkpoint)==protocol['checkpoint_sha256'] and digest(final_path)==protocol['closed_final_manifest_sha256'];assert_holdout_closed(final_path,root=ROOT)
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        result=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,overall=overall,per_date=per_date,development_reliability_gate_passed=accepted,
            original_checkpoint_unchanged=True,production_promoted=False,final_images_or_labels_read=0,model_training_performed=False)
        dump(folder/'run.json',result);dump(folder/'development_predictions.json',rows);dump(ROOT/'models/pklot_fresh_classifier_baseline.json',result)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Frozen crop classifier fresh-development reliability baseline',started_at=protocol['started_at'],finished_at=result['finished_at'],source_ids=';'.join(protocol['source_ids']),split_ids='Fresh12development frames/3dates;final6closed',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Original PKLot ResNet18crop classifier unchanged',epochs=0,batch_size=32,random_seed=127,hardware='CPU/Torch4threads',execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(dict(overall=overall,per_date=per_date,gate=accepted)),logs=folder.relative_to(ROOT).as_posix(),checkpoints='Original checkpoint unchanged',code_revision_basis='fde889c plus sealed source/new-date manifests',implementation_sha256=hashes[paths[0]],conclusions='Development gate='+str(accepted)+';not final/new-camera/fusion accuracy;no threshold/weight change or promotion')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,overall=overall,per_date=per_date,gate=accepted),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));state=read(state_path);raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)
if __name__=='__main__':main()
