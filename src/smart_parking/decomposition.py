"""Bounded grayscale SVD lesson; no detector preprocessing or trained model."""
import numpy as np
from PIL import Image


def decompose(array):
    if np.iscomplexobj(array):raise ValueError('Use real grayscale values')
    array=np.asarray(array,dtype=np.float64)
    if array.ndim!=2 or not array.size or min(array.shape)<1 or array.size>262144 or max(array.shape)>1024:
        raise ValueError('Use a nonempty grayscale matrix no larger than 512 by 512 pixels in total')
    if not np.isfinite(array).all() or array.min()<0 or array.max()>1:
        raise ValueError('Grayscale values must be finite and between zero and one')
    u,s,vh=np.linalg.svd(array,full_matrices=False)
    return dict(input=array.copy(),u=u,s=s,vh=vh)


def reconstruct(factors,rank):
    if isinstance(rank,(bool,np.bool_)) or not isinstance(rank,(int,np.integer)) or not 1<=rank<=len(factors['s']):
        raise ValueError('Choose a whole-number rank between one and the smaller image dimension')
    return (factors['u'][:,:rank]*factors['s'][:rank])@factors['vh'][:rank]


def rank_report(factors,rank):
    restored=reconstruct(factors,rank);original=factors['input'];height,width=original.shape
    mse=float(np.mean((original-restored)**2));energy=float(np.sum(factors['s']**2))
    # Counts include all U, S and Vh factor entries, with identical float64 dtype.
    entries=int(rank*(height+width+1));original_entries=int(original.size)
    return dict(rank=int(rank),mse=mse,max_absolute_error=float(np.max(np.abs(original-restored))),
                psnr_db=float(-10*np.log10(mse)) if mse>0 else None,
                retained_energy_fraction=float(np.sum(factors['s'][:rank]**2)/energy) if energy else None,
                original_float64_entries=original_entries,factor_float64_entries=entries,
                original_float64_bytes=original_entries*8,factor_float64_bytes=entries*8,
                factor_to_original_float64_ratio=entries/original_entries,
                discarded_energy=float(np.sum(factors['s'][rank:]**2)),
                scope='Unclipped numerical reconstruction; display alone clips to [0,1]. Not JPEG size, detector accuracy or a trained model')


def image_factors(image):
    # Fixed teaching size bounds runtime; original source bytes remain untouched.
    gray=np.asarray(image.convert('L').resize((256,160),Image.Resampling.BILINEAR),dtype=np.float64)/255
    return decompose(gray)


def plot_decomposition(image,rank=16):
    import matplotlib.pyplot as plt
    factors=image_factors(image);report=rank_report(factors,rank);restored=reconstruct(factors,rank)
    fig,axes=plt.subplots(2,2,figsize=(10,6.3))
    axes[0,0].imshow(factors['input'],cmap='gray',vmin=0,vmax=1);axes[0,0].set_title('Loaded image: grayscale 256 x 160')
    axes[0,1].imshow(np.clip(restored,0,1),cmap='gray',vmin=0,vmax=1);axes[0,1].set_title(f'Rebuilt from {rank} patterns (rank {rank})')
    for ax in axes[0]:ax.axis('off')
    axes[1,0].plot(np.arange(1,len(factors['s'])+1),factors['s']);axes[1,0].axvline(rank,color='#cc5533',linestyle='--')
    axes[1,0].set(xlabel='Pattern number',ylabel='Singular value',title='Stronger patterns come first')
    error=axes[1,1].imshow(np.abs(factors['input']-restored),cmap='magma')
    axes[1,1].set_title(f'Absolute numerical error; MSE {report["mse"]:.6f}');axes[1,1].axis('off');fig.colorbar(error,ax=axes[1,1],fraction=.04)
    ratio=report['factor_to_original_float64_ratio']
    fig.suptitle(f'Image compression lesson: storage {ratio:.1%} of uncompressed grayscale numbers')
    fig.text(.5,.015,'Equal number formats compared, not JPEG bytes. No vehicle-detection accuracy was measured.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.96))
    return fig,report
