"""Experimental image-only alignment of a configured parking view.

No occupancy labels enter matching. An accepted transform is a geometric
proposal, not authenticated camera identity or guaranteed slot correspondence.
See the separately recorded development validation before any deployment use.
"""
import numpy as np

DEFAULTS=dict(work_size=(768,448),features=3000,ratio=.75,ransac_pixels=4.,
              min_inliers=20,min_inlier_ratio=.35,min_spatial_coverage=.10,
              min_area_ratio=.5,max_area_ratio=2.,max_corner_shift=.30,
              min_frame_overlap=.65)

def describe(image,config=None):
    import cv2
    from PIL import Image
    settings={**DEFAULTS,**(config or {})}
    gray=np.asarray(image.convert('L').resize(settings['work_size'],Image.Resampling.BILINEAR))
    keypoints,descriptors=cv2.ORB_create(nfeatures=settings['features']).detectAndCompute(gray,None)
    return dict(points=np.float32([k.pt for k in keypoints]).reshape(-1,2),descriptors=descriptors)

def check_transform(matrix,size,config=None):
    """Reject degenerate, mirrored, extreme or mostly off-frame proposals."""
    import cv2
    s={**DEFAULTS,**(config or {})};h=np.asarray(matrix,dtype=float)
    if h.shape!=(3,3) or not np.isfinite(h).all() or abs(np.linalg.det(h))<1e-10 or abs(h[2,2])<1e-10:
        return dict(accepted=False,reason='invalid or singular transform')
    h=h/h[2,2];width,height=size
    corners=np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]])
    homogeneous=np.column_stack([corners,np.ones(4)])@h.T
    if (homogeneous[:,2]<=1e-6).any():return dict(accepted=False,reason='projective horizon crosses view')
    transformed=(homogeneous[:,:2]/homogeneous[:,2:]).astype('float32')
    if not cv2.isContourConvex(transformed) or cv2.contourArea(transformed,oriented=True)<=0:
        return dict(accepted=False,reason='mirrored or nonconvex view')
    area=cv2.contourArea(corners);ratio=cv2.contourArea(transformed)/area
    shift=float(np.linalg.norm(transformed-corners,axis=1).max()/np.hypot(width,height))
    overlap=float(cv2.intersectConvexConvex(corners,transformed)[0]/area)
    stats=dict(area_ratio=float(ratio),max_corner_shift_fraction=shift,frame_overlap_fraction=overlap)
    if not s['min_area_ratio']<=ratio<=s['max_area_ratio'] or shift>s['max_corner_shift'] or overlap<s['min_frame_overlap']:
        return dict(accepted=False,reason='transform outside conservative view bounds',**stats)
    return dict(accepted=True,reason='geometric proposal within bounds',**stats)

def estimate(reference,target,config=None,seed=67):
    import cv2
    s={**DEFAULTS,**(config or {})};stats=dict(accepted=False,matches=0,inliers=0,inlier_ratio=0.,reason='insufficient image features')
    a,b=reference['descriptors'],target['descriptors']
    if a is None or b is None or min(len(a),len(b))<2:return None,stats
    pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(a,b,k=2)
    good=[pair[0] for pair in pairs if len(pair)==2 and pair[0].distance<s['ratio']*pair[1].distance]
    # Unique target features prevent many source features from voting for one point.
    unique={}
    for match in sorted(good,key=lambda m:m.distance):unique.setdefault(match.trainIdx,match)
    good=list(unique.values());stats['matches']=len(good)
    if len(good)<s['min_inliers']:return None,stats
    source=reference['points'][[m.queryIdx for m in good]];destination=target['points'][[m.trainIdx for m in good]]
    cv2.setRNGSeed(seed)
    matrix,inlier=cv2.findHomography(source,destination,cv2.RANSAC,s['ransac_pixels'],maxIters=2000,confidence=.995)
    if matrix is None or inlier is None:return None,{**stats,'reason':'no robust transform'}
    keep=inlier.ravel().astype(bool);count=int(keep.sum());fraction=count/len(good)
    width,height=s['work_size']
    coverage=min(cv2.contourArea(cv2.convexHull(points[keep]))/(width*height) for points in [source,destination]) if count>=3 else 0.
    stats.update(inliers=count,inlier_ratio=fraction,spatial_coverage=float(coverage))
    if count<s['min_inliers'] or fraction<s['min_inlier_ratio'] or coverage<s['min_spatial_coverage']:
        return None,{**stats,'reason':'insufficient distributed geometric support'}
    checked=check_transform(matrix,s['work_size'],s);stats.update(checked)
    return (matrix if checked['accepted'] else None),stats

def development_rows(rows):
    """Filter before opening any source; final/unknown splits are never loaded."""
    return [r for r in rows if r.get('split') in {'train','validation'}]
