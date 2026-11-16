# Native-detail crop development candidate

The candidate preserves original-video detail rather than enlarging an already reduced image. Its protocol was sealed in `experiments/results/UVG-TILES-20261026T141429817814Z/protocol.json` before crop inference. The completed result improves provided-positive recall and mask overlap but **fails admission**. This is development work on HighwayView, not a final evaluation or app promotion.

## Method and fixed comparison

The reference is the unchanged 960-internal-resolution study on the same 11 frames and 153 eligible car/truck observations. Its full-frame detections and masks are retained in their original order. Four fixed overlapping crops span the whole 3840×2160 publisher preview. Each crop covers 60% of source width and height and is resized to 960×540 before the unchanged model call. Thus a source object occupies about 1.67 times as many input pixels as in the full-frame view. The crop grid is independent of answer labels and camera-specific parking geometry.

Class rules, score and mask thresholds (0.5), and box matching IoU (0.5) remain unchanged. A crop detection touching an artificial interior crop edge within two input pixels is rejected as potentially partial; genuine outer source edges are retained. Proposals are considered in descending score with deterministic tile/index ties. Same-class crop duplicates with IoU ≥0.5 against a kept detection are suppressed. A higher-scoring crop never deletes a reference detection. Accepted masks are placed back on the declared common 960×540 grid using nearest-neighbour resizing and explicit offsets.

Seven software test cases include the declared tile extents, 50 seeded inverse-coordinate fixtures, bottom/right placement, artificial versus outer edges, boolean mask projection, invalid input rejection and preservation of full-frame detections. These are synthetic software fixtures, not real detector performance or extra scientific runs.

The experiment permits at most 88 crop model calls and 900 seconds, uses seed 141 and has a `CANCEL` file check between calls. Per-frame predictions, crop outputs, packed masks and progress are saved. Models run sequentially with no overlapping trainer. The reference full-frame inference is not repeated: its saved outputs are bound by hashes, and newly decoded native frames must reproduce the archived resized input pixels exactly.

## Frozen gates and interpretation

The original absolute gates remain: each detector must match at least 75% of the same eligible supplied positives, zero-inclusive Mask IoU must reach 0.5, and Mask recall must be within five percentage points of Faster. Additional gates require at least five percentage points of positive-recall gain per detector and at least 0.05 zero-inclusive Mask-IoU gain, per-frame/per-class non-regression, at least 95% retention of the 87 reference-matched masks, and at most 0.02 mean-IoU loss on those **same** reference objects.

The estimated model cost includes the cached full-frame reference cost plus actual crop model calls and must be at most six times the reference. This estimate excludes data preparation and does not establish deployment FPS. Runtime and call limits are operational limits, not scientific accuracy.

The frozen output-volume gate allows at most 22 additional predictions unassigned against the 153 eligible labels per detector. It is a conservative volume constraint, **not** a verified false-positive count or precision gate. Some added detections can correspond to the 41 supplied smaller objects outside that eligible subset. Both all-194 and eligible-153 results and unassigned counts must therefore be reported. Background truth remains unestablished. A failed gate must be preserved rather than relaxed after viewing outcomes.

Missing truth masks remain unknown rather than empty background or invented zero-IoU targets. The existing 11-frame reference has raster support for all 153 eligible objects; its five absent/vanished smaller masks remain outside that gate. Repeated observations from one short clip are correlated, and upstream pretraining overlap has not been audited. No parking-bay vacancy, automatic parking-region segmentation, exhaustive precision/mAP or independent final accuracy is measured here.

Original publisher assets, CC BY 4.0 attribution, source/licence records and failed experiments are preserved. Source IDs remain SRC-DS-019 and SRC-DOC-021; creator is Tampere University / Ultra Video Group, UVG-VCM, Partanen et al. (2026). The whole HighwayDrive sequence remains reserved and unopened. A passing development result alone would still require a frozen method and tested durable whole-sequence final controller before any final access.

## Actual measured outcome

The run completed 88 crop calls in 400.593 seconds. There was no training, parameter grid or repeated full-frame inference. All original detector weights, frozen Singapore methods, reference files and source reservations are unchanged.

| Measure | Full-frame 960 reference | Full frame plus native crops |
|---|---:|---:|
| Faster matches, same 153 eligible positives | 102 (66.67%) | 139 (90.85%) |
| Mask matches, same 153 eligible positives | 87 (56.86%) | 113 (73.86%) |
| Faster matches, all 194 supplied positives | 102 (52.58%) | 146 (75.26%) |
| Mask matches, all 194 supplied positives | 87 (44.85%) | 113 (58.25%) |
| Mask IoU, all 153 supported eligible targets | 0.467224 | 0.599371 |
| Mask IoU, same 87 reference-matched targets | 0.821670 | 0.823097 |
| Reference mask-match retention | — | 87/87 |
| Faster total predictions / eligible-unassigned | 185 / 83 | 266 / 127 |
| Mask total predictions / eligible-unassigned | 124 / 37 | 209 / 96 |

Every measured frame and both supplied classes retain or improve positive-recall counts. Faster class matches increase from 95 to 132 cars and remain 7 trucks; Mask matches increase from 84 to 107 cars and from 3 to 6 trucks. The original full-frame detections remain unchanged, and all 11 reference mask-array prefixes are bit-identical. Independent verification from archived packed masks reproduces all 153 candidate mask IoUs.

Three gates fail: Mask recall is below 75%, its recall trails Faster by more than five percentage points, and additional eligible-unassigned outputs exceed the frozen +22 limits (+44 Faster and +59 Mask). The gates are preserved. The same-87-mask non-regression, ≥95% retention, relative positive/overlap gain, per-frame/per-class and runtime gates pass. Estimated model cost is 4.949× reference for Faster and 4.756× for Mask, including the previously measured reference branch; these are not deployment frame rates.

Seven extra Faster matches concern smaller supplied objects outside the eligible subset. Thus the +44 eligible-unassigned increase includes seven such recovered labels. Even against all 194 labels, unassigned counts increase by 37 Faster and 59 Mask. These remaining unassigned outputs must not be silently classified as true or false: exhaustive background truth is unestablished.

### Descriptive known-nonroad check

After the frozen trial, a separate descriptive audit used the supplied train boxes on the same selected development frames. It counted road-labelled predictions overlapping a supplied train at box IoU ≥0.5. There are ten supplied train observations. Full-frame results contain 6 such Faster predictions on 6 frames and 8 Mask predictions on 8 frames; the crop candidate contains 7 on 6 frames and 9 on 8 frames. This is a traceable known class-confusion subset, not an exhaustive false-positive count or independent precision estimate. The audit uses saved predictions, performs no model inference, adds no trial count and does not change the failed gate result. Its script and evidence are retained alongside the run.

The larger number of supplied road-vehicle matches therefore comes with unresolved output-volume and semantic risks. Do not change the app, remap train labels, lower thresholds or open HighwayDrive from this result. A next step should address cross-view duplicate/semantic conflicts with a prespecified bounded hypothesis or qualify fresh development data with appropriate negative evidence, rather than repeat crop/threshold grids or relabel unassigned outputs as correct.

The current pointer is `reports/uvg_tiles_latest.json`; card `models/uvg_tile_development.json` records gates, exact weights and scope. `summary.csv` and `development_comparison.png` are regenerated from completed reports only. All 343 software tests pass. The graph and fixed frame-300 reference/addition overlay were visually inspected. Physical deployment, parking-bay occupancy, independent final generalization and student mastery remain unverified.
