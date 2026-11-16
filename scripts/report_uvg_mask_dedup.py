"""Visualize the rejected automatic rule and exact saved false-suppression cases."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest


def main():
    out=ROOT/'experiments/results/UVG-MASK-DEDUP-20261026T144351078557Z';run=json.loads((out/'run.json').read_text());source=ROOT/run['native_folder'];ref=ROOT/run['reference_folder'];prior=json.loads((source/'run.json').read_text());old=prior['results']['maskrcnn'];metrics=run['metrics'];review=json.loads((out/'review_only.json').read_text())
    assert not run['component_gates_passed'] and review['automatic_removals']==0
    fig,axes=plt.subplots(1,2,figsize=(10,4.4));colors=['#627f9d','#b65750']
    bars=axes[0].bar(['Native-crop outputs','Automatic suppression'],[113,metrics['eligible_matches']],color=colors)
    for bar in bars:axes[0].text(bar.get_x()+bar.get_width()/2,bar.get_height()+2,str(int(bar.get_height()))+'/153',ha='center')
    axes[0].set_ylim(0,153);axes[0].set_title('Supplied-positive matches lost')
    bars=axes[1].bar(['Native-crop outputs','Automatic suppression'],[old['mask_zero_inclusive_mean_iou'],metrics['zero_inclusive_mask_iou']],color=colors)
    for bar in bars:axes[1].text(bar.get_x()+bar.get_width()/2,bar.get_height()-.07,f'{bar.get_height():.3f}',ha='center',color='white')
    axes[1].axhline(old['mask_zero_inclusive_mean_iou']-.005,ls='--',c='#923d36',lw=1);axes[1].set_ylim(0,1);axes[1].set_title('Same 153 supported targets: mask IoU')
    for ax in axes:ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('Automatic mask deletion rejected — archived DEVELOPMENT validation',fontsize=12)
    fig.text(.06,.025,'26 crop outputs removed, but two valid supplied matches lost. Frozen preservation gates failed.\nReview-only export retains all 209 predictions byte-for-byte and flags 53 possible conflicts involving 86 outputs.\nReview flags are not confirmed duplicates, occupancy answers, a new accuracy result or app integration.',fontsize=8)
    fig.tight_layout(rect=[0,.16,1,.93]);fig.savefig(out/'rejected_rule_comparison.png',dpi=150);plt.close(fig)
    losses=json.loads((out/'lost_positive_diagnostic.json').read_text())['lost'];assert len(losses)==2
    fig,axes=plt.subplots(2,2,figsize=(10,6));bindings={}
    for row,loss in enumerate(losses):
        f=loss['frame'];image_path=ref/f'input_{f:04d}.png';key=image_path.relative_to(ROOT).as_posix();assert digest(image_path)==prior['reference_hashes'][key];bindings[key]=digest(image_path)
        image=np.asarray(Image.open(image_path).convert('RGB'));frame=json.loads((source/f'maskrcnn_{f:04d}.json').read_text());packed=np.load(source/f'maskrcnn_{f:04d}_masks.npz',allow_pickle=False);masks=np.unpackbits(packed['packed'],axis=-1,count=960).astype(bool)
        removed=loss['old_prediction_index'];retained=loss['suppression']['retained_index'];a=frame['predictions'][retained]['box'];b=frame['predictions'][removed]['box'];gt=loss['truth']['box']
        left=max(0,int(min(a[0],b[0],gt[0]))-10);right=min(960,int(max(a[2],b[2],gt[2]))+11);top=max(0,int(min(a[1],b[1],gt[1]))-8);bottom=min(540,int(max(a[3],b[3],gt[3]))+9)
        for column in range(2):
            crop=image.copy()
            if column:
                crop[masks[retained]]=(crop[masks[retained]]*.6+np.array([70,150,245])*.4).astype(np.uint8)
                crop[masks[removed]]=(crop[masks[removed]]*.4+np.array([245,90,55])*.6).astype(np.uint8)
            ax=axes[row,column];ax.imshow(crop[top:bottom,left:right],extent=(left,right,bottom,top),interpolation='nearest')
            ax.add_patch(Rectangle((gt[0],gt[1]),gt[2]-gt[0],gt[3]-gt[1],fill=False,edgecolor='#39bd71',lw=2,ls='--'))
            if column:
                for box,color in [(a,'#428ee0'),(b,'#ee654a')]:ax.add_patch(Rectangle((box[0],box[1]),box[2]-box[0],box[3]-box[1],fill=False,edgecolor=color,lw=1.5))
            ax.set_title(f"Frame {f}, supplied car {loss['truth']['track_id']}" if not column else 'Blue broad output retained; orange valid output removed',fontsize=9)
            ax.set_xticks([]);ax.set_yticks([])
    fig.suptitle('Predicted-mask containment does not prove a safe replacement',fontsize=12)
    fig.text(.05,.025,'Green dashed: supplied target. Blue/orange: actual saved predictions and masks. Both retained broad outputs lacked a qualifying supplied match.\nThese are two posthoc counterexamples from the same development clip, not independent final evidence.\nUVG-VCM, Tampere University / Ultra Video Group, CC BY 4.0; derived cropped overlays. No prediction or class is changed in review-only output.',fontsize=8)
    fig.tight_layout(rect=[0,.13,1,.94]);fig.savefig(out/'false_suppression_cases.png',dpi=150);plt.close(fig)
    (out/'figure_bindings.json').write_text(json.dumps(dict(input_report_sha256=digest(out/'run.json'),context_image_hashes=bindings,generator_sha256=digest(Path(__file__)),
        outputs={name:digest(out/name) for name in ['rejected_rule_comparison.png','false_suppression_cases.png']},new_model_inference=False,new_trial_counted=False),indent=2)+'\n')
    print(str(out/'false_suppression_cases.png'))


if __name__=='__main__':main()
