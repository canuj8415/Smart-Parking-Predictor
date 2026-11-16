"""Source identity conflicts cannot silently suppress or misattribute a dataset."""
import csv,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.source_catalog import register_source,require_source_identity

class SourceCatalogTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root);self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'sources.csv'
        with self.path.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['source_id','resource','source_url']);w.writeheader();w.writerow(dict(source_id='A',resource='Original',source_url='https://example.test/a'))
    def test_conflicting_id_is_rejected_without_modifying_original(self):
        before=self.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'different resource'):register_source(self.path,dict(source_id='A',resource='Other',source_url='https://example.test/b'))
        self.assertEqual(self.path.read_bytes(),before)
    def test_identical_registration_is_idempotent_and_new_unicode_source_appends(self):
        record=dict(source_id='A',resource='Original',source_url='https://example.test/a');before=self.path.read_bytes()
        self.assertFalse(register_source(self.path,record));self.assertEqual(self.path.read_bytes(),before)
        self.assertTrue(register_source(self.path,dict(source_id='B',resource='Échantillon',source_url='https://example.test/b')))
        with self.path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        self.assertEqual(rows[-1]['resource'],'Échantillon')
    def test_acquisition_requires_pre_registered_correct_identity(self):
        self.assertEqual(require_source_identity(self.path,'A','Original','https://example.test/a')['source_id'],'A')
        for ident,name,url in [('A','Wrong','https://example.test/a'),('MISSING','New','https://example.test/new')]:
            with self.assertRaisesRegex(ValueError,'before acquisition'):require_source_identity(self.path,ident,name,url)
