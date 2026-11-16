# Why the latest training ideas were rejected

Imagine practising driving in a second car park. You may improve at that new
practice route while making more mistakes on a route you previously knew.
We saw a similar trade-off in the parking classifier experiments.

| Checkpoint | Mistakes on the same2,028development examples | Wrong confident-empty decisions |
|---|---:|---:|
| Starting research comparison | 12 | 4 |
| Plain mixing of the two training sources | 20 | 6 |
| Mixing plus a teacher-retention penalty | 18 | 6 |
| Comparison selected by the fixed rule | 12 | 4 |

The teacher penalty asks the new head to stay near the starting head's answers
on the original **training** examples. It did not beat the starting comparison.
Both attempts stopped after two epochs under the fixed early-stopping rule.
The running app keeps its original production model;the starting research
comparison is a separate,previously unpromoted checkpoint.

The plain experiment corrected3development mistakes but introduced11new ones.
Most regressions were in UFPR05. This is more informative than only seeing a
net increase of8errors. The paired CSV matches the same image and space identity
before counting changes.

On the added source's16,448**already-seen training examples**,mistakes fell from
1,588to497. That shows better training fit. It does not measure accuracy on a
new car park or at night. The four previously inspected views happened to show
day/night scenes;they are not an independent exam.

The code protects three different roles:

- Training examples change model weights.
- Development examples select and compare candidates. These have been reused.
- A final test needs genuinely fresh independent data and a frozen protocol.

We did not reopen consumed final groups to rescue either result. We also did
not replace the app with a model that failed the development comparison.
All caches,failed weights,source hashes and training curves remain saved.
The difference between20and18mistakes does not isolate the effect of the
teacher penalty;runtime random-order consumption can differ between programs.

The current Excel report is linked by `reports/source_training_latest.json`.
It preserves both failed attempts and the earlier report. The paired change
records live under the run linked by `models/source_transfer_diagnostics.json`.

Next,we will qualify the captured Singapore history for a separate forecasting
study. Before any new learned predictor is tested,we must reserve a fresh future
time period across all car parks. Singapore aggregate counts can check forecasts;
they cannot grade the vehicle detector or the camera occupancy classifier.
