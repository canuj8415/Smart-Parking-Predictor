# Real traffic detector and mask development study

The higher-resolution candidate improved the measured results, but neither setting passed the frozen quality gates. The product keeps its existing setting and weights. HighwayDrive remains entirely reserved and unopened. These results are development evidence from one short traffic clip, not parking occupancy accuracy or independent final acceptance.

## What was measured

Source SRC-DS-019 is the official UVG-VCM HighwayView preview and its supplied v1.0 annotations. Source/licence/acquisition details and the two retained annotation-qualification failures are in [UVG_DEVELOPMENT_GUIDE.md](UVG_DEVELOPMENT_GUIDE.md). Attribute Tampere University / Ultra Video Group, Partanen et al. (2026), UVG-VCM, CC BY 4.0, and identify derived resized overlays.

Two protocols were saved and hash-bound before their respective inference passes. Seed 138, the same 11 fixed development frames, unannotated 960×540 inputs, original Faster R-CNN and Mask R-CNN weights, score threshold 0.5, mask threshold 0.5 and same-class box IoU threshold 0.5 were retained. The first trial uses an internal maximum side of 640 pixels; the only candidate changes that internal side to 960, retaining more of the input detail. Both use the actual `VisionEngine` model construction and product vehicle filter. No weights or production source were changed, and no training or downloads occurred during inference.

The selected frames contain 194 supplied car/truck observations from 34 persistent tracks. The eligible gate covers 153 observations from 32 tracks whose supplied boxes are at least 4×4 pixels on the common input. The other 41 smaller observations remain visible in separate all-positive results. Ten train observations are outside the product's vehicle-class scope and are explicitly excluded. Observations repeat across 11 frames of one ten-second sequence: they are not 194 independent vehicles or independent scenes.

Matching is deterministic, class-aware maximum-cardinality assignment at box IoU ≥0.5. Each prediction supports at most one supplied object. Unassigned predictions are recorded, but are not labelled false positives: exhaustive background truth has not been established. This study therefore does not report precision/mAP or full traffic counting accuracy.

## Actual results

| Measure | Default internal side 640 | Candidate internal side 960 |
|---|---:|---:|
| Faster supplied-positive matches, eligible | 88/153 (57.52%) | 102/153 (66.67%) |
| Mask R-CNN supplied-positive matches, eligible | 67/153 (43.79%) | 87/153 (56.86%) |
| Faster matches over all 194 supplied positives | 45.36% | 52.58% |
| Mask R-CNN matches over all 194 supplied positives | 34.54% | 44.85% |
| Mask IoU, all 153 eligible supported targets, valid misses score zero | 0.3420 | 0.4672 |
| Mask IoU on matched targets only | 0.7810 | 0.8217 |
| Faster total timed model calls, 11 frames | 38.315 s | 52.617 s |
| Mask total timed model calls, 11 frames | 20.784 s | 34.232 s |
| Entire recorded trial duration | 169.110 s | 198.265 s |

Higher resolution adds 14 Faster matches and 20 Mask matches. It passes the prespecified ≥5 percentage-point gain for both detectors, ≥0.05 zero-inclusive mask-IoU gain, per-frame and per-class non-regression, and ≤3× model-time checks. Faster class matches change from 82 to 95 cars and 6 to 7 trucks; Mask matches change from 64 to 84 cars and remain 3 trucks. No measured frame loses eligible-positive recall.

Both settings nevertheless fail the retained absolute requirements: ≥75% eligible-positive recall in each detector, mask IoU ≥0.5 with valid misses included, and Mask box recall within five percentage points of Faster. The candidate is the better development setting under these limited comparisons, not an accepted replacement. Measured model-call time increases by factors 1.373 and 1.647; these timings include tensor conversion/model resizing/postprocessing and exclude model loading, source preparation and ground-truth work. They do not establish real-time parking-entrance throughput.

## Why the mask denominators matter

IoU is intersection area divided by union area. A good mask on a detected car cannot compensate for a missed car. The matched-only value omits misses and therefore looks much stronger. The zero-inclusive value retains all eligible supported targets and assigns zero when a valid target has no qualifying matched detection.

Missing raster truth is different: it remains unknown and is excluded rather than assigned zero or treated as empty background. Across all 194 selected positives, one subpixel object has no original PNG support and four more lose their tiny support during the declared nearest-neighbour resize. All five are below the eligible size gate; all 153 eligible objects retain raster support. BGR-to-RGB conversion and transparent-pixel exclusion are explicit. The previous qualification failures remain recorded.

## Saved evidence and reproducibility

- Default: `experiments/results/UVG-DETECTORS-20261026T131246880705Z`.
- Candidate: `experiments/results/UVG-DETECTORS-20261026T131820602234Z`.
- Each retains protocol/binding, exact source snapshots, input/source/weight/code hashes, resized inputs, supplied targets, packed binary masks, per-frame predictions/matches and measured results. Candidate inputs and target JSON are byte-identical to the reference. Original and candidate weights are identical.
- The default inference finished successfully but its latest-pointer export failed because a relative path was not resolved. The saved report was published without repeating inference. The original interruption and separate repair receipt are retained; relative/absolute-path and escape tests cover the fix. It is one completed trial, not a second inference run.
- Independent arithmetic verification reloaded saved packed masks and reproduced all 153 zero-inclusive mask scores in each run. No raw data, fresh model inference or extra trial count was needed.
- `scripts/report_uvg_detectors.py` reads the two archived reports to regenerate the chart, class/size CSV and fixed middle-frame mask comparison. It performs no inference or holdout access. The figure includes all car/truck masks on fixed frame 300, not a best-score example.
- All 324 software tests pass. The actual existing offline-installed Python environment and package versions are recorded in the wakeup evidence folder; no package was installed. Physical disconnection, a new machine and student mastery were not tested.

Next, diagnose the remaining misses with a bounded, prespecified development study of raw class/score outputs and object size. Do not repeat resolution grids, lower thresholds or remap trains without appropriate negative evidence. Keep false-vacancy protection, source integrity and held-out evaluation requirements. A final evaluation requires passing development criteria and a tested canonical whole-sequence durable claim; its failure must consume the whole reserved source group. No final controller or final-data opening is justified by this result.
