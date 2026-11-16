import copy
import random
import unittest
import numpy as np
from smart_parking.tiled_detection import tile_plan,map_box,mask_to_view,touches_inner_edge,select_additions


class TiledDetectionTests(unittest.TestCase):
    def test_declared_native_plan_covers_source_with_overlap(self):
        self.assertEqual(tile_plan((3840,2160)),[(0,0,2304,1296),(1536,0,3840,1296),(0,864,2304,2160),(1536,864,3840,2160)])

    def test_bottom_right_mapping(self):
        tile=tile_plan((3840,2160))[-1]
        np.testing.assert_allclose(map_box([0,0,960,540],tile,(3840,2160),(960,540)),[384,216,960,540])

    def test_seeded_coordinate_inverse(self):
        rng=random.Random(141)
        for _ in range(50):
            w,h=rng.randint(50,3000),rng.randint(50,2000);tile=rng.choice(tile_plan((w,h)))
            x,y=rng.uniform(0,800),rng.uniform(0,400);box=[x,y,x+100,y+100]
            mapped=map_box(box,tile,(w,h),(960,540))
            inverse=[(mapped[i]*([w,h][i%2])/[960,540][i%2]-tile[i%2])*[960,540][i%2]/(tile[i%2+2]-tile[i%2]) for i in range(4)]
            np.testing.assert_allclose(inverse,box,atol=1e-10)

    def test_only_artificial_edges_reject_clipped_objects(self):
        tile=tile_plan((3840,2160))[0]
        self.assertFalse(touches_inner_edge([0,0,10,10],tile,(3840,2160),(960,540)))
        self.assertTrue(touches_inner_edge([950,20,960,50],tile,(3840,2160),(960,540)))

    def test_mask_projection_does_not_wrap_or_shift(self):
        mask=np.ones((540,960),dtype=bool);canvas=mask_to_view(mask,tile_plan((3840,2160))[-1],(3840,2160),(960,540))
        self.assertEqual(canvas.sum(),576*324);self.assertFalse(canvas[:216].any());self.assertFalse(canvas[:,:384].any());self.assertTrue(canvas[216:,384:].all())

    def test_higher_score_crop_does_not_replace_full_frame(self):
        base=[dict(label='car',box=[0,0,10,10],score=.6)];before=copy.deepcopy(base)
        proposals=[dict(label='car',box=[0,0,10,10],score=.99,tile_index=0,proposal_index=0),dict(label='truck',box=[0,0,10,10],score=.8,tile_index=0,proposal_index=1)]
        accepted,duplicates=select_additions(base,proposals)
        self.assertEqual(accepted,[1]);self.assertEqual(duplicates,[0]);self.assertEqual(base,before)

    def test_invalid_geometry_and_mask_type_fail(self):
        with self.assertRaises(ValueError):tile_plan((0,20))
        with self.assertRaises(ValueError):map_box([-1,0,20,20],(0,0,50,50),(100,100),(20,20))
        with self.assertRaises(ValueError):mask_to_view(np.zeros((20,20)),(0,0,50,50),(100,100),(20,20))
