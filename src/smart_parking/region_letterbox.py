"""Image/bay-mask letterboxing;validity describes padding,not annotation certainty."""
from pathlib import PurePosixPath
import numpy as np
from PIL import Image


def letterbox_plan(native_size,output_size=(256,144)):
    if any(type(v) is not int or v<1 for v in [*native_size,*output_size]):
        raise ValueError('Positive integer image dimensions required')
    w,h=native_size;ow,oh=output_size;scale=min(ow/w,oh/h)
    nw=min(ow,max(1,round(w*scale)));nh=min(oh,max(1,round(h*scale)))
    return dict(native_size=[w,h],output_size=[ow,oh],resized_size=[nw,nh],
                offset=[(ow-nw)//2,(oh-nh)//2],scale_xy=[nw/w,nh/h])


def letterbox_arrays(rgb,native_mask,output_size=(256,144),fill=(124,116,104)):
    if rgb.mode!='RGB' or native_mask.mode!='L' or rgb.size!=native_mask.size:
        raise ValueError('Aligned RGB image and native L mask required')
    if not set(np.unique(np.asarray(native_mask))).issubset({0,255}):
        raise ValueError('Binary source mask required')
    plan=letterbox_plan(rgb.size,output_size);size=tuple(plan['resized_size']);offset=tuple(plan['offset'])
    image=Image.new('RGB',output_size,fill);image.paste(rgb.resize(size,Image.Resampling.BILINEAR),offset)
    mask=Image.new('L',output_size,0);mask.paste(native_mask.resize(size,Image.Resampling.NEAREST),offset)
    valid=np.zeros((output_size[1],output_size[0]),dtype=bool);x,y=offset;w,h=size;valid[y:y+h,x:x+w]=True
    target=np.asarray(mask)>0
    if np.any(target&~valid):raise ValueError('Target leaked into padding')
    return np.asarray(image).copy(),target,valid,plan


def check_admitted_frames(frames,publisher_names):
    if set(publisher_names)!={'train','valid'}:raise ValueError('Only publisher TRAIN/VALID names admitted')
    allowed={name.casefold():role for role,names in publisher_names.items() for name in names}
    if len(allowed)!=sum(map(len,publisher_names.values())):raise ValueError('Duplicate/cross-role admitted name')
    seen=set()
    for f in frames:
        name=f['name'];key=name.casefold()
        if PurePosixPath(name).name!=name or '\\' in name or not name.lower().endswith('.jpg'):
            raise ValueError('Unsafe source image name')
        role={'train':'train','validation':'valid'}.get(f['role'])
        if f['source_id']!='SRC-DS-021' or role is None or allowed.get(key)!=role or key in seen:
            raise ValueError('Unadmitted,duplicate or role-conflicting source frame')
        seen.add(key)
    if seen!=set(allowed):raise ValueError('Incomplete admitted development cohort')
    return True
