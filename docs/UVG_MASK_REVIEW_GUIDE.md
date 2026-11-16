# Rejected automatic suppression and inspection-only output

The automatic mask rule reduced output count but lost two correctly matched cars. It is rejected. The derived review-only export retains the original 209 Mask R-CNN predictions and their masks, adds inspection flags and performs no automatic removal or class remapping. It is a research aid, not a deployed app feature or a new detector-accuracy result.

## Fixed component experiment

`UVG-MASK-DEDUP-20261026T144351078557Z` was sealed before applying the rule to archived native-crop development results. It uses the same 11 HighwayView frames, 153 eligible and 194 total supplied car/truck observations, seed 142 and zero neural-model calls. The run completed in 0.968 seconds. Inputs, protocol, implementation snapshots, model/reference/source hashes and packed masks are retained.

All full-frame predictions are protected. Only crop additions can be suppressed. The fixed rule considers a same-class addition a duplicate when box intersection over the smaller box is at least 0.8 and mask intersection over the smaller mask is at least 0.85, with at least 16 pixels in the smaller mask. Different-class overlaps, tiny masks and empty predicted mask support remain inspection cases. None of these conditions proves that two predictions represent the same true object or that one is the better representative.

The frozen component gates require at least ten removed crop predictions, no eligible/all-positive, per-frame or per-class match loss, at most 0.005 loss of zero-inclusive mask IoU, the same 0.005 limit on the same 113 previously matched targets, unchanged reference outputs and no class remapping. These are narrower component checks; the overall native-crop admission failures remain in force.

| Measure | Native-crop source | Automatic rule |
|---|---:|---:|
| Predictions | 209 | 183 |
| Eligible supplied matches | 113/153 | 111/153 |
| All supplied matches | 113/194 | 111/194 |
| Zero-inclusive mask IoU, same 153 targets | 0.599371 | 0.590373 |
| Mask IoU on same 113 prior matches | 0.811538 | 0.799354 |
| Prior matched objects retained | — | 111/113 |
| Supplied car / truck matches | 107 / 6 | 105 / 6 |

The 26 removals pass the output-reduction gate but fail the preservation and mask-quality gates. The original predictions, failed candidate and exact failure evidence are preserved. No threshold was relaxed after seeing this result. Unassigned predictions are still not an exhaustive false-positive count.

## Two observed false-suppression cases

- Frame 361, supplied car track 18: the correctly matched crop output was suppressed at box containment 1.0 and mask containment 1.0. The retained wider prediction had no qualifying supplied match.
- Frame 600, supplied car track 19: the correctly matched crop output had score 0.968349 but was suppressed at box containment 0.990600 and mask containment 0.971831. The retained wider prediction again had no qualifying supplied match.

`false_suppression_cases.png` shows the saved common-input pixels, supplied target and actual predicted boxes/masks. The image is magnified with nearest-neighbour display so its coarse evaluation pixels remain visible. Similarity or containment of predicted masks does not establish a safe replacement. These are posthoc explanations from the same exposed development clip, not independent final evidence or a verified taxonomy of every unassigned output.

## Inspection-only engineering fallback

`smart_parking.mask_review.review_candidates` converts possible same-class duplicates and overlapping-class/tiny/empty-mask conditions into review records. It returns every original prediction index, changes no prediction, score, mask or class, and has no occupancy-answer or training interface. The derived `review_only.json` refers to hash-bound original prediction/mask files instead of creating an altered detection set.

The actual archive export retains all 209 predictions, creates 53 review records and flags 86 unique outputs. That is a substantial inspection burden, not calibrated uncertainty or proof that the flags are correct. The exporter asserts unchanged prediction and mask bytes; synthetic tests cover nested same-class predictions, different-class conflicts, mutation and empty input. This derived export and its ordinary regression checks do not count as a second scientific trial or improve the failed model metrics.

All 355 software tests pass, including the eight automatic-rule cases and four review-only cases. A separate artifact check reproduces the saved candidate mask scores and verifies that filtered arrays are exactly the selected original arrays. The plots were visually reviewed. No new model inference, source-video read, app integration, physical-offline/new-machine/manual-browser acceptance or student mastery is claimed by this component experiment.

Source SRC-DS-019/SRC-DOC-021 remains UVG-VCM, Tampere University / Ultra Video Group, Partanen et al. (2026), CC BY 4.0; images are attributed derived crop overlays. Original media, pretrained weights, frozen Singapore study and final claims are unchanged. HighwayDrive remains entirely reserved and unopened. The next priority should be fresh development data or independent negative/region-label qualification, rather than repeated containment-threshold sweeps on this one clip.

Evidence: `reports/uvg_mask_dedup_latest.json`, `models/uvg_mask_duplicate_development.json` and the experiment folder above. The safe retained research baseline remains the original native-crop output, whose overall recall-gap/output-volume gates also failed; no product promotion is justified.
