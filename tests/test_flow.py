"""Synthetic counting-rule fixtures, never reported as camera accuracy."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.flow import GateCounter

def vehicle(x,y=50,label='car',score=.95):
    return dict(label=label,score=score,box=[x-4,y-4,x+4,y+4])

def counter(**kwargs):
    return GateCounter(image_size=[200,100],line=[[100,10],[100,90]],
                       max_distance_fraction=.15,deadband_pixels=2,**kwargs)

class FlowTests(unittest.TestCase):
    def sequence(self,c,positions,start=0,step=.1,y=50):
        events=[]
        for i,x in enumerate(positions):events+=c.update([vehicle(x,y)],start+i*step)['events']
        return events
    def test_entry_exit_and_no_stationary_recounts(self):
        c=counter();events=self.sequence(c,[120,115,105,99,95,90,85,85,90,98,105,110,115])
        # Directed downward gate: positive is left; right-to-left enters.
        self.assertEqual([e['event_type'] for e in events],['entry','exit'])
        self.assertEqual((c.entries,c.exits),(1,1))
    def test_initial_observation_never_counts_and_jitter_is_ignored(self):
        c=counter();self.assertEqual(self.sequence(c,[101,99,102,98,101,99]),[])
        self.assertEqual((c.entries,c.exits),(0,0))
    def test_infinite_line_extension_is_not_a_gate(self):
        c=counter();self.assertEqual(self.sequence(c,[120,115,105,95,90],y=5),[])
    def test_sampling_gap_cannot_imply_crossing(self):
        c=counter();self.sequence(c,[120,115]);self.sequence(c,[90,85],start=2)
        self.assertEqual(c.entries,0);self.assertEqual(c.gap_resets,1)
    def test_missing_detection_drops_crossing_memory(self):
        c=counter();self.sequence(c,[120,115]);c.update([], .2)
        self.assertEqual(self.sequence(c,[90,85],start=.3),[])
    def test_class_duplicate_suppression(self):
        c=counter();out=c.update([vehicle(120),vehicle(120,label='truck',score=.9)],0)
        self.assertEqual(len(out['tracks']),1);self.assertEqual(out['discarded_duplicates'],1)
    def test_ambiguous_match_does_not_reuse_identity(self):
        c=counter();first=c.update([vehicle(115,40),vehicle(115,60)],0)
        result=c.update([vehicle(105,50)],.1)
        self.assertNotIn(result['tracks'][0]['track_id'],[x['track_id'] for x in first['tracks']])
        self.assertGreater(result['ambiguous_matches'],0);self.assertEqual(result['events'],[])
    def test_multiple_distinct_vehicles_and_reversed_entry_mapping(self):
        c=counter(entry_direction='positive_to_negative');events=[]
        for i,x in enumerate([120,115,105,95,90]):
            events+=c.update([vehicle(x,30),vehicle(x,70)],i*.1)['events']
        self.assertEqual([x['event_type'] for x in events],['exit','exit'])
        self.assertEqual(len({x['track_id'] for x in events}),2)
    def test_bad_time_view_config_and_boxes_fail(self):
        for kwargs in [dict(max_gap_seconds=0),dict(ambiguity_ratio=1),dict(stable_observations=1),dict(confidence=float('nan'))]:
            with self.assertRaises(ValueError):counter(**kwargs)
        c=counter();c.update([vehicle(120)],0)
        for t in [0,-1,float('nan')]:
            with self.assertRaises(ValueError):c.update([],t)
        with self.assertRaises(ValueError):c.update([],1,image_size=[100,100])
        with self.assertRaises(ValueError):c.update([vehicle(201)],1)
    def test_low_confidence_and_nonvehicle_ignored(self):
        out=counter().update([vehicle(120,score=.6),vehicle(120,label='person')],0)
        self.assertEqual(out['tracks'],[])

if __name__=='__main__':unittest.main()
