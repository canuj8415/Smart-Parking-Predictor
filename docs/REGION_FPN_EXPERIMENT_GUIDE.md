# Image-only region experiment, 27 October 2026

Run `REGION-FPN-V1-20261027T061402381508Z` improved equal-camera development IoU
from0.287151 to0.581960, but failed four acceptance gates and was not promoted.
The original app and all original/best/failed checkpoints remain preserved.
There are200 TRAIN and30 DEV images from three familiar cameras. See
REGION_DATASET_V2_GUIDE.md for qualification and source boundaries.

| Camera | DEV images | New image model IoU | Original U-Net IoU | Conditional TRAIN template IoU |
|---|---:|---:|---:|---:|
| PUCPR | 8 | 0.612145 | 0.293329 | 1.000000 |
| UFPR04 | 6 | 0.573749 | 0.188825 | 0.283890 |
| UFPR05 | 16 | 0.559986 | 0.379300 | 1.000000 |

These are bay-footprint IoU values, not occupancy accuracy or final evidence.
The original comparator shares the256x144 RGB cache and uses its192x112 input,
then interpolates probabilities to the common target grid. Its earlier final
benchmark and exact native-image app input pipeline are separate evidence.
Candidate mean Dice0.734500; worst-image IoU0.452406. MeanIoU0.80, each-camera0.75,
each-image0.65 and template-regression0.05 gates failed. Improvement and camera
nonregression versus the original passed. No gate or threshold was relaxed.

The sealed recipe uses seed169, frozen ImageNet ResNet18 features and BN state,
a32-channel feature-pyramid decoder, TRAIN-only weighted BCE plus Dice,
AdamW0.001/wd0.0001, batch8, no augmentation, four CPU threads, max8epochs and
patience3. Epoch7 was selected; eight epochs completed. The measured phase after
initial input/code checks took8.990seconds; sampled process RSS peak was
1,462,673,408bytes, not a system-wide peak. Feature tensors occupy256,245,760bytes.
Protocol/source/split/config hashes and all per-image metrics are retained.

Selected failed checkpoint:
`models/checkpoints/region_fpn/REGION-FPN-V1-20261027T061402381508Z/epoch_7_061428042517.pt`,
SHA256 `bee3fa7dbcdf68321adbb73c9706c684104de61926fef3d2f323ec0f03af556a`.
The same folder retains last.pt with optimizer/RNG/batch order for interrupted
execution. The900second deadline and cancellation file are checked per batch;
completed runs refuse to run again. Weights/features/exact predictions remain
local outside Git and the accepted demo. Sources are existing SRC-DS-001 PKLot
(Almeida et al./UFPR,CC BY4.0) and SRC-MOD-003 TorchVision ImageNet ResNet18 under
recorded local academic terms; no new acquisition or weight redistribution.

The decoder receives image features only. The comparator explicitly receives
camera identity and TRAIN mask geometry. Two cameras have identical TRAIN/DEV
mask patterns, explaining template1.0 without perfect image understanding.
UFPR04 TRAIN has three mask patterns represented56/8/8times; its DEV pattern is
among the eight-example TRAIN patterns. This does not prove physical camera
movement or causally explain model errors. TRAIN-only36x64 mask reconstruction
scored0.898799; it is not a proven architecture ceiling or another experiment.

Next seal a controlled longer-budget trial with the same recipe and admission
gates. Later pattern-balanced sampling or finer spatial features should be
separate changes. Reusing DEV does not create independent final evidence.
All17consumed and16quarantined PKLot groups and other final sources remain closed.

Software suite460/OK includes frozen BN/parameters, decoder gradients, TRAIN-only
templates and equal-camera metrics. Training had zero normal forbidden accesses;
its unqualified-cache negative control was denied. Three source-bound worst DEV
error panels were visually reviewed. Full explanation and evidence:
`reports/region_fpn_REGION-FPN-V1-20261027T061402381508Z/EXPLANATION.md`.

Notebook12 executes six code cells with six archived inputs, three inline panels
and a synthetic IoU example. Actual local Jupyter and raw/prospective-read,
project-write and external-DNS denial controls passed. A first startup stalled
before kernel launch; only the verified owned processes were stopped, evidence
preserved, and the local retry passed. No model call or extra trial was added.
Python audits are not OS isolation or physical offline/student mastery evidence.
The accepted468-file demo still includes only its previously tested notebook08.
Official university, physical offline/new-machine and visible manual acceptance
remain open. Singapore learned final closure remains27October10:51UTC/16:21IST.
