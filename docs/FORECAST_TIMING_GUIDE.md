# Why “30 minutes” needs a clock check

Imagine asking at 9:00: “How many spaces will be free at 9:30?” The car park's
sensor does not send readings exactly on the half-hour. Our historical experiment
places real readings onto a half-hour timetable by taking a prior reading no
more than 20 minutes old. It never fills from a future reading.

In this **made-up teaching example**, the 9:30 timetable entry uses a sensor
reading from 9:10. The answer used for scoring came only 10 minutes after the
9:00 forecast, even though the timetable says 30 minutes.

| Clock item | Teaching example | Meaning |
|---|---|---|
| Forecast origin | 9:00 | When the prediction is issued |
| Last input reading | 8:50 | What the sensor most recently reported |
| Grid target | 9:30 | The nominal forecast target |
| Actual target reading | 9:10 | The real measurement used for scoring |
| Target reading age at grid time | 20 minutes | 9:30 minus 9:10 |
| Actual target lead | 10 minutes | 9:10 minus 9:00 |
| Reading-to-reading interval | 20 minutes | 9:10 minus 8:50 |

The code now keeps all these timestamps and ages in new window records. Future
candidate prediction exports retain the same details. Existing data, features,
trained weights and old experiment files remain unchanged.

For the **actual 322 Birmingham development windows**, the scored readings were
19.32–29.37 minutes after the forecast origin; the median was 28.77 minutes.
The reading-to-reading interval was 19.98–40.05 minutes. These are different
clock comparisons, so they must not be called one exact 30-minute sensor test.
The original source does not specify a timezone; we preserve its wall-clock
timestamps and do not label them UTC.

| Actual target lead | Windows | Frozen candidate MAE | Persistence MAE |
|---|---:|---:|---:|
| 10–15 minutes | 0 | Not evaluable | Not evaluable |
| 15–20 minutes | 8 | 16.95 spaces | 7.12 spaces |
| 20–25 minutes | 1 | 10.52 spaces | 13.00 spaces |
| 25–30 minutes | 313 | 21.04 spaces | 41.15 spaces |

MAE is the average absolute error: an error of 7 spaces means the prediction
missed the recorded count by 7 spaces on average in that group. Lower is better.
The one-window and eight-window groups are too small to establish reliability.
An empty group has no score; it does not have perfect zero error.

The earlier trend candidate's overall development MAE remains 20.9015 spaces
against persistence at 40.2205. Its acceptance gate still fails because some
car parks regress. The audit reuses saved development predictions and adds no
independent final-test or live-model evidence. Nothing was retrained or promoted.

Evidence: `experiments/results/FORECAST-TIMING-20261024T234223029035Z/` contains
the frozen protocol, exact source/code hashes, timestamped CSV/JSON, before/after
window comparison and figure. The app now describes **30-minute grid targets**.
Its updated wording has software checks; no new desktop visual inspection is
claimed. The Singapore live feed has a separate actual-later-observation protocol
and does not validate this Birmingham neural model or any camera predictions.

Data source: UCI Parking Birmingham, source ID SRC-DS-003,
https://archive.ics.uci.edu/dataset/482/parking+birmingham . Original files and
acquisition evidence remain under `data/raw/uci_parking_birmingham/` and
`data/resource_receipts.jsonl`.
