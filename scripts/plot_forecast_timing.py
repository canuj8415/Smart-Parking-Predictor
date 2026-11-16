"""Recreate the descriptive timing audit figure without new model evaluation."""
import argparse,json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('run');args=parser.parse_args()
    folder=(ROOT/'experiments/results'/args.run).resolve()
    if not folder.is_relative_to((ROOT/'experiments/results').resolve()):raise ValueError('Choose a project experiment')
    report=json.loads((folder/'run.json').read_text());rows=json.loads((folder/'validation_timing.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(12,4.2))
    axes[0].hist([x['actual_target_lead_minutes'] for x in rows],bins=[10,15,20,25,30],color='#3679a8',edgecolor='white')
    axes[0].set(xlabel='Actual sensor reading minus forecast origin (minutes)',ylabel='Development windows',title='Nominal grid lead:30min; actual readings vary')
    for low,high in zip([10,15,20,25],[15,20,25,30]):
        count=sum(low<=x['actual_target_lead_minutes'] and (x['actual_target_lead_minutes']<high or high==30 and x['actual_target_lead_minutes']<=high) for x in rows)
        axes[0].text((low+high)/2,count+4,str(count),ha='center')
    axes[0].set_ylim(0,350)
    strata=report['validation_by_actual_lead'];x=np.arange(len(strata));width=.35
    axes[1].bar(x-width/2,[p['candidate_mae_spaces'] if p['candidate_mae_spaces'] is not None else np.nan for p in strata],width,label='Frozen trend candidate')
    axes[1].bar(x+width/2,[p['persistence_mae_spaces'] if p['persistence_mae_spaces'] is not None else np.nan for p in strata],width,label='Persistence')
    axes[1].set_xticks(x,[p['actual_target_lead_bin']+'\nn='+str(p['windows']) for p in strata]);axes[1].set(ylabel='MAE (parking spaces)',title='Descriptive errors on reused development data');axes[1].legend()
    axes[1].text(0,2,'No data',ha='center',fontsize=9)
    fig.suptitle('Birmingham timing audit: no retraining, no final-test evaluation',fontsize=13)
    fig.text(.5,.01,'Source: UCI Parking Birmingham (SRC-DS-003). Empty groups have no score; small groups do not establish reliability.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.94]);fig.savefig(folder/'timing_audit.png',dpi=150);plt.close(fig)
    record=dict(script_sha256=digest(Path(__file__)),input_sha256={p:digest(folder/p) for p in ['run.json','validation_timing.json']},figure_sha256=digest(folder/'timing_audit.png'))
    (folder/'figure_provenance.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(folder/'timing_audit.png')
