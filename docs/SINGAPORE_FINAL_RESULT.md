# Singapore frozen prospective study

The frozen trend model reduced paired mean absolute error by 15.53%,
from 7.338578 to 6.198763 parking spaces. The final acceptance gate FAILED:
the worst origin regressed by 0.514513 spaces,
exceeding the prespecified 0.5-space limit. No threshold was relaxed and no app model was promoted.

There were 23,960 genuine pre-target forecasts, 18,557 matched
later observations (77.45%), 18 matched
global origins and 1,337 carpark/lot-type series. Missing forecasts have
no invented target or zero error. Targets fall within the frozen 20â€“45-minute observation window;
this is not an exact 30-minute benchmark. Forecasts within an origin are correlated.

All seven frozen checks: {"macro_origin_noninferior": true, "matching_coverage": true, "minimum_global_origins": true, "minimum_matched_forecasts": true, "minimum_series": true, "no_material_origin_regression": false, "raw_mae_gain": true}.

The global final interval is consumed, including all carparks, aliases and failed evaluations.
Do not tune or retest a changed method on it. An overall average gain does not erase a failed
origin-retention gate. Any future method needs a new protocol and fresh future interval.
The Birmingham LSTM is a separate model; this result establishes no camera/segmentation/
occupancy accuracy or universal guarantee. Local acquisition/commit clocks are audit evidence,
not independent external timestamp attestations. Missed account-limit periods were not backfilled.

Source SRC-LIVE-001: official data.gov.sg parking availability; Singapore Open Data Licence 1.0.
This report renders saved metrics only. It does not open raw target JSON or run the scorer again.
Result: SG-FINAL-20261027T105114261864Z; SHA256 82d50469b1ff858f08ec1acb80e4e73ede8ea56ac093803e855fef7d15ce17d7.


Continuation: Next seal a bounded mixed-source region experiment: PKLot200TRAIN/30DEV plus ACPDS231TRAIN/35DEV. Read models/acpds_region_dataset.json and models/acpds_region_baselines.json. Specify matched coarse-FPN control, source sampling, identical initialization/fixed optimizer step budget, validation-based selection and source-specific absolute/old-view retention gates BEFORE fitting. Do not sweep thresholds on the same development cohort.

Software checks: 475 tests passed; all-valid loss/gradient parity passed36 seeded cases.
