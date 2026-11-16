# Target architecture — design only

**Implementation update:** Python/Jupyter is active. The dataset preparation module and audit notebook exist; all model/application boxes remain targets. Python PyTorch replaces the original native-runtime proposal. No model has been trained.

The diagrams describe the target application. Supporting data preparation is implemented; model choices still await the university audit and model smoke tests.

## 1. System architecture

```mermaid
flowchart TD
  I[Image / video / optional camera] --> V[Validate input and camera identity]
  V --> P[Decode and preprocess]
  L[Validated camera-specific slot layout] --> A
  P --> D[Vehicle detector]
  P --> C[Slot crop classifier]
  P --> S[Semantic / instance mask branch]
  D --> A[Vehicle-to-slot assignment and occupancy fusion]
  C --> A
  S --> A
  A --> T[Temporal smoothing and timestamped events]
  T --> H[Validated occupancy history]
  H --> F[Forecast baseline and trained LSTM]
  A --> U[Local dashboard and exports]
  F --> U
  T --> U
```

The system looks at a view of the lot, gathers evidence for each configured
space, then displays counts. A separate history branch predicts later counts
only when compatible observations and a trained model exist. Segmentation is a
distinct learned branch; manually drawn slot regions are configuration data.

## 2. Data-flow diagram

```mermaid
flowchart LR
  F[Frame plus capture time] --> B[Boxes / classes / scores]
  F --> M[Masks plus class or instance IDs]
  F --> P[Slot crop probabilities]
  B --> O[Per-slot state and evidence]
  M --> O
  P --> O
  O --> E[Timestamped transitions]
  O --> N[Totals including uncertain]
  E --> X[Local event and history files]
  N --> X
  X --> R[Graphs / reports / eligible sequence windows]
```

A frame becomes structured evidence. Evidence becomes slot states and counts;
these outputs are saved with provenance so results can be reproduced.

## 3. Model architecture sketches

```mermaid
flowchart LR
  X[Explicit numeric features] --> H[From-scratch MLP hidden layer] --> Y[Binary output]
  P[Slot image crop] --> C[Small CNN or ResNet features] --> Q[Occupancy output]
  I[Full image] --> D[YOLO or Faster R-CNN] --> B[Vehicle boxes]
  I --> S[Segmentation network] --> M[Semantic or instance masks]
  T[Past occupancy windows] --> L[LSTM] --> F[Bounded future count]
  V[Parking crop] --> E[VAE encoder: mean and log variance]
  E --> Z[Reparameterized latent sample] --> R[Decoder reconstruction]
```

Each model answers a different question: classify a slot, locate a vehicle,
label pixels, predict a later count, or reconstruct/generate image patches.
These are not interchangeable tasks. Exact layers and shapes will be documented
when architecture and data dimensions are selected.

## 4. Training pipeline

```mermaid
flowchart LR
  A[Versioned manifest and fixed split] --> B[Training-only transforms]
  B --> C[Native model forward pass]
  C --> D[Loss against correct labels]
  D --> E[Gradients and optimizer update]
  E --> C
  C --> V[Validation selection]
  V --> K[Best and final checkpoints plus configuration]
  K --> T[Once-frozen final test evaluation]
```

Training changes weights. Validation selects settings/checkpoints. The held-out
test set evaluates the frozen procedure. Manual gradients are required for the
baseline; Python PyTorch can provide autodiff for the main models.

## 5. Inference pipeline

```mermaid
flowchart LR
  C[Load local config and models] --> V[Validate schemas and model shapes]
  V --> I[Read valid input]
  I --> P[Apply checkpoint preprocessing]
  P --> M[Model predictions]
  M --> O[Assignment / uncertainty / optional smoothing]
  O --> R[Overlay and count exports]
  V --> E[Visible actionable error if incompatible]
```

Inference uses saved weights without learning new ones. Missing models or a
wrong camera layout produce clear errors rather than fabricated outputs.

## 6. Module dependencies

```mermaid
flowchart TD
  UI[Interface / CLI] --> APP[Application coordinator]
  APP --> CV[Classification / detection / segmentation]
  APP --> OCC[Occupancy / geometry]
  APP --> TS[History / forecasting]
  APP --> IO[Input / config / exports]
  CV --> PRE[Preprocessing]
  CV --> RT[Python PyTorch runtime]
  TRAIN[Training executables] --> DATA[Dataset and manifest tools]
  TRAIN --> RT
  LAB[Math / baseline / learning-rule labs] --> CORE[Small core utilities]
  VAE[Separate VAE experiment executable] --> RT
  TEST[Tests and evaluation] --> OCC
  TEST --> LAB
  TEST --> DATA
```

The interface calls small modules with clear inputs/outputs. The VAE lab stays
separate so an experimental generative model cannot prevent occupancy analysis.

## 7. Data preparation

```mermaid
flowchart LR
  A[Original sources and notices] --> B[Hash / decode / annotation validation]
  B --> C[Manifest with camera / date / source-frame identity]
  C --> D[Grouped split or chronological split]
  D --> E[Leakage audit]
  E --> F[Training transforms and fitted normalization]
  F --> G[Versioned model-ready data]
```

Check provenance and grouping before producing training examples. Splitting
after augmentation would risk putting copies of the same input on both sides.

## 8. Testing and evaluation

```mermaid
flowchart LR
  U[Math / gradient / geometry unit tests] --> I[Image and video integration tests]
  I --> M[Task-specific held-out metrics]
  M --> R[Robustness and failure-case review]
  R --> O[Disconnected build / launch / export test]
  O --> S[Student explanation and live modification]
```

Correct small components are necessary but insufficient. The complete product
also needs real unseen-data evaluation, offline operation and student mastery.

## 9. Deployment

```mermaid
flowchart TD
  PC[Single Windows laptop] --> APP[Python app and local environment]
  PC --> CFG[Layouts and settings]
  PC --> W[Local model checkpoints]
  PC --> IN[Local images / video / optional camera]
  APP --> OUT[Local overlays / CSV events / graphs]
  CACHE[Cached build tools and dependency archives] --> BUILD[Optional fresh offline build]
  BUILD --> APP
```

The proposed demonstration uses one computer with all needed files stored
locally. Successful offline execution and successful offline rebuilding are
separate claims and require separate evidence.

## Proposed module contracts

- `Frame`: image, source/camera ID, capture time and sequence identity. For still
  images without trusted time, do not silently use processing time as capture time.
- `SlotLayout`: camera ID, reference image size, unique slot IDs and valid polygons.
  Reject a mismatched view; scale only when documented geometry allows it.
- `Detection`: vehicle class, bounding box, score and frame reference. A raw score
  is not automatically calibrated confidence.
- `MaskPrediction`: pixel labels or per-instance masks with explicit task type.
- `SlotObservation`: slot ID, occupied/vacant/uncertain, supporting evidence,
  model version and timestamp validity.
- `CountSummary`: total, occupied, vacant, uncertain. Enforce
  `total = occupied + vacant + uncertain`; uncertainty is never counted as free.
- `Forecast`: target time/horizon, capacity, predicted count, model/dataset
  provenance and real/simulated flag. Reject insufficient history and incompatible
  sampling intervals. Document clipping or another bounded output mechanism.

## Occupancy and vehicle-flow decisions

Candidate evidence includes crop probabilities and vehicle-slot overlap. Use
one-to-one assignment where appropriate to reduce double-counting, with an
explicit ambiguous state for occlusion and neighboring-slot conflicts. A missing
detection alone must not prove vacancy. Calibrate thresholds on validation data.
Temporal smoothing must reset on unrelated inputs, camera changes or sequence gaps.

Slot state changes are occupancy events. Actual entrance/exit flow requires
track identities and verified line/zone crossings in suitable footage. Do not
label state changes as entrance/exit counts. Debounced occupancy events are implemented; entrance/exit tracking remains unimplemented.
