"""Research gradient transform; first-order geometry is not model acceptance."""
import numpy as np


def guard_auxiliary_gradient(reference,auxiliary):
    """Remove opposition to reference and cap auxiliary norm at reference norm.

    Returns float64 vectors for a future plain-SGD experiment. This says nothing
    about finite-step loss, AdamW momentum/preconditioning or DEV retention.
    A zero reference gradient suppresses the auxiliary direction conservatively.
    """
    a=np.asarray(reference,dtype=np.float64);b=np.asarray(auxiliary,dtype=np.float64)
    if a.ndim!=1 or a.shape!=b.shape or not a.size or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Aligned nonempty finite gradients required')
    with np.errstate(over='ignore',invalid='ignore'):
        aa=float(a@a);dot=float(a@b)
    if not np.isfinite(aa) or not np.isfinite(dot):raise ValueError('Gradient geometry overflow')
    if aa==0:return np.zeros_like(b)
    guarded=b.copy()
    if dot<0:guarded-=dot/aa*a
    norm=float(np.linalg.norm(guarded));reference_norm=float(np.sqrt(aa))
    if not np.isfinite(norm):raise ValueError('Auxiliary gradient norm overflow')
    if norm>reference_norm:guarded*=reference_norm/norm
    return guarded
