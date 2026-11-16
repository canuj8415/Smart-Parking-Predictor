# Local demonstration and reproducibility

## Five-minute demonstration

1. Launch `launch_parking.cmd` and load the real training-split demonstration sample.
2. Explain that its layout contains geometry/IDs, not the occupancy answers.
3. Run Faster R-CNN and then Mask R-CNN; point out boxes versus actual masks.
4. Read occupied/vacant/uncertain counts and save the real overlay/JSON.
5. Show the separate experimental semantic parking-region mask and its weak IoU.
6. Open the forecast tab: the original LSTM loses to persistence; the separate
   archived later-date candidate has MAE31.72versus39.07spaces. These are saved
   historical results, not live predictions or the image camera's history.
7. Load the saved Singapore snapshot offline, showing its age/source. Online,
   explicitly refresh the feed to get a current reading; no cloud inference occurs.
8. Show the 2D/3D convolution lab and manual numerical agreement.
9. Change the confidence threshold or a layout polygon; explain the consequences.

The notebook `02_parking_product.ipynb` provides the same model/data path with
executed outputs. The VAE and synthetic MLP experiments are independent teaching
modules, not evidence that generated images improve parking detection.

## Local assets required

- Python environment with pinned direct app/notebook dependencies.
- Three original pretrained checkpoints in `models/pretrained/`.
- Project-trained ResNet occupancy, semantic U-Net and LSTM checkpoints in
  `models/checkpoints/`; VAE/MLP checkpoints for the extra learning labs.
- Matching local sample images and `configs/layouts/`.
- Birmingham split files and model experiment predictions for the historical chart.
- Saved Singapore raw JSON for cached live-data display.
- Optional project-local OpenCV wheel/install for video.

Core inference uses `weights=None` and loads explicit local state dictionaries;
it does not ask TorchVision to fetch models. `get_live(refresh=False)` reads a
saved file. Only explicit acquisition/setup scripts and online Refresh contact
external sources.

## What is and is not verified

The relocated local demo now has a bounded validation of both actual detector
routes, exports, archived forecasts, saved live readings, convolution arithmetic,
progress tables and two local video samples. It runs from a copied folder with
original-workspace fallback denied and Python networking blocked. The installed
Python runtime is reused. See [the package guide](DEMO_PACKAGE_GUIDE.md) and its
exact validation/manifest. It uses a training example and scores no accuracy.

The app now cancels its pending polling callback on close. The first package's
nonfatal teardown warning and the corrected version are both preserved. Hidden
native widgets and mocked dialogs do not establish visible/manual acceptance.

Real image inference and the product notebook were executed with local assets.
The network-disabled-process smoke test, if present in product evidence, blocks
outbound calls in that process. It is not a claim that Windows networking was
physically disconnected. A fresh offline installation on a new computer and a
genuine network-disconnected rehearsal remain separate acceptance tasks.

Keep the cached weights/data/runtime available before evaluation. Do not rely on
Git alone: large datasets, model binaries and processed CSVs are intentionally
excluded from ordinary history. The original archive and checkpoints remain on
this machine; exact hashes and paths are in the resource inventory and receipts.

Do not show the live feed as current when disconnected. Cached/stale status is
an essential part of the offline fallback, not a model failure to hide.
