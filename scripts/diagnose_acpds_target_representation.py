"""Sealed TRAIN-only ACPDS target-representation diagnostic (label-only, no model).

Question: does re-representing ACPDS TRAIN bay-union masks on the stride-4 (36x64)
grid used by the region decoders, then bilinear upsampling and a 0.5 threshold, by
itself lose enough of the target to explain the ~0.53 ACPDS DEVELOPMENT IoU?
Only SRC-DS-021 TRAIN records are opened. DEVELOPMENT/TEST are never opened.
This is NOT model accuracy, NOT a prediction on unseen images and NOT a proven
upper bound; it is one fixed interpolation reconstruction of labels.
"""
import ast
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.mask_reconstruction import reconstruct  # noqa: E402

MANIFEST = 'data/processed/acpds_region_v1/ACPDS-REGION-DATA-20261027T101700848553Z/manifest.json'
MANIFEST_SHA = '84e99f49e42488985bea490c8ca8ce230dff844830c1f5a01eb9365c004e5937'
PKLOT_REFERENCE = 'experiments/results/REGION-FPN-V1-20261027T061402381508Z/posthoc_train_diagnostic.json'
SEED, SAMPLE, FACTOR, THRESHOLD = 187, 32, 4, .5
DEV_INTERPRETATION_REFERENCE = dict(
    value=0.5336515113242111, source='region_detail_guarded best recorded ACPDS DEV mean IoU (already reported)',
    use='interpretation only after the fact;never used to choose sample, grid, mode or threshold')
DECISION_RULE = dict(
    not_dominant='mean_valid_iou>=0.85: stride-4 target representation is NOT the dominant ACPDS limit;do not start a finer-output training hypothesis on this basis',
    supports='mean_valid_iou<0.70: supports one finer-resolution output-representation training hypothesis',
    partial='otherwise: representation contributes but does not explain the gap;no training hypothesis selected from this diagnostic alone')
CODE = ['scripts/diagnose_acpds_target_representation.py', 'src/smart_parking/mask_reconstruction.py',
        'src/smart_parking/region_validity.py', 'tests/test_mask_reconstruction.py']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def valid_mask_metrics():
    """Load the project metric without importing torch (function is pure NumPy)."""
    src = (ROOT / 'src/smart_parking/region_validity.py').read_text(encoding='utf-8')
    node = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'valid_mask_metrics'][0]
    ns = {'np': np}
    exec(ast.get_source_segment(src, node), ns)
    return ns['valid_mask_metrics']


def select(records):
    train = sorted((r for r in records if r['role'] == 'train' and r['source_id'] == 'SRC-DS-021'), key=lambda r: r['index'])
    chosen = np.random.default_rng(SEED).choice(len(train), size=SAMPLE, replace=False)
    return [train[i] for i in sorted(chosen.tolist())], len(train)


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_id = 'ACPDS-TARGET-REPRESENTATION-' + stamp
    for previous in (ROOT / 'experiments/results').glob('ACPDS-TARGET-REPRESENTATION-*/run.json'):
        raise SystemExit('Completed diagnostic exists (%s);refusing rerun for counts' % previous.parent.name)
    out = ROOT / 'experiments/results' / run_id
    out.mkdir(parents=True, exist_ok=False)
    state_path = ROOT / 'data/automation_state.json'
    state = read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert digest(ROOT / MANIFEST) == MANIFEST_SHA
    manifest = read(ROOT / MANIFEST)
    chosen, pool = select(manifest['records'])
    assert pool == 231 and all(r['role'] == 'train' and r['publisher_role'] == 'train' for r in chosen)
    protocol = dict(run_id=run_id, sealed_at=datetime.now(timezone.utc).isoformat(), seed=SEED, sample=SAMPLE,
                    train_pool=pool, source_ids=['SRC-DS-021'], dataset_manifest=MANIFEST, manifest_sha256=MANIFEST_SHA,
                    selected=[dict(index=r['index'], name=r['name'], cache=r['cache'], cache_sha256=r['cache_sha256']) for r in chosen],
                    representation=dict(grid=[36, 64], factor=FACTOR, down='area(exact 4x4 mean)', up='bilinear align_corners=False',
                                        threshold=THRESHOLD, full=[144, 256]),
                    validity='Score nonpadding pixels only via project valid_mask_metrics;letterbox offset 32px is a multiple of 4 so no coarse cell mixes padding and image horizontally',
                    decision_rule=DECISION_RULE, dev_interpretation_reference=DEV_INTERPRETATION_REFERENCE,
                    pklot_reference=dict(path=PKLOT_REFERENCE, sha256=digest(ROOT / PKLOT_REFERENCE)),
                    code_sha256={c: digest(ROOT / c) for c in CODE}, grids_or_retuning=False,
                    forbidden=['ACPDS DEVELOPMENT pixels', 'ACPDS TEST (closed)', 'Singapore final (consumed)', 'raw images'],
                    scope='Label-only interpolation reconstruction;not model accuracy or upper bound')
    dump(out / 'protocol.json', protocol)
    protocol_sha = digest(out / 'protocol.json')
    state['active_validation_jobs'] = [dict(run_id=run_id, pid=os.getpid(), maximum_seconds=120)]
    dump(state_path, state)
    started = datetime.now(timezone.utc).isoformat(); t0 = time.perf_counter()
    try:
        opened = []; masks = []; valid = []
        for r in chosen:
            path = ROOT / r['cache']
            assert path.parent == (ROOT / MANIFEST).parent and digest(path) == r['cache_sha256']
            with np.load(path, allow_pickle=False) as z:
                masks.append(z['mask'].copy()); valid.append(z['valid'].copy())
            opened.append(r['cache'])
        masks = np.stack(masks); valid = np.stack(valid)
        assert not np.any(masks & ~valid)
        rebuilt = reconstruct(masks, FACTOR, THRESHOLD)
        metric = valid_mask_metrics()(rebuilt, masks, valid)
        lost = (masks & ~rebuilt & valid).sum((1, 2)); added = (rebuilt & ~masks & valid).sum((1, 2))
        # errors within 2 px of the padding edge (bilinear blends padding-cell zeros there)
        edge = np.zeros_like(valid[0]); cols = np.where(valid[0].any(0))[0]
        edge[:, cols[0]:cols[0] + 2] = True; edge[:, cols[-1] - 1:cols[-1] + 1] = True
        edge_errors = ((rebuilt ^ masks) & valid & edge).sum((1, 2))
        bay_px = [r['target_pixels'] / r['slots'] for r in chosen]
        patterns = len({hashlib.sha256(m.tobytes()).hexdigest() for m in masks})
        for row, r, a, b, e, s in zip(metric['per_image'], chosen, lost, added, edge_errors, bay_px):
            row.update(name=r['name'], foreground_pixels=int(r['target_pixels']), slots=r['slots'], mean_pixels_per_bay=s,
                       false_negative_pixels=int(a), false_positive_pixels=int(b), padding_edge_error_pixels=int(e))
        iou = np.array([p['iou'] for p in metric['per_image']]); fg = np.array([p['foreground_pixels'] for p in metric['per_image']])
        bays = np.array(bay_px)
        R = metric['mean_image_iou']
        verdict = 'not_dominant' if R >= .85 else ('supports' if R < .70 else 'partial')
        pk = read(ROOT / PKLOT_REFERENCE)['train_reconstruction']
        duration = time.perf_counter() - t0
        result = dict(run_id=run_id, started_at=started, finished_at=datetime.now(timezone.utc).isoformat(), duration_seconds=duration,
                      protocol_sha256=protocol_sha, seed=SEED, images=len(chosen), distinct_mask_patterns=patterns, independent_views=len({r['camera_id'] for r in chosen}),
                      reconstruction=metric,
                      summary=dict(mean_valid_iou=R, median_valid_iou=float(np.median(iou)), minimum_valid_iou=metric['minimum_image_iou'],
                                   mean_valid_dice=metric['mean_image_dice'], false_negative_pixels=int(lost.sum()), false_positive_pixels=int(added.sum()),
                                   padding_edge_error_share=float(edge_errors.sum() / max(1, int(lost.sum() + added.sum()))),
                                   mean_pixels_per_bay=float(bays.mean()), median_pixels_per_bay=float(np.median(bays)), coarse_cell_pixels=FACTOR * FACTOR,
                                   spearman_like_corr_iou_vs_bay_pixels=float(np.corrcoef(np.argsort(np.argsort(iou)), np.argsort(np.argsort(bays)))[0, 1]),
                                   corr_iou_vs_foreground=float(np.corrcoef(iou, fg)[0, 1])),
                      pklot_train_reference=dict(mean_image_iou=pk['mean_image_iou'], macro_camera_iou=pk['macro_camera_iou'], images=pk['images'],
                                                 note='Same scheme, 200 PKLot TRAIN masks, no padding;reproduced exactly by the NumPy port before this run'),
                      dev_interpretation_reference=DEV_INTERPRETATION_REFERENCE, verdict=verdict, verdict_text=DECISION_RULE[verdict],
                      gap_to_dev_reference=R - DEV_INTERPRETATION_REFERENCE['value'],
                      opened_files=opened, development_or_test_opened=False, models_trained=0, model_calls=0,
                      environment=dict(python=platform.python_version(), numpy=np.__version__, machine='Cowork Linux VM on user laptop (CPU)'),
                      limitations='32 of 231 TRAIN masks;union-of-bay-polygon target (partial labels, outside union unverified);one fixed scheme;'
                                  'learned decoders may represent sub-cell detail better or worse than bilinear;DEV reference reused and not independent.')
        dump(out / 'run.json', result)
        print(json.dumps(dict(run_id=run_id, verdict=verdict, **result['summary']), indent=1))
        return run_id
    finally:
        s = read(state_path); s['active_validation_jobs'] = []; dump(state_path, s)


if __name__ == '__main__':
    main()
