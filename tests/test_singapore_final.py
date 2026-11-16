"""Synthetic scoring intervals only; no real reserved targets or final claims."""
import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import test_singapore_issuance as fixtures
from smart_parking.provenance import digest
from smart_parking.singapore_final import evaluate_study, _claim_path, paired_metrics
from smart_parking.singapore_issuance import _observations


class SingaporeFinalTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.SingaporeIssuanceTests()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.fixture.reservation['claim_registry'] = 'claims'
        self.fixture.write('reservation.json', self.fixture.reservation)
        self.fixture.selection['reservation_sha256'] = digest(self.root/'reservation.json')
        self.fixture.write('selection.json', self.fixture.selection)
        self.fixture.config.update(reservation_sha256=digest(self.root/'reservation.json'),
            selection_sha256=digest(self.root/'selection.json'),
            final_gate=dict(min_matched_forecasts=1, min_global_matched_origins=1, min_matched_series=1,
                min_matched_fraction_of_resolved_forecasts=.75, raw_mae_relative_improvement_min=.01,
                macro_origin_mae_noninferior=True, max_each_origin_mae_regression_spaces=.5,
                no_score_before=self.fixture.reservation['final_target_end']))
        self.fixture.write('config.json', self.fixture.config)
        self.manifest = dict(source_id='SRC-LIVE-001', issuance_config='config.json',
            issuance_config_sha256=digest(self.root/'config.json'), frozen_at='2026-01-01T00:03:00+00:00',
            implementation_hashes={'runtime.py': digest(self.root/'runtime.py')})
        self.fixture.write('scorer.json', self.manifest)
        self.closed = datetime.fromisoformat('2026-01-01T02:51:00+00:00')

    def tearDown(self):
        self.fixture.tearDown()

    def issue(self):
        self.assertEqual(self.fixture.call()['issued'], 1)

    def target(self, name='target', at='2026-01-01T01:31:00+00:00', available=55, capacity=100):
        self.fixture.receipts.append(self.fixture.feed(name, at, available, capacity))
        self.fixture.save_receipts()

    def call(self, at=None):
        return evaluate_study(self.root/'scorer.json', root=self.root, clock=lambda: at or self.closed)

    def consumed(self):
        return _claim_path(self.fixture.reservation, self.root).exists()

    def test_positive_pair_is_scored_only_after_global_claim_and_exactly_once(self):
        self.issue(); self.target()
        def observed_after_claim(root, receipt):
            self.assertTrue(self.consumed())
            return _observations(root, receipt)
        with patch('smart_parking.singapore_final._observations', side_effect=observed_after_claim):
            result = self.call()
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(result['metrics']['final_gate_passed'])
        self.assertEqual(result['metrics']['learned_mae_spaces'], 0)
        self.assertEqual(result['metrics']['persistence_same_cohort_mae_spaces'], 5)
        with self.assertRaises(ValueError):
            self.call()

    def test_early_closure_and_no_issuance_never_decode_targets(self):
        with patch('smart_parking.singapore_final._observations', side_effect=AssertionError('No target decoding allowed')):
            result = self.call(datetime.fromisoformat('2026-01-01T02:50:59+00:00'))
            self.assertEqual(result['status'], 'not_ready')
            self.assertEqual(self.call()['status'], 'not_evaluable_no_eligible_issuance')
        self.assertFalse(self.consumed())
        self.assertFalse((self.root/'experiments').exists())

    def test_first_received_target_is_used_not_the_best_later_answer(self):
        self.issue()
        self.target('first', '2026-01-01T01:24:00+00:00', 54)
        self.target('later', '2026-01-01T01:31:00+00:00', 55)
        result = self.call()
        self.assertEqual(result['metrics']['learned_mae_spaces'], 1)
        self.assertEqual(result['metrics']['persistence_same_cohort_mae_spaces'], 4)

    def test_capacity_change_does_not_bridge_to_a_convenient_later_value(self):
        self.issue()
        self.target('changed', '2026-01-01T01:11:00+00:00', 55, 110)
        self.target()
        result = self.call()
        self.assertEqual(result['metrics']['matched'], 0)
        self.assertIsNone(result['metrics']['learned_mae_spaces'])
        self.assertFalse(result['metrics']['final_gate_passed'])
        report = json.loads((self.root/result['result_path']).read_text())
        self.assertEqual(report['missing_reasons']['fresh_capacity_change_before_match'], 1)

    def test_missing_target_is_unscored_not_zero_error(self):
        self.issue()
        result = self.call()
        self.assertEqual(result['metrics']['expired_unmatched'], 1)
        self.assertEqual(result['metrics']['matched_fraction'], 0)
        self.assertIsNone(result['metrics']['persistence_same_cohort_mae_spaces'])
        self.assertFalse(result['metrics']['accuracy_evaluable'])
        self.assertTrue(self.consumed())

    def test_corrupt_target_callback_failure_consumes_interval(self):
        self.issue(); self.target()
        receipt = self.fixture.receipts[-1]
        self.fixture.write(receipt['local_path'], 'not-json', raw=True)
        receipt['sha256'] = digest(self.root/receipt['local_path'])
        self.fixture.save_receipts()
        with self.assertRaises(ValueError):
            self.call()
        self.assertTrue(self.consumed())
        with self.assertRaises(ValueError):
            self.call()

    def test_counterfeit_issue_context_is_detected_after_claim(self):
        self.issue(); self.target()
        batch_path = next((self.root/'batches').glob('*.jsonl'))
        row = json.loads(batch_path.read_text())
        row.update(origin_available=49, persistence_available=49, predicted_available=53.5)
        self.fixture.write(batch_path, json.dumps(row)+'\n', raw=True)
        receipt_path = next((self.root/'batch_receipts').glob('*.receipt.json'))
        receipt = json.loads(receipt_path.read_text()); receipt['batch_sha256'] = digest(batch_path)
        self.fixture.write(receipt_path, receipt)
        with self.assertRaises(ValueError):
            self.call()
        self.assertTrue(self.consumed())

    def test_outcomes_smuggled_into_issuance_fail_before_claim(self):
        self.issue(); self.target()
        batch_path = next((self.root/'batches').glob('*.jsonl'))
        row = json.loads(batch_path.read_text()); row['target_available'] = 55
        self.fixture.write(batch_path, json.dumps(row)+'\n', raw=True)
        receipt_path = next((self.root/'batch_receipts').glob('*.receipt.json'))
        receipt = json.loads(receipt_path.read_text()); receipt['batch_sha256'] = digest(batch_path)
        self.fixture.write(receipt_path, receipt)
        with self.assertRaises(ValueError):
            self.call()
        self.assertFalse(self.consumed())

    def test_frozen_scoring_source_change_or_late_freeze_is_rejected(self):
        self.fixture.write('runtime.py', 'changed', raw=True)
        with self.assertRaises(ValueError):
            self.call()
        self.fixture.write('runtime.py', 'synthetic runtime', raw=True)
        self.manifest['frozen_at'] = '2026-01-01T01:00:00+00:00'
        self.fixture.write('scorer.json', self.manifest)
        with self.assertRaises(ValueError):
            self.call()

    def test_metric_coverage_and_zero_baseline_cannot_claim_improvement(self):
        forecast = dict(forecast_id='one')
        match = dict(forecast_id='one', issued_at='synthetic-time', car_park_id='SYNTHETIC',
                     lot_type='C', learned_absolute_error=0, persistence_absolute_error=0)
        metrics = paired_metrics([forecast, dict(forecast_id='two')], [match], self.fixture.config)
        self.assertEqual(metrics['matched_fraction'], .5)
        self.assertIsNone(metrics['relative_improvement'])
        self.assertFalse(metrics['checks']['raw_mae_gain'])
        self.assertFalse(metrics['checks']['matching_coverage'])

    def test_mismatched_ids_and_nonfinite_errors_do_not_enter_paired_metrics(self):
        match = dict(forecast_id='one', issued_at='synthetic-time', car_park_id='SYNTHETIC',
                     lot_type='C', learned_absolute_error=0, persistence_absolute_error=1)
        for row in [dict(match, forecast_id='another'), dict(match, learned_absolute_error=float('nan')),
                    dict(match, persistence_absolute_error=-1)]:
            with self.assertRaises(ValueError):
                paired_metrics([dict(forecast_id='one')], [row], self.fixture.config)
