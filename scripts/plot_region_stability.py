"""Scientific comparison of saved masks; no inference or final-label loading."""
import json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
RUN='REGION-STABILITY-FINAL-20261025T105044848266Z'
if __name__=='__main__':
    folder=ROOT/'experiments/results'/RUN;result=json.loads((folder/'run.json').read_text());rows=result['final_evaluation']['frames']
    indices=[next(i for i,r in enumerate(rows) if r['camera_id']==c) for c in sorted({r['camera_id'] for r in rows})]
    fig,axes=plt.subplots(3,4,figsize=(13,8.3),dpi=150)
    columns=[('source','Actual source image'),('truth','Reference region union'),('neural','Frozen RGB-only CNN'),('hybrid','Known-camera router')]
    for line,index in enumerate(indices):
        camera=rows[index]['camera_id'];mode='CNN only' if result['final_evaluation']['effective_cnn_controlled_fraction'][camera]==1 else 'stored geometry only'
        for col,(name,title) in enumerate(columns):
            ax=axes[line,col]
            with Image.open(folder/f'final_{name}_{index:02d}.png') as im:ax.imshow(im.copy(),cmap=None if name=='source' else 'gray',vmin=0,vmax=255)
            ax.set_xticks([]);ax.set_yticks([])
            if line==0:ax.set_title(title,fontsize=11)
            if col==0:ax.set_ylabel(camera+'\n'+mode,fontsize=10)
    fig.suptitle('Later-date region masks: geometry and neural contributions are separate',fontsize=14)
    fig.text(.02,.02,'PKLot / Almeida et al., UFPR, CC BY 4.0 (SRC-DS-001). Derived images/masks; first sealed frame per camera.\nSix-image known-camera test, not unseen-camera discovery or automatic slot IDs. No model rerun for this figure.',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,.94));fig.savefig(folder/'mask_comparison.png');plt.close(fig)
    (folder/'figure_provenance.json').write_text(json.dumps(dict(source_run=RUN,indices=indices,selection='First sealed frame per camera, metadata order; no error-based selection',inputs='Saved final_source/truth/neural/hybrid PNG files only; original final images/XML not reopened'),indent=2)+'\n',encoding='utf-8')
