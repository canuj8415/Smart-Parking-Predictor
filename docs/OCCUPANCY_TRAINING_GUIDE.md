# What the extra training achieved

Imagine an attendant who learned from two parking-camera views. We now gave that attendant labelled practice photos from a third view too. We trained a separate candidate, while keeping the original app model intact.

| Data | Photos | Separate dates | Labelled spaces | Missing answers excluded |
|---|---:|---:|---:|---:|
| Training: practice with answers | 170 | 32 | 10,104 | 704 |
| Validation: choose and check the model | 45 | 12 | 2,028 | 396 |
| Final test: sealed exam | 6 | 3 camera/date groups | Still unknown | Not read |

Dates stay in one role. Different spaces in one photo and repeated photos of the same car park are related observations, not thousands of independent scenes. Missing labels never mean “empty.” All three camera views appear in training and validation.

The ResNet image features stayed fixed. Only its small final decision layer learned new weights. Training stopped after eight passes through the training data; the second pass performed best on validation. Continuing to reduce training loss made validation loss worse, which suggests overfitting. We kept the earlier checkpoint.

| Classifier on the same 2,028 validation spaces | Original | Candidate |
|---|---:|---:|
| Wrong forced yes/no answers | 46 | 12 |
| Forced yes/no accuracy | 97.73% | 99.41% |
| Confident wrong “empty” answers | 6 | 4 |
| Correct confident “empty” answers | 622 | 665 |
| Confident wrong “occupied” answers | 29 | 5 |
| Needs review | 33 | 19 |

Forced yes/no accuracy and review-band counts are different ways of examining the same predictions; do not add their counts together. On the smaller, recently selected 720-example development set, forced mistakes fell from 17 to 6. These are development results used to select the candidate, not its final-test accuracy.

We then loaded the candidate into the actual app engines for the same 12 development photos. The detector can flag a disagreement with the space classifier for review. Known slot geometry was supplied; this check does not prove automatic parking-space segmentation.

| Combined pipeline: 720 development spaces | Correct empty | Wrong empty | Wrong occupied | Needs review |
|---|---:|---:|---:|---:|
| Original + Faster R-CNN | 88 | 0 | 10 | 16 |
| Candidate + Faster R-CNN | 99 | 0 | 2 | 14 |
| Original + Mask R-CNN | 87 | 1 | 10 | 16 |
| Candidate + Mask R-CNN | 100 | 0 | 2 | 13 |

No wrong “empty” answers were observed in the candidate's combined check on these development photos. Other errors and review answers remain. This is not a promise about the next driver, another camera or live operation.

The candidate passed the checks fixed before training and before the combined evaluation. **It has not replaced the app model.** Next comes one frozen paired comparison with the six sealed final photos. Their pixels and answer labels remain unopened. A failed final evaluation would still consume those dates.

## Where the real data and results are

| Item | Saved location |
|---|---|
| Original licensed PKLot archive | `data/raw/pklot_subset/PKLot.tar.gz` |
| Selected training/validation JPEG/XML copies | `data/raw/pklot_occupancy_expansion_v1/` |
| Exact files, dates, roles, hashes and label counts | `data/manifests/occupancy_expansion_v1.json` |
| Source creator, URLs, terms and receipts | `data/source_manifest.csv`; `data/resource_receipts.jsonl`; `docs/THIRD_PARTY_SOURCES.md` |
| Data qualification | `models/occupancy_expansion_data_card.json` |
| Training, epoch curves, checkpoint and validation details | `models/occupancy_expansion_candidate.json`; its unique `experiments/results/` folder |
| Combined detector check | `models/occupancy_expansion_fusion_candidate.json` |
| Easy summary | `reports/occupancy_training_latest.json` |
| Executed Python/Jupyter lesson | `notebooks/09_occupancy_training_and_tradeoffs.ipynb` |

Open lesson09 to see the real learning curves, comparison tables, remaining errors and questions to practise explaining. It reads saved results rather than training again. No student answers or understanding have been assumed.

The Singapore live feed has its own raw JSON snapshots, normalized CSV history and later-observation forecast scores. It cannot grade camera detections or these occupancy labels. The existing Excel/PDF/slides and copied offline demonstration remain dated earlier snapshots.

## 26 October 2026 / once-only paired occupancy final and retained replacement failure

Later final update:the6previously sealed photos are now consumed. Candidate forced errors8->4/336and combined totals improve,but the frozen rainy-view correct-vacancy-retention check fails13/14<95percent. Original app model kept. Earlier sealed statements describe their dated training/development stage. Read [the final-test guide](OCCUPANCY_FINAL_GUIDE.md) and the new Excel report;do not replay the final.
