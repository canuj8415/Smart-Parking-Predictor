"""Representative, inspectable 2D and 3D convolution with numerical verification."""
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

def manual_conv2d(array,kernel):
    a=np.asarray(array,dtype=np.float32);k=np.asarray(kernel,dtype=np.float32)
    if a.ndim!=2 or k.ndim!=2 or min(a.shape[0]-k.shape[0],a.shape[1]-k.shape[1])<0:raise ValueError('Kernel/input shape mismatch')
    return np.array([[np.sum(a[y:y+k.shape[0],x:x+k.shape[1]]*k) for x in range(a.shape[1]-k.shape[1]+1)] for y in range(a.shape[0]-k.shape[0]+1)])

def convolution_demo(image):
    gray=np.asarray(image.convert('L').resize((128,80)),dtype=np.float32)/255
    kernel=np.array([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=np.float32)
    response=F.conv2d(torch.tensor(gray)[None,None],torch.tensor(kernel)[None,None])[0,0].numpy()
    # Educational synthetic numeric volume, not a fabricated parking recording.
    volume=torch.arange(3*5*5,dtype=torch.float32).reshape(1,1,3,5,5)/75
    kernel3=torch.ones(1,1,2,3,3)/18
    response3=F.conv3d(volume,kernel3)[0,0].numpy()
    manual=np.array([[[volume[0,0,z:z+2,y:y+3,x:x+3].mean().item() for x in range(3)] for y in range(3)] for z in range(2)])
    return dict(input=gray,kernel=kernel,response=response,
        volume=volume[0,0].numpy(),kernel3=kernel3[0,0].numpy(),response3=response3,
        max_2d_error=float(np.abs(response-manual_conv2d(gray,kernel)).max()),
        max_3d_error=float(np.abs(response3-manual).max()),
        explanation='2D Sobel cross-correlation on real image; 3D averaging on a labelled educational numeric volume. A 3D kernel spans depth/time and two spatial axes. Neither operation is a trained model.')

def plot_convolutions(image):
    import matplotlib.pyplot as plt
    demo=convolution_demo(image)
    fig,axes=plt.subplots(2,3,figsize=(11,6))
    axes[0,0].imshow(demo['input'],cmap='gray');axes[0,0].set_title('Real image: grayscale input')
    axes[0,1].imshow(demo['kernel'],cmap='coolwarm');axes[0,1].set_title('2D edge kernel: 3 × 3')
    axes[0,2].imshow(demo['response'],cmap='coolwarm');axes[0,2].set_title('2D response: stride 1, no padding')
    axes[1,0].imshow(demo['volume'][0],cmap='viridis');axes[1,0].set_title('Educational 3 × 5 × 5 volume: slice 0')
    axes[1,1].imshow(demo['response3'][0],cmap='viridis');axes[1,1].set_title('3D output depth slice 0')
    axes[1,2].imshow(demo['response3'][1],cmap='viridis');axes[1,2].set_title('3D output depth slice 1')
    for ax in axes.flat:ax.axis('off')
    fig.suptitle('Convolution laboratory — numerical demonstration, not model results')
    fig.tight_layout();return fig,demo
