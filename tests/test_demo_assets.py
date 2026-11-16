"""Synthetic asset-pointer and training/final isolation fixtures."""
import csv,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.demo_assets import load_demo_assets,select_training_demo
from smart_parking.provenance import digest


class DemoAssetTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[1]/'.cache/test_tmp';base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'data/manifests').mkdir(parents=True);(self.root/'configs').mkdir()
        (self.root/'training.jpg').write_bytes(b'synthetic bytes, never decoded')
        (self.root/'layout.json').write_text(json.dumps(dict(slots=[dict(id='fixture',polygon=[[0,0],[4,0],[4,4]])])))
        self.row=dict(split='train',camera_id='fixture',date='2020-01-01',image='training.jpg',layout_path='layout.json',image_sha256=digest(self.root/'training.jpg'))
        with (self.root/'data/manifests/pklot_frames.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(self.row));w.writeheader();w.writerow(dict(self.row,split='test',image='unopened-final.jpg'));w.writerow(self.row)

    def test_missing_final_file_is_never_opened_by_demo_selection(self):
        record,image,layout=load_demo_assets(self.root)
        self.assertEqual(record['split'],'train');self.assertEqual(image.name,'training.jpg')
        self.assertFalse((self.root/'unopened-final.jpg').exists())

    def test_configured_demo_is_hash_bound_and_rejects_corruption(self):
        record=select_training_demo(self.root)
        (self.root/'configs/demo_sample.json').write_text(json.dumps(record))
        self.assertEqual(load_demo_assets(self.root)[0],record)
        (self.root/'layout.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'checksum changed'):load_demo_assets(self.root)

    def test_final_role_and_escaping_config_are_rejected(self):
        record=select_training_demo(self.root);path=self.root/'configs/demo_sample.json'
        path.write_text(json.dumps(dict(record,split='test')))
        with self.assertRaisesRegex(ValueError,'training example'):load_demo_assets(self.root)
        path.write_text(json.dumps(dict(record,image='../outside.jpg')))
        with self.assertRaisesRegex(ValueError,'outside project'):load_demo_assets(self.root)
