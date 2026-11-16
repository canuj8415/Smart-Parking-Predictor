"""Real parking-feature windows and a controlled NumPy MLP trainer (MLP-03, EXP-01).

Features come from real Birmingham car-park counts (SRC-DS-003) in the existing chronological
day-level split. Each example pairs one observation with the SAME car park's next observation
on the SAME capture date within 45 minutes (no cross-split, cross-day or cross-car-park windows).
Label: next occupancy rate >= 0.85.
"""
import csv
from datetime import datetime
import numpy as np
from smart_parking.mlp import MLP

FEATURES = ['rate_now', 'rate_change_prev', 'has_prev', 'hour_sin', 'hour_cos', 'weekday_sin', 'weekday_cos', 'log_capacity']
FULL_THRESHOLD = .85
MAX_GAP_MINUTES = 45


def load_rows(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def next_observation_windows(rows):
    """Return X (N,8), y (N,), keys. Rows must all come from one split."""
    splits = {r['split'] for r in rows}
    if len(splits) != 1:
        raise ValueError('Windows must stay within one split')
    groups = {}
    for r in rows:
        groups.setdefault((r['car_park_id'], r['capture_date']), []).append(r)
    X = []; y = []; keys = []
    for (park, day), items in sorted(groups.items()):
        items.sort(key=lambda r: r['timestamp'])
        times = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S') for r in items]
        rates = [int(r['occupancy']) / int(r['capacity']) for r in items]
        for i in range(len(items) - 1):
            gap = (times[i + 1] - times[i]).total_seconds() / 60
            if not 0 < gap <= MAX_GAP_MINUTES:
                continue
            prev_ok = i > 0 and 0 < (times[i] - times[i - 1]).total_seconds() / 60 <= MAX_GAP_MINUTES
            hour = times[i].hour + times[i].minute / 60; wd = times[i].weekday()
            X.append([rates[i], rates[i] - rates[i - 1] if prev_ok else 0., float(prev_ok),
                      np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24),
                      np.sin(2 * np.pi * wd / 7), np.cos(2 * np.pi * wd / 7), np.log(int(items[i]['capacity']))])
            y.append(int(rates[i + 1] >= FULL_THRESHOLD)); keys.append((park, items[i]['timestamp']))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int), keys


def balanced_accuracy(y, p):
    y = np.asarray(y); pred = (np.asarray(p).ravel() >= .5).astype(int)
    tpr = (pred[y == 1] == 1).mean() if (y == 1).any() else np.nan
    tnr = (pred[y == 0] == 0).mean() if (y == 0).any() else np.nan
    return float((tpr + tnr) / 2)


def log_loss(y, p):
    p = np.clip(np.asarray(p).ravel(), 1e-12, 1 - 1e-12); y = np.asarray(y)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _loss_grad(model, x, y, l2=0., dropout=0., rng=None):
    P = model.parameters
    hidden = np.tanh(x @ P['w1'] + P['b1'])
    mask = None
    if dropout > 0:
        mask = (rng.random(hidden.shape) >= dropout) / (1 - dropout)  # inverted dropout
        hidden_used = hidden * mask
    else:
        hidden_used = hidden
    score = hidden_used @ P['w2'] + P['b2']; prob = 1 / (1 + np.exp(-np.clip(score, -40, 40)))
    yy = y.reshape(-1, 1).astype(float)
    dz = (prob - yy) / len(x)
    dh = dz @ P['w2'].T
    if mask is not None:
        dh = dh * mask
    dh = dh * (1 - hidden ** 2)
    g = {'w2': hidden_used.T @ dz + l2 * P['w2'], 'b2': dz.sum(0), 'w1': x.T @ dh + l2 * P['w1'], 'b1': dh.sum(0)}
    return g


def train_mlp(xtr, ytr, xva, yva, hidden=16, learning_rate=.05, optimizer='momentum', momentum=.9, init_scale=1.,
              l2=0., dropout=0., batch_size=64, epochs=30, standardize=True, seed=0):
    """Mini-batch training with one switch per controlled factor. Returns (model, history, scaler)."""
    if optimizer not in ('sgd', 'momentum', 'nesterov') or not 0 <= dropout < 1 or batch_size < 1:
        raise ValueError('Invalid configuration')
    mu, sd = (xtr.mean(0), xtr.std(0) + 1e-8) if standardize else (np.zeros(xtr.shape[1]), np.ones(xtr.shape[1]))
    a = (xtr - mu) / sd; b = (xva - mu) / sd
    model = MLP(inputs=xtr.shape[1], hidden=hidden, seed=seed)
    for k in ('w1', 'w2'):
        model.parameters[k] *= init_scale
    rng = np.random.default_rng(seed + 1000)
    m = 0. if optimizer == 'sgd' else momentum
    history = []
    for epoch in range(epochs):
        order = rng.permutation(len(a))
        for s in range(0, len(a), batch_size):
            idx = order[s:s + batch_size]
            g = _loss_grad(model, a[idx], ytr[idx], l2, dropout, rng)
            model.step(g, learning_rate, m, nesterov=(optimizer == 'nesterov'))
        ptr = model.forward(a)[0]; pva = model.forward(b)[0]
        history.append(dict(epoch=epoch + 1, train_loss=log_loss(ytr, ptr), validation_loss=log_loss(yva, pva),
                            validation_balanced_accuracy=balanced_accuracy(yva, pva)))
        if not np.isfinite(history[-1]['train_loss']):
            break
    return model, history, (mu, sd)
