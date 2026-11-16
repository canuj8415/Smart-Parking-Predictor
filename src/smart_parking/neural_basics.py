"""Unit I foundations in NumPy: McCulloch-Pitts neuron, Rosenblatt perceptron, sigmoid neuron.

Teaching code with explicit formulas; no learned production model.
"""
import numpy as np


def mcculloch_pitts(x, weights, threshold):
    """Fires (1) when the weighted sum of binary inputs reaches the threshold: y = [w.x >= theta]."""
    x = np.asarray(x)
    if x.ndim not in (1, 2) or not np.isin(x, [0, 1]).all():
        raise ValueError('Binary inputs required')
    w = np.asarray(weights, dtype=float)
    if w.shape != (x.shape[-1],):
        raise ValueError('One weight per input required')
    return (x @ w >= threshold).astype(int)


# Classic hand-set logic gates (weights, threshold)
GATES = {'AND': ([1, 1], 2), 'OR': ([1, 1], 1), 'NOT': ([-1], 0), 'NAND': ([-1, -1], -1)}


def gate(name, x):
    w, t = GATES[name]
    return mcculloch_pitts(x, w, t)


def perceptron_train(x, y, learning_rate=1., epochs=50, seed=0):
    """Rosenblatt rule: w <- w + eta (t - y_hat) x, with bias as w0. Returns (w, b, errors per epoch).

    Converges in finitely many updates when the data are linearly separable (perceptron
    convergence theorem); for XOR it never reaches zero errors.
    """
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=int)
    if x.ndim != 2 or y.shape != (len(x),) or not np.isin(y, [0, 1]).all() or learning_rate <= 0:
        raise ValueError('N,D inputs, binary labels and positive learning rate required')
    rng = np.random.default_rng(seed)
    w = np.zeros(x.shape[1]); b = 0.; history = []
    for _ in range(epochs):
        errors = 0
        for i in rng.permutation(len(x)):
            pred = int(x[i] @ w + b >= 0)
            delta = y[i] - pred
            if delta:
                w += learning_rate * delta * x[i]; b += learning_rate * delta; errors += 1
        history.append(errors)
        if errors == 0:
            break
    return w, b, history


def perceptron_predict(x, w, b):
    return (np.asarray(x, dtype=float) @ w + b >= 0).astype(int)


def sigmoid(z):
    z = np.clip(np.asarray(z, dtype=float), -40, 40)
    return 1 / (1 + np.exp(-z))


def sigmoid_neuron(x, w, b):
    """Smooth neuron: y = sigma(w.x + b); derivative sigma' = sigma(1 - sigma)."""
    return sigmoid(np.asarray(x, dtype=float) @ np.asarray(w, dtype=float) + b)


def sigmoid_derivative(z):
    s = sigmoid(z)
    return s * (1 - s)
