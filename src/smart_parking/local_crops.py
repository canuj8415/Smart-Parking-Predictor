"""Local allocation for already validated, image-bounded RGB parking polygons.

The reference layout.crop_slot remains unchanged. Adoption requires an exact
pixel comparison, not merely similar predictions or visually similar crops.
"""
import math
from PIL import Image,ImageDraw


def crop_slot_local(image,slot,size=96):
    if image.mode!='RGB' or type(size) is not int or size<1:raise ValueError('RGB image and positive integer size required')
    points=slot['polygon']
    if len(points)<3 or any(len(p)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p) for p in points):raise ValueError('Finite polygon required')
    if any(not 0<=x<image.width or not 0<=y<image.height for x,y in points):raise ValueError('Polygon must be image-bounded')
    left=max(0,math.floor(min(p[0] for p in points)));top=max(0,math.floor(min(p[1] for p in points)))
    right=min(image.width,math.ceil(max(p[0] for p in points))+1);bottom=min(image.height,math.ceil(max(p[1] for p in points))+1)
    box=(left,top,right,bottom);mask=Image.new('L',(right-left,bottom-top),0)
    ImageDraw.Draw(mask).polygon([(x-left,y-top) for x,y in points],fill=255)
    masked=Image.new('RGB',mask.size,(127,127,127));masked.paste(image.crop(box),mask=mask)
    return masked.resize((size,size),Image.Resampling.BILINEAR)
