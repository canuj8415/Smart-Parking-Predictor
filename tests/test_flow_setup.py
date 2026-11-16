"""Synthetic file fixtures test setup binding and output integrity, not accuracy."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.flow_setup import video_preview,make_setup,validate_setup,run_configured_flow
from smart_parking.app import ParkingApp

class FlowSetupTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'fixture.avi'
        import cv2,numpy as np
        writer=cv2.VideoWriter(str(self.source),cv2.VideoWriter_fourcc(*'MJPG'),10,(64,48))
        self.assertTrue(writer.isOpened())
        for i in range(12):writer.write(np.full((48,64,3),i*10,dtype=np.uint8))
        writer.release();self.image,self.identity=video_preview(self.source)
        self.setup=make_setup(self.identity,[[2,24],[61,24]],'negative_to_positive')
        self.engine=SimpleNamespace(model_name='SYNTHETIC-TEST-STUB',weight_sha256=None,resolution=64)
        def analyze(image,layout,confidence):
            self.assertIsNone(layout)
            return dict(detections=[],counts=None,latency_seconds=0,occupancy_evaluated=False),image.copy()
        self.engine.analyze=analyze

    def test_saved_setup_rejects_same_dimensions_different_bytes_or_view(self):
        self.assertEqual(validate_setup(self.setup,self.identity),self.setup['gate'])
        for key,value in [('source_sha256','other'),('first_frame_rgb_sha256','other'),('image_size',[64,49])]:
            altered=dict(self.identity);altered[key]=value
            with self.assertRaisesRegex(ValueError,'different video'):validate_setup(self.setup,altered)
        for line,direction in [([[2,2],[2,2]],'negative_to_positive'),([[2,24],[65,24]],'negative_to_positive'),([[2,24],[61,24]],'')]:
            with self.assertRaises(ValueError):make_setup(self.identity,line,direction)

    def test_real_pipeline_exports_bounded_synthetic_frames_and_identity(self):
        folder=self.root/'outputs';seen=[]
        result=run_configured_flow(self.setup,folder,self.engine,max_frames=2,callback=lambda *v:seen.append(v))
        self.assertEqual(result['processed_frames'],2);self.assertEqual(len(seen),2)
        self.assertFalse(result['occupancy_evaluated']);self.assertTrue(result['flow_enabled'])
        evidence=json.loads((folder/'source_and_gate.json').read_text())
        self.assertTrue(evidence['source_verified_before']);self.assertTrue(evidence['source_verified_after'])
        self.assertFalse(evidence['accuracy_evaluated'])
        with self.assertRaisesRegex(ValueError,'empty results'):run_configured_flow(self.setup,folder,self.engine,max_frames=2)

    def test_changed_source_and_bad_limits_fail_before_result_folder(self):
        altered=copy.deepcopy(self.setup);altered['video']['source_sha256']='wrong'
        folder=self.root/'not-created'
        with self.assertRaisesRegex(ValueError,'different video'):run_configured_flow(altered,folder,self.engine,max_frames=1)
        self.assertFalse(folder.exists())
        for limit in (0,241,True,2.5):
            with self.assertRaisesRegex(ValueError,'between 1 and 240'):run_configured_flow(self.setup,folder,self.engine,max_frames=limit)

    def test_file_mutation_during_processing_is_retained_but_rejected(self):
        def corrupt(*args,**kwargs):
            self.source.write_bytes(self.source.read_bytes()+b'changed')
            return {'processed_frames':1}
        folder=self.root/'invalid'
        with patch('smart_parking.video.process_video',side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,'changed during processing'):run_configured_flow(self.setup,folder,self.engine,max_frames=1)
        self.assertFalse(json.loads((folder/'source_and_gate.json').read_text())['source_verified_after'])

    def test_editor_rejects_margin_clicks_duplicates_and_busy_input(self):
        state=SimpleNamespace(busy=False,flow_drawing=True,flow_image=self.image,
            flow_origin=(10,20),flow_scale=2,flow_points=[],show_flow_image=lambda:None)
        ParkingApp.add_flow_point(state,SimpleNamespace(x=0,y=0));self.assertEqual(state.flow_points,[])
        point=SimpleNamespace(x=14,y=28)
        ParkingApp.add_flow_point(state,point);ParkingApp.add_flow_point(state,point)
        self.assertEqual(state.flow_points,[[2,4]])
        state.busy=True;ParkingApp.add_flow_point(state,SimpleNamespace(x=40,y=60));self.assertEqual(len(state.flow_points),1)
        state.busy=False;ParkingApp.add_flow_point(state,SimpleNamespace(x=40,y=60))
        self.assertFalse(state.flow_drawing);self.assertEqual(state.flow_points,[[2,4],[15,20]])

    def test_entry_direction_must_be_chosen_and_polarity_matches_arrow(self):
        class Value:
            def __init__(self,value):self.value=value
            def get(self):return self.value
        state=SimpleNamespace(flow_identity=self.identity,flow_points=[[2,24],[61,24]],flow_direction=Value(''))
        with self.assertRaisesRegex(ValueError,'direction'):ParkingApp.current_flow_setup(state)
        for label,polarity in [('Along orange arrow','negative_to_positive'),('Against orange arrow','positive_to_negative')]:
            state.flow_direction=Value(label)
            self.assertEqual(ParkingApp.current_flow_setup(state)['gate']['entry_direction'],polarity)

    def test_cancellation_before_first_frame_is_not_a_zero_traffic_claim(self):
        folder=self.root/'cancelled'
        result=run_configured_flow(self.setup,folder,self.engine,max_frames=2,cancel=lambda:True)
        self.assertTrue(result['cancelled']);self.assertIsNone(result['flow_diagnostics'])
        self.assertEqual(json.loads((folder/'source_and_gate.json').read_text())['status'],'cancelled')

    def test_processing_error_keeps_explicit_failed_manifest(self):
        folder=self.root/'failed'
        with patch('smart_parking.video.process_video',side_effect=RuntimeError('fixture failure')):
            with self.assertRaisesRegex(RuntimeError,'fixture failure'):run_configured_flow(self.setup,folder,self.engine,max_frames=1)
        evidence=json.loads((folder/'source_and_gate.json').read_text())
        self.assertEqual(evidence['status'],'failed');self.assertEqual(evidence['error'],'fixture failure')

if __name__=='__main__':unittest.main()
