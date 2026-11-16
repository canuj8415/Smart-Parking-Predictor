"""Sealed TRAIN-only frozen-feature linear probe on ACPDS (in-domain separability).

Question: do the frozen ImageNet ResNet18 features used by every region decoder
linearly separate ACPDS bay-union vs non-bay cells on the stride-4 grid when the
probe is trained in-domain on ACPDS TRAIN images and scored on held-out TRAIN
images (image-level folds)? Only SRC-DS-021 TRAIN caches are opened; DEV/TEST never.
Not a deployable model, not DEV/final accuracy, not a promotion candidate.

  seal: python scripts/probe_acpds_frozen_features.py seal      (no torch; selects/hashes, writes protocol)
  run : python scripts/probe_acpds_frozen_features.py run <protocol.json> --root <copy root>
"""
import ast, hashlib, json, os, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/processed/acpds_region_v1/ACPDS-REGION-DATA-20261027T101700848553Z/manifest.json'
MANIFEST_SHA = '84e99f49e42488985bea490c8ca8ce230dff844830c1f5a01eb9365c004e5937'
WEIGHTS = 'models/pretrained/resnet18_imagenet.pth'
SEED, SAMPLE, FOLDS = 188, 64, 4
PROBE = dict(model='sklearn LogisticRegression', C=1.0, penalty='l2', solver='lbfgs', max_iter=2000, class_weight=None,
             features='frozen layer1..layer4 bilinear(align_corners=False) to 36x64, concat 960ch, standardized with training-fold valid-cell mean/std',
             cell_target='area 4x4 mask mean >=.5 (stride4 representation, see trial116)', cell_support='fully valid 4x4 cells only',
             output='cell probability (0 in invalid cells) bilinear upsampled to 144x256, >=.5, scored on nonpadding pixels')
COMPARATOR = 'Positional prior: training-fold pixelwise mean of full-resolution TRAIN masks >=.5 (no image content)'
DECISION_RULE = dict(
    sufficient='probe mean held-out IoU>=0.70 AND probe-prior>=0.05: frozen features linearly separate ACPDS bays in-domain;encoder adaptation NOT indicated by this;next hypothesis concerns decoder supervision/data',
    insufficient='probe mean held-out IoU<0.55: frozen features poorly separable even in-domain;supports one encoder-adaptation hypothesis',
    partial='otherwise: no training hypothesis selected from this diagnostic alone')
CODE = ['scripts/probe_acpds_frozen_features.py', 'src/smart_parking/mask_reconstruction.py', 'src/smart_parking/region_validity.py']
NORMALIZATION = dict(mean=[.485, .456, .406], std=[.229, .224, .225])

digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p, v): Path(p).write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')


def seal():
    for prev in (ROOT / 'experiments/results').glob('ACPDS-FEATURE-PROBE-*/protocol.json'):
        raise SystemExit('Sealed probe already exists: ' + prev.parent.name)
    state = read(ROOT / 'data/automation_state.json')
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert digest(ROOT / MANIFEST) == MANIFEST_SHA
    used = read(ROOT / 'experiments/results/ACPDS-TARGET-REPRESENTATION-20261116T093422210992Z/protocol.json')
    train = sorted((r for r in read(ROOT / MANIFEST)['records'] if r['role'] == 'train' and r['source_id'] == 'SRC-DS-021'), key=lambda r: r['index'])
    assert len(train) == 231
    rng = np.random.default_rng(SEED)
    chosen = sorted(rng.choice(len(train), SAMPLE, replace=False).tolist())
    folds = (np.arange(SAMPLE) % FOLDS)[rng.permutation(SAMPLE)].tolist()
    rid = 'ACPDS-FEATURE-PROBE-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'experiments/results' / rid; out.mkdir(parents=True, exist_ok=False)
    sel = [dict(index=train[i]['index'], name=train[i]['name'], camera_id=train[i]['camera_id'], cache=train[i]['cache'],
                cache_sha256=train[i]['cache_sha256'], fold=f) for i, f in zip(chosen, folds)]
    overlap = len({s['index'] for s in sel} & {s['index'] for s in used['selected']})
    dump(out / 'protocol.json', dict(run_id=rid, sealed_at=datetime.now(timezone.utc).isoformat(), seed=SEED, sample=SAMPLE, folds=FOLDS,
        fold_unit='image (each ACPDS image is a unique view id;physical/date near-duplicate independence unknown)',
        source_ids=['SRC-DS-021','SRC-MOD-003'], dataset_manifest=MANIFEST, manifest_sha256=MANIFEST_SHA,
        weights=WEIGHTS, weights_sha256=digest(ROOT / WEIGHTS), normalization=NORMALIZATION, input_size=[256, 144], selected=sel,
        overlap_with_trial116_sample=overlap, probe=PROBE, comparator=COMPARATOR, decision_rule=DECISION_RULE,
        references=dict(label_reconstruction_trial116=0.9660646445389558, dev_model_mean_iou=0.5336515113242111,
                        use='interpretation only;not used for any configuration choice'),
        code_sha256={c: digest(ROOT / c) for c in CODE}, grids_or_retuning=False,
        forbidden=['ACPDS DEVELOPMENT', 'ACPDS TEST (closed)', 'Singapore final (consumed)', 'raw images'],
        scope='In-domain TRAIN cross-validated linear separability of frozen features;not model/DEV/final accuracy'))
    print(rid, digest(out / 'protocol.json'))


def valid_mask_metrics(root):
    src = (root / 'src/smart_parking/region_validity.py').read_text(encoding='utf-8')
    node = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'valid_mask_metrics'][0]
    ns = {'np': np}; exec(ast.get_source_segment(src, node), ns); return ns['valid_mask_metrics']


def run(protocol_path, root):
    import torch
    from torch.nn import functional as F
    from torchvision.models import resnet18
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    root = Path(root); sys.path.insert(0, str(root / 'src'))
    from smart_parking.mask_reconstruction import area_downsample, bilinear_upsample
    p = read(protocol_path); out = Path(protocol_path).parent
    assert not (out / 'run.json').exists(), 'Completed probe;refusing rerun'
    assert all(digest(root / c) == h for c, h in p['code_sha256'].items()) and digest(root / p['weights']) == p['weights_sha256']
    started = datetime.now(timezone.utc).isoformat(); t0 = time.perf_counter()
    torch.manual_seed(p['seed']); torch.set_num_threads(max(1, os.cpu_count() or 1))
    rgb, mask, valid = [], [], []
    for s in p['selected']:
        f = root / s['cache']; assert digest(f) == s['cache_sha256']
        with np.load(f, allow_pickle=False) as z: rgb.append(z['rgb'].copy()); mask.append(z['mask'].copy()); valid.append(z['valid'].copy())
    rgb, mask, valid = np.stack(rgb), np.stack(mask), np.stack(valid)
    net = resnet18(weights=None); net.load_state_dict(torch.load(root / p['weights'], map_location='cpu'), strict=True); net.eval()
    mean = torch.tensor(p['normalization']['mean'])[None, :, None, None]; std = torch.tensor(p['normalization']['std'])[None, :, None, None]
    feats = []
    with torch.no_grad():
        for i in range(0, len(rgb), 8):
            x = torch.from_numpy(rgb[i:i + 8]).permute(0, 3, 1, 2).float() / 255.
            b = net; y = b.maxpool(b.relu(b.bn1(b.conv1((x - mean) / std)))); a = b.layer1(y); c = b.layer2(a); d = b.layer3(c); e = b.layer4(d)
            size = a.shape[-2:]
            feats.append(torch.cat([a] + [F.interpolate(t, size=size, mode='bilinear', align_corners=False) for t in (c, d, e)], 1).permute(0, 2, 3, 1).numpy())
    feats = np.concatenate(feats).astype(np.float32)  # N,36,64,960
    assert feats.shape[1:3] == (36, 64)
    cell_t = area_downsample(mask, 4) >= .5; cell_v = area_downsample(valid, 4) == 1.
    fold = np.array([s['fold'] for s in p['selected']]); metric = valid_mask_metrics(root)
    probe_pred = np.zeros_like(mask); prior_pred = np.zeros_like(mask); aucs = []; fold_info = []
    for k in range(p['folds']):
        tr, te = fold != k, fold == k
        X = feats[tr][cell_v[tr]]; y = cell_t[tr][cell_v[tr]]
        mu, sd = X.mean(0), X.std(0) + 1e-6
        clf = LogisticRegression(C=p['probe']['C'], solver='lbfgs', max_iter=p['probe']['max_iter'], class_weight=None)
        clf.fit((X - mu) / sd, y)
        prob = np.zeros(cell_t[te].shape)
        prob[cell_v[te]] = clf.predict_proba((feats[te][cell_v[te]] - mu) / sd)[:, 1]
        aucs.append(float(roc_auc_score(cell_t[te][cell_v[te]], prob[cell_v[te]])))
        probe_pred[te] = bilinear_upsample(prob, mask.shape[1:]) >= .5
        prior_pred[te] = mask[tr].mean(0)[None] >= .5
        fold_info.append(dict(fold=k, train_images=int(tr.sum()), test_images=int(te.sum()), train_cells=int(len(y)), positive_rate=float(y.mean()),
                              iterations=int(clf.n_iter_[0]), converged=bool(clf.n_iter_[0] < p['probe']['max_iter']), heldout_cell_auroc=aucs[-1]))
    probe_m = metric(probe_pred & valid, mask, valid); prior_m = metric(prior_pred & valid, mask, valid)
    P, Q = probe_m['mean_image_iou'], prior_m['mean_image_iou']
    verdict = 'sufficient' if (P >= .70 and P - Q >= .05) else ('insufficient' if P < .55 else 'partial')
    for row, s in zip(probe_m['per_image'], p['selected']): row.update(name=s['name'], fold=s['fold'])
    result = dict(run_id=p['run_id'], started_at=started, finished_at=datetime.now(timezone.utc).isoformat(), duration_seconds=time.perf_counter() - t0,
                  protocol_sha256=digest(protocol_path), seed=p['seed'], images=len(rgb), folds=fold_info,
                  probe=probe_m, positional_prior=prior_m,
                  summary=dict(probe_mean_iou=P, probe_min_iou=probe_m['minimum_image_iou'], probe_mean_dice=probe_m['mean_image_dice'],
                               prior_mean_iou=Q, probe_minus_prior=P - Q, mean_heldout_cell_auroc=float(np.mean(aucs)),
                               label_reconstruction_reference=p['references']['label_reconstruction_trial116'], dev_model_reference=p['references']['dev_model_mean_iou']),
                  verdict=verdict, verdict_text=p['decision_rule'][verdict], models_trained=p['folds'], model_type='linear probes (not saved, not deployable)',
                  development_or_test_opened=False,
                  environment=dict(python=platform.python_version(), torch=torch.__version__, numpy=np.__version__, machine='Claude cloud workspace CPU (files staged from project, hashes verified)'),
                  limitations='64 of 231 TRAIN images;in-domain TRAIN CV, not DEV/final;ACPDS view/date/near-duplicate independence unknown so held-out folds may be optimistic;'
                              'partial bay-union labels;one fixed linear probe;ImageNet weights only.')
    dump(out / 'run.json', result)
    print(json.dumps(dict(run_id=p['run_id'], verdict=verdict, **result['summary']), indent=1))


if __name__ == '__main__':
    if sys.argv[1] == 'seal': seal()
    else: run(sys.argv[2], sys.argv[sys.argv.index('--root') + 1])
