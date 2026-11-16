import unittest
from smart_parking.anchor_support import assign_bottom_center,support_diagnostics,support_gates

def layout():
    return dict(camera_id='fixture',image_size=[80,60],slots=[
        dict(id='upper',polygon=[[1,1],[39,1],[39,29],[1,29]]),
        dict(id='lower',polygon=[[1,30],[39,30],[39,58],[1,58]])])

class AnchorSupportTests(unittest.TestCase):
    def test_uses_bottom_point_not_projected_box_area(self):
        result=assign_bottom_center((80,60),layout(),[dict(id=0,score=.9,box=[5,5,30,50])])
        self.assertIsNone(result[0]['vehicle_id']);self.assertEqual(result[1]['vehicle_id'],0)
        self.assertEqual(result[1]['anchor_xy'],[17.5,50])
        self.assertNotIn('state',result[0])

    def test_outside_bottom_not_clipped_into_edge_slot(self):
        result=assign_bottom_center((80,60),layout(),[dict(id=0,score=.9,box=[5,5,30,60])])
        self.assertTrue(all(r['vehicle_id'] is None for r in result))

    def test_one_vehicle_and_deterministic_overlapping_slot_tie(self):
        a=layout();a['slots'][1]['polygon']=a['slots'][0]['polygon']
        result=assign_bottom_center((80,60),a,[dict(id=0,score=.9,box=[5,5,30,20])])
        self.assertEqual([r['vehicle_id'] for r in result],[None,0])

    def test_malformed_boxes_ids_and_scores_refused(self):
        for ds in [[dict(id=-1,score=.9,box=[5,5,30,50])],
                   [dict(id=0,score=float('nan'),box=[5,5,30,50])],
                   [dict(id=0,score=.9,box=[30,5,5,50])],
                   [dict(id=0,score=.9,box=[5,5,30,50])]*2]:
            with self.assertRaises(ValueError):assign_bottom_center((80,60),layout(),ds)

    def test_reduced_false_support_cannot_hide_lost_occupied_support(self):
        rows=[dict(image='A',slot_id='1',label=1,reference_id=0,anchor_id=None),
              dict(image='A',slot_id='2',label=1,reference_id=1,anchor_id=0),
              dict(image='A',slot_id='3',label=0,reference_id=2,anchor_id=None),
              dict(image='A',slot_id='4',label=0,reference_id=None,anchor_id=None)]
        metrics=support_diagnostics(rows);self.assertEqual(metrics['reference_occupied_support_retention']['fraction'],.5)
        checks=support_gates(metrics,dict(minimum_each_truth_count=2,false_support_fraction_of_reference_max=.5,occupied_support_retention_min=.95,image_occupied_support_retention_min=.9))
        self.assertTrue(checks['false_support_reduced']);self.assertFalse(checks['occupied_support_retained'])
        with self.assertRaises(ValueError):support_diagnostics(rows+rows[:1])
