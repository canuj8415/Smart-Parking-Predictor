"""Render source-labelled reliability diagnostics from completed frozen trials."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.layout import read_pklot_xml,crop_slot
from smart_parking.provenance import digest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('classifier_run');parser.add_argument('fusion_run');args=parser.parse_args()
    cfolder=ROOT/'experiments/results'/args.classifier_run;ffolder=ROOT/'experiments/results'/args.fusion_run
    c=json.loads((cfolder/'run.json').read_text());f=json.loads((ffolder/'run.json').read_text())
    assert c['metrics']['samples']==f['labelled_slots']
    fig,axes=plt.subplots(1,3,figsize=(12,4.7))
    matrices=[c['metrics']['hard_confusion'],c['metrics']['selective_confusion'],f['fused']['confusion']]
    titles=['Classifier at 0.5','Classifier with uncertainty','Existing detector + classifier']
    for ax,matrix,title in zip(axes,matrices,titles):
        a=np.asarray(matrix);ax.imshow(a,cmap='Blues',vmin=0,vmax=max(max(row) for row in c['metrics']['hard_confusion']))
        ax.set_xticks(range(a.shape[1]),['Vacant','Occupied']+(['Uncertain'] if a.shape[1]==3 else []),rotation=20,ha='right')
        ax.set_yticks([0,1],['True vacant','True occupied']);ax.set_title(title,fontsize=12)
        for y in range(2):
            for x in range(a.shape[1]):ax.text(x,y,str(a[y,x]),ha='center',va='center',color='white' if a[y,x]>270 else '#123333',fontsize=13)
    fig.suptitle('Same 948 labelled development crops; 396 slots have no usable occupancy label',fontsize=13)
    fig.text(.5,.015,'PKLot / Almeida et al. / UFPR / CC BY 4.0. Classifier weights and thresholds unchanged. Known cameras; no full-camera accuracy claim.',ha='center',fontsize=8.5)
    fig.tight_layout(rect=[0,.1,1,.9]);fig.savefig(ffolder/'occupancy_confusion_comparison.png',dpi=150);plt.close(fig)
    examples=json.loads((cfolder/'error_examples.json').read_text())
    if examples:
        fig,axes=plt.subplots(1,len(examples),figsize=(3.2*len(examples),3.9));axes=np.atleast_1d(axes)
        predictions=json.loads((ffolder/'predictions.json').read_text());lookup={(r['source_frame'],r['slot_id']):r for r in predictions}
        for ax,row in zip(axes,examples):
            with Image.open(ROOT/row['source_frame']) as image:
                image=image.convert('RGB');layout=read_pklot_xml(ROOT/row['annotation'],image.size);slot=next(s for s in layout['slots'] if s['id']==row['slot_id']);crop=crop_slot(image,slot)
                assert hashlib.sha256(b'RGB:96x96\0'+crop.tobytes()).hexdigest()==row['crop_rgb_sha256']
                ax.imshow(crop)
            fused=lookup[(row['source_frame'],row['slot_id'])]['fused_state']
            ax.set_title(f"{row['camera_id']} / slot {row['slot_id']}\n{row['date']}\nOccupied score {row['occupied_score']:.3f}",fontsize=10)
            ax.set_xlabel(f"Band: {row['selective_state']}\nFused: {fused}",fontsize=10);ax.set_xticks([]);ax.set_yticks([])
        fig.suptitle('Provided label: occupied. Lowest-score hard false-vacancy examples',fontsize=13)
        fig.text(.5,.015,'Original PKLot labels are the reference, without independent human relabelling. Crops are actual masked model inputs. CC BY 4.0.',ha='center',fontsize=8.5)
        fig.tight_layout(rect=[0,.1,1,.85]);fig.savefig(ffolder/'false_vacancy_examples.png',dpi=150);plt.close(fig)
    record=dict(script_sha256=digest(Path(__file__)),classifier_run_sha256=digest(cfolder/'run.json'),fusion_run_sha256=digest(ffolder/'run.json'),
        figures={p.name:digest(p) for p in ffolder.glob('*.png')})
    (ffolder/'figure_provenance.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Saved same-cohort confusion and actual-input error figures')
