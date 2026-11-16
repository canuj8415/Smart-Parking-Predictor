"""Use one declared evaluation grid when training image resolution changes."""
from torch.nn import functional as F

def project_logits(logits,grid_size=(192,112)):
    width,height=grid_size
    if width<1 or height<1:raise ValueError('Evaluation grid must be positive')
    if logits.shape[-2:]==(height,width):return logits
    return F.interpolate(logits,size=(height,width),mode='bilinear',align_corners=False)
