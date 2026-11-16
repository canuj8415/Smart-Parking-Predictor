import copy,unittest
import numpy as np
from smart_parking.vision import assign_occupancy,_assign_occupancy_dense_reference
from smart_parking.occupancy_patches import assign_occupancy_patches,prepare_slot_patches

def layout():return dict(camera_id='fixture',image_size=[80,60],slots=[dict(id='A',polygon=[[.2,.7],[34.9,1.4],[36.2,48.1],[1.8,50.3]]),dict(id='B',polygon=[[36,1],[78,1],[78,58],[36,58]])])
def detection(i=0):return dict(id=i,score=.9,box=[5.4,7.2,30.8,42.9])
class OccupancyPatchTests(unittest.TestCase):
    def compare(self,ds,ms,p):
        a=layout();before=copy.deepcopy(a);expected=_assign_occupancy_dense_reference((80,60),a,ds,ms,p);self.assertEqual(expected,assign_occupancy_patches((80,60),a,ds,ms,p));self.assertEqual(expected,assign_occupancy((80,60),a,ds,ms,p));self.assertEqual(a,before)
    def test_box_and_threshold_endpoints_match(self):
        for p in [None,[0,.25],[.25,.75],[.5,1]]:self.compare([detection()],[None],p)
    def test_full_instance_masks_match(self):
        m=np.zeros((60,80),dtype=bool);m[4:39,8:34]=True;self.compare([detection()],[m],[.2,.8])
    def test_ties_preserve_one_vehicle_one_slot(self):
        self.compare([dict(id=0,score=.8,box=[0,0,79,59]),dict(id=1,score=.8,box=[0,0,79,59])],[None,None],[.1,.1])
    def test_no_detection_never_proves_vacancy_without_classifier(self):
        self.compare([],[],None);self.assertTrue(all(o['state']=='uncertain' for o in assign_occupancy_patches((80,60),layout(),[],[],None)))
    def test_missing_lengths_duplicate_ids_and_bad_masks_refused(self):
        for ds,ms,p in [([detection()],[],None),([],[],[.1]),([detection(),detection()],[None,None],None),([detection()],[np.zeros((60,80))],None)]:
            with self.assertRaises(ValueError):assign_occupancy_patches((80,60),layout(),ds,ms,p)
    def test_patches_are_readonly_and_smaller_than_full_slot_stack(self):
        patches=prepare_slot_patches((80,60),layout());self.assertLess(sum(m.nbytes for _,m,_ in patches),2*80*60);self.assertTrue(all(not m.flags.writeable for _,m,_ in patches))
