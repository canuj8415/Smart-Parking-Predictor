"""First-order geometry of two fixed decoder gradients; no weight updates."""
import numpy as np


def gradient_geometry(pklot,acpds):
    a=np.asarray(pklot,dtype=np.float64);b=np.asarray(acpds,dtype=np.float64)
    if a.ndim!=1 or a.shape!=b.shape or not a.size or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Aligned nonempty finite gradient vectors required')
    with np.errstate(over='ignore',invalid='ignore'):
        aa=float(a@a);bb=float(b@b);dot=float(a@b)
    if not all(np.isfinite(x) for x in [aa,bb,dot]):raise ValueError('Gradient geometry overflow')
    an=float(np.sqrt(aa));bn=float(np.sqrt(bb))
    cosine=float(np.clip(dot/(an*bn),-1,1)) if an and bn else None
    # Direction is minus the equal-source mean gradient, without an optimizer.
    pk_derivative=-.5*(aa+dot);ac_derivative=-.5*(bb+dot)
    return dict(pklot_gradient_norm=an,acpds_gradient_norm=bn,gradient_dot=dot,
        cosine=cosine,cosine_defined=cosine is not None,
        acpds_to_pklot_norm_ratio=bn/an if an else None,
        conflicting=bool(dot<0),pklot_equal_descent_directional_derivative=pk_derivative,
        acpds_equal_descent_directional_derivative=ac_derivative,
        pklot_first_order_worsens=bool(pk_derivative>0),acpds_first_order_worsens=bool(ac_derivative>0))
