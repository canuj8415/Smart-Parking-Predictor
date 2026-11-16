"""Camera-specific polygons, original PKLot XML and raster masks."""
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

def polygon_area(points):
    return abs(sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1])))/2

def orientation(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def validate_layout(layout,image_size=None):
    width,height=layout['image_size']
    if not isinstance(width,int) or not isinstance(height,int) or min(width,height)<1:raise ValueError('Invalid layout image size')
    if image_size and tuple(image_size)!=(width,height):raise ValueError('Layout/image dimensions differ; choose the correct camera layout')
    if not layout.get('camera_id'):raise ValueError('Layout requires camera identity')
    if not layout.get('slots'):raise ValueError('Layout contains no parking spaces')
    ids=set()
    for slot in layout['slots']:
        if not slot.get('id') or slot['id'] in ids:raise ValueError('Slot IDs must be nonempty and unique')
        ids.add(slot['id']);points=[tuple(p) for p in slot['polygon']]
        if len(points)<3 or len(set(points))!=len(points):raise ValueError('A polygon requires at least three distinct vertices')
        if any(len(p)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in p) for p in points):raise ValueError('Non-finite polygon coordinates')
        if any(not (0<=x<width and 0<=y<height) for x,y in points):raise ValueError('Polygon outside image bounds')
        if polygon_area(points)<4:raise ValueError('Degenerate parking polygon')
        n=len(points)
        for i in range(n):
            a,b=points[i],points[(i+1)%n]
            for j in range(i+1,n):
                if j in {i,(i+1)%n} or (j+1)%n==i:continue
                c,d=points[j],points[(j+1)%n]
                if orientation(a,b,c)*orientation(a,b,d)<0 and orientation(c,d,a)*orientation(c,d,b)<0:
                    raise ValueError('Self-intersecting polygon')
    return layout

def read_pklot_xml(path,image_size):
    xml=ET.parse(path).getroot();slots=[]
    for space in xml.findall('space'):
        contour=space.find('contour')
        if contour is None:continue
        # Original PKLot files use both <point> and <Point>; preserve coordinates.
        points=[[int(p.attrib['x']),int(p.attrib['y'])] for p in contour if p.tag.lower()=='point']
        label=space.attrib.get('occupied')
        slots.append(dict(id=str(space.attrib['id']),polygon=points,
                          ground_truth_occupied=int(label) if label in {'0','1'} else None))
    return validate_layout(dict(schema_version=1,camera_id=xml.attrib.get('id','pklot'),
        image_size=list(image_size),origin='Original PKLot slot polygons; not predictions',slots=slots))

def load_layout(path,image_size=None):
    return validate_layout(json.loads(Path(path).read_text(encoding='utf-8')),image_size)

def slot_mask(slot,image_size):
    mask=Image.new('L',tuple(image_size),0);ImageDraw.Draw(mask).polygon([tuple(p) for p in slot['polygon']],fill=255)
    return mask

def crop_slot(image,slot,size=96):
    points=slot['polygon'];xs=[p[0] for p in points];ys=[p[1] for p in points]
    box=(max(0,math.floor(min(xs))),max(0,math.floor(min(ys))),
         min(image.width,math.ceil(max(xs))+1),min(image.height,math.ceil(max(ys))+1))
    masked=Image.new('RGB',image.size,(127,127,127));masked.paste(image,mask=slot_mask(slot,image.size))
    return masked.crop(box).resize((size,size),Image.Resampling.BILINEAR)

def union_mask(layout,size=None):
    mask=Image.new('L',tuple(layout['image_size']),0);draw=ImageDraw.Draw(mask)
    for slot in layout['slots']:draw.polygon([tuple(p) for p in slot['polygon']],fill=255)
    return mask.resize(size,Image.Resampling.NEAREST) if size else mask
