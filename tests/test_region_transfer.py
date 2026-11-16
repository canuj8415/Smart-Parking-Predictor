"""Architecture and reservation properties; synthetic inputs are not accuracy data."""
import sys,unittest
from pathlib import Path
import torch
from torchvision.models import resnet18
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.region_transfer import FrozenRegionEncoder,RegionDecoder,reserve_fresh_final

class RegionTransferTests(unittest.TestCase):
    def test_frozen_encoder_keeps_batchnorm_and_decoder_can_learn(self):
        torch.set_num_threads(2);torch.manual_seed(1)
        encoder=FrozenRegionEncoder(resnet18(weights=None));encoder.train()
        before=encoder.stem[1].running_mean.clone();rgb=torch.rand(1,3,112,192)
        feature=encoder(rgb);decoder=RegionDecoder();logits=decoder(rgb,feature)
        self.assertEqual(logits.shape,(1,1,112,192));logits.square().mean().backward()
        self.assertTrue(torch.equal(before,encoder.stem[1].running_mean));self.assertFalse(encoder.training)
        self.assertTrue(all(not p.requires_grad and p.grad is None for p in encoder.parameters()))
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in decoder.parameters()))
    def test_fresh_reservation_excludes_used_dates_and_requires_later_dates(self):
        pairs=[];validation=[]
        for folder,camera,month in [('parking1a','ufpr04',1),('parking1b','ufpr05',2),('parking2','pucpr',3)]:
            validation.append(dict(camera_id=camera,date=f'2020-{month:02}-03'))
            for day in [2,4,5]:
                date=f'2020-{month:02}-{day:02}'
                for i in [0,1]:pairs.append(dict(date=date,image=f'data/raw/pklot_subset/PKLot/{folder}/sunny/{date}/{i}.jpg',annotation='closed.xml'))
        used={f'2020-{month:02}-05' for month in [1,2,3]};reserved=reserve_fresh_final(pairs,used,validation)
        self.assertEqual(len(reserved),6);self.assertFalse({r['date'] for r in reserved}&used)
        self.assertTrue(all(r['date'].endswith('-04') and r['split']=='test' for r in reserved))
    def test_no_eligible_new_date_fails_instead_of_reusing_a_test(self):
        with self.assertRaisesRegex(ValueError,'No fresh later'):reserve_fresh_final([],set(),[dict(camera_id=c,date='2020-01-01') for c in ['pucpr','ufpr04','ufpr05']])

if __name__=='__main__':unittest.main()
