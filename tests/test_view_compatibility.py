import unittest
import numpy as np
from smart_parking.view_compatibility import assess_homography,decide


class ViewCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.points=np.array([(x,y) for x in np.linspace(40,600,8) for y in np.linspace(30,330,6)])
        self.mask=np.ones(len(self.points),bool)

    def check_matrix(self,h,points=None,mask=None):
        src=self.points if points is None else points
        value=np.c_[src,np.ones(len(src))]@h.T;dst=value[:,:2]/value[:,2,None]
        return assess_homography(h,src,dst,self.mask if mask is None else mask,(640,360))

    def test_identity_supported_but_camera_translation_rejected(self):
        self.assertTrue(self.check_matrix(np.eye(3))['compatible'])
        h=np.eye(3);h[0,2]=32
        self.assertFalse(self.check_matrix(h)['compatible'])

    def test_support_must_be_many_spatially_distributed_inliers(self):
        self.assertFalse(self.check_matrix(np.eye(3),self.points[:10],self.mask[:10])['compatible'])
        self.assertFalse(self.check_matrix(np.eye(3),self.points*.01)['compatible'])
        keep=self.mask.copy();keep[:25]=False
        self.assertFalse(self.check_matrix(np.eye(3),mask=keep)['compatible'])

    def test_invalid_geometry_rejected(self):
        for h in [np.zeros((3,3)),np.full((3,3),np.nan)]:
            self.assertFalse(assess_homography(h,self.points,self.points,self.mask,(640,360))['compatible'])
        with self.assertRaises(ValueError):assess_homography(np.eye(3),self.points,self.points[:-1],self.mask,(640,360))

    def test_correspondence_error_rejected(self):
        r=assess_homography(np.eye(3),self.points,self.points+10,self.mask,(640,360))
        self.assertFalse(r['compatible'])

    def test_reference_consensus_never_warps_or_authenticates(self):
        self.assertFalse(decide([dict(compatible=True),dict(compatible=False),dict(compatible=False)])['compatible'])
        r=decide([dict(compatible=True)]*3);self.assertTrue(r['compatible']);self.assertFalse(r['authentication']);self.assertFalse(r['automatic_warp'])
        with self.assertRaises(ValueError):decide([])
