"""Source-bound occupancy crops;source indices never become classifier targets."""
import math
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw


def select_source_rows(rows, maximum=32):
    if type(maximum) is not int or maximum < 1:
        raise ValueError('Positive integer crop cap required')
    ordered=sorted(rows,key=lambda r:r['source_line'])
    if len({r['source_line'] for r in ordered})!=len(ordered):raise ValueError('Duplicate source line')
    n=min(len(ordered),maximum)
    positions=[] if n==0 else [0] if n==1 else [i*(len(ordered)-1)//(n-1) for i in range(n)]
    return [ordered[i] for i in positions]


def prepare_occupancy_crop(image,row,support,size=96,minimum_side=12,minimum_known=.95):
    if type(row['class_id']) is not int or row['class_id'] not in {0,1}:raise ValueError('Unknown source class')
    if type(size) is not int or size<2 or type(minimum_side) is not int or minimum_side<1 or not 0<minimum_known<=1:raise ValueError('Invalid crop parameters')
    if not 3<=len(row['normalized_polygon'])<=64 or any(len(p)!=2 or any(not math.isfinite(v) or not 0<=v<=1 for v in p) for p in row['normalized_polygon']):raise ValueError('Invalid normalized geometry')
    target=1-row['class_id']
    if support.shape!=(image.height,image.width):raise ValueError('Support/image dimensions disagree')
    points=[(x*(image.width-1),y*(image.height-1)) for x,y in row['normalized_polygon']]
    box=(max(0,math.floor(min(x for x,y in points))),max(0,math.floor(min(y for x,y in points))),
        min(image.width,math.ceil(max(x for x,y in points))+1),min(image.height,math.ceil(max(y for x,y in points))+1))
    width,height=box[2]-box[0],box[3]-box[1]
    details=dict(source_class_id=row['class_id'],model_label=target,box=list(box),width=width,height=height)
    if min(width,height)<minimum_side:return None,dict(details,accepted=False,reason='native_box_side_below12')
    own=Image.new('1',(width,height))
    ImageDraw.Draw(own).polygon([(round(x)-box[0],round(y)-box[1]) for x,y in points],fill=1)
    own=np.asarray(own,dtype=bool)
    keep=own&(support[box[1]:box[3],box[0]:box[2]]==target)
    fraction=float(keep.sum()/max(1,own.sum()))
    details.update(polygon_pixels=int(own.sum()),unambiguous_pixels=int(keep.sum()),known_fraction=fraction)
    if own.sum()==0 or fraction<minimum_known:return None,dict(details,accepted=False,reason='unambiguous_support_below95percent')
    values=np.asarray(image.convert('RGB').crop(box)).copy();values[~keep]=127
    crop=Image.fromarray(values).resize((size,size),Image.Resampling.BILINEAR)
    return crop,dict(details,accepted=True,reason=None)


def balanced_source_weights(rows,masses=None):
    """Equal classes/cameras within each source;configured total source mass."""
    masses=masses or {'SRC-DS-001':.75,'SRC-DS-018':.25}
    if not rows or abs(sum(masses.values())-1)>1e-10 or any(v<=0 for v in masses.values()):raise ValueError('Invalid source masses')
    if {r['source_id'] for r in rows}!=set(masses):raise ValueError('Missing or unexpected training source')
    counts=Counter((r['source_id'],r.get('camera_id','collection'),r['label']) for r in rows)
    if any(r['label'] not in {0,1} for r in rows):raise ValueError('Unknown model target')
    strata=Counter(k[0] for k in counts)
    weights=[len(rows)*masses[r['source_id']]/(strata[r['source_id']]*counts[(r['source_id'],r.get('camera_id','collection'),r['label'])]) for r in rows]
    return weights
