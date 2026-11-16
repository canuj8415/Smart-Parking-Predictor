"""Classical learning rules in NumPy (RULE-01): Hebbian, Oja (modified Hebbian), competitive,
error-correction (delta/LMS) and energy-based (Hopfield) learning.

Key difference in what drives each update:
- Hebbian / Oja: correlation of pre- and post-synaptic activity; no target labels (unsupervised).
- Competitive: only the winning unit moves toward the input; no labels.
- Error-correction (delta): update proportional to (target - output); supervised.
- Energy (Hopfield): Hebbian storage of patterns; recall descends an energy function.
"""
import numpy as np


def hebbian(x, epochs=1, learning_rate=.01, seed=0):
    """Plain Hebb: dw = eta * y * x with y = w.x. Weight norm grows without bound."""
    x = np.asarray(x, dtype=float); rng = np.random.default_rng(seed)
    w = rng.normal(0, .1, x.shape[1]); norms = []
    for _ in range(epochs):
        for i in rng.permutation(len(x)):
            y = w @ x[i]; w = w + learning_rate * y * x[i]
        norms.append(float(np.linalg.norm(w)))
    return w, norms


def oja(x, epochs=50, learning_rate=.01, seed=0):
    """Oja's rule: dw = eta * y * (x - y w). Stays near unit norm and converges to the first
    principal component of zero-mean data."""
    x = np.asarray(x, dtype=float); rng = np.random.default_rng(seed)
    w = rng.normal(0, .1, x.shape[1]); norms = []
    for _ in range(epochs):
        for i in rng.permutation(len(x)):
            y = w @ x[i]; w = w + learning_rate * y * (x[i] - y * w)
        norms.append(float(np.linalg.norm(w)))
    return w, norms


def competitive(x, units=3, epochs=20, learning_rate=.1, seed=0):
    """Winner-take-all: the closest prototype moves toward the input, others unchanged."""
    x = np.asarray(x, dtype=float); rng = np.random.default_rng(seed)
    prototypes = x[rng.choice(len(x), units, replace=False)].copy()
    for _ in range(epochs):
        for i in rng.permutation(len(x)):
            k = int(np.argmin(((prototypes - x[i]) ** 2).sum(1)))
            prototypes[k] += learning_rate * (x[i] - prototypes[k])
    assignment = np.argmin(((x[:, None, :] - prototypes[None]) ** 2).sum(2), axis=1)
    return prototypes, assignment


def delta_rule(x, t, epochs=100, learning_rate=.01, seed=0):
    """Error-correction / LMS: dw = eta (t - y) x for a linear unit y = w.x + b. Returns MSE history."""
    x = np.asarray(x, dtype=float); t = np.asarray(t, dtype=float); rng = np.random.default_rng(seed)
    w = np.zeros(x.shape[1]); b = 0.; mse = []
    for _ in range(epochs):
        for i in rng.permutation(len(x)):
            e = t[i] - (w @ x[i] + b); w += learning_rate * e * x[i]; b += learning_rate * e
        mse.append(float(np.mean((t - (x @ w + b)) ** 2)))
    return w, b, mse


def hopfield_store(patterns):
    """Hebbian storage W = (1/N) sum p p^T with zero diagonal; patterns in {-1,+1}."""
    p = np.asarray(patterns, dtype=float)
    if not np.isin(p, [-1, 1]).all():
        raise ValueError('Bipolar patterns required')
    w = p.T @ p / p.shape[1]; np.fill_diagonal(w, 0)
    return w


def hopfield_energy(w, s):
    s = np.asarray(s, dtype=float)
    return float(-.5 * s @ w @ s)


def hopfield_recall(w, s, sweeps=10, seed=0):
    """Asynchronous updates; energy never increases (symmetric W, zero diagonal)."""
    s = np.asarray(s, dtype=float).copy(); rng = np.random.default_rng(seed); energies = [hopfield_energy(w, s)]
    for _ in range(sweeps):
        changed = False
        for i in rng.permutation(len(s)):
            new = 1. if w[i] @ s >= 0 else -1.
            if new != s[i]:
                s[i] = new; changed = True
            energies.append(hopfield_energy(w, s))
        if not changed:
            break
    return s, energies
