"""Plot comparable broader-development results from completed recorded studies."""
import argparse,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data_run');p.add_argument('training_run');args=p.parse_args()
    data_folder=ROOT/'experiments/results'/args.data_run;train_folder=ROOT/'experiments/results'/args.training_run
    audit=json.loads((data_folder/'run.json').read_text());trained=json.loads((train_folder/'run.json').read_text())
    assert trained['split_manifest_sha256']==audit['development_manifest_sha256']
    manifest=json.loads((ROOT/audit['development_manifest']).read_text());validation=[r for r in manifest['frames'] if r['split']=='validation']
    assert len(validation)==24
    names=['Frozen prior','New training','Train geometry'];colors=['#879DA8','#147D82','#BA652C']
    values=[audit['frozen_replay']['overall']['frozen_candidate']['pixel_iou'],trained['validation']['overall']['pixel_iou'],audit['frozen_replay']['overall']['train_geometry']['pixel_iou']]
    fig,axes=plt.subplots(1,2,figsize=(12,5.1));axes[0].bar(names,values,color=colors);axes[0].set(ylim=(0,1),ylabel='Common-grid region IoU',title='Same 24 development frames')
    axes[0].axhline(.8,color='#555555',linestyle='--',label='Overall acceptance minimum')
    for i,value in enumerate(values):axes[0].text(i,value+.02,f'{value:.3f}',ha='center')
    cameras=['pucpr','ufpr04','ufpr05'];x=np.arange(3);width=.24
    for offset,name,color in zip([-1,0,1],names,colors):
        if name=='Frozen prior':camera_values=[audit['frozen_replay'][c]['frozen_candidate']['pixel_iou'] for c in cameras]
        elif name=='New training':camera_values=[trained['validation']['per_camera'][c]['pixel_iou'] for c in cameras]
        else:camera_values=[audit['frozen_replay'][c]['train_geometry']['pixel_iou'] for c in cameras]
        axes[1].bar(x+offset*width,camera_values,width,label=name,color=color)
    thresholds=[max(.65,audit['frozen_replay'][c]['train_geometry']['pixel_iou']-.1) for c in cameras]
    axes[1].scatter(x,thresholds,marker='_',s=1200,color='#222222',label='Per-camera acceptance')
    axes[1].set_xticks(x,cameras);axes[1].set(ylim=(0,1.06),ylabel='Common-grid region IoU',title='Eight validation frames per camera')
    a,b=axes[0].get_legend_handles_labels();c,d=axes[1].get_legend_handles_labels()
    fig.legend(a+c,b+d,loc='lower center',bbox_to_anchor=(.5,.065),ncol=3,frameon=False,fontsize=9,markerscale=.35)
    fig.suptitle('Broader development on known cameras; sealed final images remain closed')
    fig.text(.5,.01,'PKLot / Almeida et al. / UFPR / CC BY 4.0. Different training cohorts; comparison uses the same 24 new development frames.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.20,1,.94]);fig.savefig(train_folder/'broader_comparison.png',dpi=150);plt.close(fig)
    # Predeclared visual sample: first chronological validation frame per camera.
    chosen=[next(i for i,r in enumerate(validation) if r['camera_id']==c) for c in cameras]
    fig,axes=plt.subplots(3,4,figsize=(12,7))
    for row,index in enumerate(chosen):
        frame=validation[index]
        paths=[ROOT/frame['image'],data_folder/f'validation_truth_{index:02}.png',data_folder/f'validation_candidate_{index:02}.png',train_folder/f'validation_candidate_{index}.png']
        for col,path in enumerate(paths):
            with Image.open(path) as image:
                axes[row,col].imshow(image.convert('RGB').resize((192,112)) if col==0 else np.asarray(image),cmap=None if col==0 else 'gray',vmin=0 if col else None,vmax=255 if col else None)
            axes[row,col].axis('off')
        axes[row,0].set_title(frame['camera_id']+' / '+frame['date'],fontsize=9)
        if row==0:
            for col,title in enumerate(['Real image','Annotated slot union','Frozen prior','New candidate']):
                if col:axes[0,col].set_title(title,fontsize=10)
    fig.suptitle('Representative development frames: first selected frame per camera')
    fig.text(.5,.01,'PKLot / CC BY 4.0. Common 192x112 grid. White means parking-region mask; these are not individual slot IDs or vehicle masks.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.045,1,.94]);fig.savefig(train_folder/'broader_mask_examples.png',dpi=150);plt.close(fig)
    (train_folder/'figure_provenance.json').write_text(json.dumps(dict(script_sha256=digest(Path(__file__)),data_run_sha256=digest(data_folder/'run.json'),training_run_sha256=digest(train_folder/'run.json'),
        visual_policy='First selected validation frame per camera, declared in plotting code',selected_frame_indices=chosen,
        figures={name:digest(train_folder/name) for name in ['broader_comparison.png','broader_mask_examples.png']}),indent=2),encoding='utf-8')
    print('Saved broader development comparison and mask examples')
