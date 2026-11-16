"""Preserve reference full-mask rasterization;allocate RGB only inside the box."""
import math
from PIL import Image
from .layout import slot_mask


def crop_slot_exact(image,slot,size=96):
    if image.mode!='RGB' or type(size) is not int or size<1:raise ValueError('RGB image and positive integer size required')
    points=slot['polygon']
    if len(points)<3 or any(len(p)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p) for p in points):raise ValueError('Finite polygon required')
    if any(not 0<=x<image.width or not 0<=y<image.height for x,y in points):raise ValueError('Polygon must be image-bounded')
    box=(max(0,math.floor(min(x for x,y in points))),max(0,math.floor(min(y for x,y in points))),min(image.width,math.ceil(max(x for x,y in points))+1),min(image.height,math.ceil(max(y for x,y in points))+1))
    # Keep ImageDraw's original full-canvas scan conversion. Translating the
    # polygon before rasterization is not equivalent for every observed polygon.
    mask=slot_mask(slot,image.size).crop(box)
    masked=Image.new('RGB',mask.size,(127,127,127));masked.paste(image.crop(box),mask=mask)
    return masked.resize((size,size),Image.Resampling.BILINEAR)
