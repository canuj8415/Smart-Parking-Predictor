# Faster preparation without changing model inputs

The existing parking crop draws a full-image polygon mask, pastes a full-image
RGB copy over grey, crops the space's bounding box, and resizes to 96 by 96.
For the new 4,000 by 3,000 photographs, those full RGB copies dominate much of
the preparation work. Changing that work must preserve the exact input bytes.

| Method | Polygon mask | RGB paste | Qualification |
|---|---|---|---|
| Existing `layout.crop_slot` | Original full canvas | Full canvas | Reference; unchanged |
| `local_crops.crop_slot_local` | Translated into the local box | Local box | Rejected on a real development crop |
| `exact_crops.crop_slot_exact` | Original full canvas, then cropped | Local box | Requires completed equivalence/performance report |

The first candidate passed five unit tests and 2,000 seeded synthetic fixtures.
The real-data check nevertheless found seven differing RGB channel values in
GOPR6550.JPG, slot 9. Moving the polygon into a smaller drawing canvas changed
the raster for that observed geometry. The failed source, protocol, traceback,
partial proofs and result remain preserved. Do not use that candidate for model
inputs. A regression test now reproduces the discrepancy using the same training
polygon on a synthetic constant-colour image.

The revised method keeps the original full-size mask. It crops both that mask
and the original RGB image to the same box before pasting over a grey box.
Each pixel therefore uses the original mask decision at the original image
coordinate. The resize step is unchanged. This avoids the full-image RGB paste
while retaining the full-image mask allocation; it does not eliminate all
full-image work.

The sealed version-2 protocol compares all 9,746 spaces in the 266 admitted
development images and a separate 2,000-case synthetic fixture suite. The two
functions alternate which runs first. Timers surround only crop calls; decoding,
hashing and cache encoding are excluded. Every output must have identical bytes,
every cache must round-trip exactly, bindings must remain unchanged, and the
reference-to-revised crop-time ratio must reach two. Local timings describe
this process and environment, rather than deployment or full inference speed.

Only a passing completed run publishes `reports/acpds_exact_crop_cache_latest.json`.
The cache has separate TRAIN and validation roles, explicit binary labels,
original image/layout hashes and a SHA256 for every RGB crop and file. Each
completed image has a proof file so a bounded invocation can resume. A partial
cache is not an accepted dataset. The failed version-1 cache is not reused.

The two candidates are distinct implementation-validation trials. Individual
polygons, synthetic cases, unit tests and cache files are not recorded runs.
The first rejection counts as a failed completed trial, even though its runner
initially saved the exception in a file called `interrupted.json`; the separate
`run.json` explains that outcome and preserves the original error log.

No neural model is evaluated here. Pixel equality does not establish parking
accuracy, correct geometry for another camera, semantic parking-area labels or
universal correctness on all possible inputs. The helpers require finite,
image-bounded RGB polygons. All source TEST images/labels and earlier consumed
final cohorts remain closed. The original application function stays unchanged.

This cache supports a later bounded representation-adaptation experiment with
the same model inputs. Such an experiment still needs its own fixed selection
and retention gates; a faster cache cannot qualify a model that failed readiness.

## 27 October 2026 IST / rejected raster translation and exact crop-cache validation

Completed revised trial EXACT-CROP-CACHE-V2-20261027T001729204282Z has zero byte mismatches on 9,746 real crops and 2,000 synthetic fixtures. The measured crop-time ratio is 12.96; implementation gate=True. Full evidence:models/exact_crop_cache_validation.json. Rejected V1:models/exact_crop_cache_v1_failed.json. No production helper or scientific result changed.
