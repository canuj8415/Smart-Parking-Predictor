"""Create a source-bound student explanation and deterministic development examples.

Reads only this completed development run. Example selection is the first
image/slot in protocol order satisfying each stated condition; no extra inference.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def report(path):
    from PIL import Image,ImageDraw
    out=Path(path).resolve();run=read(out/'run.json');p=read(out/'protocol.json');assert run['protocol_sha256']==digest(out/'protocol.json')
    target=ROOT/'reports'/('acpds_fusion_'+run['run_id']);target.mkdir(exist_ok=False)
    records=[read(out/f'frame_{i:03}.json') for i in range(35)];frames={f['name']:f for f in p['frames']}
    definitions=[('unsafe_vacancy_flagged','original',lambda r:r['label']==1 and r['classifier_state']=='vacant' and r['fusion_state']=='uncertain'),
                 ('unsafe_vacancy_remaining','original',lambda r:r['label']==1 and r['fusion_state']=='vacant'),
                 ('correct_vacancy_sent_to_review','last_block',lambda r:r['label']==0 and r['classifier_state']=='vacant' and r['fusion_state']=='uncertain')]
    examples=[]
    for category,method,predicate in definitions:
        matches=[(record,row) for record in records for row in record['methods'][method] if predicate(row)]
        if not matches:examples.append(dict(category=category,method=method,available=False));continue
        record,row=matches[0];frame=frames[row['image']];assert digest(ROOT/frame['image'])==frame['image_sha256'];layout=read(ROOT/frame['layout']);slot=next(s for s in layout['slots'] if s['id']==row['slot_id']);poly=slot['polygon'];d=next((d for d in record['detector_result']['detections'] if d['id']==row['vehicle_id']),None)
        xs=[xy[0] for xy in poly];ys=[xy[1] for xy in poly]
        if d:xs+=d['box'][::2];ys+=d['box'][1::2]
        with Image.open(ROOT/frame['image']) as image:
            bounds=(max(0,int(min(xs))-120),max(0,int(min(ys))-120),min(image.width,int(max(xs))+121),min(image.height,int(max(ys))+121));crop=image.convert('RGB').crop(bounds)
        draw=ImageDraw.Draw(crop);points=[(x-bounds[0],y-bounds[1]) for x,y in poly];draw.line(points+[points[0]],fill='#ff3355',width=5)
        if d:draw.rectangle([d['box'][0]-bounds[0],d['box'][1]-bounds[1],d['box'][2]-bounds[0],d['box'][3]-bounds[1]],outline='#2288ff',width=5)
        crop.thumbnail((1000,700));canvas=Image.new('RGB',(max(740,crop.width),crop.height+90),'#14202b');canvas.paste(crop,(0,90));label='occupied' if row['label'] else 'vacant';draw=ImageDraw.Draw(canvas)
        for i,line in enumerate([category.replace('_',' '),f"{row['image']} slot {row['slot_id']} | label={label} | method={method}",f"Classifier score={row['probability_occupied']:.6f} (uncalibrated) | fusion={row['fusion_state']}","Red: supplied bay polygon. Blue: assigned detection box, if present."]):draw.text((12,8+i*19),line,fill='white')
        filename=category+'.png';canvas.save(target/filename);examples.append(dict(category=category,method=method,available=True,row=row,source_id='SRC-DS-021',image_sha256=frame['image_sha256'],layout_sha256=frame['layout_sha256'],detector=d,crop_original_bounds=list(bounds),preview=filename,preview_sha256=digest(target/filename),selection='First matching image/slot in protocol order,not a representative random sample'))
    table=['| Frozen score method | Classifier false vacant | Fusion false vacant | Unsafe vacancies flagged | Correct vacancies sent to review | Fusion uncertainty | Correct-vacancy retention | Gate |','|---|---:|---:|---:|---:|---:|---:|---|']
    for name,value in run['methods'].items():
        m=value['metrics'];table.append(f"| {name} | {m['classifier']['false_vacant']} | {m['fusion']['false_vacant']} | {m['unsafe_vacancies_flagged']} | {m['correct_vacancies_sent_to_review']} | {m['fusion']['uncertainty']}/1904 ({m['fusion']['uncertainty_fraction']:.2%}) | {m['correct_vacancy_retention']['retained']}/{m['correct_vacancy_retention']['eligible']} ({m['correct_vacancy_retention']['fraction']:.2%}) | {'PASS' if value['development_gate_passed'] else 'FAIL'} |")
    text='''# What detector/classifier disagreement costs

This development study asks whether an existing detector can warn about unsafe
empty answers from a crop classifier. It uses 35 already exposed ACPDS VALID
photos and 1,904 supplied parking spaces (831 occupied, 1,073 vacant). Each photo
gets one actual Faster R-CNN640 inference at confidence0.5. Original and research
last-block classifier scores are frozen from earlier runs; neither is retrained,
recomputed or installed. Assignment uses the unchanged0.12overlap and0.25/0.75
state thresholds. This is supplied-geometry development,not a blind final/video
or automatic parking-region benchmark.

'''+ '\n'.join(table)+'''

A false vacant is an occupied space called vacant. A warning changes that answer
to uncertain; it does not make it a correct occupied answer. The same rule can
also send a genuinely vacant space to review. Retention counts how many of the
classifier's already-correct confident vacant answers remain usable. A perfect
accuracy among a tiny set of decided spaces would not imply useful coverage.

The gates were frozen before detector analysis: no more than1%of occupied spaces
called vacant,no more than10%uncertain,at least95%global and90%per-image retention
of correct confident vacancies. Images with no eligible correct vacant baseline
are reported with a null retention,not invented100%. Both methods are reported;
this run does not choose a new threshold/model or replace the original app.

Ground-plane polygons and projected vehicle boxes can overlap neighboring spaces;
provided labels and viewpoints also have limitations. The diagnostic examples
show first qualifying cases in fixed order,not a representative sample or proof
of a single causal explanation. Red marks supplied geometry; blue marks an
assigned detector box. No exhaustive detector precision/mAP was measured.

The worker processes five photos at a time,checkpoints each result,and enforces
time,memory and cancellation guards. Seven sequential batches are one completed
experiment,not35frames or70method comparisons. Original model weights and all
TEST reservations remain unchanged. Singapore aggregate availability is separate.

For a student explanation: two sensors disagree about a bay. A camera box can
raise a warning about a classifier's empty answer,but it cannot make that answer
safe merely by hiding it. Explain both warnings that prevented unsafe vacancy
and correct vacancy answers lost to review,using their actual denominators.
'''
    (target/'EXPLANATION.md').write_text(text,encoding='utf-8')
    manifest=dict(run_id=run['run_id'],run_sha256=digest(out/'run.json'),protocol_sha256=digest(out/'protocol.json'),reporter_sha256=digest(__file__),examples=examples,
                  explanation_sha256=digest(target/'EXPLANATION.md'),new_model_calls=0,final_access=False,source_rights='SRC-DS-021 explicit MIT content grant;original source receipts preserved',visual_review='Pending actual agent inspection;rendering alone is not verification')
    dump(target/'manifest.json',manifest);dump(ROOT/'reports/acpds_fusion_explanation_latest.json',dict(path=target.relative_to(ROOT).as_posix(),manifest_sha256=digest(target/'manifest.json')));print(target)

if __name__=='__main__':report(sys.argv[1])
