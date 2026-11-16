import copy
from pathlib import Path
import tempfile
import unittest
import torch
from smart_parking.region_guarded_training import source_step,save_pair_state,load_pair_state
from smart_parking.region_validity import masked_bay_loss


class GuardedTrainingTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(181)
        self.x=torch.randn(8,1,3,3);self.y=(self.x>.3).float();self.valid=torch.ones_like(self.y,dtype=torch.bool)

    def pair(self,lr=.01):
        torch.manual_seed(182);first=torch.nn.Conv2d(1,1,1)
        models={'raw':first,'guarded':copy.deepcopy(first)}
        return models,{k:torch.optim.SGD(v.parameters(),lr=lr,foreach=False) for k,v in models.items()}

    def test_raw_update_matches_direct_equal_source_batch_objective(self):
        models,opts=self.pair();direct=copy.deepcopy(models['raw']);opt=torch.optim.SGD(direct.parameters(),lr=.01,foreach=False)
        batch=[0,1,4,5];loss=masked_bay_loss(direct(self.x[batch]),self.y[batch],self.valid[batch],2.)
        loss.backward();opt.step()
        source_step(models['raw'],opts['raw'],self.x,self.y,self.valid,[0,1],[4,5],2.,False)
        for a,b in zip(direct.parameters(),models['raw'].parameters()):torch.testing.assert_close(a,b,atol=1e-7,rtol=1e-7)

    def test_mid_pair_interruption_restores_models_optimizer_groups_cursor_and_logs_exactly(self):
        full,fo=self.pair();interrupted,io=self.pair();protocol='synthetic-only';schedule={'fixture':'fixed8pairs'}
        expected=[]
        for step in range(8):
            expected.append({k:source_step(v,fo[k],self.x,self.y,self.valid,[step%4,(step+1)%4],[4+step%4,4+(step+1)%4],2.,k=='guarded') for k,v in full.items()})
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'last.pt';training=dict(cursor=0,logs=[])
            save_pair_state(path,interrupted,io,training,protocol,schedule)
            try:
                for step in range(8):
                    row={}
                    for name,model in interrupted.items():
                        row[name]=source_step(model,io[name],self.x,self.y,self.valid,[step%4,(step+1)%4],[4+step%4,4+(step+1)%4],2.,name=='guarded')
                        if step==4 and name=='raw':raise InterruptedError('Synthetic interruption after only raw arm changed')
                    training['cursor']+=1;training['logs'].append(row);save_pair_state(path,interrupted,io,training,protocol,schedule)
            except InterruptedError:pass
            resumed,ro=self.pair(lr=99.)
            restored=load_pair_state(path,resumed,ro,protocol,schedule)
            self.assertEqual(restored['cursor'],4);self.assertEqual(ro['raw'].param_groups[0]['lr'],.01)
            for step in range(restored['cursor'],8):
                row={k:source_step(v,ro[k],self.x,self.y,self.valid,[step%4,(step+1)%4],[4+step%4,4+(step+1)%4],2.,k=='guarded') for k,v in resumed.items()}
                restored['logs'].append(row);restored['cursor']+=1;save_pair_state(path,resumed,ro,restored,protocol,schedule)
            self.assertEqual(restored['logs'],expected);self.assertEqual(restored['cursor'],8)
            for name in full:
                for a,b in zip(full[name].parameters(),resumed[name].parameters()):self.assertTrue(torch.equal(a,b))
                self.assertEqual(fo[name].state_dict(),ro[name].state_dict())

    def test_mismatched_checkpoint_binding_rejected_before_mutating_live_models(self):
        models,opts=self.pair()
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'last.pt';save_pair_state(path,models,opts,{'cursor':0},'sealed',{'data':'one'})
            before={k:{n:t.clone() for n,t in m.state_dict().items()} for k,m in models.items()}
            with self.assertRaises(ValueError):load_pair_state(path,models,opts,'changed',{'data':'one'})
            for k,m in models.items():
                for n,t in m.state_dict().items():self.assertTrue(torch.equal(before[k][n],t))

    def test_adam_or_momentum_is_rejected_and_guard_cast_is_bounded(self):
        models,opts=self.pair();model=models['guarded']
        for opt in [torch.optim.AdamW(model.parameters()),torch.optim.SGD(model.parameters(),lr=.01,momentum=.9),torch.optim.SGD(model.parameters(),lr=.01,maximize=True)]:
            with self.assertRaises(ValueError):source_step(model,opt,self.x,self.y,self.valid,[0,1],[4,5],2.,True)
        result=source_step(model,opts['guarded'],self.x,self.y,self.valid,[0,1],[4,5],2.,True)
        self.assertLessEqual(result['typed_relative_projection_violation'],1e-5)
        self.assertLessEqual(result['typed_relative_descent_violation'],1e-5)
        self.assertLessEqual(result['typed_auxiliary_norm_ratio'],1.00001)
