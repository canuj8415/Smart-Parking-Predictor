import sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.mlp import MLP

class ManualNetworkTests(unittest.TestCase):
    def test_all_analytic_gradients_match_finite_differences(self):
        model=MLP();x=np.array([[0.,0.],[0.,1.],[1.,0.],[1.,1.]])
        self.assertLess(model.gradient_check(x,[0,1,1,0]),1e-5)

    def test_sgd_momentum_updates_and_checkpoint_round_trip(self):
        model=MLP();initial={k:v.copy() for k,v in model.parameters.items()}
        gradients={k:np.ones_like(v) for k,v in initial.items()}
        model.step(gradients,.1,.5);model.step(gradients,.1,.5)
        for k in initial:np.testing.assert_allclose(model.parameters[k],initial[k]-.25)
        temp_root=Path(__file__).resolve().parents[1]/'.cache/test_tmp'
        temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            if not Path(folder).resolve().is_relative_to(temp_root.resolve()):raise RuntimeError('Unexpected temporary directory')
            path=Path(folder)/'weights.npz';model.save(path);loaded=MLP.load(path)
            np.testing.assert_array_equal(loaded.forward([[.2,.7]])[0],model.forward([[.2,.7]])[0])

    def test_invalid_inputs_and_optimizer_settings(self):
        model=MLP()
        with self.assertRaises(ValueError):model.forward([[np.nan,1.]])
        with self.assertRaises(ValueError):model.forward([[1.,2.,3.]])
        with self.assertRaises(ValueError):model.step({},-.1,0)

if __name__=='__main__':unittest.main()
