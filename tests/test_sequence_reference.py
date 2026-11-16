"""Synthetic labelled-ID paths test reference geometry and partial-label scope."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.flow import GateCounter
from smart_parking.sequence_reference import reference_crossings,match_reference_events,box_iou

class SequenceReferenceTests(unittest.TestCase):
    def config(self):return GateCounter(image_size=[200,100],line=[[100,10],[100,90]],time_unit='frames',max_gap_frames=1,deadband_pixels=2).config
    def rows(self):return [dict(frame_index=i,objects=[dict(object_id=1,box=[x-4,46,x+4,54])]) for i,x in enumerate([120,115,105,95,90])]
    def test_publisher_identity_crossing_does_not_depend_on_association_distance(self):
        rows=self.rows();events=reference_crossings(rows,self.config());self.assertEqual(len(events),1);self.assertEqual(events[0]['frame_index'],4)
        rows[2]['objects']=[];self.assertEqual(reference_crossings(rows,self.config()),[])
    def test_partial_reference_never_invents_precision_or_empty_perfection(self):
        self.assertIsNone(match_reference_events([],[],{})['annotated_event_recall'])
        ref=[dict(object_id=1,frame_index=4,event_type='entry')];pred=[dict(track_id=7,frame_index=5,event_type='entry'),dict(track_id=8,frame_index=5,event_type='entry')]
        r=match_reference_events(ref,pred,{(5,7):1});self.assertEqual(r['recovered_events'],1);self.assertEqual(r['unmatched_predicted_events'],1);self.assertFalse(r['precision_evaluable'])
    def test_box_overlap(self):
        self.assertEqual(box_iou([0,0,10,10],[0,0,10,10]),1)
        self.assertEqual(box_iou([0,0,10,10],[11,0,20,10]),0)
