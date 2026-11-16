"""One bounded, label-free PKLot TRAIN/DEV stored-layout compatibility study."""
import argparse
from datetime import datetime,timezone
import json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def prepare():
    now=datetime.now(timezone.utc);run_id='VIEW-COMPATIBILITY-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/results'/run_id;out.mkdir(parents=True,exist_ok=False)
    manifest=ROOT/'data/manifests/region_broader_development_v1.json';card=ROOT/'models/region_stability_candidate.json'
    assert digest(manifest)=='04da0c629bdfcdabaa8a0099e3383015ad031f7c4614c9b60dcf40b494ebb60d'
    frames=read(manifest)['frames'];summary=read(card)['training_prior_summary']
    stable=sorted(c for c,v in summary.items() if v['cnn_controlled_fraction']==0 and len(v['training_dates'])>=3)
    references={}
    for camera in stable:
        train=[f for f in frames if f['split']=='train' and f['camera_id']==camera];dates=sorted({f['date'] for f in train})
        references[camera]=[sorted([f for f in train if f['date']==dates[i]],key=lambda f:f['image'])[0] for i in [0,len(dates)//2,len(dates)-1]]
    dev=[f for f in frames if f['split']=='validation'];assert len(dev)==24 and len(stable)==2
    # Only image paths are bound/read. No current-frame XML or final paths opened.
    inputs=[manifest,card]+[ROOT/f['image'] for f in dev]+[ROOT/f['image'] for rows in references.values() for f in rows]
    code=['scripts/validate_view_compatibility.py','src/smart_parking/view_compatibility.py','tests/test_view_compatibility.py']
    p=dict(run_id=run_id,prepared_at=now.isoformat(),seed=143,source_ids=['SRC-DS-001'],
        hypothesis='Three label-blind TRAIN-date visual references can conservatively distinguish compatible stored-layout views from other cameras and synthetic large camera movement on reused DEVELOPMENT.',
        references=references,development=dev,stable_cameras=stable,selection='First lexicographic TRAIN image on first/middle/last training date;no mask/occupancy labels used',
        configuration=dict(orb_features=1000,max_side=640,ratio=.75,ransac_pixels=3,min_inliers=30,min_inlier_fraction=.25,min_span_each_axis=.1,max_median_reprojection=2,max_corner_fraction=.005,required_reference_support=2),
        synthetic_transforms=['shift_x_5percent','rotate_5degrees','horizontal_flip'],
        gates=dict(min_real_compatible_rate=.8,min_per_camera_compatible_rate=.5,max_real_wrong_camera_accepts=0,min_synthetic_changed_rejection_rate=.95),
        input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},implementation_hashes={f:digest(ROOT/f) for f in code},
        protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        maximum_seconds=300,final_images_opened=0,final_annotations_opened=0,semantic_annotations_opened=0,production_promoted=False,
        limits='Reused three represented cameras;development diagnostic,not authentication/unseen-camera/final accuracy. Synthetic movements are not real relocation labels. No app integration or automatic homography warp.')
    dump(out/'protocol.json',p);dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json'),sealed_before_image_decoding=True));print(str(out/'protocol.json'))


def run(path):
    import cv2,numpy as np
    from PIL import Image
    from smart_parking.view_compatibility import describe,compare,decide
    path=Path(path).resolve();out=path.parent;p=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256']
    assert not (out/'progress.json').exists() and not (out/'run.json').exists()
    for f,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    statepath=ROOT/'data/automation_state.json';s=read(statepath);assert not s['active_training_jobs'] and not s['active_validation_jobs']
    s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),phase='Bounded TRAIN/DEV view check;no neural inference')];dump(statepath,s)
    start=datetime.now(timezone.utc);timer=time.monotonic();rows=[];decoded=set();cv2.setNumThreads(1)
    def load(f):
        decoded.add(f['image'])
        with Image.open(ROOT/f['image']) as im:return np.array(im.convert('RGB'))
    try:
        refs={c:[describe(load(f)) for f in records] for c,records in p['references'].items()}
        for frame in p['development']:
            if time.monotonic()-timer>p['maximum_seconds'] or (out/'CANCEL').exists():raise InterruptedError('Bounded trial cancelled')
            image=load(frame);features=describe(image)
            for requested,reference in refs.items():
                comparisons=[compare(r,features,p['seed']) for r in reference]
                rows.append(dict(image=frame['image'],date=frame['date'],actual_camera=frame['camera_id'],requested_camera=requested,kind='real_development',comparison=comparisons,**decide(comparisons)))
            if frame['camera_id'] in refs:
                height,width=image.shape[:2]
                transform=cv2.getRotationMatrix2D((width/2,height/2),5,1)
                variants=dict(shift_x_5percent=cv2.warpAffine(image,np.float32([[1,0,.05*width],[0,1,0]]),(width,height)),rotate_5degrees=cv2.warpAffine(image,transform,(width,height)),horizontal_flip=np.ascontiguousarray(image[:,::-1]))
                for name,changed in variants.items():
                    features=describe(changed);comparisons=[compare(r,features,p['seed']) for r in refs[frame['camera_id']]]
                    rows.append(dict(image=frame['image'],actual_camera=frame['camera_id'],requested_camera=frame['camera_id'],kind='synthetic_changed_view',transform=name,comparison=comparisons,**decide(comparisons)))
            dump(out/'progress.json',dict(last_image=frame['image'],decisions=len(rows),distinct_original_images_decoded=len(decoded),cancellable=True))
        real=[r for r in rows if r['kind']=='real_development'];correct=[r for r in real if r['actual_camera']==r['requested_camera']];wrong=[r for r in real if r['actual_camera']!=r['requested_camera']];synthetic=[r for r in rows if r['kind']=='synthetic_changed_view']
        metrics=dict(real_same_camera_pairs=len(correct),real_same_camera_accepted=sum(r['compatible'] for r in correct),real_same_camera_acceptance_rate=float(np.mean([r['compatible'] for r in correct])),real_wrong_camera_pairs=len(wrong),real_wrong_camera_accepted=sum(r['compatible'] for r in wrong),synthetic_changed_pairs=len(synthetic),synthetic_changed_rejected=sum(not r['compatible'] for r in synthetic),synthetic_rejection_rate=float(np.mean([not r['compatible'] for r in synthetic])),per_camera_acceptance={c:float(np.mean([r['compatible'] for r in correct if r['actual_camera']==c])) for c in refs})
        g=p['gates'];checks=dict(real_same_view_coverage=metrics['real_same_camera_acceptance_rate']>=g['min_real_compatible_rate'],per_camera_coverage=min(metrics['per_camera_acceptance'].values())>=g['min_per_camera_compatible_rate'],real_wrong_camera_rejected=metrics['real_wrong_camera_accepted']==0,synthetic_changed_view_rejected=metrics['synthetic_rejection_rate']>=g['min_synthetic_changed_rejection_rate'],protected_hashes_unchanged=all(digest(ROOT/f)==h for f,h in p['protected_hashes'].items()))
        dump(out/'decisions.json',rows);result=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,protocol_sha256=digest(path),seed=p['seed'],metrics=metrics,checks=checks,development_gate_passed=all(checks.values()),distinct_original_images_decoded=len(decoded),semantic_annotations_opened=0,final_images_opened=0,final_annotations_opened=0,neural_calls=0,production_promoted=False,environment=dict(python=sys.version,opencv=cv2.__version__,numpy=np.__version__),scope=p['limits'])
        dump(out/'run.json',result);print(json.dumps(result,indent=2))
    except BaseException as error:
        dump(out/'interrupted.json',dict(error=repr(error),decisions_completed=len(rows),distinct_original_images_decoded=len(decoded)));raise
    finally:
        s=read(statepath);s['active_validation_jobs']=[j for j in s['active_validation_jobs'] if j['run_id']!=p['run_id']];dump(statepath,s)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args()
    run(args.run) if args.run else prepare()
