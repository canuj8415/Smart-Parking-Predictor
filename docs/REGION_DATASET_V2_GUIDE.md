# Qualified bay-footprint dataset, 27 October 2026

The dataset is ready for a bounded image-only segmentation experiment. No model
was trained or promoted during this qualification. The target is the union of
the parking-bay polygons supplied by PKLot: it does not label every parking area,
identify individual slots, or establish vehicle occupancy.

Run: `REGION-DATA-V2-20261027T054847435415Z`. Source: SRC-DS-001, the preserved
official UFPR PKLot archive. Existing source and licence records apply. The
original archive is 3,860,376,865 bytes, SHA256
`df182f46184fc29fb7ef3cd293b49cae52599365d9fe9415c4e7e7ea7ded9f79`.

| Camera | TRAIN images | Development images |
|---|---:|---:|
| PUCPR | 80 | 8 |
| UFPR04 | 72 | 6 |
| UFPR05 | 48 | 16 |
| Total | 200 | 30 |

Seed 168 selected four images per existing TRAIN date and two per development
date, from the current 50 TRAIN and 15 development groups. All 17 consumed final
groups and 16 unresolved groups remain excluded. No new group was admitted.
These are familiar source cameras, and development is available for selection;
neither constitutes fresh final or unseen-camera evidence.

Before decoding selected images or reading their annotations, the runner hashed
all 12,417 JPEG members, including unindexed names as protected unknown groups.
All hashes were unique: no exact cross-group byte aliases or selected duplicate
JPEGs were found. Hash-connected groups would have been excluded conservatively.
This detects exact copies, not transformed or perceptually similar images.
Closed and quarantined JPEGs were used only as opaque bytes; their images and
XML labels were not decoded or parsed.

The 230 admitted pairs produced RGB arrays at 256 x 144 (bilinear resize) and
boolean union masks (nearest-neighbor resize of native polygon masks). XML
geometry is validated against native image dimensions. Occupancy labels are not
training targets. Each compressed NPZ was read back exactly; no frame failed.
The arrays total 22,314,729 bytes. Foreground fractions range from
0.1047092013888889 to 0.2151421440972222. Source-member, raw-asset and cache hashes
are recorded for every pair, with 460 acquisition receipts. The measured
qualification phase took 72.303 seconds, after initial input/archive checks and
excluding protocol preparation and later visual review.

The manifest is
`data/processed/pklot_region_v2/REGION-DATA-V2-20261027T054847435415Z/manifest.json`,
SHA256 `640dee731bd7d070fda114a86b534c9d646e3fc05e56431e910d7be938cffc9b`.
Raw images/XML and NPZ arrays remain local and are not duplicated into Git or the
accepted offline demo. An exact manifest copy, source snapshots, per-frame
journals, full byte-hash table, protocol binding and three TRAIN overlay examples
are retained in the experiment result folder. The original archive plus the
sealed protocol identifies every selected member if caches need reconstruction;
the completed runner refuses to overwrite a recorded result.

Three first-admitted TRAIN overlays, one per camera, were visually inspected.
The polygons align with the supplied bay footprints. This is a sanity check,
not an independent annotation audit or an accuracy sample. Software regression:
456 tests passed, including five split-admission tests. The normal offline
file-access audit recorded zero forbidden accesses; its unqualified-image
negative control was blocked.

Next experiment: implement a separate frozen ImageNet ResNet18 feature pyramid
with a small binary decoder, using these RGB arrays and masks. Record source,
config and split hashes and freeze the training/selection gates before fitting.
Use bounded CPU execution, checkpoints, cancellation and early stopping. Compare
the chosen checkpoint on exactly these 30 development images against the
original image-only U-Net and a distinctly labelled TRAIN-only camera-template
baseline. Static camera geometry can make this task easy without demonstrating
image-driven generalization; the template comparison is essential. Report
per-camera and per-image IoU/Dice, not only pooled pixels. Do not sweep thresholds
or relax failed gates to obtain a pass. The recipe and numeric gates are not yet
sealed; no predictions have been inspected on this cohort.

Save new candidate weights in a separate run directory. Never run the legacy
segmentation training entry point, which writes the original checkpoint. A
development pass alone does not authorize final testing or production promotion.
Fresh, rights-qualified final groups still need a separate reservation and claim.
The accepted offline copy and all original/best/failed checkpoints are preserved.
