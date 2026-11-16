"""Experimental frozen ResNet features with a spatial region decoder.

The encoder uses separately attributed local ImageNet weights. The decoder is
project-trained on known-camera dates; neither module authenticates a camera.
"""
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import torch
from torch import nn
from torch.nn import functional as F

CAMERAS={'parking1a':'ufpr04','parking1b':'ufpr05','parking2':'pucpr'}

class FrozenRegionEncoder(nn.Module):
    def __init__(self,backbone):
        super().__init__()
        self.stem=nn.Sequential(backbone.conv1,backbone.bn1,backbone.relu,backbone.maxpool)
        self.layer1=backbone.layer1;self.layer2=backbone.layer2;self.layer3=backbone.layer3
        self.requires_grad_(False);self.train(False)
    def train(self,mode=True):
        # Pretrained BN statistics must never change during decoder fitting.
        return super().train(False)
    @torch.no_grad()
    def forward(self,x):
        a=self.layer1(self.stem(x));b=self.layer2(a);c=self.layer3(b)
        return a,b,c

def coordinates(like):
    batch,_,height,width=like.shape
    y,x=torch.meshgrid(torch.linspace(-1,1,height,device=like.device,dtype=like.dtype),
                       torch.linspace(-1,1,width,device=like.device,dtype=like.dtype),indexing='ij')
    return torch.stack([x,y]).unsqueeze(0).expand(batch,-1,-1,-1)

class RegionDecoder(nn.Module):
    def __init__(self):
        super().__init__()
        def block(a,b):return nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.ReLU(),nn.Conv2d(b,b,3,padding=1),nn.ReLU())
        self.context=nn.Sequential(nn.Linear(256,16),nn.ReLU())
        self.deep=nn.Sequential(nn.Conv2d(274,64,1),nn.ReLU())
        self.middle=block(64+128,64);self.shallow=block(64+64,32)
        self.full=block(32+3+2,16);self.out=nn.Conv2d(16,1,1)
    def forward(self,rgb,features):
        a,b,c=features;context=self.context(c.mean((2,3)))[:,:,None,None].expand(-1,-1,*c.shape[-2:])
        x=self.deep(torch.cat([c,context,coordinates(c)],1))
        x=self.middle(torch.cat([F.interpolate(x,size=b.shape[-2:],mode='bilinear',align_corners=False),b],1))
        x=self.shallow(torch.cat([F.interpolate(x,size=a.shape[-2:],mode='bilinear',align_corners=False),a],1))
        x=F.interpolate(x,size=rgb.shape[-2:],mode='bilinear',align_corners=False)
        return self.out(self.full(torch.cat([x,rgb,coordinates(rgb)],1)))

def reserve_fresh_final(pairs,used_dates,validation_rows):
    """Reserve later, unconsumed dates from index metadata, without decoding labels."""
    grouped=defaultdict(lambda:defaultdict(list))
    for row in pairs:
        try:datetime.strptime(row['date'],'%Y-%m-%d')
        except ValueError:continue
        camera=CAMERAS.get(Path(row['image']).parts[4])
        if camera and row['date'] not in used_dates:grouped[camera][row['date']].append(row)
    reserved=[]
    for camera in sorted(CAMERAS.values()):
        last=max(r['date'] for r in validation_rows if r['camera_id']==camera)
        eligible=sorted(day for day,rows in grouped[camera].items() if day>last and len(rows)>=2)
        if not eligible:raise ValueError('No fresh later final date available for '+camera)
        day=eligible[-1];options=sorted(grouped[camera][day],key=lambda r:r['image'])
        reserved.extend(dict(**row,camera_id=camera,split='test') for row in [options[0],options[-1]])
    return reserved
