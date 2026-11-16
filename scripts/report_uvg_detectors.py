"""Summarize already completed development runs; never infer or reopen raw data."""
import argparse
import csv
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest


def main(paths):
    runs=[(Path(p).resolve(),json.loads(Path(p).read_text(encoding='utf-8'))) for p in paths]
    assert len(runs)==2 and [r['detector_resolution'] for _,r in runs]==[640,960]
    assert all(p.is_relative_to((ROOT/'experiments/results').resolve()) for p,_ in runs)
    out=runs[1][0].parent;rows=[];buckets=[]
    for path,run in runs:
        for kind in ['fasterrcnn','maskrcnn']:
            result=run['results'][kind]
            rows.append(dict(run_id=run['run_id'],internal_max_side=run['detector_resolution'],model=kind,
                input_width=960,input_height=540,frames=11,provided_car_truck_observations=194,
                eligible_observations=result['eligible_provided']['provided_positives'],matched_eligible=result['eligible_provided']['matched_positives'],
                eligible_provided_recall=result['eligible_provided']['recall'],all_provided_recall=result['all_provided']['recall'],
                supported_eligible_masks=result['supported_masks'],mask_zero_inclusive_iou=result['mask_zero_inclusive_mean_iou'],
                matched_only_mask_iou=result['matched_mask_mean_iou'],mean_timed_model_seconds=result['model_forward_total_seconds']/11,
                report_sha256=digest(path),scope='DEVELOPMENT provided positives;not exhaustive precision,occupancy or final accuracy'))
            groups={}
            for f in run['frames']:
                targets=json.loads((path.parent/f'truth_{f:04d}.json').read_text())['objects']
                measured=json.loads((path.parent/f'{kind}_{f:04d}.json').read_text())
                matched={m['truth_index'] for m in measured['all_provided']['matches']}
                for i,target in enumerate(targets):
                    side=min(target['box'][2]-target['box'][0],target['box'][3]-target['box'][1])
                    size='under4px' if side<4 else '4to8px' if side<8 else '8to16px' if side<16 else '16pxPlus'
                    key=(target['label'],size);n,m=groups.get(key,(0,0));groups[key]=(n+1,m+(i in matched))
            for (label,size),(n,m) in sorted(groups.items()):buckets.append(dict(run_id=run['run_id'],model=kind,internal_max_side=run['detector_resolution'],label=label,minimum_box_side_bucket=size,provided=n,matched=m,provided_recall=m/n))
    for name,values in [('summary.csv',rows),('class_size_diagnostic.csv',buckets)]:
        with (out/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
    fig,axes=plt.subplots(1,2,figsize=(11,4.5));colors=['#607c9e','#2e9680']
    for j,(_,run) in enumerate(runs):
        values=[run['results'][k]['eligible_provided']['recall'] for k in ['fasterrcnn','maskrcnn']]
        bars=axes[0].bar([i+(-.18 if j==0 else .18) for i in range(2)],values,width=.34,color=colors[j],label=f"Internal max side {run['detector_resolution']}")
        for bar,kind in zip(bars,['fasterrcnn','maskrcnn']):
            d=run['results'][kind]['eligible_provided'];axes[0].text(bar.get_x()+bar.get_width()/2,bar.get_height()+.025,f"{d['matched_positives']}/{d['provided_positives']}",ha='center',fontsize=9)
        result=run['results']['maskrcnn'];values=[result['mask_zero_inclusive_mean_iou'],result['matched_mask_mean_iou']]
        bars=axes[1].bar([i+(-.18 if j==0 else .18) for i in range(2)],values,width=.34,color=colors[j])
        for bar in bars:axes[1].text(bar.get_x()+bar.get_width()/2,bar.get_height()-.06,f'{bar.get_height():.3f}',ha='center',fontsize=9,color='white')
    axes[0].set_xticks([0,1],['Faster R-CNN','Mask R-CNN']);axes[0].set_title('Provided-positive recall at box IoU >= 0.5')
    axes[0].axhline(.75,ls='--',c='#a33a3a',lw=1,label='Frozen recall gate 0.75');axes[0].legend(fontsize=8,loc='upper left')
    axes[1].set_xticks([0,1],['Zero-inclusive\n(valid misses score 0)','Matched objects only\n(misses omitted)']);axes[1].set_title('Mask R-CNN: two different denominators')
    axes[1].plot([-.4,.4],[.5,.5],ls='--',c='#a33a3a',lw=1);axes[1].text(-.4,.515,'Gate 0.5',color='#a33a3a',fontsize=8)
    for ax in axes:ax.set_ylim(0,1.03);ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.2)
    fig.suptitle('UVG HighwayView DEVELOPMENT — unchanged weights, one resolution candidate',fontsize=12)
    fig.text(.06,.025,'Same 11 frames of one 10-second clip; 153 eligible car/truck observations from 32 persistent tracks.\n41 smaller observations excluded from the eligible gate; train outside product scope; unknown masks never treated as empty truth.\nProvided-label agreement only: no exhaustive precision/mAP, parking occupancy, independent final accuracy or deployment FPS.',fontsize=8)
    fig.tight_layout(rect=[0,.14,1,.94]);fig.savefig(out/'development_comparison.png',dpi=150);plt.close(fig)
    # Fixed middle frame, all available car/truck masks, never a best-score selection.
    first_folder=runs[0][0].parent
    base=np.array(Image.open(first_folder/'input_0300.png').convert('RGB'))
    targets=np.load(first_folder/'truth_masks_0300.npz',allow_pickle=False)
    supplied=np.unpackbits(targets['packed'],axis=-1,count=960).astype(bool).any(axis=0)
    panels=[('Supplied supported car/truck masks',supplied,[40,210,130])]
    for path,run in runs:
        archive=np.load(path.parent/'maskrcnn_0300_masks.npz',allow_pickle=False)
        masks=np.unpackbits(archive['packed'],axis=-1,count=960).astype(bool)
        predictions=json.loads((path.parent/'maskrcnn_0300.json').read_text())['predictions']
        selected=[i for i,p in enumerate(predictions) if p['label'] in ('car','truck')]
        union=masks[selected].any(axis=0) if selected else np.zeros((540,960),dtype=bool)
        panels.append((f"Mask R-CNN internal side {run['detector_resolution']}",union,[80,175,255]))
    fig,axes=plt.subplots(1,3,figsize=(12,3.6))
    for ax,(title,mask,color) in zip(axes,panels):
        image=base.copy();image[mask]=(image[mask]*.45+np.array(color)*.55).astype(np.uint8)
        ax.imshow(image);ax.set_title(title,fontsize=10);ax.axis('off')
    fig.suptitle('Fixed DEVELOPMENT frame 300 — supplied masks and actual model outputs',fontsize=12)
    fig.text(.03,.03,'Tampere University / Ultra Video Group, UVG-VCM, CC BY 4.0; derived resized overlays.\nBackground truth unestablished; train excluded; masks shown at fixed 0.5 score/probability thresholds. No parking occupancy or final accuracy claim.',fontsize=8)
    fig.tight_layout(rect=[0,.10,1,.95]);fig.savefig(out/'fixed_frame_mask_comparison.png',dpi=150);plt.close(fig)
    (out/'summary_bindings.json').write_text(json.dumps(dict(inputs={p.relative_to(ROOT).as_posix():digest(p) for p,_ in runs},generator_sha256=digest(Path(__file__)),
        outputs={n:digest(out/n) for n in ['summary.csv','class_size_diagnostic.csv','development_comparison.png','fixed_frame_mask_comparison.png']},model_inference=False,new_trial_counted=False),indent=2)+'\n')
    print(str(out/'development_comparison.png'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('reports',nargs=2);args=parser.parse_args();main(args.reports)
