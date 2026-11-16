"""Explicit frame order avoids fabricating physical time for image sequences."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.flow import GateCounter
from smart_parking.video import process_video

def counter(**kw):return GateCounter(image_size=[200,100],line=[[100,10],[100,90]],max_distance_fraction=.15,deadband_pixels=2,**kw)
def vehicle(x):return dict(label='car',score=.95,box=[x-4,46,x+4,54])

class FrameFlowTests(unittest.TestCase):
    def test_frame_events_never_claim_physical_seconds(self):
        c=counter(time_unit='frames',max_gap_frames=1);events=[]
        for frame,x in enumerate([120,115,105,95,90]):events+=c.update([vehicle(x)],frame)['events']
        self.assertEqual(len(events),1);self.assertIn('frame_index',events[0]);self.assertNotIn('video_time_seconds',events[0]);self.assertNotIn('max_gap_seconds',c.config)
        self.assertEqual(GateCounter(**c.config).config,c.config)
    def test_seconds_default_preserves_original_schema(self):
        c=counter();self.assertNotIn('time_unit',c.config)
        events=[]
        for i,x in enumerate([120,115,105,95,90]):events+=c.update([vehicle(x)],i*.1)['events']
        self.assertIn('video_time_seconds',events[0]);self.assertNotIn('frame_index',events[0])
    def test_missing_frames_reset_and_fractional_indices_are_rejected(self):
        c=counter(time_unit='frames',max_gap_frames=1);c.update([vehicle(120)],0);c.update([vehicle(115)],1)
        c.update([vehicle(90)],3);self.assertEqual(c.gap_resets,1);self.assertEqual(c.entries,0)
        for value in [3.1,True]:
            with self.assertRaisesRegex(ValueError,'integer frame'):c.update([],value)
        for kw in [dict(time_unit='frames'),dict(time_unit='frames',max_gap_frames=True),dict(time_unit='seconds',max_gap_frames=1)]:
            with self.assertRaises(ValueError):counter(**kw)
    def test_timestamp_video_rejects_frame_config_before_opening_source(self):
        c=counter(time_unit='frames',max_gap_frames=1)
        with self.assertRaisesRegex(ValueError,'seconds-based'):process_video('never-opened',None,None,'unused',flow_config=c.config)
