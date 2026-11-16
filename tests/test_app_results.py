"""Regression checks for stale displayed counts and mismatched export images.

State tests use small stubs, not desktop input or model result fabrication.
"""
import json,sys,tempfile,unittest
from unittest.mock import patch
from urllib.error import URLError
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.app import ParkingApp,occupancy_count_text
from smart_parking.exports import export_analysis
from smart_parking.live import get_live

class Value:
    def __init__(self,value=None):self.value=value
    def set(self,value):self.value=value

class ResultLifecycleTests(unittest.TestCase):
    def test_no_layout_does_not_display_zero_available_spaces(self):
        label=occupancy_count_text(dict(occupancy_evaluated=False,counts=None))
        self.assertIn('unavailable',label);self.assertNotIn('Available 0',label)
    def test_live_network_failure_explains_saved_snapshot_option(self):
        with patch('smart_parking.live.latest_snapshot',side_effect=FileNotFoundError),patch('smart_parking.live.urllib.request.urlopen',side_effect=URLError('DNS failure')):
            with self.assertRaisesRegex(ConnectionError,'Load saved snapshot'):
                get_live(refresh=True)

    def test_input_invalidation_clears_results_and_counts(self):
        state=SimpleNamespace(result={'counts':{'occupied':35}},analysis_image=object(),
            display_kind='analysis',layout={'slots':[{},{}]},counts=Value())
        ParkingApp.invalidate_analysis(state)
        self.assertIsNone(state.result);self.assertIsNone(state.analysis_image)
        self.assertEqual(state.display_kind,'input')
        self.assertEqual(state.counts.value,'Spaces 2     Occupied —     Available —     Uncertain —')

    def test_busy_input_change_is_rejected_before_loading(self):
        state=SimpleNamespace(busy=True)
        with self.assertRaisesRegex(ValueError,'current analysis'):
            ParkingApp.set_image(state,'this-file-should-never-be-opened.png')

    def test_canvas_edit_cannot_change_layout_during_worker(self):
        state=SimpleNamespace(busy=True,pending_polygon=[[1,1],[4,1],[4,4]])
        before=list(state.pending_polygon)
        ParkingApp.add_vertex(state,SimpleNamespace(x=2,y=2))
        ParkingApp.finish_polygon(state)
        self.assertEqual(state.pending_polygon,before)

    def test_semantic_preview_cannot_replace_saved_analysis_overlay(self):
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            if not Path(temporary).resolve().is_relative_to(root.resolve()):raise RuntimeError('Unexpected temp path')
            result={'counts':{'total':1,'occupied':1,'vacant':0,'uncertain':0}}
            output=export_analysis(temporary,result,Image.new('RGB',(8,8),'green'),
                preview_image=Image.new('RGB',(8,8),'purple'),preview_kind='experimental_semantic_mask')
            self.assertEqual(Image.open(output/'overlay.png').getpixel((0,0)),(0,128,0))
            self.assertEqual(Image.open(output/'display_preview.png').getpixel((0,0)),(128,0,128))
            self.assertEqual(json.loads((output/'analysis.json').read_text()),result)
            self.assertIn('occupancy JSON describes overlay.png only',json.loads((output/'export_metadata.json').read_text())['preview_note'])

    def test_export_without_analysis_creates_no_fake_result(self):
        with self.assertRaisesRegex(ValueError,'Run image analysis'):
            export_analysis('unused',None,None)

if __name__=='__main__':unittest.main()
