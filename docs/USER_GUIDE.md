# Use the Smart Parking application

## Start

Double-click `launch_parking.cmd` in this project folder, or run:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' run_app.py
```

Use the existing Python environment. Core image processing, forecasting,
convolution and saved snapshots use local files. Online access is explicit for
live refresh/setup. The model weights have already been acquired and local
models trained on this machine; a new machine needs the documented setup and
locally retained assets. See PYTHON_WORKFLOW.md for notebook commands.

## Image and layout

1. Click **Load real sample**. This loads a real training PKLot image and its
   matching geometry-only layout. It is a demonstration, not an independent
   accuracy test. No occupancy answers are passed into inference.
2. Choose **fasterrcnn** for ResNet-based vehicle boxes or **maskrcnn** for
   boxes plus genuine vehicle pixel masks.
3. Set the detection threshold and click **Analyze**. CPU inference takes
   seconds per image on the measured laptop, not real-time video speed.
4. Read total/occupied/available/uncertain counts. Uncertain is never added to
   available. A missed detection alone does not prove vacancy.
5. **Save results** creates a timestamped subfolder containing the actual analysis
   overlay, matching JSON observations and a checksum record. If a learned mask
   is currently displayed, it is saved separately as `display_preview.png`.

For a new view, **Open image**, then load the correct camera layout or click
**Draw spaces**. Left-click at least three polygon corners and right-click to
finish a space. Repeat and save the layout. The layout must have the correct
dimensions and view; the app cannot infer camera identity from equal dimensions.
Loading a new image resets its layout so a stale view is not silently reused.
Changing an image, layout or detection setting clears the previous occupancy
results. Click Analyze to calculate new counts. Controls are temporarily disabled
while processing; Stop video remains available.

The occupancy classifier was trained on a small real subset and can fail on new
locations, weather, motorcycles and occlusion. Raw scores are not calibrated
confidence. The yellow state exposes disagreements and low-confidence cases.

## Learned space mask

**Learned space mask** runs the separately trained small U-Net. It predicts the
union of parking-region pixels, not unique slot identities. Its held-out IoU is
currently low; use it as an experimental visualization, not reliable automatic
layout generation. Configured polygons remain editable and distinct.

## Forecast

Choose **Original experiment** or **Later-date check**, select a car park, then
**Show held-out forecast**. Both are LSTM variants: the chart names the Original
LSTM or Group-relative residual LSTM and shows that report's own recorded score
against persistence. Their evaluation dates differ. The original loses to its
baseline; the later model beats persistence on its own later-date cohort.

**Save forecast results** writes the displayed PNG, CSV, report description and
checksum metadata to your chosen folder. Changing the report or car park clears
the old plot and export snapshot. See [the forecast report guide](FORECAST_REPORTS_GUIDE.md).

These are archived historical Birmingham predictions. The displayed MAE covers
the whole selected report, not just the car park in the graph. This is separate
from the image camera and Singapore live feed. A camera-specific predictor needs
a sufficient, consistent history from that actual camera.

Training used a causal half-hour grid: each grid point can use only an earlier
real observation at most 20 minutes old. Windows with gaps, date/split/capacity
changes or no genuinely later target are rejected. Derived grid points are not
claimed to be newly measured sensor readings.

## Live parking

**Refresh official live feed** retrieves the authorized public Singapore source.
**Load saved snapshot** works offline. The app shows provider time, age and
cached/stale status; refresh is limited to once per minute. Search by car-park ID.
These readings are not inferred by our vision model. Snapshots and deduplicated
timestamped observations are saved locally with attribution and checksums.
No live forecasting accuracy is claimed before sufficient live history exists.

## Video and convolution

Video requires the project-local OpenCV decoder. Load a camera-matching layout,
then **Process video**. It analyzes every fifteenth decoded frame and records
timestamps, counts and debounced occupancy changes. **Stop video** requests
cancellation after the current inference. These are occupancy changes, not
verified entrance/exit crossing counts. A repeated still-frame clip used in
testing is a codec fixture, not real traffic evidence.
The selected detection threshold applies to video as well as image analysis;
video exports record that threshold and the actual decoded-frame count.

The convolution tab shows a real-image 2D edge kernel and an explicitly
educational 3D volume. Manual arithmetic is compared with tensor operations.
The model-information/source tab explains the stages and all local data folders.

## Reproduce training and tests

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' -m unittest discover -s tests -v
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/train_baseline.py
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/train_forecast.py
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/train_vision.py
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/train_vae.py
```

Do not rerun model selection against final test results. For a changed method,
preserve existing evidence and reserve a fresh appropriate holdout or report the
old result as development evidence. Read the semantic segmentation script's
explicit replacement-holdout rationale before reproducing that experiment.

## First learning task

Explain why the number of detected vehicles can differ from occupied parking
spaces. Give two examples from the displayed image. Then change the detection
threshold and explain which outputs changed and which should remain fixed.


## Beginner reading and detection-only video

Start with output/pdf/smart_parking_beginner_guide.pdf for a six-page explanation
of the actual product, data locations, training, results and next steps.
The desktop video workflow requires a matching layout. For integration research,
process_video(source, engine, None, output, every_seconds=2, confidence=.5)
analyses only vehicle detections: occupancy is unavailable, and CSV has no slot
counts. Time sampling requires finite, advancing presentation timestamps; invalid
timing raises an error so frame-based sampling can be chosen explicitly. Both
reported and timestamp-observed FPS are recorded; metadata can be wrong.
No-layout image results similarly show unavailable parking counts. These vehicle
detections are not a parking or flow accuracy benchmark without matching labels.


## Layouts can drift within one camera ID

A training/validation audit found different original space coordinates under the
same source camera ID. Recheck the drawn slot polygons whenever a view changes;
matching dimensions and camera name alone do not validate a layout. Experimental
image-based alignment is isolated from the app because it harmed another camera
in validation. No automatic correction or identity check is promised.
The editable report draft is reports/overleaf/smart_parking_draft/main.tex; a
local source ZIP is output/reports/smart_parking_report_draft_v001.zip. Compilation
and layout are not confirmed. The beginner PDF remains a separate earlier snapshot.


## New learning notebook

Open notebooks/03_region_transfer_and_live_coverage.ipynb in Python (Smart Parking).
Its six executed cells replay the trained region decoder, compare real images
and saved masks, and explain why a higher average can still fail the quality gate.
It loads validation rows only; the fresh final set stays closed. The live section
shows matched, expired and pending predictions. Matching coverage is not accuracy.
The latest editable report source bundle is output/reports/
smart_parking_report_draft_v002.zip; no compiled PDF/layout success is claimed.


## Tracing a saved analysis

New analysis.json records contain input_image (the processed RGB pixel fingerprint
including dimensions), layout_identity (ordered slot geometry), weight_sha256
(detector), classifier_checkpoint_sha256 and classifier_run_id. Export metadata
also fingerprints the actual saved overlay and JSON. Pixel identity differs from
the original downloaded file's checksum: JPEG metadata and file encoding are not
part of the RGB fingerprint. Use the source receipt/raw-file hash for the original.

Geometry identity excludes answer labels and descriptive metadata. The engine
copies the geometry before inference. A fingerprint identifies what was used;
it does not authenticate the camera view or establish prediction accuracy.
The real integration export/evidence is under experiments/results/
PROVENANCE-OFFLINE-20261024T212112979750Z/. Its100-slot counts refer to a different
training image, not the40-slot sample or a measured accuracy score.
