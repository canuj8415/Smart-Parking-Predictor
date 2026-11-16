"""Explain a completed TRAIN support study with fixed-order source-bound crops."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def report(path):
    from PIL import Image,ImageDraw
    out=Path(path).resolve();r=read(out/'run.json');p=read(out/'protocol.json');assert r['protocol_sha256']==digest(out/'protocol.json');target=ROOT/'reports'/('anchor_support_'+r['run_id']);target.mkdir(exist_ok=False)
    records=[read(out/f'frame_{i:03}.json') for i in range(24)];frames={f['name']:f for f in p['frames']}
    definitions=[('vacant_support_removed',lambda row:row['label']==0 and row['reference_id'] is not None and row['anchor_id'] is None),
                 ('occupied_support_lost',lambda row:row['label']==1 and row['reference_id'] is not None and row['anchor_id'] is None),
                 ('occupied_support_added',lambda row:row['label']==1 and row['reference_id'] is None and row['anchor_id'] is not None)]
    examples=[]
    for category,predicate in definitions:
        matches=[(record,row) for record in records for row in record['rows'] if predicate(row)]
        if not matches:examples.append(dict(category=category,available=False));continue
        record,row=matches[0];frame=frames[row['image']];assert frame['role']=='train' and digest(ROOT/frame['image'])==frame['image_sha256'];layout=read(ROOT/frame['layout']);slot=next(s for s in layout['slots'] if s['id']==row['slot_id']);poly=slot['polygon'];identity=row['reference_id'] if row['reference_id'] is not None else row['anchor_id'];d=next(d for d in record['detector_result']['detections'] if d['id']==identity);box=d['box'];anchor=((box[0]+box[2])/2,box[3]);xs=[v[0] for v in poly]+box[::2];ys=[v[1] for v in poly]+box[1::2]
        with Image.open(ROOT/frame['image']) as image:
            bounds=(max(0,int(min(xs))-80),max(0,int(min(ys))-80),min(image.width,int(max(xs))+81),min(image.height,int(max(ys))+81));crop=image.convert('RGB').crop(bounds)
        draw=ImageDraw.Draw(crop);points=[(x-bounds[0],y-bounds[1]) for x,y in poly];draw.line(points+[points[0]],fill='#ff3355',width=5);draw.rectangle((box[0]-bounds[0],box[1]-bounds[1],box[2]-bounds[0],box[3]-bounds[1]),outline='#2288ff',width=5)
        x,y=anchor[0]-bounds[0],anchor[1]-bounds[1];draw.ellipse((x-9,y-9,x+9,y+9),fill='#ffdc44',outline='black',width=2);crop.thumbnail((1000,680));canvas=Image.new('RGB',(max(760,crop.width),crop.height+92),'#14202b');canvas.paste(crop,(0,92));draw=ImageDraw.Draw(canvas)
        for i,line in enumerate([category.replace('_',' '),f"TRAIN {row['image']} slot {row['slot_id']} | published label={'occupied' if row['label'] else 'vacant'}",f"Full-box support ID={row['reference_id']} | bottom-center support ID={row['anchor_id']}","Red: supplied bay. Blue: relevant detector box. Yellow: box-bottom proxy, not measured contact."]):draw.text((12,8+19*i),line,fill='white')
        filename=category+'.png';canvas.save(target/filename);examples.append(dict(category=category,available=True,row=row,relevant_detection=d,anchor_proxy=list(anchor),source_id='SRC-DS-021',image_sha256=frame['image_sha256'],layout_sha256=frame['layout_sha256'],crop_bounds=list(bounds),preview=filename,preview_sha256=digest(target/filename),selection='First qualifying image/slot in seeded protocol order,not random representative examples'))
    m=r['metrics'];ret=m['reference_occupied_support_retention'];failed=[k for k,v in r['checks'].items() if not v];ratio=m['anchor']['vacant_supported']/m['reference']['vacant_supported'] if m['reference']['vacant_supported'] else None
    text=f'''# A detector box is not a ground-contact measurement

This is one fixed TRAIN-only geometric support diagnostic on 24 seeded ACPDS
photos with {m['samples']} supplied bays ({m['occupied']} occupied, {m['vacant']} vacant).
These source images and labels participated in previous model development; they
are not unseen or final data. No classifier was run or fitted. Actual Faster R-CNN
at resolution 640 ran once per photo with a 0.5 score threshold. Original full-box
overlap >= 0.12 is compared with one frozen alternative: the box's bottom-center,
floored on the original bay raster.
Points outside the image are unknown,not clipped onto an edge bay. Both methods
keep one detection per bay and one bay per detection.

| Assigned support | Original full-box overlap | Bottom-center proxy |
|---|---:|---:|
| Occupied-label bays supported | {m['reference']['occupied_supported']} | {m['anchor']['occupied_supported']} |
| Vacant-label bays supported | {m['reference']['vacant_supported']} | {m['anchor']['vacant_supported']} |
| All supplied bays supported | {m['reference']['total_supported']} | {m['anchor']['total_supported']} |

Paired retention of originally supported occupied bays: {ret['retained']}/{ret['eligible']}
({ret['fraction']:.2%}). False support on vacant-label bays is {ratio:.2%} of the
reference count. Component gate passed: {r['train_geometry_gate_passed']}. Failed
checks: {', '.join(failed) or 'none'}. Gates were frozen before analysis: at least
100 labels of each truth class, at least 50% reduction in vacant-label support,
at least 95% paired occupied support retained globally and 90% on each eligible image.

Supported means some vehicle evidence is assigned to the bay. An occupied label
does not prove the correct physical vehicle was associated, and no support is
never proof of vacancy. These are bay-label support diagnostics, not occupancy
accuracy, exhaustive detector precision/mAP or a calibrated 3D contact measurement.
Projected boxes, car direction, occlusion, camera angle and annotation limitations
can all matter. No causal decomposition was measured. Fixed-order crops illustrate
tradeoffs only; source labels stay unchanged. No threshold alternatives were tried.

The 24 frames ran in six isolated four-photo children with per-frame checkpoints
and memory, deadline and cancellation guards. Whole study duration: {r['duration_seconds']:.3f} s;
maximum sampled child RSS: {r['maximum_batch_rss_bytes']} bytes. This is one recorded
trial, not 24 runs. Original production code and weights remain unchanged, the helper
is research-only, and all VALID/TEST photos and labels stayed unopened by this trial.
Passing a TRAIN component gate would still require fresh qualified validation
before any app change;this report does not promote the alternative.

Student exercise: explain why moving a box to one point can remove a warning on
an empty bay while also losing evidence on an occupied bay. Use both denominators,
and explain why an unsupported bay must stay unknown. Independent student mastery
has not been assessed. Source: SRC-DS-021, Martin Marek ACPDS, explicit MIT content
grant and pinned-source provenance retained in the project.
'''
    (target/'EXPLANATION.md').write_text(text,encoding='utf-8');dump(target/'manifest.json',dict(run_id=r['run_id'],run_sha256=digest(out/'run.json'),protocol_sha256=digest(out/'protocol.json'),reporter_sha256=digest(__file__),explanation_sha256=digest(target/'EXPLANATION.md'),examples=examples,new_model_calls=0,validation_or_final_access=False,visual_review='Pending actual inspection;separate review receipt may follow'))
    dump(ROOT/'reports/anchor_train_explanation_latest.json',dict(path=target.relative_to(ROOT).as_posix(),manifest_sha256=digest(target/'manifest.json')));print(target)

if __name__=='__main__':report(sys.argv[1])
