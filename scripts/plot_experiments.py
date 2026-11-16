"""Publication-style figures and result tables derived only from recorded runs."""
import csv,json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

if __name__=='__main__':
    figures=ROOT/'reports/figures';figures.mkdir(parents=True,exist_ok=True)
    tables=ROOT/'reports/tables';tables.mkdir(parents=True,exist_ok=True)
    vision=json.loads((ROOT/'models/vision_model_card.json').read_text());seg=json.loads((ROOT/'models/segmentation_model_card.json').read_text());lstm=json.loads((ROOT/'models/lstm_30min_model_card.json').read_text())
    curves=json.loads((ROOT/'experiments/results'/vision['run_id']/'classifier_curves.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    axes[0].plot([r['epoch'] for r in curves],[r['train_loss'] for r in curves],label='Training');axes[0].plot([r['epoch'] for r in curves],[r['validation_loss'] for r in curves],label='Validation')
    axes[0].set(title='ResNet18 transfer head: actual loss',xlabel='Epoch',ylabel='Weighted cross-entropy');axes[0].legend()
    matrix=np.array(vision['classifier_metrics']['confusion_matrix']);im=axes[1].imshow(matrix,cmap='Blues')
    for y in range(2):
        for x in range(2):axes[1].text(x,y,str(matrix[y,x]),ha='center',va='center',color='white' if matrix[y,x]>matrix.max()/2 else 'black')
    axes[1].set(xticks=[0,1],yticks=[0,1],xticklabels=['Vacant','Occupied'],yticklabels=['Vacant','Occupied'],xlabel='Predicted',ylabel='True',title='Held-out crops: n=360')
    fig.suptitle('Small date-separated PKLot development subset; not the complete benchmark');fig.tight_layout();fig.savefig(figures/'occupancy_results.png',dpi=160);plt.close(fig)
    rows=[dict(module='Occupancy ResNet18 head',metric='Accuracy',value=vision['classifier_metrics']['accuracy'],run_id=vision['run_id'],scope='360 held-out crops from small date-grouped subset'),
          dict(module='Occupancy ResNet18 head',metric='Occupied F1',value=vision['classifier_metrics']['f1'],run_id=vision['run_id'],scope='Same 360 crops'),
          dict(module='Experimental parking U-Net',metric='Pixel IoU',value=seg['metrics']['pixel_iou'],run_id=seg['run_id'],scope='10 frames on newly reserved semantic-test dates'),
          dict(module='Historical LSTM',metric='MAE slots',value=lstm['metrics']['mae_slots'],run_id=lstm['run_id'],scope='204 Birmingham chronological test windows'),
          dict(module='Last-observation baseline',metric='MAE slots',value=lstm['metrics']['persistence_mae_slots'],run_id=lstm['run_id'],scope='Same 204 windows; baseline is better')]
    with (tables/'verified_metrics.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    provenance=dict(figures=[dict(path='reports/figures/occupancy_results.png',run_id=vision['run_id'],source_id='SRC-DS-001',
        input='models/vision_model_card.json',input_sha256=digest(ROOT/'models/vision_model_card.json'))],
        table=dict(path='reports/tables/verified_metrics.csv',source_runs=[vision['run_id'],seg['run_id'],lstm['run_id']]),
        result_claim='All values derived from actual saved predictions/run metadata; published-paper scores excluded')
    (ROOT/'reports/figure_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps(rows,indent=2))
