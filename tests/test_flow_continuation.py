"""Synthetic weak-observation rules; not real-camera accuracy evidence."""
import random,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.flow_continuation import ContinuationGateCounter


def vehicle(x, y=50, score=.95, label='car'):
    return dict(label=label,score=score,box=[x-4,y-4,x+4,y+4])


def counter():
    return ContinuationGateCounter(image_size=[200,100],line=[[100,10],[100,90]],
        time_unit='frames',max_gap_frames=1,max_distance_fraction=.15,deadband_pixels=2)


class ContinuationTests(unittest.TestCase):
    def test_weak_observation_cannot_start_track_but_can_continue_actual_score(self):
        c=counter();self.assertEqual(c.update([vehicle(120,score=.6)],0)['tracks'],[])
        first=c.update([vehicle(120)],1)['tracks'][0]['track_id']
        out=c.update([vehicle(115,score=.6)],2)
        self.assertEqual(out['tracks'][0]['track_id'],first)
        self.assertEqual(out['tracks'][0]['score'],.6)
        self.assertTrue(out['tracks'][0]['continuation_only'])
        self.assertEqual(out['weak_continuations'],1)

    def test_weak_crossing_erases_memory_and_does_not_count_on_return(self):
        c=counter();events=[];ids=[]
        for frame,(x,score) in enumerate([(120,.95),(115,.95),(95,.6),(90,.6),(85,.95),(80,.95)]):
            out=c.update([vehicle(x,score=score)],frame);events+=out['events'];ids.append(out['tracks'][0]['track_id'])
        self.assertEqual(len(set(ids)),1)
        self.assertEqual(events,[]);self.assertEqual((c.entries,c.exits),(0,0))

    def test_missing_or_long_gap_never_bridges_identity_or_crossing(self):
        for missing in [True,False]:
            c=counter();first=c.update([vehicle(120)],0)['tracks'][0]['track_id'];c.update([vehicle(115)],1)
            if missing:c.update([],2)
            self.assertEqual(c.update([vehicle(95,score=.6)],3)['tracks'],[])
            out=c.update([vehicle(90)],4)
            self.assertNotEqual(out['tracks'][0]['track_id'],first)
            self.assertEqual(out['events'],[])

    def test_ambiguous_weak_candidate_cannot_reuse_either_track(self):
        c=counter();c.update([vehicle(120,40),vehicle(120,60)],0)
        out=c.update([vehicle(115,50,score=.6)],1)
        self.assertEqual(out['tracks'],[]);self.assertEqual(out['events'],[])

    def test_high_association_is_protected_and_class_duplicates_are_not_births(self):
        c=counter();first=c.update([vehicle(120)],0)['tracks'][0]['track_id']
        out=c.update([vehicle(116,score=.9),vehicle(130,score=.6)],1)
        self.assertEqual(len(out['tracks']),1);self.assertEqual(out['tracks'][0]['track_id'],first)
        out=c.update([vehicle(112,score=.6),vehicle(112,score=.61,label='truck')],2)
        self.assertEqual(len(out['tracks']),1);self.assertEqual(out['tracks'][0]['track_id'],first)

    def test_weak_box_at_far_location_and_invalid_settings_do_not_create_identity(self):
        c=counter();c.update([vehicle(180)],0)
        self.assertEqual(c.update([vehicle(20,score=.6)],1)['tracks'],[])
        for value in [0,.7,.8,float('nan')]:
            with self.assertRaises(ValueError):
                ContinuationGateCounter(image_size=[200,100],line=[[100,10],[100,90]],continuation_confidence=value)

    def test_randomized_weak_only_updates_never_birth_identities_or_emit_counts(self):
        rng=random.Random(113)
        for case in range(500):
            c=counter()
            first=c.update([vehicle(rng.uniform(10,190),rng.uniform(10,90)) for _ in range(3)],0)
            initial={t['track_id'] for t in first['tracks']}
            for frame in range(1,6):
                observations=[vehicle(rng.uniform(10,190),rng.uniform(10,90),rng.uniform(.5,.699),rng.choice(['car','truck'])) for _ in range(4)]
                out=c.update(observations,frame)
                self.assertTrue({t['track_id'] for t in out['tracks']}<=initial)
                self.assertEqual(out['events'],[])
                self.assertEqual(out['counts'],dict(entries=0,exits=0))
            c.update([],6)
            self.assertEqual(c.update([vehicle(100,score=.6)],7)['tracks'],[])
