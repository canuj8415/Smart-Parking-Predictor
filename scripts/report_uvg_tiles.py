"""Plot completed tile evidence only; never run a model or access source data."""
import argparse
import csv
import json
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest


def main(report_path):
    path=Path(report_path).resolve();assert path.is_relative_to((ROOT/'experiments/results').resolve())
    run=json.loads(path.read_text());ref_path=ROOT/run['reference_folder']/'run.json';ref=json.loads(ref_path.read_text());assert digest(ref_path)==run['reference_report_sha256'];out=path.parent
    rows=[]
    for kind in ['fasterrcnn','maskrcnn']:
        old=ref['results'][kind];new=run['results'][kind];comparison=run['comparisons'][kind]
        rows.append(dict(model=kind,provided_eligible=153,full_frame_matched=old['eligible_provided']['matched_positives'],tile_augmented_matched=new['eligible_provided']['matched_positives'],full_frame_recall=old['eligible_provided']['recall'],tile_augmented_recall=new['eligible_provided']['recall'],
            all194_matched=new['all_provided']['matched_positives'],unassigned_against_eligible=new['eligible_provided']['unassigned_predictions'],unassigned_against_all194=new['all_provided']['unassigned_predictions'],extra_unassigned_against_eligible=comparison['extra_unassigned'],
            estimated_forward_ratio=comparison['estimated_forward_time_ratio'],scope='DEVELOPMENT providedpositives;unassignednotverifiedfalsepositives;noapp/finalclaim'))
    with (out/'summary.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    fig,axes=plt.subplots(1,2,figsize=(11,4.6));colors=['#657d9b','#287f83']
    for j,(name,source) in enumerate([('Full frame',ref),('Full frame + native crops',run)]):
        values=[source['results'][k]['eligible_provided']['recall'] for k in ['fasterrcnn','maskrcnn']]
        bars=axes[0].bar([i+(-.18 if j==0 else .18) for i in range(2)],values,width=.34,color=colors[j],label=name)
        for bar,kind in zip(bars,['fasterrcnn','maskrcnn']):
            result=source['results'][kind]['eligible_provided'];axes[0].text(bar.get_x()+bar.get_width()/2,bar.get_height()-.065,f"{result['matched_positives']}/153",ha='center',color='white',fontsize=9)
        paired=run['comparisons']['maskrcnn'];values=[source['results']['maskrcnn']['mask_zero_inclusive_mean_iou'],paired['paired_reference_mask_iou_before' if j==0 else 'paired_reference_mask_iou_after']]
        bars=axes[1].bar([i+(-.18 if j==0 else .18) for i in range(2)],values,width=.34,color=colors[j])
        for bar in bars:axes[1].text(bar.get_x()+bar.get_width()/2,bar.get_height()-.065,f'{bar.get_height():.3f}',ha='center',color='white',fontsize=9)
    axes[0].set_xticks([0,1],['Faster R-CNN','Mask R-CNN']);axes[0].set_title('Same 153 eligible supplied positives')
    axes[0].axhline(.75,ls='--',c='#aa3e3e',lw=1);axes[0].text(-.4,.765,'Absolute recall gate 0.75',fontsize=8,color='#aa3e3e')
    axes[1].set_xticks([0,1],['All 153 supported targets\n(valid misses score 0)','Same 87 reference matches\n(paired non-regression)']);axes[1].set_title('Mask overlap: same cohorts before/after')
    axes[1].plot([-.4,.4],[.5,.5],ls='--',c='#aa3e3e',lw=1)
    for ax in axes:ax.set_ylim(0,1.03);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.93),ncol=2,frameon=False,fontsize=9)
    fig.suptitle('UVG HighwayView DEVELOPMENT — fixed native-detail crop candidate',fontsize=12)
    names=dict(mask_absolute_recall='Mask recall',mask_recall_gap='detector recall gap',unassigned_volume_bound='unassigned-output budget')
    failed=[names.get(k,k.replace('_',' ')) for k,v in run['checks'].items() if not v]
    fig.text(.055,.025,'11 frames / one 10-second clip; unchanged weights, class rules and 0.5 thresholds. Full-frame outputs retained.\n'
        'Unassigned outputs are not verified false positives; 41 smaller supplied observations lie outside the eligible gate.\n'
        'All frozen gates passed: '+str(run['all_gates_passed'])+'; failed: '+(', '.join(failed) or 'none')+'. No app promotion or final/deployment claim.',fontsize=8)
    fig.tight_layout(rect=[0,.17,1,.86]);fig.savefig(out/'development_comparison.png',dpi=150);plt.close(fig)
    (out/'summary_bindings.json').write_text(json.dumps(dict(inputs={path.relative_to(ROOT).as_posix():digest(path),ref_path.relative_to(ROOT).as_posix():digest(ref_path)},
        generator_sha256=digest(Path(__file__)),outputs={p:digest(out/p) for p in ['summary.csv','development_comparison.png']},model_inference=False,new_trial_counted=False),indent=2)+'\n')
    print(str(out/'development_comparison.png'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report');args=parser.parse_args();main(args.report)
