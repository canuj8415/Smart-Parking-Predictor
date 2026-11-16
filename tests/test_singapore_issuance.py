"""Synthetic timed feeds/checkpoints only; no real forecast/final claims."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.provenance import digest
from smart_parking.singapore_issuance import issue_forecasts, load_candidate, records
from smart_parking.singapore_trend import fit_trend
from test_singapore_trend import example


class SingaporeIssuanceTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1]/'outputs/test_fixtures'
        parent.mkdir(parents=True, exist_ok=True)
        self.parent = parent.resolve()
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name).resolve()
        self.now = datetime(2026, 1, 1, 1, 1, tzinfo=timezone.utc)
        self.write('runtime.py', 'synthetic runtime', raw=True)
        self.reservation = dict(source_id='SRC-LIVE-001', carparks_scope='ALL',
            created_at='2026-01-01T00:00:00+00:00', historical_cutoff='2026-01-01T00:00:00+00:00',
            final_origin_start='2026-01-01T01:00:00+00:00', final_origin_end='2026-01-01T02:00:00+00:00',
            final_target_end='2026-01-01T02:51:00+00:00')
        self.write('reservation.json', self.reservation)
        self.write('model.json', fit_trend([example()]))
        self.selection = dict(source_id='SRC-LIVE-001', development_gate_passed=True,
            reservation_sha256=digest(self.root/'reservation.json'), checkpoint='model.json',
            checkpoint_sha256=digest(self.root/'model.json'), frozen_at='2026-01-01T00:01:00+00:00')
        self.write('selection.json', self.selection)
        self.config = dict(source_id='SRC-LIVE-001', runtime_source_hashes={'runtime.py': digest(self.root/'runtime.py')},
            reservation='reservation.json', reservation_sha256=digest(self.root/'reservation.json'),
            selection='selection.json', selection_sha256=digest(self.root/'selection.json'), frozen_at='2026-01-01T00:02:00+00:00',
            acquisition_receipts='receipts.jsonl', batch_folder='batches', batch_receipt_folder='batch_receipts')
        self.write('config.json', self.config)
        self.receipts = [self.feed('previous', '2026-01-01T00:30:00+00:00', 40),
                         self.feed('current', '2026-01-01T01:00:00+00:00', 50)]
        self.save_receipts()

    def tearDown(self):
        assert self.root != self.parent and self.root.is_relative_to(self.parent)
        self.temp.cleanup()

    def write(self, path, value, raw=False):
        target = self.root/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if raw else json.dumps(value), encoding='utf-8')

    def feed(self, name, timestamp, available, capacity=100):
        path = 'data/raw/singapore_live/'+name+'.json'
        self.write(path, dict(items=[dict(timestamp=timestamp, carpark_data=[dict(carpark_number='SYNTHETIC',
            update_datetime=timestamp, carpark_info=[dict(lot_type='C', total_lots=str(capacity), lots_available=str(available))])])]))
        return dict(source_id='SRC-LIVE-001', local_path=path, sha256=digest(self.root/path), accessed_at=timestamp)

    def save_receipts(self):
        self.write('receipts.jsonl', ''.join(json.dumps(r)+'\n' for r in self.receipts), raw=True)

    def call(self):
        return issue_forecasts(self.root/'config.json', root=self.root, clock=lambda: self.now)

    def test_real_context_binding_immutable_commit_and_deduplicated_retry(self):
        self.assertEqual(self.call()['issued'], 1)
        receipt = json.loads(next((self.root/'batch_receipts').glob('*.receipt.json')).read_text())
        forecast = records(self.root/receipt['batch_path'])[0]
        self.assertEqual(forecast['predicted_available'], 55)
        self.assertEqual(forecast['persistence_available'], 50)
        self.assertEqual(forecast['previous_receipt']['sha256'], self.receipts[0]['sha256'])
        self.assertEqual(receipt['batch_sha256'], digest(self.root/receipt['batch_path']))
        self.assertFalse(any(k in forecast for k in ['target_available', 'actual_available', 'absolute_error_spaces']))
        self.assertEqual(self.call()['issued'], 0)
        self.assertEqual(len(list((self.root/'batch_receipts').glob('*.receipt.json'))), 1)

    def test_no_early_or_late_origins_and_no_stale_snapshot_backdating(self):
        for at, status in [('2026-01-01T00:59:00+00:00', 'not_started'),
                           ('2026-01-01T02:00:00+00:00', 'origin_period_closed'),
                           ('2026-01-01T01:05:00+00:00', 'no_fresh_receipt')]:
            self.now = datetime.fromisoformat(at)
            self.assertEqual(self.call()['status'], status)
        self.assertFalse((self.root/'batches').exists())

    def test_changed_checkpoint_selection_or_runtime_is_rejected(self):
        for path in ['model.json', 'selection.json', 'runtime.py']:
            original = (self.root/path).read_bytes()
            (self.root/path).write_bytes(b'changed-synthetic-input')
            with self.assertRaises(ValueError):
                load_candidate(self.root/'config.json', self.root)
            (self.root/path).write_bytes(original)

    def test_future_receipt_never_becomes_previous_context(self):
        self.receipts.append(self.feed('future', '2026-01-01T01:30:00+00:00', 99))
        self.save_receipts()
        self.assertEqual(self.call()['issued'], 1)
        forecast = records(next((self.root/'batches').glob('*.jsonl')))[0]
        self.assertEqual(forecast['origin_available'], 50)
        self.assertEqual(forecast['previous_available'], 40)

    def test_changed_capacity_nearest_context_is_not_skipped(self):
        self.receipts.insert(1, self.feed('changed', '2026-01-01T00:45:00+00:00', 30, capacity=60))
        self.save_receipts()
        report = self.call()
        self.assertEqual(report['issued'], 0)
        self.assertEqual(report['excluded']['previous_capacity_changed'], 1)

    def test_changed_raw_or_committed_batch_fails_closed(self):
        path = self.root/self.receipts[-1]['local_path']
        original = path.read_bytes(); path.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            self.call()
        path.write_bytes(original)
        self.call()
        next((self.root/'batches').glob('*.jsonl')).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.call()

    def test_delayed_writer_leaves_no_receipted_forecasts(self):
        times = iter([self.now, datetime(2026, 1, 1, 1, 4, tzinfo=timezone.utc)])
        with self.assertRaises(ValueError):
            issue_forecasts(self.root/'config.json', root=self.root, clock=lambda: next(times))
        self.assertFalse(list((self.root/'batch_receipts').glob('*.receipt.json')))
