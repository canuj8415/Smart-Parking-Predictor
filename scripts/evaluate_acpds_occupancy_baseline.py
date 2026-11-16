"""Prespecified unchanged classifier baseline on publisher VALID development."""
import argparse,csv,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.occupancy_evaluation import occupancy_metrics
CARD=ROOT/'models/acpds_image_qualification.json';ROLES=ROOT/'data/manifests/acpds_source_roles_v1.json';CHECKPOINT=ROOT/'models/checkpoints/occupancy_resnet18.pt'
REVIEW=ROOT/'experiments/evidence/HEARTBEAT-20261026T230905Z/train_overlay_review.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    now=datetime.now(timezone.utc);rid='ACPDS-BASELINE-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    card=read(CARD);assert card['geometry_gate_passed'] and read(REVIEW)['passed'];manifest=ROOT/card['development_images'];assert digest(manifest)==card['development_images_sha256'];frames=[f for f in read(manifest)['frames'] if f['role']=='valid'];assert len(frames)==35 and sum(f['slots'] for f in frames)==1904
    assert digest(CHECKPOINT)=='72272f0fccd1ca8da9d0fa2c0c78aef47b49c757954fdac6a93ef2266b4ee1a7'
    code=['scripts/evaluate_acpds_occupancy_baseline.py','src/smart_parking/vision.py','src/smart_parking/layout.py','src/smart_parking/occupancy_evaluation.py']
    inputs=[CARD,manifest,ROLES,REVIEW,CHECKPOINT]+[ROOT/f[key] for f in frames for key in ['image','layout']]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=153,source_ids=['SRC-DS-021','SRC-MOD-003'],hypothesis='The unchanged original PKLot crop classifier may not retain acceptable vacancy reliability under action-camera views and unseen parking-lot source shift.',
        prior_exposure='All development labels structurally qualified;3TRAIN overlays visually checked;no VALID predictions or target metrics seen before protocol. Public paper aggregate descriptions known,TEST branch/pixels still closed.',
        frames=frames,input_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},implementation_hashes={p:digest(ROOT/p) for p in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        thresholds=dict(hard=.5,vacant_at_or_below=.25,occupied_at_or_above=.75),batch_size=32,maximum_seconds=300,torch_threads=4,
        gates=dict(overall_hard_accuracy_min=.95,image_hard_accuracy_min=.90,confident_false_vacant_fraction_of_occupied_max=.01,uncertain_fraction_max=.10),
        transform='Existing unmodified crop_slot:ground-polygon grey mask,axis-aligned bounding crop,96x96bilinear;existing ImageNet normalize_crop. Publisher normalized xy scaled by W-1/H-1. No perspective variant/crop grid.',
        scope='Supplied-geometry crop classifier DEVELOPMENT baseline only;no detector/fusion/end-to-end camera benchmark,no adaptation/training,finalTESTclosed,production unchanged')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in code});print(str(out/'protocol.json'))

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not (out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    for f,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),maximum_seconds=p['maximum_seconds'])];dump(ROOT/'data/automation_state.json',s)
    start=datetime.now(timezone.utc);clock=time.perf_counter();rows=[];per_image=[]
    try:
        import torch
        from PIL import Image
        from torchvision.models import resnet18
        from smart_parking.layout import crop_slot,load_layout
        from smart_parking.vision import normalize_crop
        torch.manual_seed(p['seed']);torch.set_num_threads(p['torch_threads']);model=resnet18(weights=None);model.fc=torch.nn.Linear(512,2);model.load_state_dict(torch.load(CHECKPOINT,map_location='cpu',weights_only=True)['state_dict']);model.eval()
        for frame in p['frames']:
            assert frame['role']=='valid';layout=load_layout(ROOT/frame['layout'])
            with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
            frame_rows=[]
            for offset in range(0,len(layout['slots']),p['batch_size']):
                if (out/'CANCEL').exists() or time.perf_counter()-clock>p['maximum_seconds']:raise InterruptedError('Baseline cancelled/deadline')
                slots=layout['slots'][offset:offset+p['batch_size']];x=torch.stack([normalize_crop(crop_slot(image,slot)) for slot in slots])
                with torch.inference_mode():probs=torch.softmax(model(x),dim=1)[:,1].tolist()
                frame_rows.extend(dict(image=frame['name'],image_sha256=frame['image_sha256'],slot_id=slot['id'],label=slot['ground_truth_occupied'],probability_occupied=prob) for slot,prob in zip(slots,probs))
            rows.extend(frame_rows);m=occupancy_metrics([r['label'] for r in frame_rows],[r['probability_occupied'] for r in frame_rows]);per_image.append(dict(image=frame['name'],**m));dump(out/'progress.json',dict(images_completed=len(per_image),samples=len(rows),duration_seconds=time.perf_counter()-clock))
        assert len(rows)==1904 and len(per_image)==35
        overall=occupancy_metrics([r['label'] for r in rows],[r['probability_occupied'] for r in rows]);g=p['gates'];checks=dict(overall_hard_accuracy=overall['hard']['accuracy_on_covered']>=g['overall_hard_accuracy_min'],every_image_hard_accuracy=all(m['hard']['accuracy_on_covered']>=g['image_hard_accuracy_min'] for m in per_image),confident_false_vacant_fraction=overall['selective']['fraction_of_occupied_called_vacant']<=g['confident_false_vacant_fraction_of_occupied_max'],uncertain_fraction=overall['selective']['uncertain']/len(rows)<=g['uncertain_fraction_max'])
        for f,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        r=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=p['seed'],protocol_sha256=digest(path),checkpoint_sha256=digest(CHECKPOINT),overall=overall,macro_image_hard_accuracy=sum(m['hard']['accuracy_on_covered'] for m in per_image)/len(per_image),per_image=per_image,checks=checks,development_reliability_gate_passed=all(checks.values()),production_promoted=False,weights_changed=False,training_performed=False,final_images_or_semantics_opened=False,scope=p['scope'])
        dump(out/'development_predictions.json',rows);dump(out/'run.json',r);dump(ROOT/'models/acpds_occupancy_baseline.json',r);dump(ROOT/'reports/acpds_occupancy_latest.json',r)
        reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Unchanged PKLot classifier cross-source DEVELOPMENT baseline',started_at=r['started_at'],finished_at=r['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='All35publisherVALID/1904spaces;TESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture='Original ResNet18crop classifier',random_seed=153,batch_size=32,epochs=0,hardware='CPU/Torch4threads',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(dict(overall=overall,macro_image_hard_accuracy=r['macro_image_hard_accuracy'],checks=checks)),logs=out.relative_to(ROOT).as_posix(),checkpoints='Original unchanged',code_revision_basis='7fe5e3a plus sealed cross-source baseline',implementation_sha256=digest(__file__),conclusions='Development reliability gate='+str(r['development_reliability_gate_passed'])+';no final/fusion/app promotion')
        with reg.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(ROOT/'data/automation_state.json');s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['acpds_occupancy_baseline']=r;print(json.dumps(dict(run_id=p['run_id'],duration=r['duration_seconds'],overall=overall,checks=checks),indent=2))
    except BaseException as e:
        dump(out/'interrupted.json',dict(error=type(e).__name__,detail=str(e),images_completed=len(per_image),samples=len(rows),completed_run_counted=False));s=read(ROOT/'data/automation_state.json');raise
    finally:s['active_validation_jobs']=[];dump(ROOT/'data/automation_state.json',s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
