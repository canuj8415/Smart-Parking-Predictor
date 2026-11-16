# Prospective live baseline collection

Start date: 24 October 2026. Source: authorized HDB/data.gov.sg availability feed,
`SRC-LIVE-001`. This protocol is separate from camera metrics and the historical
Birmingham neural-model development experiments.

At each development heartbeat, run `scripts/collect_prospective_live.py` once when
network access is available. This reuses the existing public acquisition code,
immutable raw snapshots, normalized CSV history, attribution and SHA-256 receipts.
Thirty-minute collection is slower than the source's minimum one-minute interval.
No separate background daemon or added scheduler is required. Respect a currently
running collector and do not overlap writes or make a retry storm on failure.

Fresh source readings (within three minutes) freeze an explicit persistence
forecast equal to the current available-space count. Provider timestamps without
an offset are interpreted as Singapore local time, UTC+08:00. The issue time,
snapshot path, capacity, car-park ID, lot type and forecast ID are saved before
the target observation exists. Repeated same-snapshot collection is deduplicated.

Later collected observations may score a forecast only if they are fresh, from
the same source/car park/lot type, with unchanged capacity, and were observed
20 to 45 minutes AFTER forecast issue. This is an explicit next-snapshot timing
window to allow normal 30-minute heartbeat timing variability. Record the actual
elapsed horizon for every score. It is not an exact 30-minute benchmark. Do not
backdate forecasts or score a not-yet-arrived target, stale reading or changed
capacity. Missing matches receive no fabricated score or zero error.

Storage: `data/processed/singapore_prospective/forecasts.jsonl`, `scores.jsonl`
and `summary.json`. Raw source data remain in `data/raw/singapore_live/`, with
normalized history in `data/processed/singapore_live_observations.csv`.

This first method is ONLY a non-neural persistence baseline. Accumulate reliable
source-consistent history and prespecify a neural prospective comparison before
claiming live neural accuracy. No aggregate feed can establish image detector,
semantic mask or camera-slot classification accuracy. The user's 100-experiment
live-data checkpoint still applies in addition to this defined history plan.

First actual outcome cohort was recorded at 22:45 IST on 24 October 2026:
1,098 matched observations, persistence MAE 2.228 spaces, actual horizons
21.43-24.31 minutes. These are one cohort of source-consistent aggregate counts,
not independent neural-model accuracy or a guarantee for daytime conditions.
The next collection must continue matching frozen predictions causally rather
than reconstructing earlier forecasts from already observed outcomes.


## Target lifecycle and matching coverage (25October2026)

The derived forecast_coverage summary separates scored, pending_before_window,
pending_in_window, awaiting_late_delivery and expired_missing_target. A target
can still arrive after its observation window because score_baseline allows
up to3minutes feed age and3minutes source observation lag. Expiry therefore
waits until latest_target+6minutes; it does not prematurely discard late delivery.
Duplicate forecast IDs raise a ledger integrity error. As-of queries exclude
future-issued forecasts and scores not yet recorded at that time.

matched_fraction_of_resolved_forecasts=scored/(scored+expired_missing_target),
when the denominator exists. Pending/grace entries do not enter that denominator.
This is target-observation coverage, not model accuracy. Missing targets do not
create fabricated error values. Keep issue-cohort counts with the aggregate MAE;
a collection gap can leave a whole cohort without evaluable targets. Derived
coverage can be recomputed from immutable forecast/score ledgers; it must not
rewrite historical predictions or measured outcomes. Schema addition leaves the
underlying next-snapshot persistence method and scoring windows unchanged.
