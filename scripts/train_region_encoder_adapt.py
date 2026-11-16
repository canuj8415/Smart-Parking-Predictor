"""Sealed paired encoder-adaptation region trial (ResNet18 layer3/4 vs frozen control).

Controlled change: ONLY the encoder (frozen vs layer3/layer4 convolutions adapted, BatchNorm
frozen, encoder LR = decoder LR/10). Both arms share the REGION-MIXED records, the same mixed
PKLot+ACPDS TRAIN schedule, the same initial decoder, update counts, loss, class weight,
selection rule and gates. DEV is the previously exposed development set (NOT independent);
no final/TEST access; never promoted by this script.

  python scripts/train_region_encoder_adapt.py --smoke         # tiny unrecorded crash check under outputs/smoke
  python scripts/train_region_encoder_adapt.py --seal-and-run  # seal protocol, then run the recorded trial
  python scripts/train_region_encoder_adapt.py --run <protocol.json>   # resume a sealed protocol
"""
import argparse, copy, csv, hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
MIXED = 'experiments/results/REGION-MIXED-20261027T112422539381Z/protocol.json'


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p, v): Path(p).write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare(smoke=False):
    state = read(ROOT / 'data/automation_state.json')
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    now = datetime.now(timezone.utc)
    rid = ('SMOKE-' if smoke else '') + 'REGION-ENCODER-ADAPT-' + now.strftime('%Y%m%dT%H%M%S%fZ')
    if not smoke:
        for prev in (ROOT / 'experiments/results').glob('REGION-ENCODER-ADAPT-*/run.json'):
            raise SystemExit('Completed encoder-adaptation trial exists: ' + prev.parent.name)
    base = (ROOT / 'outputs/smoke') if smoke else (ROOT / 'experiments/results')
    out = base / rid
    out.mkdir(parents=True, exist_ok=False)
    mixed = read(ROOT / MIXED)
    records = mixed['records']
    inputs = [MIXED, 'models/region_dataset_v2.json', 'models/acpds_region_dataset.json', 'models/pklot_current_role_ledger.json',
              'models/region_mixed.json', 'models/region_fpn_duration.json', 'models/pretrained/resnet18_imagenet.pth', 'data/source_manifest.csv']
    code = ['scripts/train_region_encoder_adapt.py', 'src/smart_parking/region_adapt.py', 'tests/test_region_adapt.py',
            'src/smart_parking/region_mixed.py', 'src/smart_parking/region_validity.py', 'src/smart_parking/region_fpn.py']
    protected = dict(mixed['protected_hashes'])
    for v in read(ROOT / 'models/region_mixed.json')['checkpoints'].values():
        protected[v['path']] = v['sha256']
    p = dict(
        run_id=rid, prepared_at=now.isoformat(), smoke=smoke, seed=189, sampler_seed=190,
        hypothesis='Adapting ResNet18 layer3/layer4 (BN frozen) improves ACPDS mean DEV IoU by >=.05 versus a matched frozen-encoder '
                   'control on the same mixed TRAIN schedule, without material PKLot regression; absolute gates also required.',
        motivation='Trial116: stride4 target representation not limiting (.966); trial117: frozen ImageNet features weakly linearly '
                   'separable on ACPDS TRAIN (.305) -> sealed verdict insufficient.',
        source_ids=['SRC-DS-001', 'SRC-DS-021', 'SRC-MOD-003'], records=records,
        source_hashes={f: digest(ROOT / f) for f in code}, input_hashes={f: digest(ROOT / f) for f in inputs},
        protected_hashes=protected, cache_hashes={r['cache']: r['cache_sha256'] for r in records},
        architecture='ImageNet ResNet18 scales1-4 + 32channel additive FPN decoder; control encoder frozen; candidate layer3/layer4 '
                     'conv weights trainable, BN eval+frozen',
        normalization=dict(mean=[.485, .456, .406], std=[.229, .224, .225]), pretrained='models/pretrained/resnet18_imagenet.pth',
        optimizer='AdamW', learning_rate=.001, encoder_learning_rate=.0001, weight_decay=.0001, batch_size=8,
        maximum_rounds=1 if smoke else 32, steps_per_round=2 if smoke else 25, patience_rounds=6, selection_minimum_improvement=.001,
        selection='Both arms maximize equal-source (.5 PKLot macro-camera IoU + .5 ACPDS mean-image IoU) on reused DEV, earliest on ties; '
                  'shared early stop only if BOTH arms stale 6 rounds',
        sampling='Both arms use the identical mixed schedule from paired_schedule(PKLot200, ACPDS231, rounds, seed190): '
                 '4 PKLot + 4 ACPDS per batch; no DEV sampling',
        controlled_change='Encoder only: frozen vs layer3/4 adapted (encoder LR 1e-4); all else identical',
        loss='masked_bay_loss; class weight from PKLot TRAIN valid pixels only, fixed for both arms', threshold=.5, augmentation='None',
        threads=4, maximum_seconds=900 if smoke else 5400, maximum_RSS_bytes=4000000000,
        relative_gates=mixed['relative_gates'], absolute_gates=mixed['absolute_gates'],
        source_scope=mixed['source_scope'] + ' DEV reused across many trials; not independent evidence.',
        final_access=False, production_promotion=False,
        run_definition='One completed recorded two-arm matched experiment, not two runs')
    dump(out / 'protocol.json', p)
    dump(out / 'protocol_binding.json', dict(sha256=digest(out / 'protocol.json')))
    print(out / 'protocol.json', flush=True)
    return out / 'protocol.json'


def run(path):
    import numpy as np
    import psutil
    import torch
    from smart_parking.region_fpn import FrozenRegionEncoder, RegionPyramidDecoder, mask_metrics
    from smart_parking.region_adapt import AdaptableRegionEncoder
    from smart_parking.region_validity import masked_bay_loss, valid_mask_metrics
    from smart_parking.region_mixed import paired_schedule, source_balanced_score, retention_checks
    path = Path(path).resolve(); out = path.parent; p = read(path); smoke = p['smoke']
    assert out.is_relative_to((ROOT / ('outputs/smoke' if smoke else 'experiments/results')).resolve()) and not (out / 'run.json').exists()
    assert digest(path) == read(out / 'protocol_binding.json')['sha256']
    assert p['source_hashes'][Path(__file__).resolve().relative_to(ROOT).as_posix()] == digest(__file__)
    bound = {**p['source_hashes'], **p['input_hashes'], **p['protected_hashes'], **p['cache_hashes']}
    for f, e in bound.items():
        assert digest(ROOT / f) == e, f
    sp = ROOT / 'data/automation_state.json'
    if not smoke:
        state = read(sp); assert not state['active_training_jobs'] and not state['active_validation_jobs']
        state['active_training_jobs'] = [dict(run_id=p['run_id'], pid=os.getpid(), phase='Paired encoder-adaptation experiment',
                                              maximum_seconds=p['maximum_seconds'], cancel_file=(out / 'CANCEL').relative_to(ROOT).as_posix(),
                                              resume_command='scripts/train_region_encoder_adapt.py --run ' + path.relative_to(ROOT).as_posix())]
        dump(sp, state)
    ckdir = (out / 'checkpoints') if smoke else (ROOT / 'models/checkpoints/region_encoder_adapt' / p['run_id'])
    ckdir.mkdir(parents=True, exist_ok=True)
    records = p['records']; allowed = {(ROOT / r['cache']).resolve() for r in records}; forbidden = []

    def audit(event, args):
        if event.startswith('socket.'):
            forbidden.append(event); raise PermissionError('Offline trainer')
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            q = Path(os.fsdecode(args[0])).resolve()
            if q.is_relative_to(ROOT / 'data/raw') or (q.suffix.casefold() in {'.jpg', '.jpeg', '.png', '.xml', '.npz', '.npy'}
                                                       and q not in allowed and not q.is_relative_to(out)):
                forbidden.append(str(q)); raise PermissionError('Raw/final/unadmitted source access blocked')
    sys.addaudithook(audit)
    started = datetime.now(timezone.utc).isoformat(); clock = time.perf_counter(); proc = psutil.Process(); peak = 0

    def boundary():
        nonlocal peak
        peak = max(peak, proc.memory_info().rss)
        if (out / 'CANCEL').exists() or time.perf_counter() - clock > p['maximum_seconds'] or peak > p['maximum_RSS_bytes']:
            raise InterruptedError('Cancel/deadline/RSS bound reached; checkpoint retained')

    def save(dest, value):
        tmp = dest.with_suffix(dest.suffix + '.partial'); torch.save(value, tmp); os.replace(tmp, dest)

    def thash(module):
        h = hashlib.sha256()
        for n, v in module.state_dict().items():
            h.update(n.encode()); h.update(v.detach().contiguous().numpy().tobytes())
        return h.hexdigest()
    try:
        torch.set_num_threads(p['threads']); torch.use_deterministic_algorithms(True); torch.manual_seed(p['seed'])
        assert len(records) == 496 and len(allowed) == 496
        rgb = []; masks = []; valid = []
        for row in records:
            boundary()
            with np.load(ROOT / row['cache'], allow_pickle=False) as d:
                a = d['rgb'].copy(); b = d['mask'].copy()
                v = d['valid'].copy() if row['study_source'] == 'acpds' else np.ones_like(b, dtype=np.bool_)
            assert a.shape == (144, 256, 3) and b.shape == (144, 256) and not np.any(b & ~v)
            rgb.append(a); masks.append(b); valid.append(v)
        rgb = np.stack(rgb); masks = np.stack(masks); valid = np.stack(valid)

        def idx(s, r): return np.array([i for i, x in enumerate(records) if x['study_source'] == s and x['role'] == r], dtype=np.int64)
        pk = idx('pklot', 'train'); ac = idx('acpds', 'train'); pd = idx('pklot', 'development'); ad = idx('acpds', 'development')
        assert [len(v) for v in [pk, ac, pd, ad]] == [200, 231, 30, 35]
        _, schedule = paired_schedule(pk, ac, p['maximum_rounds'], p['sampler_seed'])
        sched_hash = hashlib.sha256(schedule.tobytes()).hexdigest()
        np.savez_compressed(out / 'schedule.npz', mixed=schedule)
        y = torch.from_numpy(masks[:, None].astype('float32')); support = torch.from_numpy(valid[:, None])
        positive = y[pk].sum() / support[pk].sum(); weight = ((1 - positive) / positive).detach()
        mean = torch.tensor(p['normalization']['mean'])[None, :, None, None]; std = torch.tensor(p['normalization']['std'])[None, :, None, None]

        def image(batch): return (torch.from_numpy(rgb[batch]).permute(0, 3, 1, 2).float() / 255 - mean) / std
        weights = torch.load(ROOT / p['pretrained'], map_location='cpu', weights_only=True)
        frozen = FrozenRegionEncoder(weights); frozen_hash = thash(frozen)
        adapt = AdaptableRegionEncoder(weights); assert thash(adapt.backbone) == thash(frozen.backbone)
        features = None
        for batch in np.array_split(np.arange(496), 62):
            boundary(); vals = frozen(image(batch))
            if features is None:
                features = tuple(torch.empty((496, *v.shape[1:]), dtype=v.dtype) for v in vals)
            for s, v in zip(features, vals):
                s[batch] = v
        first = RegionPyramidDecoder(); decoders = {'control': first, 'candidate': copy.deepcopy(first)}
        init_hash = {k: thash(m) for k, m in decoders.items()}; assert len(set(init_hash.values())) == 1
        opts = {'control': torch.optim.AdamW(decoders['control'].parameters(), lr=p['learning_rate'], weight_decay=p['weight_decay']),
                'candidate': torch.optim.AdamW([dict(params=decoders['candidate'].parameters(), lr=p['learning_rate']),
                                                dict(params=adapt.trainable_parameters(), lr=p['encoder_learning_rate'])],
                                               weight_decay=p['weight_decay'])}

        def feats(name, batch): return tuple(f[batch] for f in features) if name == 'control' else adapt(image(batch))
        T = dict(round=0, cursor=0, loss_sum={k: 0. for k in decoders}, curves=[], best={k: dict(score=-1., path=None, stale=0) for k in decoders})
        last = ckdir / 'last.pt'
        if last.exists():
            s = torch.load(last, map_location='cpu', weights_only=True)
            assert s['protocol_sha256'] == digest(path) and s['schedule_hash'] == sched_hash
            for k in decoders:
                decoders[k].load_state_dict(s['decoders'][k]); opts[k].load_state_dict(s['optimizers'][k])
            adapt.load_state_dict(s['encoder']); T = s['training']; torch.random.set_rng_state(s['rng_state'])

        def checkpoint():
            save(last, dict(protocol_sha256=digest(path), schedule_hash=sched_hash, decoders={k: v.state_dict() for k, v in decoders.items()},
                            encoder=adapt.state_dict(), optimizers={k: v.state_dict() for k, v in opts.items()}, training=T,
                            rng_state=torch.random.get_rng_state()))
        dev = np.concatenate([pd, ad]); cams = [records[i]['camera_id'] for i in pd]

        def evaluate(name):
            decoders[name].eval(); adapt.train(False); prob = []
            with torch.no_grad():
                for b in np.array_split(dev, (len(dev) + 7) // 8):
                    boundary(); prob.append(decoders[name](feats(name, b)).sigmoid()[:, 0].numpy())
            prob = np.concatenate(prob)
            return dict(pklot=mask_metrics(prob[:30] >= .5, masks[pd], cams),
                        acpds=valid_mask_metrics(prob[30:] >= .5, masks[ad], valid[ad])), prob
        while T['round'] < p['maximum_rounds'] and not all(v['stale'] >= p['patience_rounds'] for v in T['best'].values()):
            while T['cursor'] < p['steps_per_round']:
                boundary(); batch = schedule[T['round'], T['cursor']]
                for name, dec in decoders.items():
                    dec.train(); adapt.train(name == 'candidate'); opts[name].zero_grad(set_to_none=True)
                    loss = masked_bay_loss(dec(feats(name, batch)), y[batch], support[batch], weight)
                    assert torch.isfinite(loss); loss.backward(); opts[name].step(); T['loss_sum'][name] += float(loss.detach())
                T['cursor'] += 1; checkpoint()
            curve = dict(round=T['round'] + 1, updates_per_arm=(T['round'] + 1) * p['steps_per_round'])
            for name in decoders:
                m, _ = evaluate(name); score = source_balanced_score(m['pklot'], m['acpds']); best = T['best'][name]
                better = score > best['score'] + p['selection_minimum_improvement']
                curve[name] = dict(training_loss=T['loss_sum'][name] / p['steps_per_round'], selection_score=score,
                                   pklot_macro_iou=m['pklot']['macro_camera_iou'], acpds_mean_iou=m['acpds']['mean_image_iou'], selected=better)
                if better:
                    dest = ckdir / (name + '_round_' + str(curve['round']) + '_' + datetime.now(timezone.utc).strftime('%H%M%S%f') + '.pt')
                    assert not dest.exists()
                    save(dest, dict(run_id=p['run_id'], protocol_sha256=digest(path), arm=name, round=curve['round'], updates=curve['updates_per_arm'],
                                    decoder_state_dict=decoders[name].state_dict(),
                                    encoder_state_dict=adapt.state_dict() if name == 'candidate' else None,
                                    width=32, input_size=[256, 144], normalization=p['normalization'], threshold=.5,
                                    pretrained=p['pretrained'], metrics=m))
                    best.update(score=score, path=dest.relative_to(ROOT).as_posix(), stale=0)
                else:
                    best['stale'] += 1
            T['curves'].append(curve); T['round'] += 1; T['cursor'] = 0; T['loss_sum'] = {k: 0. for k in decoders}
            checkpoint(); dump(out / 'curves.json', T['curves']); print(json.dumps(curve), flush=True)
        results = {}; ck = {}
        for name in decoders:
            b = torch.load(ROOT / T['best'][name]['path'], map_location='cpu', weights_only=True)
            decoders[name].load_state_dict(b['decoder_state_dict'])
            if name == 'candidate':
                adapt.load_state_dict(b['encoder_state_dict'])
            m, _ = evaluate(name)
            assert abs(source_balanced_score(m['pklot'], m['acpds']) - T['best'][name]['score']) < 1e-12
            results[name] = m
            ck[name] = dict(path=T['best'][name]['path'], sha256=digest(ROOT / T['best'][name]['path']),
                            selected_round=b['round'], selected_updates=b['updates'])
        relative = retention_checks(results['candidate'], results['control'], p['relative_gates'])
        ref = read(ROOT / 'models/region_fpn_duration.json'); g = p['absolute_gates']; absolute = {}
        for name, m in results.items():
            k = m['pklot']; a = m['acpds']; prev = ref['candidate']; orig = ref['original']; tmpl = ref['conditional_train_template']
            absolute[name] = dict(
                pklot_macro=k['macro_camera_iou'] >= g['pklot_macro'],
                pklot_every_camera=min(v['mean_iou'] for v in k['by_camera'].values()) >= g['pklot_camera'],
                pklot_every_image=k['minimum_image_iou'] >= g['pklot_image'],
                acpds_mean=a['mean_image_iou'] >= g['acpds_mean'], acpds_every_image=a['minimum_image_iou'] >= g['acpds_image'],
                gain_over_original=k['macro_camera_iou'] >= orig['macro_camera_iou'] + g['gain_over_original'],
                no_original_camera_regression=all(k['by_camera'][c]['mean_iou'] >= v['mean_iou'] - g['original_camera_regression'] for c, v in orig['by_camera'].items()),
                no_template_camera_regression=all(k['by_camera'][c]['mean_iou'] >= v['mean_iou'] - g['template_camera_regression'] for c, v in tmpl['by_camera'].items()),
                previous_coarse_macro_retained=k['macro_camera_iou'] >= prev['macro_camera_iou'] - g['previous_coarse_macro_regression'],
                previous_coarse_cameras_retained=all(k['by_camera'][c]['mean_iou'] >= v['mean_iou'] - g['previous_coarse_camera_regression'] for c, v in prev['by_camera'].items()),
                previous_coarse_images_retained=all(x['iou'] >= z['iou'] - g['previous_coarse_image_regression'] for x, z in zip(k['per_image'], prev['per_image'])))
        assert not forbidden and thash(frozen) == frozen_hash
        for f, e in bound.items():
            assert digest(ROOT / f) == e, f
        finished = datetime.now(timezone.utc).isoformat()
        report = dict(run_id=p['run_id'], smoke=smoke, started_at=started, finished_at=finished,
                      duration_seconds_this_invocation=time.perf_counter() - clock, peak_sampled_process_RSS_bytes=peak,
                      seed=p['seed'], sampler_seed=p['sampler_seed'], protocol_sha256=digest(path), models_trained=2,
                      completed_rounds=T['round'], updates_per_arm=T['round'] * p['steps_per_round'],
                      shared_early_stop=T['round'] < p['maximum_rounds'], checkpoints=ck, results=results,
                      relative_checks=relative, absolute_checks=absolute,
                      development_gate_passed=all(relative.values()) and all(absolute['candidate'].values()), production_promoted=False,
                      curves=T['curves'], initial_decoder_hashes=init_hash, frozen_encoder_unchanged=True, positive_weight=float(weight),
                      schedule_hash=sched_hash, normal_forbidden_accesses=list(forbidden), source_ids=p['source_ids'],
                      final_pixels_or_semantics_opened=False,
                      note='DEV reused across many trials; a passing gate would still need fresh qualified evidence before any promotion.')
        dump(out / 'run.json', report)
        if smoke:
            print('SMOKE OK', json.dumps({k: report[k] for k in ['completed_rounds', 'updates_per_arm', 'duration_seconds_this_invocation',
                                                                 'peak_sampled_process_RSS_bytes']}), flush=True)
            return
        dump(ROOT / 'models/region_encoder_adapt.json', report)
        dump(ROOT / 'reports/region_encoder_adapt_latest.json', dict(run_id=p['run_id'], result_path=(out / 'run.json').relative_to(ROOT).as_posix(),
                                                                    result_sha256=digest(out / 'run.json'), production_promoted=False))
        reg = ROOT / 'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig', newline='') as s:
            rd = csv.DictReader(s); fields = rd.fieldnames; existing = list(rd)
        assert not any(r['experiment_id'] == p['run_id'] for r in existing)
        entry = dict(experiment_id=p['run_id'], run_type='Paired encoder-adaptation region DEVELOPMENT training', started_at=started, finished_at=finished,
                     source_ids=';'.join(p['source_ids']), split_ids='PKLot200TRAIN/30DEV + ACPDS231TRAIN/35DEV(reused); all final closed',
                     configuration=path.relative_to(ROOT).as_posix(), architecture=p['architecture'], optimizer='AdamW',
                     learning_rate='decoder 1e-3; encoder layer3/4 1e-4', batch_size=8, random_seed=189, hardware='CPU',
                     execution_environment=sys.version.split()[0], training_duration=report['duration_seconds_this_invocation'],
                     evaluation_metrics=json.dumps(dict(results={k: dict(pklot_macro=v['pklot']['macro_camera_iou'], acpds_mean=v['acpds']['mean_image_iou'])
                                                                 for k, v in results.items()}, relative_checks=relative, absolute_checks=absolute)),
                     logs=out.relative_to(ROOT).as_posix(), checkpoints=json.dumps(ck), code_revision_basis='Sealed implementation/input/sampler hashes',
                     implementation_sha256=digest(__file__),
                     conclusions='Gate=' + str(report['development_gate_passed']) + '; one paired trial; DEV reused; no app promotion')
        with reg.open('a', encoding='utf-8', newline='') as s:
            csv.DictWriter(s, fieldnames=fields, lineterminator='\r\n').writerow({k: entry.get(k, '') for k in fields})
        state = read(sp); assert p['run_id'] not in state['completed_run_ids']; state['completed_run_ids'].append(p['run_id'])
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids'])); state['last_completed_run'] = p['run_id']
        state['region_encoder_adapt'] = report; dump(sp, state)
        print(json.dumps({k: report[k] for k in ['run_id', 'completed_rounds', 'updates_per_arm', 'relative_checks', 'development_gate_passed',
                                                 'duration_seconds_this_invocation']}), flush=True)
    except BaseException as error:
        dump(out / ('interrupted_' + datetime.now(timezone.utc).strftime('%H%M%S%f') + '.json'),
             dict(error=type(error).__name__, detail=str(error), completed_run_counted=False))
        raise
    finally:
        if not smoke:
            state = read(sp); state['active_training_jobs'] = []; dump(sp, state)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--run'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--seal-and-run', action='store_true'); a = ap.parse_args()
    if a.smoke:
        run(prepare(smoke=True))
    elif a.run:
        run(a.run)
    elif a.seal_and_run:
        run(prepare())
    else:
        prepare()
