# Learning to forecast from the real Singapore readings

Think of writing down the empty-space count every half hour. Keeping the last
count is our simple comparison forecast. A learned predictor must beat that
comparison on the same later observations before we consider enabling it.

| Step | Actual result |
|---|---|
| Frozen historical input | 46 official snapshots received before 26 October 2026, 07:46:23 UTC |
| Fresh admitted observations | 56,136; stale records excluded, originals retained |
| Training | 18,393 windows, 18 global collection times |
| Development | 9,202 windows, 9 global collection times |
| First learned trial | Linear ridge: 7.74 spaces error; rejected |
| Second learned trial | Absolute-error trend learner: 6.31 spaces error |
| Last-count comparison on the same windows | 6.96 spaces error |
| Current decision | Trend candidate frozen for a prospective study; app unchanged |
| Real logging milestone | 1,110 pre-target forecasts saved at 26 October, 12:09 UTC; unscored |

We know when each downloaded value actually became available because its
acquisition receipt records the time. A source's update time is not necessarily
the time our laptop received it. The features use only information already
available at the forecast issue time. Training targets also have to arrive
before the global training cutoff. Car parks and lot types are not mixed.

An example needs two recent observations with the same capacity and a later
matching reading. We do not fill missing periods with invented observations.
The target window is 20–45 minutes after issue. In this development cohort, the
actual leads are 27.30–43.01 minutes. This is not an exact 30-minute benchmark.
Thousands of car parks at nine times are still only nine global development
times; they are not thousands of independent days.

The second trial learned **one coefficient from training data only**: approximately
0.30. For example, if available spaces rose from 40 to 50 over the past half hour,
it predicts about 53 next time: the last count plus 30% of the previous increase.
Predictions stay between zero and the car park's capacity. Future target values
and the eventual target's actual lead time are never inputs.

The coefficient minimizes absolute error in the *unclipped change in space count*.
This differs from the first trial's squared error in normalized counts. It is a
small learned statistical baseline, not a neural network. The coefficient was
fitted once; no grid was selected on development results.

The trend trial reduced development error by about **9.3%**. It also passed the
rules fixed before fitting: at least 1% overall improvement, no worse average
error when each collection time has equal weight, and no individual collection
time worsening by more than half a space. Two times did worsen slightly; passing
these rules does not mean every car park or every future period improves.

Before fitting, we reserved a fresh future period across **all car parks**:

- Forecast origins: 26 October 10:00 UTC to 27 October 10:00 UTC.
- The selected model must be frozen before the first origin.
- Final target/delivery window closes 27 October 10:51 UTC.
- In India, the origin period is 26 October 15:30 to 27 October 15:30.

These future results have not been scored. A future evaluation requires
a candidate that passes development, a frozen checkpoint, and predictions really
committed before their targets arrive. The once-only guard consumes the global
period before a scoring callback reads targets;failure does not reopen it.
The learned-forecast issuer is implemented and tested with synthetic fixtures.
Its actual pre-period check correctly issued zero predictions. It records each
later eligible batch and its checksum in exclusive files with local clock times,
along with the raw acquisition receipts used for both input counts. These are
local audit records, not independent external timestamp attestations.

The frozen study configuration is `data/manifests/singapore_trend_issuance_v1.json`.
It was saved at 08:16 UTC, before the 10:00 UTC origin period. The collector command
is `python scripts/collect_singapore_study.py`; it respects the existing 30-minute
history plan and the publisher's minimum one-minute interval. No further training
or coefficient changes are allowed for this reserved study.

The final scoring callback is now implemented, tested and frozen at 08:53 UTC
on 26 October, before the reserved origin period. The frozen plan requires at least
500 matched forecasts across eight collection times and 50 series, at least 75%
matching coverage, paired last-count comparison, and the same improvement rules.
Missing targets stay unscored. If no eligible forecast was issued, we report the score as unavailable.
We cannot generate predictions after seeing the answers and call them live tests.

Run `python scripts/score_singapore_study.py` **only for this frozen study**. Before
27 October 10:51 UTC it reports `not_ready`, without decoding target JSON or
creating a final claim. After closure it checks the actual batch receipts,
reconstructs the saved predictions, claims the entire source period, and then
reads the later targets. It uses the first received qualifying target, even if a
later reading would give a better score. A fresh capacity change stops matching.

The result saves paired observation CSV, unmatched forecast IDs and reasons,
input checksums, the claim outcome and a completion receipt. A scoring failure
still consumes the period. Repeating a successfully completed command displays
its archived result; it does not run a new evaluation. No eligible issuances mean
the accuracy is unavailable, and zero matched targets produce null errors rather
than perfect scores. A final pass would still require separate app integration.

The software checks used **synthetic fixtures**, kept separately from real data:
700 issued forecasts, 688 matches and 12 missing targets across 12 times and
60 simulated car parks. Predictability was deliberately built into that fixture
to check the arithmetic. These numbers do not establish real-world accuracy.
All 284 software tests pass. The real pre-period scoring check returned pending;
no learned live or final result has been measured yet.

The first ridge trial remains rejected and preserved. The trend candidate has
passed development only; there is no learned live or final performance claim.
New readings collected after the historical cutoff can supply causal context for
frozen-model prediction, but cannot be used to refit this study's model.

Data locations:

- Original public JSON: `data/raw/singapore_live/`.
- Download URLs, times and SHA256 receipts: `data/resource_receipts.jsonl`.
- General normalized history: `data/processed/singapore_live_observations.csv`.
- This study's sealed example CSV: `data/processed/singapore_history/SG-HISTORY-20261026T074623970649Z/examples.csv`.
- Future reservation: `data/manifests/singapore_forecast_reservation_v1.json`.
- Frozen scoring implementation: `data/manifests/singapore_trend_scoring_v1.json`.
- Results and checkpoint references: `reports/singapore_forecast_study_latest.json`.
- Future learned batches: `data/processed/singapore_learned_v1/batches/`.
- Immutable batch receipts: `data/receipts/singapore_learned_v1/`.
- Software validation evidence: `reports/singapore_final_software_validation_latest.json`.

The general history continues growing. It now includes observations that are
excluded from this study's frozen training/development data. The existing rolling
persistence score and this development score use different cohorts,so their
MAE numbers must not be treated as a before/after model comparison.

Source: Singapore's official [car-park availability feed](https://api.data.gov.sg/v1/transport/carpark-availability),
SRC-LIVE-001, Singapore Open Data Licence 1.0, under the user's accepted terms.
Aggregate availability counts cannot grade vehicle detection or camera occupancy.
The Birmingham LSTM's result is a separate dataset and is not Singapore validation.

The first real learned batch has now passed a separate metadata-only integrity
check: 1,110 unique forecasts from one issue time, with valid commit times,
frozen-model reproduction and two original raw-file checksums. No raw target
JSON was decoded or learned error calculated. Raw semantic context verification
stays inside the once-only final callback. Routine health checks are not new
experiments; see `docs/SINGAPORE_ISSUANCE_HEALTH.md`.

## Read-only Python/Jupyter lesson

Open `notebooks/10_singapore_forecast_study.ipynb` for an executed explanation of
receipt times, the paired development comparison, the synthetic trend example,
and missing-target arithmetic. Its seven code cells ran in an actual Jupyter
kernel without installing pandas or another new package. It reads archived
development CSVs and frozen metadata; it never calls training, collection,
issuance or final evaluation, and does not load a growing final-result status.

The validation used project-file and Python socket audits, with expected blocked
probes for protected reads, study writes and external DNS. These are bounded
Python checks, not an OS security boundary or proof of physical disconnection.
The saved chart was visually inspected. Student explanations and a manual
browser rehearsal remain unassessed. The dated offline demo package is unchanged
and does not yet contain this lesson.

A separate minimal lesson folder now passes an actual relocated Jupyter run
using the existing offline-installed environment. It preserves all original
payload bytes and includes no raw/growing/final observations or operational
training/collection/scoring code. It requires an installed Python/Jupyter
runtime. See `docs/SINGAPORE_LESSON_PACKAGE.md`; the full app bundle is unchanged.
