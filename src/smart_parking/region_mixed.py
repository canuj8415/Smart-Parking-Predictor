"""Prespecified sampling and source-balanced selection for a paired DEV study."""
import numpy as np


def paired_schedule(pklot_train, acpds_train, rounds=32, seed=176):
    """PKLot control8 versus the same first4 plus4ACPDS, no DEV indices."""
    pk=np.asarray(pklot_train); ac=np.asarray(acpds_train)
    if (pk.ndim!=1 or ac.ndim!=1 or pk.dtype.kind not in 'iu' or ac.dtype.kind not in 'iu'
            or len(pk)==0 or len(pk)%8 or len(ac)<len(pk)//2 or rounds<1
            or len(np.unique(pk))!=len(pk) or len(np.unique(ac))!=len(ac)
            or len(np.intersect1d(pk,ac)) or np.any(pk<0) or np.any(ac<0)):
        raise ValueError('Disjoint unique nonnegative integer TRAIN pools; PKLot multiple8 and enough ACPDS required')
    generator=np.random.default_rng(seed); other=np.random.default_rng(seed+1)
    control=[];mixed=[]
    for _ in range(rounds):
        a=generator.permutation(pk).reshape(-1,8)
        b=other.permutation(ac)[:len(pk)//2].reshape(-1,4)
        control.append(a);mixed.append(np.concatenate([a[:,:4],b],axis=1))
    return np.asarray(control,dtype=np.int64),np.asarray(mixed,dtype=np.int64)


def source_balanced_score(pklot,acpds):
    a=float(pklot['macro_camera_iou']);b=float(acpds['mean_image_iou'])
    if not all(np.isfinite(x) and 0<=x<=1 for x in [a,b]):
        raise ValueError('Finite source IoU in [0,1] required')
    return (a+b)/2


def retention_checks(candidate,control,gates):
    pk=candidate['pklot'];base=control['pklot'];ac=candidate['acpds']
    if set(pk['by_camera'])!=set(base['by_camera']) or len(pk['per_image'])!=len(base['per_image']):
        raise ValueError('Aligned PKLot development cameras/images required')
    return dict(acpds_gain=ac['mean_image_iou']-control['acpds']['mean_image_iou']>=gates['acpds_gain'],
        pklot_macro_retained=pk['macro_camera_iou']>=base['macro_camera_iou']-gates['pklot_macro_regression'],
        every_pklot_camera_retained=all(pk['by_camera'][c]['mean_iou']>=v['mean_iou']-gates['pklot_camera_regression'] for c,v in base['by_camera'].items()),
        every_pklot_image_retained=all(a['index']==b['index'] and a['camera_id']==b['camera_id'] and a['iou']>=b['iou']-gates['pklot_image_regression'] for a,b in zip(pk['per_image'],base['per_image'])))
