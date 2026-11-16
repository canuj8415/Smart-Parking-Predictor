"""Labelled software fixtures;generated boxes/scores are not camera truth."""
import random
import numpy as np


def small_case(seed,index):
    rng=random.Random(seed+index);w=rng.randint(32,160);h=rng.randint(24,120);slots=[]
    for i in range(rng.randint(1,10)):
        left=rng.uniform(0,w-6);top=rng.uniform(0,h-6);right=rng.uniform(left+4,w-1);bottom=rng.uniform(top+4,h-1)
        points=[[left,top],[right,top+.05*(bottom-top)],[right-.04*(right-left),bottom],[left+.02*(right-left),bottom-.03*(bottom-top)]]
        slots.append(dict(id=str(i),polygon=points))
    layout=dict(camera_id='synthetic-software-fixture',image_size=[w,h],slots=slots);ds=[];masks=[]
    for i in range(rng.randint(0,12)):
        x=rng.uniform(-w*.1,w*.9);y=rng.uniform(-h*.1,h*.9);ds.append(dict(id=i,score=rng.choice([.5,.75,.9,1.]),box=[x,y,rng.uniform(x+.1,w*1.1),rng.uniform(y+.1,h*1.1)]))
        if (i+index)%3==0:masks.append(None)
        elif (i+index)%3==1:masks.append(np.random.default_rng(seed+index*31+i).random((h,w))>.7)
        else:masks.append(np.zeros((h,w),dtype=bool))
    p=None if index%5==0 else [rng.choice([0.,.25,.5,.75,1.,rng.random()]) for s in slots]
    return (w,h),layout,ds,masks,p


def large_case():
    w,h=1920,1080;slots=[]
    for row in range(8):
        for col in range(12):
            x=col*160;y=row*135;slots.append(dict(id=str(len(slots)),polygon=[[x+2.2,y+2.7],[x+150.1,y+8.3],[x+151.3,y+125.6],[x+5.9,y+128.2]]))
    ds=[dict(id=i,score=.8+(i%3)*.05,box=[(i%12)*160+.5,(i//12)*270+.9,(i%12)*160+155.5,(i//12)*270+260.9]) for i in range(24)]
    return (w,h),dict(camera_id='synthetic-resource-fixture',image_size=[w,h],slots=slots),ds,[None]*len(ds),[[0.,.25,.5,.75,1.][i%5] for i in range(96)]
