"""Sealed one-variable-at-a-time MLP study on real Birmingham parking windows (MLP-03, EXP-01).

Pre-registered: baseline config, the single factor changed in each condition, seeds, data
(TRAIN fit / VALIDATION report only; TEST split never read), metrics and the noise rule.
Writes experiments/results/<run>/protocol.json then run.json. Registry/state recording is done
separately after any concurrent job finishes.

  python scripts/run_mlp_controlled_study.py
"""
import hashlib, json, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.mlp import MLP  # noqa: E402
from smart_parking.mlp_training import (FEATURES, FULL_THRESHOLD, load_rows, next_observation_windows, train_mlp,  # noqa: E402
                                        balanced_accuracy, log_loss)

SPLIT = 'data/splits/birmingham-global-days-v1'
BASELINE = dict(hidden=16, learning_rate=.05, optimizer='momentum', momentum=.9, init_scale=1., l2=0., dropout=0.,
                batch_size=64, epochs=30, standardize=True)
CONDITIONS = [('baseline', {}), ('optimizer=sgd', dict(optimizer='sgd')), ('optimizer=nesterov', dict(optimizer='nesterov')),
              ('learning_rate=0.01', dict(learning_rate=.01)), ('learning_rate=0.2', dict(learning_rate=.2)),
              ('init_scale=0.1', dict(init_scale=.1)), ('init_scale=3', dict(init_scale=3.)),
              ('normalization=off', dict(standardize=False)), ('l2=1e-3', dict(l2=1e-3)), ('dropout=0.2', dict(dropout=.2)),
              ('batch_size=16', dict(batch_size=16)), ('batch_size=256', dict(batch_size=256))]
SEEDS = [0, 1, 2]
CODE = ['scripts/run_mlp_controlled_study.py', 'src/smart_parking/mlp.py', 'src/smart_parking/mlp_training.py']
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p, v): Path(p).write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')


def main():
    for prev in (ROOT / 'experiments/results').glob('MLP-CONTROLLED-*/run.json'):
        raise SystemExit('Completed study exists: ' + prev.parent.name)
    rid = 'MLP-CONTROLLED-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'experiments/results' / rid; out.mkdir(parents=True, exist_ok=False)
    files = {f: digest(ROOT / SPLIT / f) for f in ['train.csv', 'validation.csv']}
    protocol = dict(run_id=rid, sealed_at=datetime.now(timezone.utc).isoformat(), source_ids=['SRC-DS-003'],
                    data=dict(split=SPLIT, files=files, test_split_read=False,
                              task='Next same-car-park same-day observation within 45 min: rate >= %.2f' % FULL_THRESHOLD, features=FEATURES),
                    baseline=BASELINE, conditions=[dict(name=n, change=c) for n, c in CONDITIONS], seeds=SEEDS,
                    metrics='Final-epoch VALIDATION log loss and balanced accuracy, mean and sd over seeds;training curves kept',
                    noise_rule='A change counts as a real effect only if |mean diff vs baseline| > 2 x baseline seed sd for that metric',
                    reference='Persistence rule: predict full if rate_now >= threshold (no learning)',
                    not_covered='Data augmentation is not meaningful for these tabular count features and is not run',
                    code_sha256={c: digest(ROOT / c) for c in CODE}, scope='Course optimisation study on validation days;not a deployment model or test accuracy')
    dump(out / 'protocol.json', protocol)
    t0 = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    tr = load_rows(ROOT / SPLIT / 'train.csv'); va = load_rows(ROOT / SPLIT / 'validation.csv')
    xtr, ytr, _ = next_observation_windows(tr); xva, yva, _ = next_observation_windows(va)
    persistence = balanced_accuracy(yva, (xva[:, 0] >= FULL_THRESHOLD).astype(float))
    results = {}
    for name, change in CONDITIONS:
        cfg = dict(BASELINE, **change); runs = []
        for seed in SEEDS:
            model, hist, (mu, sd) = train_mlp(xtr, ytr, xva, yva, seed=seed, **cfg)
            runs.append(dict(seed=seed, final=hist[-1], best_validation_loss=min(h['validation_loss'] for h in hist), curve=hist))
            if name == 'baseline' and seed == 0:
                model.save(out / 'baseline_seed0_mlp.npz'); dump(out / 'baseline_seed0_scaler.json', dict(mean=mu.tolist(), std=sd.tolist(), features=FEATURES))
                loaded = MLP.load(out / 'baseline_seed0_mlp.npz')
                roundtrip = bool(np.array_equal(loaded.forward((xva - mu) / sd)[0], model.forward((xva - mu) / sd)[0]))
        loss = np.array([r['final']['validation_loss'] for r in runs]); bacc = np.array([r['final']['validation_balanced_accuracy'] for r in runs])
        results[name] = dict(config=cfg, validation_loss_mean=float(loss.mean()), validation_loss_sd=float(loss.std()),
                             balanced_accuracy_mean=float(bacc.mean()), balanced_accuracy_sd=float(bacc.std()), runs=runs)
    base = results['baseline']
    for name, r in results.items():
        if name == 'baseline':
            continue
        dl = r['validation_loss_mean'] - base['validation_loss_mean']; db = r['balanced_accuracy_mean'] - base['balanced_accuracy_mean']
        r['effect'] = dict(loss_diff=dl, balanced_accuracy_diff=db,
                           loss_effect_real=bool(abs(dl) > 2 * max(base['validation_loss_sd'], 1e-12)),
                           balanced_accuracy_effect_real=bool(abs(db) > 2 * max(base['balanced_accuracy_sd'], 1e-12)))
    run = dict(run_id=rid, started_at=started, finished_at=datetime.now(timezone.utc).isoformat(), duration_seconds=time.perf_counter() - t0,
               protocol_sha256=digest(out / 'protocol.json'), train_windows=int(len(ytr)), validation_windows=int(len(yva)),
               train_positive_rate=float(ytr.mean()), validation_positive_rate=float(yva.mean()),
               persistence_reference_balanced_accuracy=persistence, results=results, baseline_checkpoint_roundtrip_exact=roundtrip,
               models_trained=len(CONDITIONS) * len(SEEDS), test_split_read=False,
               environment=dict(python=platform.python_version(), numpy=np.__version__))
    dump(out / 'run.json', run)
    print(rid, 'windows', len(ytr), len(yva), 'persistence', round(persistence, 4))
    for n, r in results.items():
        e = r.get('effect', {})
        print('%-20s loss %.4f+-%.4f  bacc %.4f+-%.4f  %s' % (n, r['validation_loss_mean'], r['validation_loss_sd'], r['balanced_accuracy_mean'],
                                                          r['balanced_accuracy_sd'], {k: v for k, v in e.items() if 'real' in k}))


if __name__ == '__main__':
    main()
