"""Synthetic integration of reference geometry with the candidate config."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.flow import GateCounter
from smart_parking.flow_continuation import ContinuationGateCounter
from smart_parking.sequence_evaluation import evaluate_cached_sequence


class SequenceEvaluationTests(unittest.TestCase):
    def test_candidate_identity_options_do_not_change_reference_geometry(self):
        config=GateCounter(image_size=[200,100],line=[[100,10],[100,90]],time_unit='frames',
            max_gap_frames=1,max_distance_fraction=.15,deadband_pixels=2).config
        records=[]
        for i,x in enumerate([120,115,105,95,90]):
            box=[x-4,46,x+4,54]
            records.append(dict(frame_index=i,result=dict(detections=[dict(label='car',score=.95,box=box)]),
                                reference_objects=[dict(object_id=1,box=box)]))
        baseline,_=evaluate_cached_sequence(records,[200,100],config,GateCounter,scored_from=0)
        candidate,_=evaluate_cached_sequence(records,[200,100],dict(config,continuation_confidence=.5),ContinuationGateCounter,scored_from=0)
        self.assertEqual(candidate['reference_events'],baseline['reference_events'])
        self.assertEqual(candidate['metrics'],baseline['metrics'])
        self.assertEqual(candidate['metrics']['recovered_events'],1)
