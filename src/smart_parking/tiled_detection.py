"""Fixed overlapping native-detail crops and baseline-preserving augmentation."""
import math
import numpy as np
from PIL import Image
from .positive_instances import box_iou


def tile_plan(size):
    width,height=size
    if any(type(v) is not int or v<4 for v in size):raise ValueError('Integer source dimensions >=4 required')
    w=width*3//5;h=height*3//5
    return [(x,y,x+w,y+h) for y in [0,height-h] for x in [0,width-w]]


def map_box(box,tile,source_size,view_size):
    width,height=source_size;vw,vh=view_size;x0,y0,x1,y1=tile
    if not 0<=x0<x1<=width or not 0<=y0<y1<=height:raise ValueError('Invalid tile extent')
    if len(box)!=4 or any(not math.isfinite(v) for v in box) or not 0<=box[0]<box[2]<=vw or not 0<=box[1]<box[3]<=vh:raise ValueError('Invalid tile-input box')
    return [(x0+box[0]*(x1-x0)/vw)*vw/width,(y0+box[1]*(y1-y0)/vh)*vh/height,
            (x0+box[2]*(x1-x0)/vw)*vw/width,(y0+box[3]*(y1-y0)/vh)*vh/height]


def touches_inner_edge(box,tile,source_size,view_size,tolerance=2):
    # Outer source edges may contain genuinely truncated supplied objects.
    x0,y0,x1,y1=tile;width,height=source_size;vw,vh=view_size
    map_box(box,tile,source_size,view_size)
    return ((x0>0 and box[0]<=tolerance) or (y0>0 and box[1]<=tolerance)
            or (x1<width and box[2]>=vw-tolerance) or (y1<height and box[3]>=vh-tolerance))


def mask_to_view(mask,tile,source_size,view_size):
    mask=np.asarray(mask)
    if mask.dtype!=bool or mask.ndim!=2 or tuple(mask.shape[::-1])!=tuple(view_size):raise ValueError('Expected boolean tile-input mask')
    width,height=source_size;vw,vh=view_size;x0,y0,x1,y1=tile
    map_box([0,0,vw,vh],tile,source_size,view_size)
    left,right=round(x0*vw/width),round(x1*vw/width);top,bottom=round(y0*vh/height),round(y1*vh/height)
    canvas=np.zeros((vh,vw),dtype=bool)
    canvas[top:bottom,left:right]=np.asarray(Image.fromarray(mask).resize((right-left,bottom-top),Image.Resampling.NEAREST),dtype=bool)
    return canvas


def select_additions(baseline,proposals,iou_threshold=.5):
    """Never delete/reorder reference detections; suppress same-class additions.

    This bounds duplication, not exhaustive false-positive error.
    """
    if not 0<iou_threshold<=1:raise ValueError('Invalid duplicate threshold')
    kept=list(baseline);accepted=[];duplicates=[]
    order=sorted(range(len(proposals)),key=lambda i:(-proposals[i]['score'],proposals[i]['tile_index'],proposals[i]['proposal_index']))
    for i in order:
        obj=proposals[i]
        if any(obj['label']==old['label'] and box_iou(obj['box'],old['box'])>=iou_threshold for old in kept):duplicates.append(i)
        else:kept.append(obj);accepted.append(i)
    return accepted,duplicates
