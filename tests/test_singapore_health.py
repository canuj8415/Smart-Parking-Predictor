"""Synthetic metadata/batch fixtures; no real future outcomes or claims."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import test_singapore_issuance as fixtures
from smart_parking.provenance import digest
from smart_parking.singapore_health import check_issuance


class SingaporeHealthTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.SingaporeIssuanceTests(); self.fixture.setUp()
        self.root = self.fixture.root; self.as_of = '2026-01-01T01:02:00+00:00'

    def tearDown(self):
        self.fixture.tearDown()

    def issue(self):
        self.fixture.call()

    def call(self):
        return check_issuance(self.root/'config.json', root=self.root, as_of=self.as_of)

    def revise_batch(self, change):
        path = next((self.root/'batches').glob('*.jsonl')); row = json.loads(path.read_text())
        change(row); self.fixture.write(path, json.dumps(row)+'\n', raw=True)
        receipt_path = next((self.root/'batch_receipts').glob('*.receipt.json'))
        receipt = json.loads(receipt_path.read_text()); receipt['batch_sha256'] = digest(path)
        self.fixture.write(receipt_path, receipt)

    def test_positive_check_never_decodes_raw_json_or_matches_targets(self):
        self.issue(); original = Path.read_text
        def protected(path, *args, **kwargs):
            if path.resolve().is_relative_to((self.root/'data/raw').resolve()):
                raise AssertionError('Raw JSON must never be decoded for health checks')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', protected), patch('smart_parking.singapore_final._score_targets', side_effect=AssertionError('No target scoring')):
            result = self.call()
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['forecasts_logged'], 1)
        self.assertEqual(result['raw_files_hashed_once'], 2)
        self.assertFalse(result['performance_evaluated'])
        self.assertFalse(result['raw_semantic_context_verified'])
        self.assertFalse((self.root/'claims').exists())

    def test_empty_metadata_is_not_fabricated_successful_accuracy(self):
        result = self.call()
        self.assertEqual(result['status'], 'no_eligible_forecasts_yet')
        self.assertEqual(result['forecasts_logged'], 0)
        self.assertFalse(result['target_json_decoded'])
        self.assertNotIn('mae_spaces', result)

    def test_changed_batch_and_raw_bytes_are_rejected(self):
        self.issue(); path = next((self.root/'batches').glob('*.jsonl'))
        before = path.read_bytes(); path.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.call()
        path.write_bytes(before)
        (self.root/self.fixture.receipts[0]['local_path']).write_bytes(b'changed')
        with self.assertRaises(ValueError): self.call()

    def test_unreceipted_partial_batch_is_attention_and_not_counted(self):
        self.issue(); (self.root/'batches/partial.jsonl').write_text('unfinished synthetic fixture')
        result = self.call()
        self.assertEqual(result['status'], 'attention_unreceipted_batches')
        self.assertEqual(result['forecasts_logged'], 1)
        self.assertEqual(result['unreceipted_batches'], ['batches/partial.jsonl'])

    def test_outcome_fields_and_wrong_predictions_are_rejected(self):
        self.issue()
        path = next((self.root/'batches').glob('*.jsonl')); before = path.read_bytes()
        self.revise_batch(lambda row: row.update(actual_available=99))
        with self.assertRaises(ValueError): self.call()
        path.write_bytes(before)
        self.revise_batch(lambda row: row.update(predicted_available=99))
        with self.assertRaises(ValueError): self.call()

    def test_future_commit_and_changed_target_window_are_rejected(self):
        self.issue(); path = next((self.root/'batch_receipts').glob('*.receipt.json'))
        saved = json.loads(path.read_text()); changed = dict(saved, finalized_at='2026-01-01T01:03:00+00:00')
        self.fixture.write(path, changed)
        with self.assertRaises(ValueError): self.call()
        self.fixture.write(path, saved)
        self.revise_batch(lambda row: row.update(latest_target='2026-01-01T03:00:00+00:00'))
        with self.assertRaises(ValueError): self.call()

    def test_duplicate_ids_rejected_and_raw_hashing_cached_across_rows(self):
        self.issue(); batch_path = next((self.root/'batches').glob('*.jsonl')); row = json.loads(batch_path.read_text())
        self.fixture.write(batch_path, json.dumps(row)+'\n'+json.dumps(row)+'\n', raw=True)
        receipt_path = next((self.root/'batch_receipts').glob('*.receipt.json'))
        receipt = json.loads(receipt_path.read_text()); receipt.update(forecasts=2, batch_sha256=digest(batch_path))
        self.fixture.write(receipt_path, receipt)
        calls = []
        def recorded(path):
            calls.append(Path(path)); return digest(path)
        with patch('smart_parking.singapore_health.digest', side_effect=recorded):
            with self.assertRaises(ValueError): self.call()
        raw_calls = [p for p in calls if p.is_relative_to(self.root/'data/raw')]
        self.assertEqual(len(raw_calls), 2)
