import json,tempfile,unittest
from pathlib import Path
from scripts.acquire_acpds_training import ROOT,verified_cached
from smart_parking.provenance import digest
class AcpdsCacheReceiptTests(unittest.TestCase):
    def setUp(self):
        folder=ROOT/'.cache/test_tmp';folder.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=folder);self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'image.bin';self.path.write_bytes(b'fixture');self.record=dict(source_id='SRC-DS-021',local_path=self.path.relative_to(ROOT).as_posix(),sha256=digest(self.path),role='train')
    def test_matching_single_receipt_is_reused(self):self.assertEqual(verified_cached(self.path,[self.record],'train'),self.record)
    def test_unreceipted_file_refused(self):
        with self.assertRaises(ValueError):verified_cached(self.path,[],'train')
    def test_changed_bytes_refused(self):
        self.path.write_bytes(b'changed')
        with self.assertRaises(ValueError):verified_cached(self.path,[self.record],'train')
    def test_wrong_role_or_source_refused(self):
        for r in [dict(self.record,role='valid'),dict(self.record,source_id='other')]:
            with self.assertRaises(ValueError):verified_cached(self.path,[r],'train')
    def test_ambiguous_receipts_refused(self):
        with self.assertRaises(ValueError):verified_cached(self.path,[self.record,self.record],'train')
