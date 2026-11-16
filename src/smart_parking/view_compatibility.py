"""Conservative stored-layout view check; visual compatibility, not authentication."""
import numpy as np


def assess_homography(matrix, reference_points, query_points, inliers, size):
    width,height=size
    if width<2 or height<2:raise ValueError('Positive image dimensions required')
    src=np.asarray(reference_points,dtype=float);dst=np.asarray(query_points,dtype=float)
    keep=np.asarray(inliers,dtype=bool).reshape(-1)
    if src.ndim!=2 or src.shape[1:]!=(2,) or src.shape!=dst.shape or len(keep)!=len(src):
        raise ValueError('Paired two-dimensional correspondences required')
    result=dict(compatible=False,matches=len(src),inliers=int(keep.sum()),reason='insufficient_geometric_support')
    if matrix is None or len(src)<30 or keep.sum()<30 or keep.mean()<.25:return result
    h=np.asarray(matrix,dtype=float)
    if h.shape!=(3,3) or not np.isfinite(h).all() or not np.isfinite(src).all() or not np.isfinite(dst).all():return result
    if abs(np.linalg.det(h))<1e-12:return result
    def project(points):
        value=np.c_[points,np.ones(len(points))]@h.T
        if np.any(np.abs(value[:,2])<1e-9):return None
        return value[:,:2]/value[:,2,None]
    corners=np.array([[0,0],[width-1,0],[width-1,height-1],[0,height-1]],float)
    mapped=project(corners);fitted=project(src[keep])
    if mapped is None or fitted is None:return result
    diagonal=float(np.hypot(width,height))
    displacement=float(np.linalg.norm(mapped-corners,axis=1).max()/diagonal)
    residual=float(np.median(np.linalg.norm(fitted-dst[keep],axis=1)))
    span=np.ptp(src[keep],axis=0)/[width,height]
    result.update(corner_displacement_fraction=displacement,median_reprojection_pixels=residual,
                  reference_span_fraction=span.tolist(),inlier_fraction=float(keep.mean()))
    result['compatible']=bool(np.isfinite(mapped).all() and displacement<=.005 and residual<=2 and (span>=.1).all())
    result['reason']='compatible_visual_geometry' if result['compatible'] else 'changed_or_uncertain_view'
    return result


def describe(image):
    import cv2
    value=np.asarray(image)
    if value.ndim!=3 or value.shape[2]!=3 or value.dtype!=np.uint8:raise ValueError('RGB uint8 image required')
    height,width=value.shape[:2]
    if min(width,height)<32:raise ValueError('Image too small for view check')
    scale=min(1.,640/max(width,height));size=(round(width*scale),round(height*scale))
    gray=cv2.cvtColor(cv2.resize(value,size),cv2.COLOR_RGB2GRAY)
    points,descriptors=cv2.ORB_create(nfeatures=1000).detectAndCompute(gray,None)
    return dict(native_size=(width,height),size=size,points=np.array([p.pt for p in points],np.float32).reshape(-1,2),descriptors=descriptors)


def compare(reference, query, seed=143):
    import cv2
    if reference['native_size']!=query['native_size'] or reference['size']!=query['size']:
        return dict(compatible=False,reason='dimensions_changed',matches=0,inliers=0)
    a,b=reference['descriptors'],query['descriptors']
    if a is None or b is None or len(a)<2 or len(b)<2:return dict(compatible=False,reason='insufficient_features',matches=0,inliers=0)
    pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(a,b,k=2)
    good=[p[0] for p in pairs if len(p)==2 and p[0].distance<.75*p[1].distance]
    src=np.array([reference['points'][p.queryIdx] for p in good],np.float32).reshape(-1,2)
    dst=np.array([query['points'][p.trainIdx] for p in good],np.float32).reshape(-1,2)
    if len(src)<30:return dict(compatible=False,reason='insufficient_matches',matches=len(src),inliers=0)
    cv2.setRNGSeed(seed);h,mask=cv2.findHomography(src,dst,cv2.RANSAC,3.,maxIters=2000,confidence=.995)
    return assess_homography(h,src,dst,np.zeros(len(src),bool) if mask is None else mask,reference['size'])


def decide(comparisons):
    if len(comparisons)!=3:raise ValueError('Exactly three independent-date references required')
    support=sum(r['compatible'] is True for r in comparisons)
    return dict(compatible=support>=2,supporting_references=support,reference_count=3,
                action='stored_geometry_candidate' if support>=2 else 'needs_review',
                authentication=False,automatic_warp=False)
