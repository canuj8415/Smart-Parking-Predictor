"""Synthetic metadata/claim fixtures;not real CNR images or model accuracy."""
import csv,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.cnrpark_metadata import COLLECTION,canonical_row,global_date_split
from smart_parking.cnrpark_holdouts import assert_closed,evaluate_once
from smart_parking.provenance import digest
def dump(path,value):path.write_text(json.dumps(value),encoding='utf-8')
class CNRMetadataTests(unittest.TestCase):
    def row(self):return dict(camera='01',year='2015',month='11',day='12',hour='7',minute='9',slot_id='184',weather='S',datetime='2015-11-12_07.09',image_url='CNR-EXT/PATCHES/SUNNY/2015-11-12/camera1/S_2015-11-12_07.09_C01_184.jpg',occupancy='not-read')
    def test_calendar_path_and_targets_remain_separate(self):
        value=canonical_row(self.row(),2);self.assertEqual(value['capture_date'],'2015-11-12');self.assertNotIn('occupancy',value)
        for change in [dict(image_url='../outside.jpg'),dict(day='31'),dict(camera='02'),dict(datetime='2015-11-13_07.09')]:
            with self.assertRaises(ValueError):canonical_row(dict(self.row(),**change),2)
    def test_all_cameras_share_one_global_date_partition(self):
        rows=[dict(collection=COLLECTION,capture_date=f'2015-11-{i:02}',camera_id=c) for i in range(1,21) for c in ['01','02','09']]
        result,mapping=global_date_split(rows)
        for day in mapping:self.assertEqual(len({r['split'] for r in result if r['capture_date']==day}),1)
        self.assertEqual([mapping[f'2015-11-{i:02}'] for i in [1,13,17]],['train','validation','reserved_final'])
class CNRClaimTests(unittest.TestCase):
    def setUp(self):
        self.fixture_root=(Path(__file__).resolve().parents[1]/'outputs/test_fixtures').resolve();self.fixture_root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=self.fixture_root);self.root=Path(self.temp.name).resolve();self.claims=self.root/'claims'
        assert self.root.is_relative_to(self.fixture_root)
        for name in ['metadata.csv','archive.zip','model.pt']:(self.root/name).write_bytes(b'synthetic-fixture')
        parent=self.root/'parent.csv'
        with parent.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['split','capture_date','collection']);writer.writeheader();writer.writerow(dict(split='reserved_final',capture_date='2016-02-12',collection=COLLECTION))
        self.res=self.root/'reservation.json';value=dict(collection=COLLECTION,reserved_dates=['2016-02-12'],reserved_rows=1,parent_manifest='parent.csv',source_metadata='metadata.csv',source_archive='archive.zip')
        for key in ['parent_manifest','source_metadata','source_archive']:value[key+'_sha256']=digest(self.root/value[key])
        dump(self.res,value);self.protocol=self.root/'protocol.json';self.choice=self.root/'choice.json';self.weight=self.root/'model.pt';self.freeze(True)
    def tearDown(self):
        assert self.root.resolve().is_relative_to(self.fixture_root) and self.root.resolve()!=self.fixture_root
        self.temp.cleanup()
    def freeze(self,permission):
        common=dict(reservation_sha256=digest(self.res),checkpoint_sha256=digest(self.weight));dump(self.protocol,dict(common,image_analysis_authorized=permission))
        dump(self.choice,dict(common,protocol_sha256=digest(self.protocol),validation_gate_passed=True))
    def evaluate(self,callback):return evaluate_once(self.res,self.choice,self.protocol,self.weight,'SYNTHETIC-TEST',callback,root=self.root,receipts=self.claims,expected_reservation_sha256=digest(self.res),expected_protocol_sha256=digest(self.protocol))
    def test_unqualified_image_rights_block_before_callback(self):
        self.freeze(False)
        with self.assertRaises(ValueError):self.evaluate(lambda _:self.fail('callback ran'))
        self.assertFalse(self.claims.exists())
    def test_failed_callback_consumes_dates_even_after_source_alias(self):
        def fail(_):raise RuntimeError('Synthetic callback failure')
        with self.assertRaises(RuntimeError):self.evaluate(fail)
        value=json.loads(self.res.read_text());value['source_id']='RENAMED';dump(self.res,value)
        with self.assertRaises(ValueError):assert_closed(self.res,self.root,self.claims)
    def test_parent_source_change_rejects_before_callback(self):
        (self.root/'metadata.csv').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.evaluate(lambda _:self.fail('callback ran'))
    def test_success_claim_is_durable_and_cannot_be_replayed(self):
        self.assertEqual(self.evaluate(lambda _:7),7)
        with self.assertRaises(ValueError):self.evaluate(lambda _:self.fail('replayed'))
    def test_partial_parent_membership_is_rejected(self):
        value=json.loads(self.res.read_text());value['reserved_rows']=2;dump(self.res,value);self.freeze(True)
        with self.assertRaises(ValueError):self.evaluate(lambda _:self.fail('callback ran'))
if __name__=='__main__':unittest.main()
