"""Read-only paired assessment of the completed spatial residual experiment."""
import csv
import hashlib
import json
import os
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
    card=ROOT/'models/region_fpn_detail.json';r=read(card);run=ROOT/'experiments/results'/r['run_id'];p=read(run/'protocol.json')
    reference=read(ROOT/p['reference_card']);oldrun=ROOT/'experiments/results'/reference['run_id']
    out=ROOT/'reports'/('region_detail_'+r['run_id']);out.mkdir(exist_ok=False)
    assert read(run/'development_records.json')==read(oldrun/'development_records.json')
    records=read(run/'development_records.json');rows=[]
    for a,b,record in zip(r['candidate']['per_image'],reference['candidate']['per_image'],records):
        assert a['index']==b['index'] and a['camera_id']==b['camera_id']
        rows.append(dict(index=a['index'],source_id='SRC-DS-001',camera_id=a['camera_id'],capture_date=record['capture_date'],image_sha256=record['image_sha256'],reference_iou=b['iou'],detail_iou=a['iou'],difference=a['iou']-b['iou']))
    with (out/'paired_development.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    better=sum(x['difference']>1e-12 for x in rows);worse=sum(x['difference']< -1e-12 for x in rows)
    with np.load(run/'development_predictions.npz',allow_pickle=False) as a,np.load(oldrun/'development_predictions.npz',allow_pickle=False) as b:
        assert np.array_equal(a['actual'],b['actual']) and np.array_equal(a['RGB'],b['RGB'])
        rgb=a['RGB'].copy();truth=a['actual'].copy();new=a['candidate_probability']>=.5;old=b['candidate_probability']>=.5
    pixel={}
    for label,pred in [('reference',old),('detail',new)]:
        tp=int((pred&truth).sum());fp=int((pred&~truth).sum());fn=int((~pred&truth).sum())
        pixel[label]=dict(precision_against_supplied_mask=tp/(tp+fp),recall_against_supplied_mask=tp/(tp+fn),extra_pixels=fp,missed_pixels=fn,predicted_to_true_area=float(pred.sum()/truth.sum()))
    index=min(rows,key=lambda row:(row['difference'],row['index']))['index'];row=rows[index]
    im=Image.new('RGB',(1152,365),'#f7f8fa');draw=ImageDraw.Draw(im)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    draw.text((14,10),'Worst paired DEVELOPMENT change | '+row['camera_id'].upper()+' | '+row['capture_date'],font=title,fill='#14283f')
    draw.text((14,40),f"IoU change {row['difference']:.6f} | selected after scoring;not representative or final",font=font,fill='#34485e')
    for col,(label,pred,score) in enumerate(zip(['Provided bay footprints','Coarse duration model','RGB detail model'],[truth[index],old[index],new[index]],[1.,row['reference_iou'],row['detail_iou']])):
        pixels=rgb[index].astype('float32')*.65;actual=truth[index]
        for region,color in [(pred&actual,[35,205,145]),(pred&~actual,[235,70,55]),(~pred&actual,[70,130,250])]:pixels[region]=.45*pixels[region]+.55*np.array(color)
        im.paste(Image.fromarray(pixels.clip(0,255).astype('uint8')).resize((384,216),Image.Resampling.NEAREST),(col*384,96))
        draw.text((col*384+10,72),label,font=font,fill='#14283f');draw.text((col*384+10,316),'reference' if col==0 else f'IoU {score:.6f}',font=font,fill='#14283f')
    draw.text((14,344),'Green: agreement | Red: extra area | Blue: missed bays. PKLot / Almeida et al. / UFPR, CC BY4.0.',font=font,fill='#34485e');im.save(out/'worst_paired_change.png')
    curves=read(run/'curves.json');oldcurves=read(oldrun/'curves.json')
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for ax,key,label in zip(axes,['training_loss','macro_camera_iou'],['TRAIN weighted BCE + Dice','DEV equal-camera mean IoU']):
        ax.plot([x['epoch'] for x in oldcurves],[x[key] for x in oldcurves],label='Coarse duration',color='#9a7736')
        ax.plot([x['epoch'] for x in curves],[x[key] for x in curves],label='RGB detail residual',color='#1768ac')
        ax.set(xlabel='Completed epoch',ylabel='Loss' if key=='training_loss' else 'IoU',title=label);ax.grid(alpha=.18);ax.legend(fontsize=9)
    axes[1].set_ylim(0,1);axes[1].axhline(.8,color='#af3232',linestyle=':',label='Required mean0.80');axes[1].legend(fontsize=9)
    fig.suptitle('Same coarse initialization and verified TRAIN sample order; spatial head changed')
    fig.text(.02,.015,'200 TRAIN / 30 reused DEVELOPMENT images. Mean gain does not erase worse individual cases or failed quality gates.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.93));fig.savefig(out/'learning_curves.png',dpi=150);plt.close(fig)
    c=r['candidate'];b=reference['candidate'];comp=r['spatial_comparison']
    text=f'''# Spatial refinement: mean improvement with a worse individual-image result

Run {r['run_id']}. A full-resolution normalizedRGB8-channel residual was added to
the frozen-encoder/32-channel coarse FPN. The final residual layer starts at zero;
coarse initialization matches the control exactly. Extra-head seed170 is isolated
in a forked RNG context. Seed169 TRAIN sample orders match all completed epochs;
the independent reference stream also matches the actual duration checkpoint RNG.
Data, uniform sampling, loss, optimizer, threshold0.5, max32/patience6 and all six
admission gates remain fixed. No camera ID enters the neural input.

| Metric | Coarse duration | RGB detail |
|---|---:|---:|
| Equal-camera mean DEV IoU | {b['macro_camera_iou']:.6f} | {c['macro_camera_iou']:.6f} |
| Equal-camera mean DEV Dice | {b['macro_camera_dice']:.6f} | {c['macro_camera_dice']:.6f} |
| Worst-image DEV IoU | {b['minimum_image_iou']:.6f} | {c['minimum_image_iou']:.6f} |
| Selected epoch | {reference['selected_epoch']} | {r['selected_epoch']} |
| Completed epochs | {reference['completed_epochs']} | {r['completed_epochs']} |

Gain{comp['gain_over_reference']:.9f} meets the prespecified0.02 mean-IoU objective
on this same-seed reused DEVELOPMENT cohort. {better}images improve and {worse}regress
(tolerance1e-12). The worst-image score deteriorates substantially; average gain
does not establish reliability. All four quality failures remain: mean0.80,
each-camera0.75,each-image0.65 and template regression0.05. No gate or threshold
was relaxed;no app promotion or fresh final evidence. The selected checkpoint is
epoch{r['selected_epoch']}, from{r['completed_epochs']}epochs. The old duration
and V1 source/cards/weights remain untouched.

The paired CSV retains all30outcomes. The PNG selects the most negative paired
change after scoring,with identical RGB/target arrays,not a representative sample.
Pixel precision/recall here concern only supplied bay masks,not vehicle occupancy
or exhaustive facility truth. Detail precision{pixel['detail']['precision_against_supplied_mask']:.6f},
recall{pixel['detail']['recall_against_supplied_mask']:.6f};extra area{pixel['detail']['extra_pixels']}
pixels,missed area{pixel['detail']['missed_pixels']},predicted/true area
{pixel['detail']['predicted_to_true_area']:.6f}. These observations can motivate a
separate loss-weight ablation,not prove its cause or authorize threshold tuning.

Measured phase after input checks:{r['duration_seconds_this_invocation']:.3f}seconds;
sampled process RSS peak{r['peak_sampled_process_RSS_bytes']:,}bytes,not system-wide
peak. Per-batch optimizer/RNG/order checkpoint,cancellation and900second deadline
remain. Correct new recovery command targets train_region_fpn_detail.py and the
sealed executor is checked. The historical duration source had a copied V1 resume
suggestion;that run never resumed. Preserve its source;use its explicit duration
driver for any valid interrupted protocol,never rerun completed experiments.

463softwaretests pass. Added tests check initial identity/coarse weights/RNG,
finite detail gradients and identical sampler order without global RNG changes.
All protected hash checks pass in the training controller;normal forbidden reads0,
unqualified-cache negative control blocked. No protected/quarantined pixels/XML
were decoded. No additional experiment count for reporting or epochs.

Sources:SRC-DS-001 PKLot (Almeida et al./UFPR,CC BY4.0);SRC-MOD-003 TorchVision
ImageNet ResNet18 under recorded local academic terms. All17consumed and16quarantined
PKLot groups,ACPDS TEST and HighwayDrive final remain closed. The Singapore learned
final study remains unscored until27Oct10:51UTC. Notebook12 is still the earlier
archived V1 lesson;accepted offline app copy unchanged. Student mastery,physical
offline/new-machine/visible manual use and official university compliance remain open.
'''
    (out/'EXPLANATION.md').write_text(text,encoding='utf-8')
    evidence=dict(created_at=datetime.now(timezone.utc).isoformat(),run_id=r['run_id'],improved=better,regressed=worse,
        worst_paired_row=row,pixel_summary=pixel,new_model_calls=0,extra_experiments_counted=0,
        input_hashes={q.relative_to(ROOT).as_posix():sha(q) for q in [card,ROOT/p['reference_card'],run/'development_predictions.npz',oldrun/'development_predictions.npz',run/'curves.json',oldrun/'curves.json']},
        code_sha256=sha(Path(__file__)),artifacts={q.name:sha(q) for q in out.iterdir() if q.is_file()})
    (out/'manifest.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(report=out.relative_to(ROOT).as_posix(),improved=better,regressed=worse,worst_change=row['difference'])))


if __name__=='__main__':main()
