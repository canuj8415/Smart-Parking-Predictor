"""Research-only plain-SGD source updates and atomic paired restart state."""
import os
from pathlib import Path
import numpy as np
import torch
from .region_validity import masked_bay_loss
from .region_gradient_guard import guard_auxiliary_gradient
from .region_gradients import gradient_geometry


def source_step(model,optimizer,features,target,valid,pklot,acpds,positive_weight,guarded):
    if not isinstance(optimizer,torch.optim.SGD) or any(g['momentum'] or g['weight_decay'] or g['nesterov'] or g.get('maximize',False) for g in optimizer.param_groups):
        raise ValueError('Plain SGD without momentum or weight decay required')
    parameters=tuple(model.parameters())
    if not parameters or any(p.device.type!='cpu' or p.dtype!=torch.float32 for p in parameters):
        raise ValueError('CPU float32 parameters required;float64 geometry converted explicitly')
    gradients=[];losses=[]
    optimizer.zero_grad(set_to_none=True)
    for indices in [pklot,acpds]:
        batch=features[indices] if isinstance(features,torch.Tensor) else tuple(f[indices] for f in features)
        loss=masked_bay_loss(model(batch),target[indices],valid[indices],positive_weight)
        parts=torch.autograd.grad(loss,parameters)
        gradients.append(torch.cat([g.detach().reshape(-1) for g in parts]).double().numpy())
        losses.append(float(loss.detach()))
    a,b=gradients;geometry=gradient_geometry(a,b)
    auxiliary=guard_auxiliary_gradient(a,b) if guarded else b
    combined=torch.from_numpy((a+auxiliary)*.5).to(torch.float32)
    typed=combined.double().numpy();aa=float(a@a);actual_auxiliary=2*typed-a
    projection_violation=max(0.,-float(a@actual_auxiliary))/aa if aa else 0.
    cap_ratio=float(np.linalg.norm(actual_auxiliary)/np.sqrt(aa)) if aa else None
    descent_violation=max(0.,.5*aa-float(a@typed))/aa if aa else 0.
    if guarded and (projection_violation>1e-5 or descent_violation>1e-5 or (cap_ratio is not None and cap_ratio>1.00001)):
        raise ValueError('Typed guarded gradient exceeds prespecified numerical tolerance')
    cursor=0
    for parameter in parameters:
        parameter.grad=combined[cursor:cursor+parameter.numel()].reshape_as(parameter).clone();cursor+=parameter.numel()
    optimizer.step()
    if not all(torch.isfinite(p).all() for p in parameters):raise ValueError('Nonfinite updated parameters')
    return dict(pklot_loss=losses[0],acpds_loss=losses[1],combined_loss=sum(losses)/2,
        cosine_before=geometry['cosine'],typed_auxiliary_norm_ratio=cap_ratio,
        typed_relative_projection_violation=projection_violation,typed_relative_descent_violation=descent_violation,
        typed_pklot_directional_derivative=-float(a@typed),guarded=bool(guarded))


def save_pair_state(path,models,optimizers,training,protocol_sha256,schedule_hashes):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.partial')
    torch.save(dict(protocol_sha256=protocol_sha256,schedule_hashes=schedule_hashes,
        models={k:v.state_dict() for k,v in models.items()},optimizers={k:v.state_dict() for k,v in optimizers.items()},
        training=training,rng_state=torch.random.get_rng_state()),temporary)
    os.replace(temporary,path)


def load_pair_state(path,models,optimizers,protocol_sha256,schedule_hashes):
    saved=torch.load(path,map_location='cpu',weights_only=True)
    if (saved['protocol_sha256']!=protocol_sha256 or saved['schedule_hashes']!=schedule_hashes
            or set(saved['models'])!=set(models) or set(saved['optimizers'])!=set(optimizers)):
        raise ValueError('Paired checkpoint protocol/sampling/model binding changed')
    for name in models:
        models[name].load_state_dict(saved['models'][name]);optimizers[name].load_state_dict(saved['optimizers'][name])
    torch.random.set_rng_state(saved['rng_state'])
    return saved['training']
