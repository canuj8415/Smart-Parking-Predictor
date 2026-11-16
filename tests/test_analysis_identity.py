"""Synthetic images and a fake detector check provenance, not model accuracy."""
import copy,sys,unittest
from pathlib import Path
from PIL import Image
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.analysis_identity import image_identity,layout_identity
from smart_parking.vision import VisionEngine

def layout():return dict(camera_id='fixture',image_size=[8,8],slots=[dict(id='A',polygon=[[1,1],[6,1],[6,6],[1,6]],ground_truth_occupied=1)])

class AnalysisIdentityTests(unittest.TestCase):
    def test_same_processed_pixels_match_but_pixel_and_shape_changes_do_not(self):
        a=Image.new('RGB',(2,4),'red');b=Image.new('RGB',(4,2),'red')
        self.assertEqual(image_identity(a),image_identity(a.convert('RGBA')))
        self.assertNotEqual(image_identity(a)['sha256'],image_identity(b)['sha256'])
        b=a.copy();b.putpixel((0,0),(0,0,0));self.assertNotEqual(image_identity(a)['sha256'],image_identity(b)['sha256'])
    def test_ground_truth_labels_and_key_order_do_not_change_geometry_fingerprint(self):
        a=layout();b=copy.deepcopy(a);b['origin']='description only';b['slots'][0]['ground_truth_occupied']=0
        self.assertEqual(layout_identity(a),layout_identity(b));self.assertIsNone(layout_identity(None))
    def test_slot_order_and_coordinate_changes_are_distinct(self):
        a=layout();a['slots'].append(dict(id='B',polygon=[[0,0],[2,0],[2,2],[0,2]]));b=copy.deepcopy(a);b['slots'].reverse()
        self.assertNotEqual(layout_identity(a)['sha256'],layout_identity(b)['sha256'])
        b=copy.deepcopy(a);b['slots'][0]['polygon'][0]=[0,0]
        self.assertNotEqual(layout_identity(a)['sha256'],layout_identity(b)['sha256'])
    def test_result_uses_owned_geometry_snapshot_even_if_caller_mutates_layout(self):
        original=layout();expected=layout_identity(original);engine=VisionEngine.__new__(VisionEngine)
        def predict(images):
            original['slots'][0]['polygon'][0]=[0,0]
            return [dict(boxes=torch.tensor([[1.,1.,6.,6.]]),labels=torch.tensor([3]),scores=torch.tensor([.99]))]
        engine.model=predict;engine.model_name='software-fixture';engine.weight_sha256='not-weights';engine.classifier=None
        image=Image.new('RGB',(8,8));result,_=engine.analyze(image,original)
        self.assertEqual(result['layout_identity'],expected);self.assertEqual(result['input_image'],image_identity(image))
        self.assertEqual(result['slots'][0]['slot_overlap'],1.);self.assertNotEqual(layout_identity(original),expected)

if __name__=='__main__':unittest.main()
