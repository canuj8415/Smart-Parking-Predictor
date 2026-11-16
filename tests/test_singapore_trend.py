"""Synthetic software fixtures, not observed parking performance."""
import copy
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.singapore_trend import fit_trend, predict_available, causal_trend


def example(current=50, previous=40, target=55):
    return dict(capacity=100, origin_available=current, previous_available=previous,
                target_available=target, issued_at='2026-01-01T01:00:00+00:00',
                origin_available_at='2026-01-01T01:00:00+00:00',
                previous_available_at='2026-01-01T00:30:00+00:00',
                origin_observed_at='2026-01-01T00:59:00+00:00',
                previous_observed_at='2026-01-01T00:29:00+00:00',
                previous_gap_minutes=30)


class SingaporeTrendTests(unittest.TestCase):
    def test_weighted_median_resists_many_small_changes(self):
        rows = [example(50, 30, 65)] + [example(50, 49, 50)]*5
        model = fit_trend(rows)
        self.assertEqual(model['coefficient'], .75)
        self.assertEqual(predict_available(model, [example()]), [57.5])

    def test_zero_changes_and_constrained_ties(self):
        self.assertEqual(fit_trend([example(50, 50, 90)])['coefficient'], 0)
        self.assertEqual(fit_trend([example(target=40)])['coefficient'], 0)
        self.assertEqual(fit_trend([example(target=90)])['coefficient'], 1)
        self.assertEqual(fit_trend([example(target=50), example(target=60)])['coefficient'], 0)

    def test_randomized_unclipped_objective_is_minimal(self):
        rng = random.Random(132)
        for _ in range(100):
            rows = [example(rng.randrange(101), rng.randrange(101), rng.randrange(101)) for _ in range(23)]
            alpha = fit_trend(rows)['coefficient']
            def loss(a):
                return sum(abs(row['target_available']-row['origin_available']-a*causal_trend(row)[2]) for row in rows)
            self.assertLessEqual(loss(alpha), min(loss(i/100) for i in range(101))+1e-8)

    def test_target_values_and_actual_future_lead_never_used_for_prediction(self):
        model = fit_trend([example()]);row = example();before = copy.deepcopy(row)
        changed = dict(row, target_available=100, actual_target_lead_minutes=999)
        self.assertEqual(predict_available(model, [row]), predict_available(model, [changed]))
        self.assertEqual(row, before)

    def test_missing_or_inconsistent_causal_context_is_rejected(self):
        for changes in [dict(previous_available_at='2026-01-01T01:00:00+00:00'),
                        dict(origin_available_at='2026-01-01T01:01:00+00:00'),
                        dict(previous_gap_minutes=29), dict(capacity=True),
                        dict(origin_available='1.5'), dict(target_available=101)]:
            with self.assertRaises(ValueError):
                fit_trend([dict(example(), **changes)])
        with self.assertRaises(ValueError):
            fit_trend([])

    def test_frozen_model_validation_and_physical_bounds(self):
        model = fit_trend([example(target=90)])
        self.assertEqual(predict_available(model, [example(99, 0), example(1, 100)]), [100, 0])
        for value in [float('nan'), float('inf'), -1, 2, True]:
            with self.assertRaises(ValueError):
                predict_available(dict(model, coefficient=value), [example()])
