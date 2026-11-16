"""One preregistered development-only geometry audit and alignment experiment."""
import hashlib,json,os,sys,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.registration import DEFAULTS,describe,estimate,development_rows
from smart_parking.layout import read_pklot_xml,union_mask
from smart_parking.provenance import digest
import cv2

def metrics(p,a):
    p=np.asarray(p,dtype=bool);a=np.asarray(a,dtype=bool)
    if p.shape!=a.shape:raise ValueError('Mask shape mismatch')
    union=int((p|a).sum());intersection=int((p&a).sum())
    return dict(pixel_iou=intersection/union if union else 1.,dice=2*intersection/max(1,int(p.sum()+a.sum())),pixels=int(a.size))

def run():
    started=datetime.now(timezone.utc);clock=time.perf_counter();cv2.setNumThreads(2)
    ident='REGISTRATION-DEV-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/ident;folder.mkdir(parents=True)
    manifest=ROOT/'data/manifests/segmentation_known_camera_v1.json'
    rows=development_rows(json.loads(manifest.read_text())['frames'])
    protocol=dict(run_id=ident,started_at=started.isoformat(),source_id='SRC-DS-001',seed=67,scope='Training/validation only; final paths filtered before opening images or annotations',
        hypothesis='A camera ID may contain multiple source geometries; image-only registration of training layouts improves masks on development dates with changed views.',
        config=DEFAULTS,environment=dict(opencv=cv2.__version__,numpy=np.__version__,opencv_threads=2,thread_limits={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}),reference_selection='Same-camera training references only; accepted proposal with most RANSAC inliers, tie broken by reference image path. No target label enters selection.',
        comparator='Train-only per-camera majority union mask and the selected reference mask without alignment',
        gate='All six validation frames accepted, aggregate IoU >=0.85, every camera >=0.70, no camera IoU regression >0.02 vs train-only majority baseline. Development only; no automatic promotion.',
        manifest_sha256=digest(manifest),code_sha256=digest(Path(__file__)),registration_code_sha256=digest(ROOT/'src/smart_parking/registration.py'),layout_code_sha256=digest(ROOT/'src/smart_parking/layout.py'),
        input_hashes={r['image']:digest(ROOT/r['image']) for r in rows},annotation_hashes={r['annotation']:digest(ROOT/r['annotation']) for r in rows},
        references=['https://docs.opencv.org/4.13.0/dc/dc3/tutorial_py_matcher.html','https://docs.opencv.org/4.13.0/d1/de0/tutorial_py_feature_homography.html'])
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    prepared=[]
    for row in rows:
        image=Image.open(ROOT/row['image']).convert('RGB');layout=read_pklot_xml(ROOT/row['annotation'],image.size)
        geometry=sorted([dict(id=s['id'],polygon=s['polygon']) for s in layout['slots']],key=lambda s:s['id'])
        prepared.append(dict(row=row,image=image,features=describe(image),mask=np.asarray(union_mask(layout,DEFAULTS['work_size'])),
            geometry_sha256=hashlib.sha256(json.dumps(geometry,sort_keys=True).encode()).hexdigest(),slot_count=len(layout['slots'])))
    train=[p for p in prepared if p['row']['split']=='train'];validation=[p for p in prepared if p['row']['split']=='validation']
    baseline={c:np.stack([p['mask']>127 for p in train if p['row']['camera_id']==c]).mean(0)>=.5 for c in sorted({p['row']['camera_id'] for p in train})}
    audit=[dict(**p['row'],geometry_sha256=p['geometry_sha256'],slot_count=p['slot_count'],majority_iou=metrics(baseline[p['row']['camera_id']],p['mask']>127)['pixel_iou']) for p in prepared]
    (folder/'geometry_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    results=[];predictions=[];actual=[];majorities=[];selected_masks=[]
    # Validation labels below are used only for scoring after image-only selection.
    for number,p in enumerate(validation):
        camera=p['row']['camera_id'];attempts=[]
        for reference in sorted([r for r in train if r['row']['camera_id']==camera],key=lambda r:r['row']['image']):
            matrix,stats=estimate(reference['features'],p['features'],seed=67)
            attempts.append((reference,matrix,stats))
        eligible=[a for a in attempts if a[1] is not None]
        selected=sorted(eligible,key=lambda a:(-a[2]['inliers'],a[0]['row']['image']))[0] if eligible else None
        base=baseline[camera];truth=p['mask']>127
        if selected:
            reference,matrix,stats=selected
            proposal=cv2.warpPerspective(reference['mask'],matrix,DEFAULTS['work_size'],flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=0)>127
            raw=reference['mask']>127
        else:reference=None;matrix=None;stats=None;proposal=base.copy();raw=base.copy()
        record=dict(image=p['row']['image'],date=p['row']['date'],camera_id=camera,accepted=bool(selected),selected_reference=reference['row']['image'] if reference else None,
            transform=matrix.tolist() if matrix is not None else None,matching=stats,baseline=metrics(base,truth),selected_unaligned=metrics(raw,truth),aligned_or_explicit_baseline_fallback=metrics(proposal,truth),
            attempts=[dict(reference=a[0]['row']['image'],**a[2]) for a in attempts])
        results.append(record);predictions.append(proposal);actual.append(truth);majorities.append(base);selected_masks.append(raw)
        for name,mask in [('candidate',proposal),('truth',truth),('geometry',base)]:Image.fromarray((mask*255).astype('uint8')).save(folder/f'{name}_{number}.png')
    overall={name:metrics(np.stack(values),np.stack(actual)) for name,values in [('candidate',predictions),('camera_geometry',majorities),('selected_unaligned',selected_masks)]}
    per_camera={c:{name:metrics(np.stack([values[i] for i,p in enumerate(validation) if p['row']['camera_id']==c]),np.stack([actual[i] for i,p in enumerate(validation) if p['row']['camera_id']==c])) for name,values in [('candidate',predictions),('camera_geometry',majorities)]} for c in baseline}
    accepted=sum(r['accepted'] for r in results)
    gate=accepted==6 and overall['candidate']['pixel_iou']>=.85 and all(v['candidate']['pixel_iou']>=.7 and v['candidate']['pixel_iou']>=v['camera_geometry']['pixel_iou']-.02 for v in per_camera.values())
    report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,train_frames=len(train),validation_frames=len(validation),final_frames_opened=0,
        geometry_variants={c:len({p['geometry_sha256'] for p in prepared if p['row']['camera_id']==c}) for c in baseline},accepted_frames=accepted,metrics=overall,per_camera=per_camera,quality_gate_passed=gate,production_changed=False,
        limitations=['Six development frames from three represented cameras, not an independent final test','Known camera ID supplied; not camera identification','Planar homography cannot guarantee correct alignment under parallax, shadows, vehicle motion or annotation-policy changes','This is geometric layout transfer, not learned semantic segmentation or occupancy accuracy','Rejected transforms explicitly fall back only for comparison; not presented as successful proposals'])
    for name,obj in [('run.json',report),('validation_predictions.json',results)]: (folder/name).write_text(json.dumps(obj,indent=2),encoding='utf-8')
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text());state['completed_run_ids'].append(ident);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=ident;state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':run()
