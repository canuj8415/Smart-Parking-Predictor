# Can the program mistakenly promise a free space?

Imagine arriving at a parking space because a sign says “free”, then finding a
car already there. That is a **false-vacancy** error. We measured it separately
from ordinary classification accuracy using the existing frozen models.

The new check uses 24 development photographs from six dates across three known
cameras. Their configured polygons contain 1,344 slots. Only 948 have an explicit
occupied/vacant answer in the source XML. Four photographs each lack the
occupancy attribute for 99 slots, leaving 396 slots unscored. We do not fill
those answers with guesses. Label coverage is 70.54% of these selected slots.

| Fixed method | Wrong “free” calls | All “free” calls | Uncertain |
|---|---:|---:|---:|
| Classifier at threshold 0.5 | 4 | 399 | 0 |
| Classifier with existing uncertainty band | 3 | 395 | 6 |
| Existing detector and classifier together | 1 | 388 | 13 |

All rows refer to the **same 948 labelled slots**. The classifier makes the
ordinary occupied/vacant decision at 0.5. The uncertainty band calls a space
vacant only when its occupied score is at most 0.25, occupied when it is at least
0.75, and otherwise uncertain. These scores are not safety guarantees.

The existing detector adds another check. If it matches a vehicle to a space
that the classifier calls vacant, the program returns uncertain. In this trial,
that changed seven vacancy calls: two were occupied according to the source
labels, and five were vacant. The extra caution caught two risky errors and
withheld five otherwise correct vacancy calls.

One false-vacancy case remains: UFPR05, slot 40, on 21 March 2013. The saved
diagnostic figure shows the actual masked crop, its low occupied score, and the
remaining wrong decision. We retain the case rather than tuning the thresholds
after seeing this evaluation.

The combined pipeline's wrong-free fraction is 1/388, or 0.26%, among its free
calls. It answers 935/948 labelled cases and leaves 13 uncertain. Accuracy among
those 935 answered cases is 98.82%. These denominators differ. Neither figure
is a complete-camera, new-camera or whole-project accuracy percentage.

The proposed diagnostic rule asks for at most 1% wrong-free calls overall, at
least 80% decision coverage, and at most 2% wrong-free calls in each camera with
enough free predictions. The classifier alone fails the camera check. The
existing combined pipeline passes this limited diagnostic. The remaining error,
missing labels and small number of date groups still matter.

No weights, thresholds or application rules changed. This is additional evidence
about the current implementation. The original 95.28% score on 360 test crops
remains a separate historical result with a different sample composition. The
parking-region model and forecasting models retain their own acceptance failures.

Evidence and data locations:

- Frozen classifier: `experiments/results/OCCUPANCY-BROADER-20261025T084307397022Z/`.
- Existing combined pipeline: `experiments/results/OCCUPANCY-FUSION-20261025T084837737165Z/`.
- Row-level answers and predictions: `observations.csv` and `predictions.json` in
  the combined-pipeline folder.
- Exact missing-label record: `data/manifests/broader_occupancy_label_coverage_v1.json`.
- Original photographs/XML: `data/raw/pklot_subset/`; originals remain unchanged.
- Source URLs, licence and acquisition receipts: `data/source_manifest.csv` and
  `data/resource_receipts.jsonl`.

PKLot, Almeida and colleagues / UFPR, [publisher page](https://web.inf.ufpr.br/vri/databases/parking-lot-database/),
CC BY 4.0, provides the original images
and labels. The project adds masked crops, model outputs and diagnostic figures.
The publisher page describes XML occupancy annotations, but the reviewed page
does not establish a default for missing attributes. The official readme fetch
timed out. Our declared evaluation policy keeps those attributes unknown.
