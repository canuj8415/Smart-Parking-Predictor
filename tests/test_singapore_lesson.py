"""Small synthetic lesson-policy/arithmetic fixtures, not model evaluation."""
import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src')); sys.path.insert(0, str(ROOT/'scripts'))
from smart_parking.singapore_lesson import pair_development, teaching_prediction, table_html
from singapore_lesson_guard import path_decision


def example(prediction):
    return dict(source_id='SRC-LIVE-001', car_park_id='SYNTHETIC', lot_type='C', role='development', capacity='10',
        issued_at='2026-01-01T01:00:00+00:00', target_observed_at='2026-01-01T01:30:00+00:00',
        target_available_at='2026-01-01T01:31:00+00:00', previous_available_at='2026-01-01T00:30:00+00:00',
        origin_available_at='2026-01-01T01:00:00+00:00', origin_available='4', target_available='6',
        learned_available=str(prediction), learned_absolute_error=str(abs(prediction-6)), persistence_absolute_error='2')


class SingaporeLessonTests(unittest.TestCase):
    def pair(self, a, b):
        return pair_development(a, b, '2026-01-01T02:00:00+00:00', '2026-01-01T00:30:00+00:00')

    def test_identical_cohort_and_original_inputs_are_preserved(self):
        a, b = [example(5)], [example(6)]; before = copy.deepcopy((a, b))
        row = self.pair(a, b)[0]
        self.assertEqual((row['persistence_error'], row['ridge_error'], row['trend_error']), (2, 1, 0))
        self.assertEqual((a, b), before)

    def test_different_targets_series_and_duplicate_ids_are_rejected(self):
        for rows in [[dict(example(6), car_park_id='OTHER')], [dict(example(6), target_available='7')], [example(6), example(6)]]:
            with self.assertRaises(ValueError):
                self.pair([example(5)], rows)

    def test_postcutoff_noncausal_and_nonfinite_rows_are_rejected(self):
        for changes in [dict(target_available_at='2026-01-01T02:01:00+00:00'),
                        dict(origin_available_at='2026-01-01T01:01:00+00:00'), dict(role='final')]:
            with self.assertRaises(ValueError):
                self.pair([dict(example(5), **changes)], [dict(example(6), **changes)])
        with self.assertRaises(ValueError):
            self.pair([example(5)], [dict(example(6), learned_available='nan')])

    def test_stored_errors_are_checked_against_actual_paired_values(self):
        with self.assertRaises(ValueError):
            self.pair([example(5)], [dict(example(6), learned_absolute_error='1')])

    def test_synthetic_arithmetic_caps_and_no_future_truth(self):
        row = teaching_prediction(40, 50, 30, 100, .3)
        self.assertEqual(row['prediction'], 53)
        self.assertEqual(row['data_kind'], 'synthetic_teaching_example')
        self.assertEqual(teaching_prediction(0, 99, 30, 100, 1)['prediction'], 100)
        self.assertEqual(teaching_prediction(100, 1, 30, 100, 1)['prediction'], 0)
        for args in [(40, 50, 0, 100, .3), (True, 50, 30, 100, .3), (40, 50, 30, 100, float('nan'))]:
            with self.assertRaises(ValueError):
                teaching_prediction(*args)

    def test_project_writes_and_protected_reads_are_denied(self):
        scratch = ROOT/'outputs/synthetic_lesson_guard'
        for path in ['data/raw/a.json', 'data/processed/singapore_learned_v1/batches/a.jsonl',
                     'data/receipts/a.json', 'data/singapore_forecast_holdout_claims/a.json',
                     'experiments/results/SG-FINAL-20260101/run.json', 'reports/singapore_final_latest.json']:
            self.assertIsNotNone(path_decision(ROOT/path, False, ROOT, scratch))
        self.assertIsNotNone(path_decision(ROOT/'data/manifests/a.json', True, ROOT, scratch))
        self.assertIsNone(path_decision(scratch/'output.png', True, ROOT, scratch))
        self.assertIsNone(path_decision(ROOT/'data/manifests/a.json', False, ROOT, scratch))

    def test_standard_python_table_escapes_values_and_checks_columns(self):
        result = table_html([{'Label': '<script>fake</script>', 'MAE': 6.309847529}])
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('6.309848', result)
        with self.assertRaises(ValueError):
            table_html([{'a': 1}, {'b': 2}])
