import copy,json,tempfile,unittest
from pathlib import Path
from smart_parking.demo_snapshot import select_snapshot
from smart_parking.provenance import digest


class DemoSnapshotTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[1]/'outputs/test_fixtures';base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base);self.root=Path(self.temp.name).resolve();assert self.root.is_relative_to(base.resolve());self.addCleanup(self.temp.cleanup)
        self.relative='data/raw/singapore_live/synthetic.json';p=self.root/self.relative;p.parent.mkdir(parents=True);p.write_bytes(b'opaque synthetic body,not valid feed JSON')
        h=digest(p);self.manifest=dict(files=[dict(path=self.relative,sha256=h,source_id='SRC-LIVE-001')]);self.scope=dict(cached_live_snapshot=self.relative,cached_live_sha256=h,cached_live_provider_timestamp='2026-01-01T00:00:00+00:00')
        self.reservation=dict(final_origin_start='2026-01-02T00:00:00+00:00');self.receipts=[dict(source_id='SRC-LIVE-001',local_path=self.relative,sha256=h,provider_timestamp=self.scope['cached_live_provider_timestamp'],accessed_at='2026-01-01T00:01:00+00:00')]

    def select(self):return select_snapshot(self.root,self.manifest,self.scope,self.reservation,self.receipts)

    def test_old_snapshot_selected_without_body_decoding(self):
        result=self.select();self.assertEqual(result['path'],self.relative);self.assertFalse(result['raw_body_decoded_during_selection'])

    def test_late_receipt_or_future_provider_cannot_be_packaged(self):
        for key,value in [('accessed_at','2026-01-02T00:00:00+00:00'),('provider_timestamp','2026-01-02T00:01:00+00:00')]:
            original=self.receipts[0][key];self.receipts[0][key]=value
            with self.assertRaises(ValueError):self.select()
            self.receipts[0][key]=original

    def test_changed_snapshot_or_scope_rejected(self):
        (self.root/self.relative).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.select()

    def test_ambiguous_receipts_or_multiple_snapshots_rejected(self):
        self.receipts.append(copy.deepcopy(self.receipts[0]))
        with self.assertRaises(ValueError):self.select()
        self.receipts.pop();self.manifest['files'].append(copy.deepcopy(self.manifest['files'][0]))
        with self.assertRaises(ValueError):self.select()

    def test_traversal_and_naive_timestamps_rejected(self):
        self.manifest['files'][0]['path']='data/raw/singapore_live/../elsewhere.json'
        with self.assertRaises(ValueError):self.select()
        self.manifest['files'][0]['path']=self.relative;self.receipts[0]['accessed_at']='2026-01-01T00:01:00'
        with self.assertRaises(ValueError):self.select()
