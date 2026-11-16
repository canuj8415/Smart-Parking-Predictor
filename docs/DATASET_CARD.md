# Dataset investigation and first acquired source

**Update, 24 October 2026:** UCI Birmingham (SRC-DS-003) has been downloaded,
inspected and split with Python. It contains 35,717 original rows; the audit
retains 35,116. See DATASET_PROVENANCE.md, SOURCE_REGISTRY.md and
`data/dataset_inventory.json` for actual files/hashes and scope. PKLot/CNRPark
remain unacquired candidates. The older candidate investigation below remains
useful, but statements about no downloads apply to those image sources only.

Research date: 24 October 2026. Published counts are source descriptions, not
counts independently obtained by inspecting downloaded data.

## PKLot

[Official source](https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/).
Authors cited there: P. Almeida, L. S. Oliveira, E. Silva Jr, A. Britto Jr and
A. Koerich; dataset paper published in 2015.

The source describes 12,417 full images at 1280 × 720, two parking lots and three
views. Weather categories are sunny, cloudy and rainy. Directories group images
by view, weather and acquisition date. Per-image XML gives parking-space
coordinates and occupied/vacant labels, supporting roughly 695,900 slot crops.
The page offers a 4.6 GB archive and states CC BY 4.0 with paper attribution.
The linked readme PDF could not be fetched during this audit.

Suitable uses: crop classification, known-slot mapping, weather/day/view tests.
Not established: vehicle bounding-box ground truth, vehicle instance masks,
learned semantic masks, exact capture cadence, complete chronological coverage,
or extracted storage size. Inspect these before using it for forecasting.

## CNRPark+EXT

[Official source](https://cnrpark.it/). The directly opened page timed out; the
search index exposed its official content. Treat package availability and terms
as preliminary until the page and archive notices can be checked directly.

Authors listed: Giuseppe Amato, Fabio Carrara, Fabrizio Falchi, Claudio Gennaro,
Claudio Vairo. The source describes a 164-space lot. Its CNRPark subset has
12,584 patches from 242 frames and two cameras; CNR-EXT has 144,965 patches from
4,081 frames and nine cameras. These are subset counts, not 144,965 full images.
Advertised patch archives are 150 × 150 images, 36.6 MB and 449.5 MB respectively;
metadata CSV is 18.1 MB. Classes include free/busy. Filenames encode camera,
date/time and slot identity. CNR-EXT covers varied weather, shadows and occlusion
across 23 collection days between November 2015 and February 2016.
The indexed page states ODbL 1.0 for CNRPark-EXT; confirm the scope and accompanying
image-content terms in downloaded notices before redistribution.

Suitable uses: compact classification and camera generalization experiments.
Full-frame resolution, package checksums, extracted size and complete chronology
remain unverified. Different views can depict the same physical space; never
sum overlapping camera counts into lot capacity.

## Proposed selection

Evaluate a small CNRPark patch subset for the first native CNN training smoke
test, and PKLot full frames/XML for slot mapping and occupancy integration.
This is a proposal, not an approved dataset selection or an executed experiment.
Retain a held-out location/view protocol for a later generalization check.

Neither source currently proves coverage of every detection and segmentation
requirement. Research an additional original annotation source only after the
university audit defines those tasks. Do not derive vehicle ground truth by
relabelling occupied parking-space polygons.

## Data preparation acceptance plan

Manifest fields: sample ID, relative path, dataset version, source image,
camera/view, physical slot ID where known, capture timestamp/timezone status,
date/session, weather, label, dimensions, file hash, annotation path and split.

1. Preserve raw archives and notices separately from processed derivatives.
2. Validate decoded images, dimensions, labels and annotation bounds; quarantine
   invalid records with explicit reasons. Verify actual package label semantics.
3. Check exact file hashes and near-duplicates. Link every crop and augmentation
   to its original full frame to prevent sibling leakage.
4. For classification, group by camera/date/session and source frame. A proposed
   70/15/15 ratio is approximate at group level. Document which generalization
   question each split tests; never force ratios by breaking groups apart.
5. For unseen-camera claims, hold out cameras completely; for cross-location
   claims, hold out a location. These answer different questions from new-day tests.
6. For forecasting, validate time order/cadence, missing periods, stable capacity
   and deduplicated physical spaces. Split chronologically with no target windows
   crossing boundaries; fit scaling only on training data. Document any permitted
   historical context at the start of validation/test periods.
7. Apply augmentation only after splitting and only to training samples. Fit
   data-dependent normalization on training records alone.
8. Save split membership and hashes. Keep test labels out of tuning decisions.
9. Report counts by class, view, day and weather; inspect representative examples.

No image-dataset leakage audit, image-archive inspection or image decoding has run.
The independent Birmingham record split and its checks have run as documented above.

## Temporal feasibility gate

Timestamped filenames do not establish a complete operational history. Check
per-camera order and cadence, missing frames, valid slot coverage and overlapping
views. Aggregate only observed, consistently defined slots. If history is
inadequate, disable real-world forecasts, collect authorized observations, or
use an explicitly labelled simulation for teaching with faculty agreement.
Simulated scores must never appear as real parking-forecast accuracy.
