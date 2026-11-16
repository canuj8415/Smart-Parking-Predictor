import tempfile
from pathlib import Path
import unittest
import torch
from smart_parking.region_fpn import RegionPyramidDecoder
from smart_parking.region_detail_adapters import build_adapter_pair
from smart_parking.region_guarded_training import source_step,save_pair_state,load_pair_state


class RegionDetailAdapterTests(unittest.TestCase):
    def setUp(self):
        threads=torch.get_num_threads();torch.set_num_threads(1);self.addCleanup(torch.set_num_threads,threads)
        torch.manual_seed(185);self.base=RegionPyramidDecoder(4)
        self.features=tuple(torch.randn(8,c,h,w) for c,h,w in [(64,2,2),(128,1,1),(256,1,1),(512,1,1)])
        self.rgb=torch.randint(0,256,(8,3,8,8),dtype=torch.uint8);self.inputs=(*self.features,self.rgb)
        self.target=(torch.rand(8,1,8,8)>.6).float();self.valid=torch.ones_like(self.target,dtype=torch.bool)

    def pair(self,lr=.01):
        models=build_adapter_pair(self.base.state_dict(),width=4,detail_width=2,detail_seed=183)
        return models,{k:torch.optim.SGD(m.parameters(),lr=lr,foreach=False) for k,m in models.items()}

    def test_initial_predictions_coarse_weights_and_caller_rng_are_exact(self):
        before=torch.random.get_rng_state().clone();models,_=self.pair()
        self.assertTrue(torch.equal(before,torch.random.get_rng_state()))
        with torch.no_grad():
            expected=self.base(self.features,output_size=(8,8))
            for model in models.values():
                self.assertTrue(torch.equal(model(self.inputs),expected))
                for name,value in model.coarse.state_dict().items():self.assertTrue(torch.equal(value,self.base.state_dict()[name]))
            changed=(*self.features,torch.zeros_like(self.rgb));self.assertTrue(torch.equal(models['detail'](changed),expected))

    def test_uint8_normalizes_once_and_invalid_input_contract_is_rejected(self):
        models,_=self.pair();model=models['detail'];rgb=torch.tensor([0,255,0],dtype=torch.uint8).reshape(1,3,1,1)
        value=model.normalize_rgb(rgb)
        self.assertAlmostEqual(float(value[0,0,0,0]),-.485/.229,places=6)
        self.assertAlmostEqual(float(value[0,1,0,0]),(1-.456)/.224,places=6)
        with self.assertRaises(ValueError):model.normalize_rgb(rgb.float())
        for adapter in models.values():
            with self.assertRaises(ValueError):adapter(self.features)
            with self.assertRaises(ValueError):adapter((*self.features,self.rgb.float()))
            with self.assertRaises(ValueError):adapter((*self.features,self.rgb[:1]))

    def test_adapter_pair_checkpoint_roundtrip_after_actual_synthetic_update(self):
        models,opts=self.pair();training={'cursor':1,'kind':'synthetic_software_fixture'}
        for name,model in models.items():source_step(model,opts[name],self.inputs,self.target,self.valid,[0,1],[4,5],2.,True)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'last.pt';save_pair_state(path,models,opts,training,'synthetic',{'fixture':'one'})
            restored,optimizers=self.pair(lr=99.);loaded=load_pair_state(path,restored,optimizers,'synthetic',{'fixture':'one'})
            self.assertEqual(loaded,training)
            for name in models:
                self.assertEqual(optimizers[name].param_groups[0]['lr'],.01)
                with torch.no_grad():self.assertTrue(torch.equal(models[name](self.inputs),restored[name](self.inputs)))

    def test_mid_pair_restart_matches_uninterrupted_adapter_weights_and_logs(self):
        full,fo=self.pair();interrupted,io=self.pair();expected=[]
        def update(model,opt,step):return source_step(model,opt,self.inputs,self.target,self.valid,[step%4,(step+1)%4],[4+step%4,4+(step+1)%4],2.,True)
        for step in range(6):expected.append({k:update(m,fo[k],step) for k,m in full.items()})
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'last.pt';state={'cursor':0,'logs':[]};save_pair_state(path,interrupted,io,state,'synthetic',{'fixture':'six'})
            try:
                for step in range(6):
                    row={}
                    for name,model in interrupted.items():
                        row[name]=update(model,io[name],step)
                        if step==2 and name=='control':raise InterruptedError('Synthetic half-pair interruption')
                    state['cursor']+=1;state['logs'].append(row);save_pair_state(path,interrupted,io,state,'synthetic',{'fixture':'six'})
            except InterruptedError:pass
            resumed,ro=self.pair(lr=99.);state=load_pair_state(path,resumed,ro,'synthetic',{'fixture':'six'});self.assertEqual(state['cursor'],2)
            for step in range(state['cursor'],6):
                state['logs'].append({k:update(m,ro[k],step) for k,m in resumed.items()});state['cursor']+=1
            self.assertEqual(state['logs'],expected);self.assertEqual(state['cursor'],6)
            for name in full:
                for key,value in full[name].state_dict().items():self.assertTrue(torch.equal(value,resumed[name].state_dict()[key]))
                self.assertEqual(fo[name].state_dict(),ro[name].state_dict())
