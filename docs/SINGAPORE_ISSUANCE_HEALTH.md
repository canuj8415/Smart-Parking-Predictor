# Check that forecasts were recorded correctly

The first real learned batch contains **1,110 forecasts**, issued at
26 October 2026, **12:09:52 UTC** and receipted within the following second.
Its declared target window is 12:29:52–12:54:52 UTC. It uses the candidate and
rules frozen before the reserved study began. This is evidence that forecasts
were logged before their targets, not evidence of their accuracy.

Run the routine integrity check from the project folder:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/check_singapore_issuance_health.py
```

It checks the recorded batch and acquisition receipts, file checksums, frozen
model/configuration, unique forecast IDs, target-window declarations, issue and
commit times, and physically bounded predictions. It reproduces predictions
from their saved inputs. Each original raw file is hashed only once per check.
It does **not decode raw observations, match targets, calculate learned errors
or create a final claim**. Raw semantic input authentication is deliberately
deferred to the once-only final callback; health is about the recorded metadata,
not current feed freshness or prediction accuracy. Local clock receipts are
audit evidence, not independent external timestamp attestations.

Results go to `reports/singapore_issuance_health_latest.json`. A partial batch
without a receipt is reported for attention and excluded from the count. A
changed checksum, duplicate ID, outcome field, invalid time or wrong prediction
raises an error. Preserve the offending files; do not repair them retroactively
or delete failures to improve a future score.

Routine checks add **no experiment count**. The one first-integration validation
is recorded separately; its `--record-trial` mode rejects a repeat registration.
The tested component has seven synthetic regression cases covering these
boundaries. All 302 software tests pass. Neither synthetic tests nor metadata
checks establish camera, neural or forecasting accuracy.

Keep collecting at the existing source-compliant cadence. Real learned scoring
remains closed until **27 October 2026, 10:51 UTC**, under the immutable global
reservation and frozen final gates. See `docs/SINGAPORE_FORECAST_STUDY.md`.
