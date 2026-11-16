"""Show the sole archived paired DEV regression; no inference or new raw reads."""
import csv
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    card=read(ROOT/'models/region_fpn_duration.json');rid=card['run_id']
    run=ROOT/'experiments/results'/rid;p=read(run/'protocol.json')
    old=ROOT/'experiments/results'/p['reference_run_id'];folder=ROOT/'reports'/('region_duration_'+rid)
    table=folder/'paired_development_differences.csv'
    with table.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    regressions=[r for r in rows if float(r['difference'])< -1e-12];assert len(regressions)==1
    row=regressions[0];index=int(row['development_index'])
    assert read(run/'development_records.json')==read(old/'development_records.json')
    record=read(run/'development_records.json')[index]
    with np.load(run/'development_predictions.npz',allow_pickle=False) as a,np.load(old/'development_predictions.npz',allow_pickle=False) as b:
        assert np.array_equal(a['actual'],b['actual']) and np.array_equal(a['RGB'],b['RGB'])
        rgb=a['RGB'][index].copy();truth=a['actual'][index].copy()
        longer=a['candidate_probability'][index]>=.5;short=b['candidate_probability'][index]>=.5
    image=Image.new('RGB',(1152,365),'#f7f8fa');draw=ImageDraw.Draw(image)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    draw.text((14,10),'Only paired DEVELOPMENT regression | '+row['camera_id'].upper()+' | '+row['capture_date'],font=title,fill='#14283f')
    draw.text((14,40),'IoU change '+f"{float(row['difference']):.6f}"+' | selected after scoring; not a representative sample or final',font=font,fill='#34485e')
    for i,(label,pred) in enumerate(zip(['Provided bay footprints','Eight-epoch model','Longer model'],[truth,short,longer])):
        pixels=rgb.astype('float32')*.65
        for region,color in [(pred & truth,[35,205,145]),(pred & ~truth,[235,70,55]),(~pred & truth,[70,130,250])]:pixels[region]=.45*pixels[region]+.55*np.array(color)
        image.paste(Image.fromarray(pixels.clip(0,255).astype('uint8')).resize((384,216),Image.Resampling.NEAREST),(384*i,96))
        draw.text((384*i+10,72),label,font=font,fill='#14283f')
        draw.text((384*i+10,316),'reference' if i==0 else 'IoU '+f"{float(row['short_iou' if i==1 else 'longer_iou']):.6f}",font=font,fill='#14283f')
    draw.text((14,344),'Green: agreement | Red: extra area | Blue: missed bays. PKLot / Almeida et al. / UFPR, CC BY4.0.',font=font,fill='#34485e')
    target=folder/'paired_regression.png';assert not target.exists();image.save(target)
    evidence=dict(created_at=datetime.now(timezone.utc).isoformat(),selection='Only negative paired DEV IoU change,tolerance1e-12,after scoring',
        source_record=record,paired_row=row,png_sha256=sha(target),
        input_hashes={q.relative_to(ROOT).as_posix():sha(q) for q in [table,run/'development_predictions.npz',old/'development_predictions.npz']},
        code_sha256=sha(Path(__file__)),new_model_calls=0,extra_experiments_counted=0,causal_explanation_claimed=False)
    (folder/'paired_regression.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(image=target.relative_to(ROOT).as_posix(),difference=float(row['difference']))))


if __name__=='__main__':main()
