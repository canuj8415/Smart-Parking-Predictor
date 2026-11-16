"""Archive paired mask results and separate software-bound evidence from accuracy."""
import csv,hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    card=ROOT/'models/region_fpn_bounded.json';r=read(card);run=ROOT/'experiments/results'/r['run_id'];p=read(run/'protocol.json')
    ref=read(ROOT/p['reference_card']);old=ROOT/'experiments/results'/ref['run_id']
    out=ROOT/'reports'/('region_bounded_'+r['run_id']);out.mkdir(exist_ok=False)
    assert read(run/'development_records.json')==read(old/'development_records.json')
    records=read(run/'development_records.json');rows=[]
    for a,b,rec in zip(r['candidate']['per_image'],ref['candidate']['per_image'],records):
        assert a['index']==b['index'] and a['camera_id']==b['camera_id']
        rows.append(dict(index=a['index'],source_id='SRC-DS-001',camera_id=a['camera_id'],capture_date=rec['capture_date'],image_sha256=rec['image_sha256'],reference_iou=b['iou'],bounded_iou=a['iou'],difference=a['iou']-b['iou']))
    with (out/'paired_development.csv').open('x',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    better=sum(x['difference']>1e-12 for x in rows);worse=sum(x['difference']< -1e-12 for x in rows)
    fig,ax=plt.subplots(figsize=(10,4));delta=[x['difference'] for x in rows]
    ax.bar(range(30),delta,color=['#247b65' if x>=0 else '#bc4749' for x in delta]);ax.axhline(0,color='#66717b',linewidth=.8)
    ax.axhline(-.05,color='#9d2528',linestyle=':',label='Prespecified paired-loss limit -0.05')
    ax.set(xlabel='Archived DEVELOPMENT image index',ylabel='Bounded minus unbounded IoU',title='Software-bound success did not prevent paired image regressions')
    ax.legend(fontsize=9);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.text(.02,.015,'Same30 familiar-camera DEV images;post-scoring comparison,not fresh final evidence.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(out/'paired_changes.png',dpi=150);plt.close(fig)
    with np.load(run/'development_predictions.npz',allow_pickle=False) as a,np.load(old/'development_predictions.npz',allow_pickle=False) as b:
        assert np.array_equal(a['RGB'],b['RGB']) and np.array_equal(a['actual'],b['actual'])
        rgb=a['RGB'].copy();truth=a['actual'].copy();new=a['candidate_probability']>=.5;previous=b['candidate_probability']>=.5
    row=min(rows,key=lambda x:(x['difference'],x['index']));index=row['index']
    im=Image.new('RGB',(1152,365),'#f7f8fa');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21)
    draw.text((14,10),'Worst paired DEVELOPMENT change | '+row['camera_id'].upper()+' | '+row['capture_date'],font=title,fill='#14283f')
    draw.text((14,40),f"IoU change {row['difference']:.6f} | selected after scoring;not representative or final",font=font,fill='#34485e')
    for col,(label,pred,value) in enumerate(zip(['Provided bay footprints','Unbounded detail model','Bounded detail model'],[truth[index],previous[index],new[index]],[1.,row['reference_iou'],row['bounded_iou']])):
        pixels=rgb[index].astype('float32')*.65;t=truth[index]
        for region,color in [(pred&t,[35,205,145]),(pred&~t,[235,70,55]),(~pred&t,[70,130,250])]:pixels[region]=.45*pixels[region]+.55*np.array(color)
        im.paste(Image.fromarray(pixels.clip(0,255).astype('uint8')).resize((384,216),Image.Resampling.NEAREST),(384*col,96));draw.text((384*col+10,72),label,font=font,fill='#14283f');draw.text((384*col+10,316),'reference' if col==0 else f'IoU {value:.6f}',font=font,fill='#14283f')
    draw.text((14,344),'Green: agreement | Red: extra area | Blue: missed bays. PKLot / Almeida et al. / UFPR, CC BY4.0.',font=font,fill='#34485e');im.save(out/'worst_paired_change.png')
    c=r['candidate'];b=ref['candidate'];comp=r['bounded_comparison'];bound=r['forward_bound_check']
    text=f'''# Bounded residual: software contract passes, reliability hypothesis fails

Run {r['run_id']}. Only the RGB residual mapping changed to
0.5*tanh(raw)*4*p*(1-p),where p is a detached current-coarse sigmoid score.
This is a score-based gate,not calibrated uncertainty. Initial parameters,
seed169/coarse and forked170/detail initialization,TRAIN sampler,loss,optimizer,
max32/patience6,threshold0.5 and all six admission gates stayed fixed. All32
epoch-order hashes match the independent stream tied to the actual unbounded
reference checkpoint. Sources/data/split/code/config hashes are sealed.

| Metric | Unbounded detail | Bounded detail |
|---|---:|---:|
| Equal-camera mean DEV IoU | {b['macro_camera_iou']:.6f} | {c['macro_camera_iou']:.6f} |
| Equal-camera mean DEV Dice | {b['macro_camera_dice']:.6f} | {c['macro_camera_dice']:.6f} |
| Worst-image DEV IoU | {b['minimum_image_iou']:.6f} | {c['minimum_image_iou']:.6f} |

Mean change{comp['gain_over_reference']:.9f} fails the prespecified gain>=0.02.
Worst paired change{comp['worst_paired_iou_change']:.9f} fails the prespecified
no-loss-beyond0.05 objective. {better}images improve,{worse}regress. All four
previous admission failures remain;no gate or threshold relaxation,app promotion,
fresh-final or occupancy claim. Selectedepoch{r['selected_epoch']}of{r['completed_epochs']}.

The finite-input software audit observes max added-logit magnitude
{bound['maximum_observed_logit_delta']:.9f}<=0.5 and preserves the sign of
{bound['strong_coarse_pixels']}current-coarse pixels whose absolute logit exceeds0.5.
This compares this trained model to its own coarse component,not a separately
trained older model or ground truth. It explains why the software property can
hold while independent image masks still regress. Three new numeric/model tests
cover bound/sign behavior,detached gate/finite raw gradient,and identical initial
parameters/RNG/zero output. Fullsuite466/OK. Generated fixtures are not accuracy.

Measured phase{r['duration_seconds_this_invocation']:.3f}seconds;sampled process RSS
peak{r['peak_sampled_process_RSS_bytes']:,}bytes,not system-wide peak. Perbatch
checkpoint/cancel/900secondlimit remain;no overlapping trainer. One pre-fit finite
audit instrumentation amendment is retained with its original unexecuted protocol
and source;no fitting or predictions preceded the amendment,no extra trial counted.
Protected hashes,encoder/BN unchanged;normal forbidden accesses0,cacheprobe blocked.

All30pairs/sourcehashes are in the CSV. The PNG chooses the worst paired loss
after scoring,not a representative sample. Source pixels/targets match exactly.
Supplied bay-union polygons are not exhaustive facility or vehicle occupancy truth.
All17consumed/16quarantined PKLot groups and other final sources remain closed.

These related fixed-view recipes remain below admission requirements. Next assess
already rights-qualified ACPDS TRAIN/VALID bay polygons as a broader development
data source before more residual/coefficient variants. Existing SRC-DS-021 roles
reserve all27TEST images/lots/views/aliases. Reuse only explicitly admitted cached
TRAIN231/VALID35 images through development_only;never deserialize the mixed TEST
partition or read/download TEST pixels. Any derived masks need a separate bounded
qualification protocol and target-semantics/duplicate/provenance checks. Existing
development exposure does not create fresh final evidence. No preparation/training
on that expanded region dataset has occurred in this report.

Current sources:SRC-DS-001 PKLot (Almeida et al./UFPR,CC BY4.0),SRC-MOD-003
TorchVision ImageNet ResNet18 under existing local academic terms. No new training
source acquisition. Notebook12 remains earlier V1 archive;accepted offline app
copy unchanged. Physical offline/new-machine/manual use,student mastery and official
university compliance remain unverified. Singapore learned final remains closed
until27October10:51UTC;aggregate availability is not camera ground truth.
'''
    (out/'EXPLANATION.md').write_text(text,encoding='utf-8')
    evidence=dict(created_at=datetime.now(timezone.utc).isoformat(),run_id=r['run_id'],improved=better,regressed=worse,worst_paired_row=row,
        input_hashes={q.relative_to(ROOT).as_posix():sha(q) for q in [card,ROOT/p['reference_card'],run/'development_predictions.npz',old/'development_predictions.npz']},
        code_sha256=sha(Path(__file__)),artifacts={q.name:sha(q) for q in out.iterdir() if q.is_file()},new_model_calls=0,extra_experiments_counted=0)
    (out/'manifest.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report=out.relative_to(ROOT).as_posix(),improved=better,regressed=worse)))


if __name__=='__main__':main()
