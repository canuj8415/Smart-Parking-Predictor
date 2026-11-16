"""Synthetic-fixture software tests for Unit I labs, learning rules, Nesterov and MLP training.

All inputs here are synthetic toy data; no real parking data or model evaluation.
"""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from smart_parking.neural_basics import gate, perceptron_train, perceptron_predict, sigmoid_derivative, sigmoid
from smart_parking.learning_rules import hebbian, oja, competitive, delta_rule, hopfield_store, hopfield_recall
from smart_parking.mlp import MLP
from smart_parking.mlp_training import next_observation_windows, train_mlp, balanced_accuracy

X2 = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])


class NeuralBasicsTests(unittest.TestCase):
    def test_mcculloch_pitts_gates(self):
        np.testing.assert_array_equal(gate('AND', X2), [0, 0, 0, 1])
        np.testing.assert_array_equal(gate('OR', X2), [0, 1, 1, 1])
        np.testing.assert_array_equal(gate('NAND', X2), [1, 1, 1, 0])
        np.testing.assert_array_equal(gate('NOT', np.array([[0], [1]])), [1, 0])

    def test_perceptron_learns_and_but_not_xor(self):
        w, b, h = perceptron_train(X2, [0, 0, 0, 1])
        self.assertEqual(h[-1], 0); np.testing.assert_array_equal(perceptron_predict(X2, w, b), [0, 0, 0, 1])
        _, _, hx = perceptron_train(X2, [0, 1, 1, 0], epochs=100)
        self.assertGreater(hx[-1], 0)

    def test_sigmoid_derivative_matches_finite_difference(self):
        z = np.linspace(-4, 4, 9); e = 1e-6
        np.testing.assert_allclose(sigmoid_derivative(z), (sigmoid(z + e) - sigmoid(z - e)) / (2 * e), atol=1e-8)


class LearningRuleTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(0)
        self.x = rng.normal(0, 1, (300, 2)) @ np.array([[3., 0.], [0., .5]])  # first axis dominates

    def test_hebbian_grows_oja_normalises_to_first_pc(self):
        _, norms = hebbian(self.x, epochs=3)
        self.assertGreater(norms[-1], norms[0])
        w, n = oja(self.x, epochs=30, learning_rate=.005)
        self.assertAlmostEqual(n[-1], 1, delta=.05); self.assertGreater(abs(w[0]), 5 * abs(w[1]))

    def test_competitive_separates_clusters(self):
        x = np.concatenate([np.random.default_rng(1).normal(c, .1, (30, 2)) for c in ([0, 0], [3, 3])])
        _, a = competitive(x, units=2, epochs=10)
        self.assertEqual(len(set(a[:30])), 1); self.assertEqual(len(set(a[30:])), 1); self.assertNotEqual(a[0], a[-1])

    def test_delta_rule_reduces_error_toward_true_weights(self):
        t = self.x @ np.array([2., -1.]) + .5
        w, b, mse = delta_rule(self.x, t, epochs=30, learning_rate=.01)
        self.assertLess(mse[-1], mse[0]); np.testing.assert_allclose(w, [2, -1], atol=.05)

    def test_hopfield_energy_never_increases_and_recalls(self):
        p = np.array([[1, -1, 1, -1, 1, -1, 1, -1], [1, 1, 1, 1, -1, -1, -1, -1]])
        w = hopfield_store(p); noisy = p[0].copy(); noisy[0] *= -1
        s, e = hopfield_recall(w, noisy)
        self.assertTrue(all(b <= a + 1e-12 for a, b in zip(e, e[1:]))); np.testing.assert_array_equal(s, p[0])


class OptimizerAndTrainingTests(unittest.TestCase):
    def test_nesterov_closed_form(self):
        m = MLP(); init = {k: v.copy() for k, v in m.parameters.items()}; g = {k: np.ones_like(v) for k, v in init.items()}
        m.step(g, .1, .5, nesterov=True); m.step(g, .1, .5, nesterov=True)
        for k in init:
            np.testing.assert_allclose(m.parameters[k], init[k] - .325)

    def test_plain_momentum_unchanged(self):
        m = MLP(); init = {k: v.copy() for k, v in m.parameters.items()}; g = {k: np.ones_like(v) for k, v in init.items()}
        m.step(g, .1, .5); m.step(g, .1, .5)
        for k in init:
            np.testing.assert_allclose(m.parameters[k], init[k] - .25)

    def test_windows_respect_park_day_gap_and_split(self):
        def r(p, ts, occ, split='train'):
            return dict(car_park_id=p, timestamp=ts, capture_date=ts[:10], capacity='100', occupancy=str(occ), split=split)
        rows = [r('A', '2016-10-04 08:00:00', 50), r('A', '2016-10-04 08:30:00', 90), r('A', '2016-10-04 10:00:00', 95),
                r('B', '2016-10-04 08:10:00', 10), r('A', '2016-10-05 08:00:00', 20)]
        X, y, keys = next_observation_windows(rows)
        self.assertEqual(keys, [('A', '2016-10-04 08:00:00')]); np.testing.assert_array_equal(y, [1])
        with self.assertRaises(ValueError):
            next_observation_windows(rows + [r('C', '2016-10-04 08:00:00', 1, 'validation')])

    def test_training_learns_separable_toy_problem(self):
        rng = np.random.default_rng(0); x = rng.normal(0, 1, (400, 3)); y = (x[:, 0] + x[:, 1] > 0).astype(int)
        for opt in ('sgd', 'momentum', 'nesterov'):
            model, hist, (mu, sd) = train_mlp(x[:300], y[:300], x[300:], y[300:], optimizer=opt, epochs=20, dropout=.1, l2=1e-4)
            self.assertGreater(hist[-1]['validation_balanced_accuracy'], .85, opt)
        self.assertEqual(balanced_accuracy([0, 1], [.2, .9]), 1.)


if __name__ == '__main__':
    unittest.main()
