# Occupancy assignment memory improvement — 27 October 2026

The working application now stores each supplied parking polygon in a small
bounding rectangle instead of retaining one full-image boolean mask per space.
It still rasterizes each polygon on the original canvas before cropping it.
That detail preserves the original fractional-coordinate drawing rules; the
earlier rejected translated-polygon crop experiment showed why it matters.

The detector still finds vehicles, the unchanged classifier scores each supplied
space, and the assignment combines their evidence. The overlap threshold remains
0.12, occupied/vacant thresholds remain 0.75/0.25, and competing detections retain
the same ordering and one-vehicle-per-space rules. Missing detection alone never
proves that a space is vacant. This change does not discover parking geometry.

## Evidence

`OCCUPANCY-PATCHES-20261027T011930811393Z` compared exact output dictionaries on
2,000 generated software cases and three previously exposed ACPDS TRAIN layouts
with generated detections/probabilities. No model or ground-truth accuracy was
scored. Separate sequential processes used the same fixed generated 1920x1080,
96-space, 24-box fixture and imported the same application stack:

| Measurement | Dense reference | Bounded slot patches |
|---|---:|---:|
| Additional sampled peak RSS | 207,122,432 bytes | 9,101,312 bytes |
| Retained slot bitmap bytes | 199,065,600 | 1,855,488 |
| Assignment duration | 8.351 seconds | 0.165 seconds |

The measured additional RSS reduction is 95.6% on this fixture. Both output
digests are identical. Sampling was every 2 ms and each child had a 900 MiB cap.
These are local fixture measurements, not guaranteed memory/speed bounds for
arbitrary cameras or the neural models.

`ASSIGNMENT-API-20261027T012959957197Z` then exercised the integrated application
on three already exposed 4000x3000 TRAIN photos. Actual Faster R-CNN at 640 and
the original classifier each ran three forward calls. All 83 supplied spaces
passed image/layout identity, ordered ID, count, state-rule and unique vehicle
support checks. Inference times were 3.768, 3.266 and 5.965 seconds; measured
worker duration was 15.814 seconds and sampled process peak was 1,275,285,504
bytes, below the prespecified 1.5 GiB cap. No labels were used for accuracy.
All three downscaled overlays were visually inspected for intact rendering.
Their visibility is not occupancy correctness certification.

The worker completed successfully, but its parent then failed to write the
result because both supplied `duration_seconds`. The original runner, protocol,
stdout, worker artifacts and error remain preserved. A separate hash-checked
recovery registered this same trial once without repeating inference. Worker
wall timestamps are explicitly derived from file modification time minus the
measured duration; the unavailable parent duration was not invented. The future
runner uses a separate parent-duration field.

Six added contract tests bring the full software suite to 432 passing tests.
The retained dense reference lets these tests compare independent implementations.
Original production weights, classifier thresholds, historical results and final
reservations stay unchanged. Preintegration qualification is reproducible at
Git checkpoint `145bdc7`; its original vision source is also saved in the wake's
evidence folder. The later API protocol binds the integrated vision source.

## Limits and next work

This reduces assignment buffers. Full-image Mask R-CNN output production,
instance-mask storage and neural-model memory remain separate unresolved risks.
The real-photo integration used Faster R-CNN only. There was no visible desktop,
native save dialog, new-machine or physical offline acceptance. The selected
451-file offline package predates this patch and needs a distinct refresh when
the next application integration milestone is ready.

The last-block research classifier still fails its vacancy-safety gates and was
not installed. This software improvement does not turn its 95.8508% development
accuracy into an acceptable model. Keep all TEST cohorts closed. A useful next
study is a single prespecified fixed-threshold Faster/classifier fusion diagnostic
on the admitted development photos, with false-vacancy, uncertainty and per-image
counts reported separately. Avoid another optimizer/threshold grid on the reused
35-image validation set.

For a student explanation: compare a large sheet of graph paper for every bay
with keeping only the rectangle around each bay. The marked squares and parking
decision stay the same; fewer empty squares are stored. Explain why this is a
software resource result rather than a gain in camera accuracy.
