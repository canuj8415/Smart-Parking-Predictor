# ACPDS development qualification

Martin Marek's Action-Camera Parking Dataset offers fresh parking views after
the previously selected PKLot groups were consumed. The [author paper](https://arxiv.org/abs/2107.12207)
explicitly includes the dataset, code and models in its MIT grant. The
[official repository](https://github.com/martin-marek/parking-space-occupancy)
is pinned at `17da2c8b33055be8019483260f0efbcbdfda0478`. Preserve the
Copyright (c) 2021 Martin Marek notice and full MIT licence in any permitted copy.
Saved primary evidence is in `docs/source_evidence/acpds_20261026/`.

The author says train, validation and test use different parking lots, with
unique image viewpoints. This is useful source evidence; we have not independently
verified locations, capture dates or pretrained-model overlap. Action-camera
photos do not establish continuous CCTV performance.

The whole publisher TEST partition, every associated lot/view/alias and its
annotations were reserved before annotation access in
`data/manifests/acpds_source_roles_v1.json`. The reader deserializes TRAIN and
VALID only. It scans the mixed JSON structurally to locate top-level boundaries;
TEST values are not deserialized or checked for semantic validity. Never load
the mixed raw JSON wholesale or use the author's loader directly on it.

The archive directory has 293 JPEG names. Development data contains 231 TRAIN
images with 7,842 spaces and 35 VALID images with 1,904 spaces. Their filenames
do not overlap. The remaining 27 archive image names default to closed, without
parsing the TEST list. No images have been acquired completely or decoded yet.
The initial footer includes 36,914 opaque noncentral compressed bytes; it is
not exclusively metadata. Exact central-directory bytes are separately retained.

The annotation member was acquired with bounded HTTP206 ranges under the same
ETag, with local header, signed data descriptor, central size and CRC agreement.
Its expanded size is 1,603,773 bytes. This is member integrity, not verification
of the entire 380,796,292-byte archive. Per-range SHA256 receipts retain actual
access times and URLs. Mixed annotations remain under ignored raw storage;
the development-only derivative and its checksum are experiment evidence.

TRAIN has 3,940 true and 3,902 false occupancy values; VALID has 831 true and
1,073 false. Values are explicit JSON booleans, consistent with the publisher
loader's int64 conversion. ROI coordinates are finite, nonnegative and in
0..1; all declared quadrilaterals have nonzero area. Image dimensions,
coordinate order and occupancy convention still need direct geometry/document
checks before cropping or reporting local accuracy. Bay polygons are supplied
geometry, not labels establishing automatic parking-region discovery or unknown
background as negative pixels.

The original protocol and two failed internal attempts are retained alongside
chained amendments. First, a header-only attempt rejected the archive's streamed
ZIP layout. Second, integer-only validation rejected publisher booleans. The
repairs did not change model thresholds, use TEST labels or add run counts.
The final callback took 1.601 seconds using already acquired ranges; this excludes
earlier discovery, network acquisition and repair work. The trial is a data
qualification run, with zero model calls and no production promotion.

Next, implement a bounded member extractor whose allowlist contains only
admitted TRAIN/VALID filenames, verify image geometry and class convention,
and record an unchanged-checkpoint validation baseline before proposing a
bounded TRAIN-only adaptation. A tested durable whole-TEST claim and frozen
acceptance gates are required before any final semantic or pixel access.
Failure must consume that final group. The author-reported 98% is not our result.

## 27 October 2026 IST / real ACPDS images qualified; unchanged classifier fails source-shift gates

The follow-on image/geometry qualification and unchanged classifier baseline are recorded in models/acpds_image_qualification.json and models/acpds_occupancy_baseline.json. Geometry passed; readiness failed. The earlier annotation-only result and its repair history remain unchanged. See docs/ACPDS_BASELINE_GUIDE.md for denominators and next steps.
