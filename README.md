# Smart Parking Occupancy and Vehicle Flow Predictor

> **About this repository:** source code, notebooks, tests, configs and docs only. Datasets, trained model weights, experiment outputs and offline installers are not included because of their size (about 1 GB). See `docs/` for the datasets and setup used.


**Working Python/Jupyter development build — 26 October 2026.**
The main image pipeline, recorded-history LSTM, live snapshot interface,
convolution laboratory and source records now run. This is not a claim of
production reliability or completion of every unverified university requirement.

## Start the product

Double-click **launch_parking.cmd**, or run from this folder:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' run_app.py
```

Click **Load real sample**, choose Faster R-CNN or Mask R-CNN, then **Analyze**.
For an explained, executed notebook, open
[02_parking_product.ipynb](notebooks/02_parking_product.ipynb).
The real sample is a hash-bound training example for demonstration, not a new
independent accuracy test. The latest selected local package combines the app,
notebook08and its offline installer set, with a fresh environment verified inside
the copied folder; see [the combined demo guide](docs/COMBINED_OFFLINE_DEMO_GUIDE.md).
Existing base Windows/Python is still required. Earlier runtime-only demo copies
are preserved. Separate app and Jupyter offline installations also pass;
see [offline app setup](docs/OFFLINE_APP_SETUP.md) and
[offline Jupyter setup](docs/OFFLINE_JUPYTER_SETUP.md). Local server, notebook
delivery and kernel execution are checked; a visible browser/manual rehearsal
and physical network-disconnection demonstration remain separate.

To open the image-pattern lesson with the verified Jupyter environment:

```powershell
$parkingNotebook = Get-Content '.\reports\offline_jupyter_latest.json' -Raw | ConvertFrom-Json
& $parkingNotebook.python '.\scripts\start_jupyter.py' --offline --notebook '08_image_patterns_and_svd.ipynb'
```

Think of the app as a parking attendant: the detector finds cars, the space
layout marks each bay, the classifier judges occupied/empty/uncertain, and the
forecast uses past counts to estimate future availability. The notebooks show
the calculations behind those steps. The Singapore feed is a separate official
count of available spaces; it cannot grade the camera's answers.

## What works

- Faster R-CNN with ResNet50 vehicle boxes; Mask R-CNN with genuine vehicle masks.
- Validated camera-specific slot polygons, an editor, occupancy counts and exports.
- A real PKLot-trained ResNet18 transfer head: 95.28% accuracy on 360 held-out
  slot crops from a small date-separated subset, not a full PKLot benchmark.
- A separate learned parking-region U-Net, currently weak/experimental (IoU 0.252).
- A genuinely trained Birmingham LSTM with its better last-observation baseline
  shown alongside it. The optional archived later-date candidate has MAE31.72
  versus39.07spaces for persistence; original runtime weights are retained.
  No forecast is fabricated for an unrelated image camera.
- Authorized Singapore live availability snapshots with source timestamps,
  stale/cache labels and local history, separated from model predictions.
- A separate Singapore forecasting study with a frozen non-neural trend
  candidate: development MAE 6.31 versus 6.96 spaces for the last-count comparison
  on the same 9,202 windows/nine collection times. Prospective logging is active
  and final scoring remains pending;
  this is not learned live accuracy or an app-model replacement.
- Verified representative 2D and 3D convolution demonstrations.
- From-scratch NumPy MLP with manual gradient checking and a separate real-crop VAE lab.
- Explicit finite-gate crossing predictions through the Python video API, local
  command and graphical setup tab. A separate identity-continuation candidate
  improves reused development tracking. Its one-sequence final has no labelled
  crossing, so counting recovery remains unavailable and final acceptance failed.
- Dated progress viewing/CSV exports in Sources & guide, plus a four-tab Excel
  progress report with sources, data locations and measured-result limitations.

The current fixed training demonstration produced 68 occupied, 32 vacant and
0 uncertain out of 100 spaces in the saved compatibility checks. An earlier
40-space demonstration produced 35 occupied, 2 vacant and 3 uncertain. These
are individual predictions, not accuracy measurements. Detection mAP and
vehicle-mask IoU remain unmeasured because this subset has slot labels rather
than vehicle-box/mask ground truth. Actual entrance/exit crossing counts are not
claimed from occupancy changes.

## Where the actual data is

Paths below are relative to this project folder. Raw source files are retained;
prepared CSVs and predictions are stored separately.

| Data | Source | Saved location | Use |
|---|---|---|---|
| Parking images and original XML space labels | PKLot, SRC-DS-001 | `data/raw/pklot_subset/`; frame inventory `data/manifests/pklot_frames.csv` | Vehicle/space/occupancy work; labelled final groups are already consumed |
| Historical Birmingham counts | UCI Parking Birmingham, SRC-DS-003 | Original CSV `data/raw/uci_parking_birmingham/dataset.csv`; prepared CSVs `data/splits/birmingham-global-days-v1/` | Time-ordered forecast training/evaluation; existing final dates cannot be reused for tuning |
| Official live availability | Singapore data.gov.sg, SRC-LIVE-001 | Original JSONs `data/raw/singapore_live/`; normalized CSV `data/processed/singapore_live_observations.csv` | Current/cached observations; later outcomes grade previously frozen baseline forecasts |
| Source URLs, licences, timestamps and checksums | All sources | `data/source_manifest.csv`, `data/resource_receipts.jsonl`, `data/dataset_inventory.json` | Trace each downloaded file and transformation |
| Saved models and measured results | Project and pretrained sources | `models/checkpoints/`, `models/pretrained/`, model cards and `experiments/EXPERIMENT_REGISTRY.csv` | Reproduce predictions and inspect successes/failures |

## Guides and evidence

- [User guide](docs/USER_GUIDE.md)
- [Fresh development test explained plainly](docs/FRESH_PARKING_DATA_GUIDE.md):
  unchanged crop classifier703/720correct;two confident false-empty calls remain.
  The later paired final is now consumed; its replacement gate failed. See
  [the final occupancy limits](docs/OCCUPANCY_FINAL_GUIDE.md); original app retained.
- [Singapore forecasting study](docs/SINGAPORE_FORECAST_STUDY.md) and
  [executed Jupyter lesson 10](notebooks/10_singapore_forecast_study.ipynb): paired
  development evidence, synthetic examples, missing-target coverage and the
  sealed future test. The lesson never opens unscored final observations.
- [Separate Singapore lesson folder](docs/SINGAPORE_LESSON_PACKAGE.md): about
  10 MB of archived inputs and helper code, tested after relocation with the
  existing offline Jupyter environment. An installed Python/Jupyter runtime is
  required; the full app bundle remains separate.
- [Forecast-log integrity checks](docs/SINGAPORE_ISSUANCE_HEALTH.md): checksums,
  timing and prediction bounds, without reading targets or calculating accuracy.
- [Traffic detection diagnosis](docs/VISUAL_DETECTION_DIAGNOSTICS.md) and
  [executed Jupyter lesson 11](notebooks/11_visual_detection_diagnostics.ipynb):
  a well-aligned truck box can still have the wrong class. Archived development
  evidence, seven executed cells and two figures; no new inference or final
  data inside the lesson, and no automatic train-to-truck remapping.
- [Native-detail traffic candidate](docs/UVG_NATIVE_DETAIL_GUIDE.md): overlapping
  source-video crops improve supplied-positive recall and mask overlap on one
  development clip, but coverage and output-volume gates still fail. The app
  and reserved final sequence remain unchanged.
- [Why automatic duplicate removal was rejected](docs/UVG_MASK_REVIEW_GUIDE.md):
  containment lost two correctly matched cars. The inspection-only export
  retains all detections and adds review flags; it changes no app predictions.
- [New CNRsource qualification](docs/CNRPARK_DATA_QUALIFICATION.md):official files
  recovered,metadata checked;image modelling still deferred pending content terms.
- [Every external source and local storage location](docs/THIRD_PARTY_SOURCES.md)
- [Source registry](docs/SOURCE_REGISTRY.md), [dataset provenance](docs/DATASET_PROVENANCE.md),
  [model provenance](docs/MODEL_PROVENANCE.md), [licensing](docs/LICENSING_RECORD.md)
- [Current verification](docs/TEST_RESULTS.md) and [implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Python/Jupyter instructions](docs/PYTHON_WORKFLOW.md), [offline demonstration](docs/OFFLINE_DEMO.md)
- [Relocated demo folder](docs/DEMO_PACKAGE_GUIDE.md), [Excel progress guide](docs/EXCEL_PROGRESS_GUIDE.md)
- [Gate-counting lesson and command](docs/GATE_FLOW_GUIDE.md),
  [executed notebook 04](notebooks/04_vehicle_gate_flow.ipynb)
- [What the forecast's target time means](docs/FORECAST_TIMING_GUIDE.md)
- [Read and export the right forecasting method](docs/FORECAST_REPORTS_GUIDE.md)
- [Project walkthrough slides](reports/presentations/smart_parking_walkthrough_v002.pptx)
  and [plain-language practice guide](docs/PRESENTATION_PRACTICE_GUIDE.md)
- [Requirement tracker](docs/REQUIREMENTS.csv), [progress](docs/PROJECT_PROGRESS.md),
  [individual work](docs/INDIVIDUAL_WORK_LOG.md), [AI assistance](docs/AI_ASSISTANCE_LOG.md)

Original datasets and weights remain local, outside ordinary Git history.
`data/resource_receipts.jsonl` records actual source URLs, times, byte counts,
hashes and storage paths. Model cards and experiment records link claims to
actual runs. No private CCTV, account credentials or paid sources were used.

## Remaining academic gates

The user explicitly selected Python/Jupyter and authorized implementing the exact
product definition supplied in the latest message. The two university documents
remain missing, so official language approval, full Unit I–V minima and rubric
are not independently verified. Student mastery, full architecture benchmarks,
full syllabus labs, final Overleaf report/presentation and a physically
network-disconnected rehearsal remain unfinished. No 100% completion is claimed.
