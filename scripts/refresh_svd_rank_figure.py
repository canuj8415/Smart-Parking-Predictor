"""Repair only the rank-grid layout; preserve the original overlapped plot."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.decomposition import image_factors,reconstruct
from smart_parking.provenance import digest


if __name__=='__main__':
    card=json.loads((ROOT/'models/svd_lesson_validation.json').read_text(encoding='utf-8'))
    assert digest(ROOT/card['image'])==card['image_sha256']
    folder=ROOT/'experiments/results'/card['run_id']
    with Image.open(ROOT/card['image']) as image:factors=image_factors(image)
    fig,axes=plt.subplots(2,3,figsize=(11,7))
    for ax,row in zip(axes.flat,card['rank_reports']):
        rank=row['rank'];ax.imshow(np.clip(reconstruct(factors,rank),0,1),cmap='gray',vmin=0,vmax=1)
        ax.set_title(f'{rank} patterns; MSE {row["mse"]:.5f}\nFactor storage {row["factor_to_original_float64_ratio"]:.1%}',fontsize=10,pad=10);ax.axis('off')
    fig.suptitle('One real training picture: more patterns retain more detail',fontsize=14)
    fig.text(.5,.025,'PKLot / Almeida et al., CC BY4.0. Derived grayscale/resized pictures. Equal numeric formats; not JPEG size or accuracy.',ha='center',fontsize=8)
    fig.subplots_adjust(left=.025,right=.975,bottom=.085,top=.86,wspace=.06,hspace=.5)
    destination=folder/'rank_comparison_reviewed.png'
    if destination.exists():raise FileExistsError('Preserve the existing reviewed figure')
    fig.savefig(destination,dpi=130);plt.close(fig)
    print(destination)
