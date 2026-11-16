# The later-date forecasting check

Imagine a parking sign currently says 50 free spaces. Predicting “still 50” is
our simple baseline. If a model predicts 45 and the later reading is 40, its error
is five spaces. We average the size of those errors; lower is better.

The frozen candidate has now passed a one-time check on eight later Birmingham
dates, 12–19 December 2016. These dates were absent from the original archived
forecast test predictions. This is a temporal holdout from the existing public
dataset, not newly collected external data or a physically blinded study.

| Same 1,853 later-date windows | Average error, spaces |
|---|---:|
| Frozen group-relative LSTM | 31.72 |
| Predict the current count again | 39.07 |
| Original production LSTM | 87.72 |

The candidate's error is **18.8% lower than persistence**. It passes the frozen
overall and per-car-park rules: at least 5% overall improvement, no more than 10%
regression for parks with at least ten windows, and sufficient date/park coverage.
All eight dates and 29 eligible parks were represented. This does not mean
81.2%, 100%, or universal forecasting accuracy. Windows overlap and are correlated.
An average error of about 32 spaces can still matter in a real car park.

There is an important timing limit. The targets sit on a half-hour grid, but
their matched real readings arrive **10.02–29.12 minutes after the origin**.
Most are between 15 and 25 minutes. We retain those actual source times and
report errors by lead-time band. This is not an exact 30-minute sensor benchmark.

Why does this check contain more dates than the earlier result? The original
grid used clock minutes 00 and 30. Many real readings arrived just after those
points and were too old for the next point under our 20-minute age rule. We
compared offsets using training-window counts alone, selected minutes 10 and 40,
and froze that choice before checking the later development outcomes. The
candidate was not retrained or selected using final outcomes.

On that broader development construction, 2,539 windows covered all ten dates;
error was 35.04 versus persistence 43.79. That passed its additional coverage
rules before any numeric reserved-date outcomes were parsed. The old 322-window
result remains a separate, sparse-cohort result, not a directly comparable score.

Before final parsing, a durable record claimed the whole source/date groups and
bound the exact model, protocol and original source checksum. A failure would
also have consumed these dates. The evaluation completed, so all eight dates are
now consumed. **Do not use them to tune a model or evaluate changed methods.**
Displaying saved predictions and checking their arithmetic does not rerun models.

In the Python desktop app, open **Availability forecast**, choose **Later-date
check**, choose a car park, and click **Show held-out forecast**. The graph reads
the saved historical result. **Original experiment** retains its own older dates
and worse published result. Changing reports clears the old graph first. The
original production weights and default report remain unchanged; this feature
does not generate Singapore or camera forecasts. Hidden native-widget/graph
checks passed, but visible layout and physical-user acceptance still need checking.

Where the data and evidence are kept:

- Source `SRC-DS-003`: UCI Parking Birmingham,
  `https://archive.ics.uci.edu/dataset/482/parking+birmingham`.
- Original archive: `data/raw/uci_parking_birmingham/parking-birmingham.zip`.
- Original row identifiers and prepared data:
  `data/splits/birmingham-global-days-v1/manifest.csv`.
- Training-only phase choice and broader development result:
  `experiments/results/FORECAST-PHASE-20261025T101202713070Z/`.
- Frozen final protocol, exact code, predictions and readable `observations.csv`:
  `experiments/results/FORECAST-FINAL-20261025T101729300425Z/`.
- The reserved identifiers remain immutable in
  `data/manifests/forecast_fresh_dates_v1.json`; consumption records are separate
  in `data/forecast_holdout_claims/`.
- Display checks and test logs:
  `experiments/evidence/HEARTBEAT-20261025T100726Z/`.
- Creator/licence details, URLs and real acquisition receipts remain in
  `data/source_manifest.csv` and `data/resource_receipts.jsonl`.

The Singapore feed remains separate. At 10:09 UTC its 19th saved snapshot brought
the prospective persistence study to 13,501 matched later observations, MAE
4.191 spaces. That is a different location/sample and does not measure this
Birmingham neural model's live accuracy or the camera models.

The whole project is still unfinished. Parking-region segmentation still fails
its acceptance rule, one observed false-vacancy case remains, real labelled flow
accuracy is unmeasured, and offline/native-UI/report/student checks remain.
