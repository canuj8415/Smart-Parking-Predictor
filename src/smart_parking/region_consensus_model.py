"""Frozen RGB decoder plus explicit known-camera, training-only geometry priors."""
import numpy as np
import torch
from torchvision.models import resnet18
from torchvision.transforms import functional as TF
from .provenance import digest
from .region_transfer import FrozenRegionEncoder,RegionDecoder
from .region_evaluation import project_logits
from .region_consensus import compose_mask


class ConsensusRegionModel:
    def __init__(self,bundle_path,encoder_path):
        bundle=torch.load(bundle_path,map_location='cpu',weights_only=True)
        if digest(encoder_path)!=bundle['encoder_weights_sha256']:raise ValueError('Encoder weights changed')
        backbone=resnet18(weights=None);backbone.load_state_dict(torch.load(encoder_path,map_location='cpu',weights_only=True))
        self.encoder=FrozenRegionEncoder(backbone);self.decoder=RegionDecoder()
        self.decoder.load_state_dict(bundle['decoder_state_dict']);self.decoder.eval();self.bundle=bundle
        self.priors={camera:{k:(v.numpy() if isinstance(v,torch.Tensor) else v) for k,v in prior.items()} for camera,prior in bundle['priors'].items()}

    @torch.inference_mode()
    def predict(self,images,camera_ids):
        if len(images)!=len(camera_ids) or not images:raise ValueError('Images and explicit camera IDs must match')
        for image,camera in zip(images,camera_ids):
            if camera not in self.priors:raise ValueError('Unknown camera; no automatic layout discovery')
            if list(image.size) not in self.bundle['source_image_sizes'][camera]:raise ValueError('Known-camera view dimensions differ')
        mean=torch.tensor([.485,.456,.406])[None,:,None,None];std=torch.tensor([.229,.224,.225])[None,:,None,None]
        neural=[]
        for at in range(0,len(images),4):
            # Explicit PIL bilinear interpolation must match the fitted decoder pipeline.
            from PIL import Image
            rgb=torch.stack([TF.to_tensor(image.convert('RGB').resize(tuple(self.bundle['input_size']),Image.Resampling.BILINEAR)) for image in images[at:at+4]])
            logits=self.decoder(rgb,self.encoder((rgb-mean)/std))
            neural.extend((project_logits(logits,tuple(self.bundle['evaluation_grid'])).sigmoid()>=.5).numpy())
        neural=np.stack(neural)
        composed=np.stack([compose_mask(mask,camera,self.priors,self.bundle.get('route_policy','unanimous_pixels')) for mask,camera in zip(neural,camera_ids)])
        return neural,composed
