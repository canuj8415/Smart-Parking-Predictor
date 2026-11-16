# What the latest parking test means

Think of each marked parking space as a yes/no question: **is a car here?**
The existing small image classifier answered 720 such questions from 12 development
photos captured on 3 previously unused dates. It got 703 right (97.64%). There were
17 wrong forced yes/no answers. With the app's usual uncertainty bands, 14 crop
answers fell into the review band; two occupied spaces were confidently called
empty. Both were the same physical slot at different times.

This identifies a concrete reliability problem. On that particular date, only 4
predictions were confidently empty and 2 were wrong. A high overall score does not
make those empty-space directions reliable. The combined check below measures whether the app's
existing vehicle detector plus space classifier catches those errors.
No weights or thresholds have been changed. This is a development crop-classifier
diagnostic,not final-test accuracy,live accuracy or the whole app's accuracy.

| Evidence | Where it is |
|---|---|
| Original full source | `data/raw/pklot_subset/PKLot.tar.gz`;SRC-DS-001with original acquisition receipts |
| Full valid paired metadata inventory | `data/splits/pklot-archive-inventory-v1/pairs.csv`;12,218valid pairs/98camera-date groups |
| Conservative fresh-date candidates | `models/pklot_unused_date_inventory.json`;205frames over6dates absent from prior evidence dates |
| Fixed group selection | `data/manifests/pklot_fresh_group_plan_v1.json`;development3dates,final3dates reserved in full |
| Actual development data | `data/raw/pklot_fresh_v1/`;12selected development JPEG/XMLpairs plus6closed final pairs |
| Development frame checks | `data/manifests/pklot_fresh_development_v1.json`;720explicit labels,no missing labels |
| Raw-copy and source checks | `models/pklot_fresh_member_qualification.json`;36files,byte-duplicate checks and archive lineage |
| Untested final reservation | `data/manifests/pklot_fresh_final_v2.json`;6photos/3camera-date groups |
| Measured development classifier result | `models/pklot_fresh_classifier_baseline.json`;per-date metrics and frozen settings |
| Latest pointer | `reports/fresh_parking_baseline_latest.json` |

The archive scan set aside 396 file records with invalid or
inconsistent source dates; none were silently repaired. It excluded any source
date mentioned in previous model, manifest, layout or experiment JSON. This is
deliberately conservative: even a metadata-only earlier mention can exclude a
date. Candidate membership alone was not treated as proof of independence;
selected members were then matched and checked against existing receipt hashes.
Exact byte duplicates were not found. Perceptually similar images remain
possible,especially with a stationary camera.

The final files were copied and fingerprinted as raw bytes. Their JPEG pixels
have not been decoded and their XML labels have not been parsed. They remain
closed while methods are developed. A future frozen,qualified comparison must
write a durable final-data claim before reading them. Failures still consume
their whole camera/date groups;choosing another frame from the same date cannot
create a new final test. Only 6 photos are reserved for that comparison, so results
will retain a narrow scope. These are known cameras on new dates,not a new car
park. Repeated slots/photos are correlated observations.

The earlier CNR source was recovered too; its 144,965 extended records match the
official image archive and 32,079 records have reserved dates. Its image-content
permissions remain unqualified, so those images remain inspection-only. Read
`CNRPARK_DATA_QUALIFICATION.md` for the exact source and usage distinction.

Original checkpoints, the 48 recorded trials, failed attempts, the copied offline demo
and dated Excel/report/slides are preserved. The account-limit gap added no work
or scores. Live Singapore collection resumed with missed target windows left
unscored;its aggregate availability feed cannot grade this camera classifier.

## The combined app check

Imagine a parking attendant who first looks at each space, then asks a second attendant to look for cars. When the two disagree, the app says “needs review.” That is different from knowing the space is occupied. These results use the same photos and unchanged settings.

| Method | Empty answers | Wrong empty | Correct empty | Wrong occupied | Needs review | Decisions /720 | Development gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Classifier crop only | 90 | 2 | 88 | 10 | 14 | 706 | Earlier coarse gate |
| fasterrcnn + same classifier | 88 | 0 | 88 | 10 | 16 | 704 | True |
| maskrcnn + same classifier | 88 | 1 | 87 | 10 | 16 | 704 | True |

The data contain 108 truly empty and 612 occupied spaces. “Decisions” excludes review answers; compare how many useful empty spaces remain as well as wrong empty answers. The same 2 crop-only false-empty examples are traced below.

| Source photo / slot 37 | Faster R-CNN fusion | Vehicle matched | Mask R-CNN fusion | Vehicle matched |
|---|---|---|---|---|
| 2013-02-28_17_55_44.jpg | uncertain | True | uncertain | True |
| 2013-02-28_18_10_44.jpg | uncertain | True | vacant | False |

Per-date details, probabilities, matched-car overlaps and frozen gates: `models/pklot_fresh_fusion_baseline.json`. Exact per-frame app outputs and two error-photo overlays per detector: `experiments/results/PKLOT-FRESH-FUSION-20261026T005210003295Z/`. Latest pointer: `reports/fresh_parking_fusion_latest.json`. Source data locations in the earlier table remain valid.

No new model was trained here. This checks what the current app already does on known cameras on new dates. The 6 reserved final photos remain untouched. Neither this development result nor the Singapore feed establishes live camera accuracy or universal reliability.

There are still useful empty spaces being missed: on 28 February, Faster correctly says “empty” for only 2 of 6 empty spaces. Mask has one wrong empty answer among its 3 empty answers that day. Both models also wrongly call 10 empty spaces occupied overall. These limits remain even though both pass the checks set before this run. A correct “empty” count on a small development sample cannot guarantee the next driver will find an empty space.

## 26 October 2026 / expanded occupancy training and real-engine development checks

A separate expanded head now passes development classifier and both actual detector-fusion gates. On720development labels,combined candidate Faster finds99correctempty/0wrongempty/2wrongoccupied/14uncertain;Mask100/0/2/13. Final6remain unopened,original app model unchanged. Read [the new plain-language training guide](OCCUPANCY_TRAINING_GUIDE.md) and notebook09for the full before/after tables and limits.

## 26 October 2026 / once-only paired occupancy final and retained replacement failure

Later final update:the6previously sealed photos are now consumed. Candidate forced errors8->4/336and combined totals improve,but the frozen rainy-view correct-vacancy-retention check fails13/14<95percent. Original app model kept. Earlier sealed statements describe their dated training/development stage. Read [the final-test guide](OCCUPANCY_FINAL_GUIDE.md) and the new Excel report;do not replay the final.
