"""Synthetic decoder/engine fixtures check plumbing, not traffic accuracy."""
import sys,tempfile,unittest,csv,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.video import process_video

class VideoSettingTests(unittest.TestCase):
    def _fixture(self,layout):
        class Capture:
            def __init__(self):self.reads=0;self.released=False
            def isOpened(self):return True
            def get(self,key):return 5 if key==0 else 200
            def read(self):
                self.reads+=1
                return (True,np.zeros((4,4,3),dtype=np.uint8)) if self.reads==1 else (False,None)
            def release(self):self.released=True
        class Engine:
            def analyze(self,image,layout,confidence):
                self.confidence=confidence
                return dict(counts=dict(total=1,occupied=0,vacant=0,uncertain=1),latency_seconds=0,slots=[]),image
        capture=Capture();engine=Engine();cv2=SimpleNamespace(VideoCapture=lambda source:capture,CAP_PROP_FPS=0,CAP_PROP_POS_MSEC=1,COLOR_BGR2RGB=2,cvtColor=lambda image,kind:image)
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temporary,patch.dict(sys.modules,{'cv2':cv2}):
            result=process_video('synthetic-fixture',engine,layout,temporary,every_n=1,confidence=.9)
            with (Path(temporary)/'observations.csv').open(newline='') as stream:records=list(csv.DictReader(stream))
            log=json.loads((Path(temporary)/'detections.jsonl').read_text().strip())
        return result,engine,capture,records,log
    def test_threshold_is_forwarded_and_natural_end_counts_only_read_frames(self):
        layout=dict(camera_id='fixture',image_size=[4,4],slots=[dict(id='A',polygon=[[0,0],[3,0],[3,3],[0,3]])])
        result,engine,capture,_,_=self._fixture(layout)
        self.assertEqual(engine.confidence,.9);self.assertEqual(result['detection_threshold'],.9)
        self.assertEqual(result['decoded_frames'],1);self.assertEqual(result['processed_frames'],1);self.assertTrue(capture.released)
    def test_detection_only_video_does_not_export_fabricated_occupancy(self):
        result,_,_,records,log=self._fixture(None)
        self.assertFalse(result['occupancy_evaluated']);self.assertFalse(log['occupancy_evaluated'])
        self.assertNotIn('occupied',records[0]);self.assertNotIn('vacant',records[0]);self.assertEqual(result['events'],[])
    def test_invalid_threshold_rejected_before_decoder_creation(self):
        for value in [0,1,-.1,1.1,float('nan')]:
            with self.assertRaisesRegex(ValueError,'threshold'):
                process_video('unused',None,None,'unused',confidence=value)
    def test_time_sampling_uses_timestamps_instead_of_unreliable_fps(self):
        class Capture:
            def __init__(self):self.reads=0;self.released=False
            def isOpened(self):return True
            def get(self,key):return 1000. if key==0 else (self.reads-1)*1000.
            def read(self):
                self.reads+=1
                return (True,np.zeros((4,4,3),dtype=np.uint8)) if self.reads<=4 else (False,None)
            def release(self):self.released=True
        class Engine:
            def analyze(self,image,layout,confidence):return dict(counts=None,detections=[],slots=[],latency_seconds=0),image
        capture=Capture();cv2=SimpleNamespace(VideoCapture=lambda source:capture,CAP_PROP_FPS=0,CAP_PROP_POS_MSEC=1,COLOR_BGR2RGB=2,cvtColor=lambda image,kind:image)
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temporary,patch.dict(sys.modules,{'cv2':cv2}):
            result=process_video('synthetic-fixture',Engine(),None,temporary,every_seconds=2)
            lines=[json.loads(line) for line in (Path(temporary)/'detections.jsonl').read_text().splitlines()]
        self.assertEqual([r['video_time_seconds'] for r in lines],[0,2]);self.assertEqual(result['decoded_frames'],4)
        self.assertEqual(result['observed_timestamp_fps'],1);self.assertFalse(result['fps_metadata_consistent']);self.assertTrue(capture.released)

    def test_configured_flow_exports_consistent_counts_without_occupancy(self):
        positions=[120,115,105,95,90]
        class Capture:
            def __init__(self):self.reads=0
            def isOpened(self):return True
            def get(self,key):return 10. if key==0 else (self.reads-1)*100.
            def read(self):
                self.reads+=1
                return (True,np.zeros((100,200,3),dtype=np.uint8)) if self.reads<=5 else (False,None)
            def release(self):pass
        class Engine:
            def __init__(self):self.index=0
            def analyze(self,image,layout,confidence):
                x=positions[self.index];self.index+=1
                return dict(detections=[dict(label='car',score=.95,box=[x-4,46,x+4,54])],slots=[],counts=None,latency_seconds=0),image
        capture=Capture();cv2=SimpleNamespace(VideoCapture=lambda source:capture,CAP_PROP_FPS=0,CAP_PROP_POS_MSEC=1,COLOR_BGR2RGB=2,cvtColor=lambda image,kind:image)
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        config=dict(image_size=[200,100],line=[[100,10],[100,90]],max_distance_fraction=.15,deadband_pixels=2)
        with tempfile.TemporaryDirectory(dir=root) as temporary,patch.dict(sys.modules,{'cv2':cv2}):
            result=process_video('synthetic-fixture',Engine(),None,temporary,every_n=1,flow_config=config)
            with (Path(temporary)/'observations.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
            logs=[json.loads(line) for line in (Path(temporary)/'detections.jsonl').read_text().splitlines()]
        self.assertTrue(result['flow_enabled']);self.assertEqual(result['flow_diagnostics']['counts'],dict(entries=1,exits=0))
        self.assertEqual(rows[-1]['entries'],'1');self.assertNotIn('occupied',rows[-1])
        self.assertEqual([e for row in logs for e in row['result']['flow']['events']],result['flow_events'])
        self.assertEqual(len(result['flow_events']),1)
if __name__=='__main__':unittest.main()
