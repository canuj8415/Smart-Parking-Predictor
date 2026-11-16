# Qualified broader bay data and frozen source-shift baselines

Data run `ACPDS-REGION-DATA-20261027T101700848553Z` passed on all266admitted ACPDS
images:231TRAIN/35development. Every image/layout/receipt hash,role,native polygon,
byte-alias check and cache round trip passed. Allnative images are4000x3000 and
letterbox to192x144 inside256x144,with32pixels padding each side. RGB fill is
(124,116,104),image resize bilinear and mask resize nearest after native raster.
The boolean validity mask covers27648nonpadding pixels. It does not establish
certainty about every real image region. Occupancy labels are not region targets.

Manifest: `data/processed/acpds_region_v1/ACPDS-REGION-DATA-20261027T101700848553Z/manifest.json`,
SHA256 `84e99f49e42488985bea490c8ca8ce230dff844830c1f5a01eb9365c004e5937`.
Each NPZ has rgb(uint8),mask(bool),valid(bool). Total compressed cache18,231,856bytes;
valid-region foreground fractions0.042065..0.497143. Data phase57.408seconds. No
download or neural call. All266JPEG hashes unique;none equals12417known PKLot
member hashes. Unknown TEST byte aliases and transformed duplicates remain
unverified. Exact target patterns:231TRAIN/35DEV,zero exact cross-role mask overlap;
this does not prove independent physical lots or pretraining independence.

All27TESTimages/lots/views/aliases remain closed. The complete source manifest
and native-coordinate layouts were used,not the early3TRAIN+35VALID subset.
Source rights/roles remain those of SRC-DS-021,Martin Marek/ACPDS,MIT2021 notice.
Targets are derived supplied bay unions,not exhaustive facility or occupancy truth.
Two fixed lexical TRAIN overlays were visually inspected;this is data sanity,
not an annotation correctness audit or representative accuracy sample.

Frozen baseline run `ACPDS-REGION-BASELINES-20261027T102856322278Z` prespecified four
unchanged models on all35DEV images,with padding ignored and threshold0.5 fixed.
The original comparator shares the commonletterbox,uses192x112input and resizes
probabilities back;this is not a native-image app replay.

| Frozen model | Mean DEV IoU | Worst image IoU |
|---|---:|---:|
| Original U-Net | 0.325371 | 0.133651 |
| Coarse duration | 0.312125 | 0.070336 |
| RGB detail | 0.259695 | 0.070568 |
| Bounded detail | 0.310879 | 0.086255 |

Allfail mean0.80/worst0.65 absolute reference gates. Earlier familiar-camera gains
did not transfer to this development source. The template is inapplicable without
matching view geometry;none was invented. Encoder35image forwards plus140model-image
forwards are one completed baseline validation trial,not175runs. Phase6.055seconds,
no fitting or promotion. These are previously exposed DEVELOPMENT images and
derived polygon targets,not fresh final or occupancy accuracy.

Data qualification and baseline are two completed trials107->109,not perframe,
polygon,testcase or method. Fullsoftware474tests passed plus4targeted checks after
empty-batch rejection. Padding-aware masked BCE+Dice and IoU/Dice helpers ensure
padding-logit/prediction changes do not affect supervised loss/metrics and invalid
loss gradients are zero. This is not whole-model invariance to padding input RGB.
Legacy unmasked trainers are incompatible with this new cache. No model was trained
with the new helpers. Every original/best/failed checkpoint remains unchanged.

Next seal a separate mixed-source experiment with PKLot200TRAIN/30DEV andACPDS
231TRAIN/35DEV. Test all-valid loss/gradient parity against the old loss before
using a matched control,explicit source sampling,nonpadding loss/metrics,fixed
optimizer budget and source-separated validation. Retain old-view regression
controls and all prior failures;no new training or gate relaxation is implied by
this guide. Fresh rights-qualified final evidence/controller remains required.

Full paired metrics,source-shift plot and explanation are in the baseline result
folder. Source credits also include PKLot/Almeida et al./UFPR,CC BY4.0 and TorchVision
ImageNet ResNet18 under recorded local academic terms. No TEST pixels/semantics
opened;normal forbidden accesses0 and both raw/source negative controls blocked.
Notebook12/accepted offline copy remain unchanged. Student mastery,physical
offline/new-machine/manual use and official university acceptance remain open.
The Singapore learned final study remains separately closed until27Oct10:51UTC.
