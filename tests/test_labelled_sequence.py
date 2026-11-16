"""Synthetic mask/image adapter fixtures before the real final loader is used."""
import hashlib,sys,tempfile,unittest
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.labelled_sequence import infer_labelled_frame


class FakeEngine:
    def __init__(self):self.calls=0
    def analyze(self,image,layout,confidence):
        assert image.mode=='RGB' and layout is None and confidence==.5
        self.calls+=1
        return dict(detections=[]),None


class LabelledSequenceTests(unittest.TestCase):
    def test_selected_object_bbox_missing_object_and_corruption_block(self):
        base=Path(__file__).resolve().parents[1]/'.cache/test_tmp';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temporary:
            root=Path(temporary);Image.new('RGB',(30,20)).save(root/'image.png')
            mask=np.zeros((20,30),dtype='uint8');mask[2:7,3:9]=1;mask[10:18,12:20]=2
            Image.fromarray(mask).save(root/'mask.png')
            row=dict(frame_index=0,image='image.png',annotation='mask.png',image_size=[30,20])
            for key in ['image','annotation']:row[key+'_sha256']=hashlib.sha256((root/row[key]).read_bytes()).hexdigest()
            engine=FakeEngine();record=infer_labelled_frame(row,root,engine)
            self.assertEqual(record['reference_objects'],[dict(object_id=1,box=[3,2,9,7])])
            mask[:]=0;Image.fromarray(mask).save(root/'mask.png')
            row['annotation_sha256']=hashlib.sha256((root/'mask.png').read_bytes()).hexdigest()
            self.assertEqual(infer_labelled_frame(row,root,engine)['reference_objects'],[])
            (root/'image.png').write_bytes(b'corrupt original')
            with self.assertRaisesRegex(ValueError,'checksum changed'):infer_labelled_frame(row,root,engine)
            self.assertEqual(engine.calls,2)
