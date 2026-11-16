"""Explicit online setup; inference never downloads assets implicitly."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import download
from torchvision.models import ResNet18_Weights
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_V2_Weights, MaskRCNN_ResNet50_FPN_Weights

if __name__=='__main__':
    entries=[('SRC-MOD-001',FasterRCNN_ResNet50_FPN_V2_Weights.COCO_V1,'fasterrcnn_resnet50_fpn_v2.pth'),
             ('SRC-MOD-002',MaskRCNN_ResNet50_FPN_Weights.COCO_V1,'maskrcnn_resnet50_fpn.pth'),
             ('SRC-MOD-003',ResNet18_Weights.IMAGENET1K_V1,'resnet18_imagenet.pth')]
    for source,weights,name in entries:
        prefix=weights.url.rsplit('-',1)[-1].split('.')[0]
        path=download(source,weights.url,'models/pretrained/'+name,'Local academic research; externally pretrained, not trained by student',prefix)
        print(source,path.name,path.stat().st_size,flush=True)
