# What improved in the parking-region experiment?

Think of tracing the parking rows onto transparent paper. If the camera and
layout stay fixed, the tracing remains useful. If the view changes, old outlines
can point to the wrong place. Our neural network tries to find regions from the
picture; a stored tracing is a different source of information.

We tested two rules using only training masks to decide where geometry was stable:

| Development method, same 24 photographs | Overall mask IoU | UFPR04 IoU | Gate |
|---|---:|---:|---|
| Original frozen image-only CNN | 0.798 | 0.667 | Fails stable-camera retention |
| Stored training-majority geometry | 0.768 | 0.285 | Comparator |
| Lock every unanimously labelled training pixel | 0.840 | 0.448 | **Fails** |
| Stored geometry only for completely stable cameras; CNN otherwise | 0.911 | 0.667 | Passes |

IoU measures overlap: matching region pixels divided by all pixels marked as a
region by either the prediction or reference. Higher is better. It is not vehicle
detection accuracy, occupancy accuracy or a universal project accuracy percentage.

The first hybrid failed even though its overall score improved. It trusted old
background pixels on a changing view, so it excluded regions the CNN could find.
We preserved that failed experiment. The revised rule has no tuned threshold:
if **any training mask differs**, use the CNN for that camera's entire image.
Otherwise use the stored geometry. Camera names do not choose the route; the
training masks do. Both rules reused development data; neither saw final labels
before its method and checkpoint were frozen.

The revised rule then passed one protected test on six later photographs:

| Same six final photographs | Overall IoU |
|---|---:|
| Known-camera stability router | **0.910** |
| Frozen image-only CNN | 0.803 |
| Stored training-majority geometry | 0.768 |

The combined method passed the frozen overlap, per-camera and added-value rules.
The changing camera, UFPR04, scored **0.662** using the CNN. PUCPR and UFPR05
used **stored geometry only**, each scoring 1.000 on these two-photo subsets.
Those two scores provide no evidence of neural image segmentation: the output
there is a tracing learned from earlier annotations. No new gradient training
or neural-weight improvement occurred in this work.

The sample is small: two images per known camera, one later date each. The
method needs an explicit correct camera ID and a matching view. Matching image
dimensions does not authenticate the view. A previously stable camera can move
later. This is not automatic layout discovery for a new camera, individual slot
identification, a calibrated reliability guarantee or an unseen-camera benchmark.

The one-time claim was flushed before any final image/XML was decoded. The six
images **and their three camera/date groups are now consumed**. Different frames
from those same groups cannot be renamed into a fresh final set. Failed attempts
also consume groups. Future changed vision methods need genuinely fresh groups.

The original application mask preview and all production weights remain unchanged.
This is a separately saved, conditional known-camera method. Runtime camera/view
verification and app integration still require work. The original RGB-only
segmentation limitations have not disappeared.

Where the real images and results are kept:

- PKLot, Almeida and colleagues / UFPR, source `SRC-DS-001`, CC BY 4.0:
  `https://web.inf.ufpr.br/vri/databases/parking-lot-database/`.
- Original working images and XML: `data/raw/pklot_subset/`.
- Exact 141 fitting images / 24 development images:
  `data/manifests/region_broader_development_v1.json`.
- Failed rule: `experiments/results/REGION-CONSENSUS-20261025T104301553632Z/`.
- Revised development rule:
  `experiments/results/REGION-STABILITY-20261025T104606763875Z/`.
- Frozen final protocol, source/code/checkpoint hashes, camera-level results and
  saved comparison picture:
  `experiments/results/REGION-STABILITY-FINAL-20261025T105044848266Z/`.
- Immutable original reservation:
  `data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json`.
- Permanent consumed-image/date records: `data/holdout_claims/`.
- Source URLs, attribution/licence records and acquisition receipts:
  `data/source_manifest.csv` and `data/resource_receipts.jsonl`.

The Singapore live feed is separate. The 10:38 UTC snapshot brought persistence
matching to 14,638 later observations, MAE 4.250 spaces. It cannot measure these
image masks or this neural network's camera accuracy. Its raw JSON, normalized
history and receipts remain in the established live-data folders.

Next, explain in your own words why a higher overall score can still fail a
camera-level rule, and why a stored tracing scoring 1.000 is not a neural model
becoming perfect. Independent student explanation is still unverified.

## 26 October: runtime view-check hypothesis rejected

A prespecified TRAIN/DEVORB-homographycheck accepts1/16matching-camera pairs,0/32wrong-camera pairs;rejects48/48syntheticshifts/rotations/flips. Usabilitygatefails;notanapp/stored-geometryauthorizationgate. No finalimages/XMLorneuralcalls. SamecameraIDisnotindependentposecertification. Existingconditionalregionresults/weights unchanged. See VIEW_COMPATIBILITY_STUDY.md and models/view_compatibility_development.json;no repeatedthresholdgrid.
