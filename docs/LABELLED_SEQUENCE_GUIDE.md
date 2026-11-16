# Testing a real car sequence against existing labels

**Current status,25October15:00UTC:** the candidate fixes the development identity
break. The separate final sequence has now been evaluated once and is consumed.
It retained the selected car's identity in70/70scored frames, but had zero reference
crossings, so crossing recovery is unavailable and the overall final gate failed.
See notebook07 and the current-result section below. Earlier sections describe
preceding steps, not unused final data.

Imagine checking a runner with a video and a coloured outline drawn by an
independent annotator. Our detector predicts where the car is. The published
outline tells us where the selected reference car is. Comparing those two is
stronger evidence than merely seeing boxes drawn on an unlabelled video.

We acquired two original DAVIS 2017 sequences from the official archive:

| Sequence | Image/mask pairs | Project role |
|---|---:|---|
| `car-turn` | 80 | Development; first five frames provide setup/context |
| `car-roundabout` | 75 | One-use final completed; entire sequence now consumed, including setup |

The 310 original files total about 20.2 MB. Bounded archive ranges avoided
downloading the full 832.8 MB ZIP. Every original member retains a checksum and
the archive's CRC. The whole ZIP checksum is unknown, because we did not acquire
the whole ZIP. Headers and pairing were checked without decoding reserved pixels.

The dataset's original metadata does not establish the physical frame rate.
Frame 20 therefore means **the twentieth numbered image**, not “20 seconds”.
The tracker now accepts explicit frame indices and emits `frame_index` events.
Ordinary timestamped video keeps its seconds-based mode. Mixing those modes is
rejected. This avoids inventing sensor timestamps or physical speed.

The development test freezes the existing Faster R-CNN/ResNet50 model and its
thresholds. It draws a finite vertical counting line at the middle of the image.
The publisher's selected foreground object, ID 1, was visually checked as the
car in setup frame 0. Its published mask supplies a reference bounding box and
persistent identity. Reference crossings use that identity directly, without
relying on the predicted tracker's association decisions.

We measure:

- Whether a predicted vehicle box overlaps the labelled car's box by at least
  0.5 IoU on each visible scored frame. These are many frames of **one car**,
  not many independent vehicles.
- Whether the tracker keeps a consistent matching identity.
- Whether predicted crossings recover the labelled object's rule-specific
  crossings, within the predeclared two-frame tolerance.

These masks identify selected foreground objects. We cannot assume every
unlabelled road vehicle is a known negative. Extra predicted crossings therefore
do not establish exhaustive false-positive rates, precision or full traffic
accuracy. The line is in the image, not a verified parking entrance. Camera
motion may affect image-plane crossings. We make no physical-speed, exact-time,
real-time operation or parking-occupancy accuracy claim from this sequence.

The first implementation processed all 80 development frames but failed while
writing the final report. Its protocol/progress/error are preserved and no valid
score was claimed. The writer was corrected and a per-frame journal added before
rerunning the same frozen development parameters. The reserved sequence remained
unopened. The failed attempt is excluded from completed experiment counts.

Data and evidence locations:

- Official publisher: `https://davischallenge.org/davis2017/code.html`.
- Original source members: `data/raw/davis2017_subset/DAVIS/JPEGImages/480p/`
  and `data/raw/davis2017_subset/DAVIS/Annotations/480p/`.
- Original README, external-source exceptions and licence snapshots:
  `data/raw/davis2017_metadata/`.
- Verified original archive ranges: `data/raw/davis2017_ranges/`.
- Frame roles and exact image/mask hashes:
  `data/manifests/davis_car_sequences_v2.json`.
- Reserved complete sequence:
  `data/manifests/davis_car_roundabout_final_v2.json`.
- Completed development summary: `models/davis_foreground_development.json`.
- Full scored predictions, original row identifiers, per-frame journal and
  readable `observations.csv`: the scored run in `experiments/results/`.
- Every acquired file's actual URL, time, checksum and archive member:
  `data/resource_receipts.jsonl`; canonical source `SRC-DS-012` in
  `data/source_manifest.csv`.

Credit: DAVIS authors, including Jordi Pont-Tuset, Federico Perazzi and Sergi
Caelles; cite Pont-Tuset and colleagues (2017) and Perazzi and colleagues (2016).
The aggregate dataset uses **CC BY-NC 4.0**. The original README states default
author ownership, with exceptions listed in `SOURCES.md`; these two selected
sequences are absent from those exceptions. We apply the aggregate noncommercial
licence for this local academic project. The separate code repository's BSD
licence was not used as permission for the footage.

Any future final test on genuinely fresh data needs a durable **whole-sequence** claim before any reserved
pixels are decoded. Image capture dates and physical fps are unknown and will
not be invented to fit another holdout format. Frozen methods, source hashes and
partial-label limitations must remain explicit.

Singapore live availability remains a separate source. Its latest raw JSON and
normalized observations stay in the existing live-data folders; they do not
measure this detector or the car sequence's tracking accuracy.

## 25 October 2026 / licensed labelled sequences and frame-index tracking

Completed scored run: `experiments/results/DAVIS-FOREGROUND-20261025T113304928428Z/`.

| Development observation | Actual result |
|---|---:|
| Labelled car box matched | 75/75 scored frames |
| Matched tracker identity present | 74/75 frames |
| Dominant predicted identity share | 70.7% |
| Label-derived crossings of the fixed midpoint line | 0 |
| Crossing recall | Not evaluable: no reference crossing |
| Exhaustive traffic precision | Not evaluable: foreground labels only |

This is one car seen repeatedly. Tracking fragments across a gap; zero consecutive
matched-ID switches does not prove uninterrupted identity. No crossing took place
under this particular gate rule, so its zero predicted count is not a positive
counting-accuracy test. Next, a setup-only gate placement can be tested using the
saved detections, without rerunning the neural detector or opening reserved data.
`recorded_at` in detector records is the processing time, not the filming time.

Source-ID correction: DAVIS is SRC-DS-012. Early acquisition/run records mistakenly
used SRC-DS-011, which already belongs to TRANCOS. Those originals remain intact.
The explicit crosswalk and append-only receipt corrections are in
`data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json`; v2 manifests correct
metadata only, with identical original image/mask bytes and unchanged roles/results.

## Earlier14:16lesson: one crossing counted, identity break identified

Think of a guard following a car with a numbered sticker. The guard can correctly
notice it crossing a painted line, yet lose sight of it briefly and give the same
car a second sticker. Counting that one crossing correctly does not solve the
identity problem.

That is our current result. A fixed rule used only the first five labelled setup
frames to place the line at image x694. Using saved detections, the replay then
recovered the one reference crossing at frame22. No new neural training or
inference was needed. Across75scored frames the car was detected75times and
matched to a track74times, but the dominant identity covered just53frames
(70.7%). The required80%identity coverage was declared before the replay, so
the candidate **fails qualification**. One car seen75times is not75independent
cars, and1/1crossing is not proof of general accuracy.

Read and run `notebooks/06_labelled_vehicle_flow.ipynb`. Its four executed Python
cells show the real scene, the line, a simple table, source attribution and these
limitations. It displays saved evidence, never opens the final footage, and needs
no pandas installation. Its source image is the original development frame22;
the chart/box overlay is a derived illustration with DAVIS attribution.

The exact results and easy CSV are in
`experiments/results/DAVIS-SETUP-20261025T141839144041Z/`:
`protocol.json` says what was decided beforehand, `setup.json` records the first
five frames' line placement, `observations.csv` lists each frame, and `run.json`
contains actual metrics and the failed check. The illustration is
`reports/figures/davis_setup_crossing_development.png`.

The75frame final sequence remains unopened. A tested whole-sequence guard now
requires a qualified frozen method and records a durable claim before any final
pixel is loaded. Even a failed final attempt consumes the sequence. Our actual
failed selection was checked and correctly blocked without opening or claiming
that final data. Next: diagnose the identity break from the saved development
detections while preserving the rule against guessing crossings through gaps.

We have located that break: at frame26the detector still supplies a box closely
matching the labelled car, but both car/truck confidence scores are about0.637,
below the tracker's0.7cutoff. The tracker drops the identity and starts a new one
at frame27. This is an explanation from the already scored development cache,
not another trial or a fix. A future change must show that retaining a tentative
identity does not create guessed crossings or duplicate cars.

Separately, the14:16UTC Singapore collection saved raw JSON at
`data/raw/singapore_live/20261025T141637382801Z.json`; normalized observations
remain in `data/processed/singapore_live_observations.csv`. It supplied1213later
matches for previously frozen persistence forecasts. There are16897matched
outcomes in total, with an average error of4.387spaces. Missing targets stay
unscored. This measures a separate availability baseline, not camera tracking.

## Current result: identity improved; final crossing score unavailable

The separate candidate keeps an existing car's identity through an unambiguous
weaker box. It does not create a car from that weak box, inflate its score, or
use it to guess a crossing. A truly missing observation still drops identity.
This policy is experimental; the original app tracker remains unchanged.

| Saved observation | Original tracker | Candidate |
|---|---:|---:|
| Development matched frames | 74/75 | 75/75 |
| Development dominant identity | 53/75 | 75/75 |
| Development labelled crossings recovered | 1/1 | 1/1 |
| Final matched/dominant identity | 70/70 | 70/70 |
| Final reference crossings | 0 | 0 |
| Final crossing recovery | Not evaluable | Not evaluable |

In plain language: the new rule solved the observed confidence-dip problem in
development. In the separate exam, the selected car never crossed the fixed line.
We can say the car was followed, but cannot give a crossing-recovery mark. Both
trackers predicted one unmatched crossing; the publisher labels omit other
vehicles, so that prediction cannot be graded as right or wrong. The overall
final gate **did not pass**. These are two repeatedly observed cars across two
sequences, not145independent cars or universal accuracy.

The entire final sequence is now consumed, including its first five setup frames.
We will not move the line or reuse it to tune/retest a changed method. The source
manifest still records the original reservation; the durable claim/outcome in
`data/sequence_holdout_claims/` records its use. New comparisons need fresh,
legitimately labelled sequences with meaningful positive-crossing evidence.

Read `notebooks/07_confidence_continuation_and_final.ipynb` for the executed Python
lesson, before/after table and identity timeline. Notebook06 is retained as the
earlier evidence snapshot. New result cards are
`models/flow_continuation_development.json` and `models/davis_sequence_final.json`.
Each points to the exact protocol, source snapshots, metrics and observations CSV
under `experiments/results/`. All originals, weights and failed attempts remain.

The latest Singapore raw snapshot is
`data/raw/singapore_live/20261025T144748436937Z.json`, collected14:47UTC. It newly
matched1124previously frozen persistence forecasts to later observations:
18021matched outcomes total, average error4.425spaces;6237expired targets remain
unscored. Its normalized CSV stays at
`data/processed/singapore_live_observations.csv`. This separate availability
baseline still does not measure camera detection/tracking accuracy.
