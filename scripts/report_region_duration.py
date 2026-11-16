"""Plot an archived same-seed duration comparison without neural inference."""
import csv
import hashlib
import json
import os
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    card_path=ROOT/'models/region_fpn_duration.json';r=read(card_path)
    run=ROOT/'experiments/results'/r['run_id'];p=read(run/'protocol.json')
    short=read(ROOT/p['reference_card']);curves=read(run/'curves.json');old=read(ROOT/p['reference_curves'])
    assert r['duration_comparison']['first8epochs_maximum_loss_difference']==0
    assert r['duration_comparison']['first8epochs_maximum_iou_difference']==0
    folder=ROOT/'reports'/('region_duration_'+r['run_id']);folder.mkdir(exist_ok=False)
    plt.rcParams.update({'font.size':10})
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for ax,key,title in zip(axes,['training_loss','macro_camera_iou'],['TRAIN weighted BCE + Dice loss','DEVELOPMENT equal-camera mean IoU']):
        ax.plot([x['epoch'] for x in curves],[x[key] for x in curves],color='#1768ac',label='Longer budget')
        ax.plot([x['epoch'] for x in old],[x[key] for x in old],color='#e28732',linestyle='--',label='Original eight epochs')
        ax.axvline(r['selected_epoch'],color='#616970',linestyle=':',linewidth=1)
        ax.set(xlabel='Completed epoch',ylabel='Loss' if key=='training_loss' else 'IoU',title=title)
        ax.grid(alpha=.18);ax.legend(fontsize=9)
    axes[1].set_ylim(0,1);axes[1].axhline(.8,color='#a83132',linestyle=':',linewidth=1)
    fig.suptitle('Same seed and recipe: first eight loss/IoU values reproduce exactly',fontsize=12)
    fig.text(.02,.015,'PKLot TRAIN200 / DEV30, three familiar cameras. Selection evidence; four admission gates still fail.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.93));fig.savefig(folder/'learning_curves.png',dpi=150);plt.close(fig)
    cameras=['pucpr','ufpr04','ufpr05'];methods=[('Original U-Net',r['original']),('Eight-epoch decoder',short['candidate']),('Longer decoder',r['candidate']),('TRAIN camera template',r['conditional_train_template'])]
    fig,ax=plt.subplots(figsize=(9.5,4.6));x=np.arange(3);width=.19
    for j,(label,metric) in enumerate(methods):
        values=[metric['by_camera'][c]['mean_iou'] for c in cameras]
        bars=ax.bar(x+(j-1.5)*width,values,width,label=label,color=['#a8b3c1','#8d74b5','#1768ac','#508d79'][j])
        ax.bar_label(bars,fmt='%.3f',fontsize=8,padding=2)
    ax.set_xticks(x,[c.upper() for c in cameras]);ax.set_ylim(0,1.12);ax.set_ylabel('Mean per-image bay-footprint IoU')
    ax.set_title('Paired DEVELOPMENT comparison; camera templates are explicitly conditional')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.11),ncol=2,fontsize=9)
    ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.text(.02,.015,'PUCPR8 / UFPR04 six / UFPR05 sixteen images. Fixed-view template1.0 is repeated geometry, not scene understanding.',fontsize=8)
    fig.tight_layout(rect=(0,.08,1,1));fig.savefig(folder/'camera_comparison.png',dpi=150);plt.close(fig)
    records=read(run/'development_records.json');rows=[]
    for a,b,record in zip(r['candidate']['per_image'],short['candidate']['per_image'],records):
        assert a['index']==b['index'] and a['camera_id']==b['camera_id']==record['camera_id']
        rows.append(dict(development_index=a['index'],source_id='SRC-DS-001',camera_id=a['camera_id'],capture_date=record['capture_date'],group_id=record['group_id'],image_sha256=record['image_sha256'],short_iou=b['iou'],longer_iou=a['iou'],difference=a['iou']-b['iou']))
    with (folder/'paired_development_differences.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    better=sum(x['difference']>1e-12 for x in rows);worse=sum(x['difference']< -1e-12 for x in rows);same=30-better-worse
    c=r['candidate'];comp=r['duration_comparison'];old_metric=short['candidate']
    text=f'''# Longer optimization helps development IoU but still fails admission

Run {r['run_id']}, seed169. This is one new controlled TRAIN/DEVELOPMENT trial.
Only the optimization stopping budget changed: maximum8->32epochs and patience3->6.
The architecture, initialization seed, uniform sampling, data/split, loss,
normalization, optimizer, learning rate, threshold and six admission gates stayed
fixed. The first eight epochs have exactly matching training losses and mean
development IoUs (maximum differences both0.0). Separate original source,
protocol, result card and failed checkpoint were preserved.

| Metric | Eight-epoch candidate | Longer candidate |
|---|---:|---:|
| Equal-camera mean DEV IoU | {old_metric['macro_camera_iou']:.6f} | {c['macro_camera_iou']:.6f} |
| Equal-camera mean DEV Dice | {old_metric['macro_camera_dice']:.6f} | {c['macro_camera_dice']:.6f} |
| Worst-image DEV IoU | {old_metric['minimum_image_iou']:.6f} | {c['minimum_image_iou']:.6f} |
| Selected epoch | {short['selected_epoch']} | {r['selected_epoch']} |
| Completed epochs | {short['completed_epochs']} | {r['completed_epochs']} |

The prespecified duration objective was gain>=0.02IoU. Actual gain is
{comp['gain_over_short']:.9f}; that objective passed on this same-seed reused DEV
cohort. It does not establish repeatability across seeds, unseen cameras or final
data. Per-image comparison: {better}improved, {worse}regressed, {same}tied (tolerance1e-12).
The CSV retains all30 paired outcomes and source IDs; gains do not erase regressions.

The longer run early-stopped after {r['completed_epochs']}epochs with epoch{r['selected_epoch']}
selected by equal-camera mean IoU. Measured phase after initial checks:
{r['duration_seconds_this_invocation']:.3f}seconds; sampled process RSS peak
{r['peak_sampled_process_RSS_bytes']:,}bytes, not a system-wide memory maximum.
Fresh feature extraction retained the same computation path rather than assuming
an old cache was equivalent. Per-batch cancellable optimizer/RNG/order checkpoints
and a900second invocation deadline remain. No overlapping trainer ran.

All four previous admission failures remain: meanIoU>=0.80, every camera>=0.75,
every image>=0.65 and camera regression<=0.05 from the TRAIN-only template. Gain
and camera nonregression against the original U-Net pass. Original common-cache
U-Net meanIoU{r['original']['macro_camera_iou']:.6f}; conditional TRAIN camera
template meanIoU{r['conditional_train_template']['macro_camera_iou']:.6f}. The
template scores1.0 on two repeated fixed-view masks, not perfect image understanding.
The UFPR04 majority template remains incompatible with its DEV target pattern.

No threshold/gate relaxation or app promotion. Bay-union labels are not exhaustive
facility/occupancy truth. All17consumed and16quarantined PKLot groups remain
excluded; no protected/quarantined image/XML decoding or other final access.
The Singapore learned final study stays separately closed until27Oct10:51UTC.

The learning curve shows that a longer budget alone is insufficient for the
unchanged quality requirements. Finer spatial features or TRAIN-only target-pattern
balancing are future separate hypotheses; repeated unchanged duration trials or
a threshold sweep would not address the demonstrated failures. Fresh rights-qualified
final data remains necessary before a general reliability or promotion claim.

Selected failed research checkpoint SHA256: {r['candidate_sha256']}.
All original/best/failed weights, prediction arrays and provenance remain local.
Source snapshots, gates, first-eight control checks and actual metrics are retained.
Sources: SRC-DS-001 PKLot, Almeida et al./UFPR,CC BY4.0; SRC-MOD-003 TorchVision
ImageNet ResNet18 under existing local academic terms. No new source download.
Full software suite460/OK; actual notebook12 remains the earlier eight-epoch
archived lesson and was not repointed. Accepted offline app copy unchanged.
Physical offline/new-machine/visible manual use, student mastery and official
university compliance remain unverified.
'''
    (folder/'EXPLANATION.md').write_text(text,encoding='utf-8')
    report=dict(created_at=datetime.now(timezone.utc).isoformat(),run_id=r['run_id'],posthoc_archived_analysis=True,
        compared_images=30,improved=better,regressed=worse,tied=same,new_model_calls=0,extra_experiments_counted=0,
        input_hashes={f:sha(ROOT/f) for f in ['models/region_fpn_duration.json',p['reference_card'],p['reference_curves'],(run/'curves.json').relative_to(ROOT).as_posix()]},
        code_sha256=sha(Path(__file__)),artifacts={q.name:sha(q) for q in folder.iterdir() if q.is_file()})
    (folder/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(report=folder.relative_to(ROOT).as_posix(),improved=better,regressed=worse,tied=same)))


if __name__=='__main__':main()
