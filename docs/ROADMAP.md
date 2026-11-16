# Proposed roadmap and acceptance gates

**Language update:** Python and Jupyter replace the original C++/native implementation plan. Treat references to native builds below as historical: the corresponding active milestones are Python environment verification, a NumPy baseline, Python PyTorch training and offline Python packaging. The first data module now works. Official scope still awaits the documents.

This is an engineering schedule derived from the user's brief, not the official
eight-week plan. Replace/reconcile it after reading the university documents.
Calendar deadlines and available study hours have not been provided.

## Eight-week working proposal

| Week | Engineering and learning focus | Evidence required before advancing |
|---|---|---|
| 1 | Audit documents; resolve scope; hardware/stack proof; image-as-numbers lesson; neuron and tensor basics | Source-linked matrix; verified Python environment; genuine parameter-update smoke test; student explanation |
| 2 | From-scratch MLP; chain rule; SGD/momentum/Nesterov; gradient checking; SVD; learning-rule labs | Passing numerical tests; training and checkpoint logs; mathematical examples; controlled optimizer runs |
| 3 | Data validation and grouped splits; Python-trained compact CNN; ResNet/transfer-learning plan | Dataset notices/manifests; leakage audit; real training/validation curves and saved configuration |
| 4 | Detection; matched architecture comparison; 2D/appropriate 3D convolution lab; slot layout/assignment | Appropriate box labels; benchmark protocol; measured detections/latency; geometry and count tests |
| 5 | Semantic and instance segmentation; occupancy integration; video/events; failure cases | Genuine masks and annotation source; IoU/Dice where applicable; end-to-end image/video outputs |
| 6 | Chronological history audit; baseline and LSTM; VAE/reparameterization and latent visualization | Real or explicitly simulated provenance; MAE comparison; bounded forecast tests; reconstruction/sample outputs |
| 7 | Integrated local application; controlled ablations; regression/robustness testing; report updates | Genuine UI/model integration; exports; task metrics; comparable experiments; documented limitations |
| 8 | Frozen final evaluation; report compilation; presentation/demo recording; disconnected build/run; unaided practice | Reproducible evidence bundle; complete Overleaf source/PDF; actual offline checks; student modification/debugging assessment |

Write report and contribution notes throughout, rather than postponing all
documentation until week 8. If a dependency slips, record a blocked task and
revise the schedule; do not silently remove difficult requirements.

## First executable milestone after primary-source audit

Target: an explainable, from-scratch MLP in the final permitted language.

Planned Python baseline files: `src/smart_parking/mlp.py`, `notebooks/02_neurons_and_mlp.ipynb`, `tests/test_mlp.py`, `configs/baseline.json`, and recorded experiment outputs. These paths are plans;
none of these files exists yet.

Implementation sequence:

1. Reproducible Python environment and neuron forward pass with explicit weights/bias.
2. Small MLP with seeded initialization, sigmoid activations and explicit loss.
3. Handwritten backward pass and SGD/momentum updates; Nesterov demonstration.
4. Finite-difference gradient comparison at a fixed non-saturated parameter point.
5. XOR training, saved parameters/logs and reload-equivalent inference.
6. Connect the baseline to documented parking features on a valid split. XOR
   success alone does not demonstrate parking performance.

Proposed numerical gate: double precision, central differences with step `1e-5`,
and compare each parameter gradient using absolute and relative tolerance `1e-5`.
Record raw max errors and investigate failures; adjust tolerance only with a
numerical justification. Include optimizer update tests and invalid shape,
non-finite input and corrupted checkpoint tests. Any educational XOR convergence
criterion must be established before the run and labelled synthetic.

## Product acceptance proposal

These are proposed engineering gates; the faculty has not supplied thresholds.

- Environment: clean, pinned Python setup succeeds. Run documented Python training and save its
  actual log, configuration, dataset/split hashes and checkpoint provenance.
- Baseline: handwritten gradients pass checks; training changes weights;
  checkpoint reload preserves predictions; student can modify a layer/update.
- Data: every used sample traces to a source, label and split; no known source
  frame, duplicate, augmented sibling or temporal target leakage remains.
- Classification: confusion matrix, precision/recall/F1 and per-condition
  performance computed from real held-out predictions. Pre-register a baseline
  and target after data inspection; do not invent an official accuracy threshold.
- Detection: correct box annotations, documented mAP convention and IoU thresholds;
  matched architecture comparison on the same detection task and test subset.
- Segmentation: distinguish semantic masks, instance masks and configured
  polygons; evaluate learned outputs against corresponding pixel annotations.
- Occupancy: expected counts verified on labelled layouts, including uncertainty,
  adjacent slots, occlusion and invalid configurations. Save overlays and errors.
- Forecasting: chronological evaluation against last-value/historical baselines;
  report MAE, sampling interval and horizon. No claim of superiority unless
  observed. Missing/inadequate history produces an unavailable state.
- Generative: actual Python VAE training; reconstruction, sampling and latent
  outputs; reconstruction and KL losses. Generated images are labelled synthetic.
- Application: images and video pass through real models to dashboard and saved
  outputs; errors are actionable; settings change actual behavior.
- Runtime: report loading time, mean/median/p95 latency, FPS with processing
  settings, and memory measurement method. No invented real-time target.
- Offline: network-disconnected launch and fresh build tested separately; local
  model/data dependencies, fallback images and paths verified.
- Academic: every verified official requirement has evidence; Overleaf sources
  compile; report claims match experiments; notices/citations and contribution
  record are complete; student performs unseen-input and modification challenges.

## Work requiring the student's participation

The student must solve exercises, explain gradients and architecture, run and
interpret experiments, inspect label/failure cases, modify configuration/code,
and complete unaided debugging/mock evaluations. Original footage collection
requires appropriate permission and student involvement. Assistance-generated
files or successful automated tests cannot establish student mastery.

## Prioritization if the available time is shorter

First confirm deadlines and official minima. Preserve source audit, permitted
Python training, from-scratch baseline, required Unit evidence, real evaluation
and offline practice. Reduce model size, cosmetic polish and optional camera
features before negotiating any academic-scope change with faculty. A compact
genuine experiment is preferable to an untested large implementation.
