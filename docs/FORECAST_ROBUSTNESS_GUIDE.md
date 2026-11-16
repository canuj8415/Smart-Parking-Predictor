# What improved in forecasting?

Imagine a car park has 20 free spaces now. The easiest forecast is “there will
still be 20 later”. This is **persistence**, our baseline. A neural network must
beat that simple answer to be useful. If it predicts 20 and the later count is
14, its error is six spaces. MAE is the average size of those errors; lower is
better. It is not an accuracy percentage.

Our earlier model could improve the overall average while making some car parks
worse. Think of a class average hiding two struggling students. The new training
procedure gives each car park a share of the score and also pays attention to the
worst relative error. It measures difficulty using only earlier training data.

The network is still a Python LSTM that learns a limited correction to “stay the
same”. It keeps the existing recent-trend constraint. Three expanding blocks
inside the training history choose one training duration. The model then trains
again on all training windows for that fixed duration, and its checkpoint is
saved before the later development outcomes are opened.

| Same development cohort | Average error, spaces | Existing development gate |
|---|---:|---|
| Stay-the-same baseline | 40.22 | Comparator |
| Earlier trend model | 20.90 | Fails the per-car-park check |
| New group-relative model | 30.20 | Passes |

The new model reduces error **24.9% relative to persistence** on 322 development
windows. It does not have the lowest overall error among the earlier candidates.
Its useful result is passing both existing checks: at least 5% overall improvement
and no more than 10% per-park regression where a park has at least ten windows.
There are 26 such parks; a further park has only three windows. All 27 show lower
observed MAE here, but those small, correlated samples do not guarantee future
performance. The two historical candidates also use slightly different numerical
reporting paths; differences below 0.001 spaces do not explain the displayed gap.

The nominal target is a half-hour grid point. Its matched real readings occur
19.32–29.37 minutes after the forecast origin here, so this is not an exact
30-minute sensor benchmark.

These development dates have been reused across project experiments. This is not
an independent final result. The selected duration reached the predeclared cap of
80 epochs; that does not prove convergence or justify extending training after
looking at these outcomes. The original app model remains unchanged.

Eight later Birmingham dates, 12–19 December 2016, are now reserved: 3,844 source
rows from 29 car parks. They are absent from the archived original forecast test
predictions. This is the existing public source, not newly collected external
data or a physically blinded collection. The reservation selected identifiers
and timestamps; it did not parse numeric final outcomes or score the candidate.

There is a further data issue to resolve first: the original fixed half-hour
grid produces relatively few admissible windows. Training used 787 windows on
ten dates; development used 322 on four dates. The reserved later dates may not
yield enough windows under that rule. We must fix and test any window/timing
procedure on training/development alone, then use a durable one-time final-data
guard. The legacy test loader is blocked while these dates are reserved. We will
report unavailable evidence honestly if suitable final examples cannot be formed.

Where the real data and results are kept:

- Birmingham source: UCI **Parking Birmingham**, source `SRC-DS-003`, at
  `https://archive.ics.uci.edu/dataset/482/parking+birmingham`.
- Original download: `data/raw/uci_parking_birmingham/parking-birmingham.zip`.
- Prepared rows and original row identifiers:
  `data/splits/birmingham-global-days-v1/manifest.csv`.
- Frozen protocol, source snapshots, training curves, fold row lists, candidate
  weights and row-level `observations.csv`:
  `experiments/results/FORECAST-GROUP-ROBUST-20261025T094258007427Z/`.
- Reserved future-date identifiers: `data/manifests/forecast_fresh_dates_v1.json`.
- Teaching notebook: `notebooks/05_forecast_robustness.ipynb`.
- Original URLs, licence details and actual acquisition checksums:
  `data/source_manifest.csv` and `data/resource_receipts.jsonl`.

The Singapore live feed is a separate source and location. Its 09:38 UTC snapshot
and normalized history are under `data/raw/singapore_live/` and
`data/processed/singapore_live_observations.csv`. At that checkpoint, 12,402
previously frozen persistence predictions had matching later readings, with MAE
4.109 spaces. That is a different task/data sample; it is not this Birmingham
neural model's live accuracy, camera accuracy or a fair head-to-head comparison.

## 25 October 2026 / clock coverage and one-time later-date forecast evaluation

Later update: the timing-coverage study and one-time reserved-date evaluation have now completed. The earlier322window scores above remain their historical cohort. Read docs/FORECAST_FINAL_EVALUATION.md for the1853window result, actual10.02–29.12min target leads, consumed-date restrictions and app report instructions.
