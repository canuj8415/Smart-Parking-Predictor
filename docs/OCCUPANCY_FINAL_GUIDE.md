# What the final parking test found

We opened the sealed exam once: six photos from three new dates on known camera views. They contained 336 labelled spaces: 236 occupied and 100 empty. Both the original model and the trained candidate answered the same questions with the same detector settings and supplied slot geometry.

| Final classifier result | Original | Candidate |
|---|---:|---:|
| Forced yes/no mistakes | 8 | 4 |
| Correct forced yes/no answers | 328 / 336 | 332 / 336 |
| Forced yes/no accuracy | 97.62% | 98.81% |

The combined app can say “needs review” instead of making a definite answer. Its counts below therefore measure a different result from forced yes/no accuracy.

| Combined final pipeline | Correct empty | Wrong empty | Wrong occupied | Needs review |
|---|---:|---:|---:|---:|
| Original with Faster R-CNN | 95 | 2 | 4 | 10 |
| Candidate with Faster R-CNN | 99 | 0 | 0 | 8 |
| Original with Mask R-CNN | 94 | 2 | 4 | 11 |
| Candidate with Mask R-CNN | 98 | 0 | 0 | 9 |

The candidate improved these overall totals. It still failed one rule fixed before opening the exam: on each camera/date, it had to keep at least 95% of the original model's correct empty-space answers. On the rainy PUCPR view, the original found all 14 empty spaces. The candidate found 13 and left one for review. That keeps 92.86%, below the fixed 95% requirement.

Imagine an attendant who avoids more wrong directions overall but overlooks one previously usable empty space in a rainy corner. Our replacement rules require both kinds of performance. **We kept the failed result and the original app model.** We have not lowered the rule after seeing the answers.

These six photos are related observations, not a universal benchmark. The UFPR04 photos show only empty spaces, so they cannot measure its occupied-case accuracy. Correct slot polygons were supplied; automatic space segmentation remains separate. Zero observed wrong-empty answers in this small candidate test does not promise zero future mistakes or live camera accuracy.

## Read the saved evidence

- Excel: `outputs/parking_final_20261026T014742Z/Smart_Parking_Final_Comparison.xlsx`. Results first; data, sources, paths and saved live-feed context second.
- CSV: the adjacent `final_slot_predictions.csv`. It has 1,344 prediction records because each of 336 source slots was checked under four model/detector configurations. These are not 1,344 independent labels.
- Full result: `models/occupancy_expansion_final.json`; exact per-frame outputs under its unique `experiments/results/` folder.
- Durable reservation and consumption records: `data/manifests/pklot_fresh_final_v2.json` and `data/holdout_claims/`.
- Training explanation and Jupyter lesson: `OCCUPANCY_TRAINING_GUIDE.md` and notebook09. The lesson now reads archived training results after the final has been consumed. It does not repeat training or final inference.

All three camera/date groups are now used, including other frames from those dates. We will not tune and test another version on them. Future model improvements need fresh final groups. The saved Excel/CSV can be reopened without repeating evaluation. A byte-identical archive copy is under `reports/occupancy_final_20261026/`.

The next independent fix is to label the app's archived forecasting methods correctly: its later-date report uses a group-relative predictor, while some current display text still says LSTM. The Singapore feed remains aggregate availability data, with its own JSON, CSV and forecast matching; it cannot grade camera recognition.
