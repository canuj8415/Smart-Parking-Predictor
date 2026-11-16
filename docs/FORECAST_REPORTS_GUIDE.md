# Read and save the right forecast

The app has two saved forecasting reports. **Both use an LSTM**, a model that learns from sequences. The original predicts the occupancy level. The later variant learns a bounded change from the last count, limits it using the recent trend, and was trained with a group-relative objective so parking locations receive more balanced attention.

## Use the app

1. Open **Availability forecast**.
2. Choose **Original experiment** or **Later-date check**, then a car park.
3. Select **Show held-out forecast**. The legend and score name the actual variant.
4. Select **Save forecast results**, then choose a folder. It saves the displayed graph, a CSV, a report description and checksum records.
5. Changing the report or car park clears the old graph. Show the new forecast before saving again.

The original report says **Original LSTM**. The later one says **Group-relative residual LSTM**. These are saved historical Birmingham forecasts, not a newly generated live forecast.

| Saved report | Evaluation dates | Recorded windows | Model MAE (spaces) | Persistence MAE (spaces) |
|---|---|---:|---:|---:|
| Original LSTM | 8–11 December 2016 | 204 | 121.21 | 61.14 |
| Group-relative residual LSTM | 12–19 December 2016 | 1,853 | 31.72 | 39.07 |

These rows use different dates and windows. Compare each model with its persistence value on the same row. The score in the app describes the whole saved report, even when its graph shows only one car park.

Think of persistence as saying “there were 100 cars at the last reading, so expect 100 again.” MAE is the mean absolute counting error. An MAE of five spaces means errors average five spaces; it is not a five-percent accuracy score.

The grid targets are half an hour apart. Real matched readings in the later report occur about 10.0–29.1 minutes after the forecast origin. The original report did not save the exact sensor lead. Missing sensor times remain blank in exports rather than being filled with the grid time.

## What is saved

| File in your chosen export folder | Meaning |
|---|---|
| `forecast.png` | The displayed graph with the correct method in its legend |
| `forecasts.csv` | The displayed car park's actual, forecast and persistence counts, with method/run IDs and recorded timestamps |
| `forecast_report.json` | Method, source, archived prediction/checkpoint hashes, whole-report score and timing scope |
| `export_metadata.json` | Checksums connecting the graph, CSV and report description |

Tested examples are under `outputs/forecast_display_checks/FORECAST-DISPLAY-EXPORT-20261026T023007776153Z/`. The exact integration pointer is `reports/forecast_display_exports_latest.json`. Source records are in `data/source_manifest.csv` and `data/resource_receipts.jsonl`;SRC-DS-003 is the UCI Birmingham dataset. Immutable parent predictions stay under their unique `experiments/results/` run folders.

This fix changes names, display and exports. It does not retrain models, recalculate their old scores or reopen raw final-test data. The Singapore feed is separate aggregate availability data. The earlier copied offline demo remains a dated snapshot until the next package update.
