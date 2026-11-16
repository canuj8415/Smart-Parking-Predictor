"""PERF-01 CPU benchmark: model loading, per-image latency (median/p95), FPS, throughput and peak RSS.

Inputs are TRAIN-split only: 10 PKLot TRAIN frames with their original slot layouts (full app
pipeline: detector + PKLot occupancy classifier + slot assignment) and 32 ACPDS TRAIN region
caches (frozen ResNet18 + existing mixed region decoder). Timing only; no accuracy is computed,
no DEV/TEST/final data are opened. Run with nothing else heavy on the CPU.

  python scripts/benchmark_performance.py
"""
import csv, hashlib, json, platform, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def summary(times):
    t = sorted(times)
    p95 = t[min(len(t) - 1, int(np.ceil(.95 * len(t))) - 1)]
    med = statistics.median(t)
    return dict(n=len(t), median_seconds=med, p95_seconds=p95, mean_seconds=statistics.fmean(t), fps_at_median=1 / med)


def main():
    import psutil, torch
    from PIL import Image
    from smart_parking.vision import VisionEngine
    from smart_parking.layout import load_layout
    from smart_parking.region_fpn import FrozenRegionEncoder, RegionPyramidDecoder
    proc = psutil.Process(); peak = [proc.memory_info().rss]
    def mark(): peak.append(proc.memory_info().rss)
    rid = 'PERF-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'experiments/results' / rid; out.mkdir(parents=True, exist_ok=False)
    frames = [r for r in csv.DictReader(open(ROOT / 'data/manifests/pklot_frames.csv', encoding='utf-8')) if r['split'] == 'train' and r['layout_path']][:10]
    for f in frames:
        assert digest(ROOT / f['image']) == f['image_sha256']
    report = dict(run_id=rid, started_at=datetime.now(timezone.utc).isoformat(), inputs=dict(pklot_train_frames=[f['image'] for f in frames]),
                  environment=dict(python=platform.python_version(), torch=torch.__version__, threads=torch.get_num_threads(),
                                   cpu=platform.processor(), machine=platform.machine(), system=platform.platform()))
    pipeline = {}
    for kind in ('fasterrcnn', 'maskrcnn'):
        t0 = time.perf_counter(); engine = VisionEngine(kind); load = time.perf_counter() - t0; mark()
        images = [Image.open(ROOT / f['image']).convert('RGB') for f in frames]
        layouts = [load_layout(ROOT / f['layout_path'], im.size) for f, im in zip(frames, images)]
        engine.analyze(images[0], layouts[0]); mark()  # warm-up, excluded
        times = []; model_times = []
        t_all = time.perf_counter()
        for im, lay in zip(images, layouts):
            t = time.perf_counter(); result, _ = engine.analyze(im, lay); times.append(time.perf_counter() - t)
            model_times.append(result['latency_seconds']); mark()
        wall = time.perf_counter() - t_all
        pipeline[kind] = dict(load_seconds=load, end_to_end=summary(times), model_reported=summary(model_times),
                              throughput_images_per_second=len(times) / wall, image_size=list(images[0].size), slots_per_image=len(layouts[0]['slots']))
        del engine
    report['app_pipeline'] = pipeline
    man = json.loads((ROOT / 'models/acpds_region_dataset.json').read_text(encoding='utf-8'))
    recs = [r for r in json.loads((ROOT / man['manifest']).read_text(encoding='utf-8'))['records'] if r['role'] == 'train'][:32]
    rgb = []
    for r in recs:
        assert digest(ROOT / r['cache']) == r['cache_sha256']
        with np.load(ROOT / r['cache'], allow_pickle=False) as z:
            rgb.append(z['rgb'].copy())
    ck = json.loads((ROOT / 'models/region_mixed.json').read_text(encoding='utf-8'))['checkpoints']['mixed']
    assert digest(ROOT / ck['path']) == ck['sha256']
    t0 = time.perf_counter()
    enc = FrozenRegionEncoder(torch.load(ROOT / 'models/pretrained/resnet18_imagenet.pth', map_location='cpu', weights_only=True))
    dec = RegionPyramidDecoder(); dec.load_state_dict(torch.load(ROOT / ck['path'], map_location='cpu', weights_only=True)['state_dict']); dec.eval()
    load = time.perf_counter() - t0; mark()
    mean = torch.tensor([.485, .456, .406])[None, :, None, None]; std = torch.tensor([.229, .224, .225])[None, :, None, None]
    times = []
    with torch.inference_mode():
        x0 = (torch.from_numpy(rgb[0][None]).permute(0, 3, 1, 2).float() / 255 - mean) / std; dec(enc(x0))
        for a in rgb:
            t = time.perf_counter(); x = (torch.from_numpy(a[None]).permute(0, 3, 1, 2).float() / 255 - mean) / std
            dec(enc(x)).sigmoid(); times.append(time.perf_counter() - t); mark()
    report['region_model'] = dict(checkpoint=ck['path'], load_seconds=load, input_size=[256, 144], per_image=summary(times), acpds_train_images=len(rgb))
    report['peak_sampled_RSS_bytes'] = max(peak)
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['scope'] = 'CPU timing on this laptop only;TRAIN-split inputs;no accuracy;not a deployment guarantee'
    (out / 'run.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['run_id', 'app_pipeline', 'region_model', 'peak_sampled_RSS_bytes']}, indent=1))


if __name__ == '__main__':
    main()
