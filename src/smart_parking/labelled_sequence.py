"""Original labelled-frame decoding/inference, called only after final claim."""
import numpy as np
from PIL import Image
from .provenance import digest


def infer_labelled_frame(row, root, engine):
    for name in ['image','annotation']:
        if digest(root/row[name])!=row[name+'_sha256']:
            raise ValueError('Original sequence asset checksum changed')
    with Image.open(root/row['annotation']) as mask:
        foreground=np.asarray(mask)==1
    ys,xs=np.where(foreground)
    objects=[]
    if len(xs):
        objects=[dict(object_id=1,box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)])]
    with Image.open(root/row['image']) as image:
        if list(image.size)!=row['image_size']:raise ValueError('Original sequence image dimensions changed')
        result,_=engine.analyze(image.convert('RGB'),None,confidence=.5)
    return dict(frame_index=row['frame_index'],result=result,reference_objects=objects)
