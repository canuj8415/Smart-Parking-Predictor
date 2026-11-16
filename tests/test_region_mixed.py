import unittest
import numpy as np
from smart_parking.region_mixed import paired_schedule,source_balanced_score,retention_checks


class MixedRegionTests(unittest.TestCase):
    def test_schedule_is_reproducible_balanced_and_shares_half_control(self):
        pk=np.arange(200);ac=np.arange(230,461)
        a,b=paired_schedule(pk,ac);c,d=paired_schedule(pk,ac)
        np.testing.assert_array_equal(a,c);np.testing.assert_array_equal(b,d)
        self.assertEqual(a.shape,(32,25,8));self.assertEqual(b.shape,a.shape)
        np.testing.assert_array_equal(a[:,:,:4],b[:,:,:4])
        self.assertTrue(np.isin(a,pk).all());self.assertTrue(np.isin(b[:,:,:4],pk).all());self.assertTrue(np.isin(b[:,:,4:],ac).all())
        for first,second in zip(a,b):
            self.assertEqual(len(np.unique(first)),200);self.assertEqual(len(np.unique(second[:,4:])),100)
        self.assertEqual(len(np.unique(b[:,:,:4])),200);self.assertEqual(len(np.unique(b[:,:,4:])),231)

    def test_schedule_rejects_invalid_or_overlapping_pools(self):
        for pk,ac in [([0]*8,list(range(10,20))),(list(range(8)),list(range(4,10))),([0,1],[2,3]),(list(range(8)),[10]),([-1]+list(range(7)),list(range(10,20))),(list(range(8)),[10.5]*4)]:
            with self.subTest(pk=pk,ac=ac),self.assertRaises(ValueError):paired_schedule(pk,ac)

    def test_source_score_weights_sources_equally_and_rejects_nonfinite(self):
        self.assertAlmostEqual(source_balanced_score({'macro_camera_iou':.8},{'mean_image_iou':.4}),.6)
        with self.assertRaises(ValueError):source_balanced_score({'macro_camera_iou':float('nan')},{'mean_image_iou':.4})

    def test_gate_rejects_single_image_regression_despite_aggregate_gain(self):
        pk=dict(macro_camera_iou=.7,by_camera={'view':{'mean_iou':.7}},per_image=[dict(index=0,camera_id='view',iou=.7)])
        base=dict(pklot=pk,acpds={'mean_image_iou':.3})
        changed=dict(pklot={**pk,'per_image':[dict(index=0,camera_id='view',iou=.64)]},acpds={'mean_image_iou':.5})
        gates=dict(acpds_gain=.05,pklot_macro_regression=.02,pklot_camera_regression=.05,pklot_image_regression=.05)
        result=retention_checks(changed,base,gates)
        self.assertTrue(result['acpds_gain']);self.assertTrue(result['pklot_macro_retained']);self.assertFalse(result['every_pklot_image_retained'])
