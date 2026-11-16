"""Executed synthetic XOR lesson; not a parking benchmark."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.mlp import MLP
from smart_parking.provenance import digest
if __name__=='__main__':
    x=np.array([[0,0],[0,1],[1,0],[1,1]],dtype=float);y=np.array([0,1,1,0])
    model=MLP();error=model.gradient_check(x,y)
    if error>1e-5:raise RuntimeError('Analytic gradients fail central-difference check')
    curves=[]
    for epoch in range(2000):
        loss,gradients=model.loss_and_gradients(x,y);model.step(gradients,.1,.9)
        if epoch%20==0:curves.append(dict(epoch=epoch,loss=loss))
    prediction=model.forward(x)[0].ravel()
    if not np.array_equal(prediction>=.5,y):raise RuntimeError('XOR convergence test failed')
    folder=ROOT/'models/checkpoints';folder.mkdir(parents=True,exist_ok=True);path=folder/'mlp_xor.npz';model.save(path)
    if not np.allclose(MLP.load(path).forward(x)[0],model.forward(x)[0]):raise RuntimeError('Checkpoint round-trip mismatch')
    run='MLP-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/run;out.mkdir(parents=True)
    result=dict(run_id=run,data_type='synthetic educational XOR, not real parking',seed=42,epochs=2000,
        optimizer='manual momentum SGD',learning_rate=.1,momentum=.9,gradient_max_absolute_error=error,
        final_loss=model.loss_and_gradients(x,y)[0],probabilities=prediction.tolist(),checkpoint_sha256=digest(path),
        code_sha256=digest(ROOT/'src/smart_parking/mlp.py'),curves=curves)
    (out/'run.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='curves'},indent=2))
