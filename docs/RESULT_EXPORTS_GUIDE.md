# Complete result exports

The working source now saves image-analysis and archived-forecast results into a private temporary folder inside the chosen destination. It publishes the final timestamped folder only after the images, records and checksum metadata have been written successfully. Handled failures and cancellation clean the files owned by that attempt; an earlier export is never replaced. The folder timestamp is UTC.

For image analysis, `overlay.png` and `analysis.json` describe the same saved analysis. An experimental semantic-mask preview, when displayed, is saved separately as `display_preview.png`. It does not replace the occupancy overlay or change its counts. `export_metadata.json` identifies and hashes every payload file, including that separate preview.

For an archived forecast, `forecast.png`, `forecasts.csv` and `forecast_report.json` preserve the displayed method, selected car park and saved prediction values. Availability must agree with capacity minus occupied counts; mismatched vector lengths, nonfinite numbers and unsupported JSON values are rejected before folder creation. Sensor timestamps remain absent when they were absent in the archived report. Overall report metrics are not rescored for the selected car park. These exports do not contain the ongoing Singapore learned study's unscored future results.

If saving fails, the app's existing save-error message reports the error. Fix the destination or data problem and save again. A timestamp collision is refused instead of overwriting the existing folder. Metadata keeps the existing field names and adds `complete: true` and a complete payload checksum map; older exports are preserved in their original format.

## Executed validation, 26 October 2026

`FORECAST-DISPLAY-EXPORT-20261026T174434533261Z` completed in 10.070 seconds. Thirteen synthetic software cases cover partial image and preview saves, unsupported/nonfinite JSON, invalid PNG, metadata-write and checksum failures, plot interruption, cancellation, inconsistent forecast vectors, invalid report metrics, name collision, successful image/preview manifests and complete forecast publication. Every case preserves prior-export sentinel bytes. These fixtures are not real parking observations or accuracy trials.

The same bounded validation exercised the actual hidden Tk app and real plots for both archived Birmingham reports: eight selected original-report windows and 75 selected later-date windows. Method labels, legends, CSV values, report identities and hashes agree; selection changes clear stale export state. Normal forbidden raw/processed/split/network attempts were zero; one explicit negative raw-read probe was blocked. The actual later-date exported PNG was visually inspected with legible title, axes and legend. No final data were rescored and no model inference or fitting occurred. All **382** software tests pass.

This is validation of handled local process failures and completed exports, not a power-loss/disk-recovery guarantee, physical disconnection, visible/manual dialog rehearsal or fresh-machine acceptance. A hard process termination can leave a hidden staging folder, but the implementation does not publish it as a completed export. Older offline packages retain their dated source bytes and do not yet contain this change; refresh and validate a new version before claiming the fix is included in those packages.

Exact code, protocol, failures, test logs and byte-preserved export copies are in `experiments/results/FORECAST-DISPLAY-EXPORT-20261026T174434533261Z/` and `experiments/evidence/HEARTBEAT-20261026T173900Z/`. Original checkpoints and consumed scientific holdout claims remain unchanged.

## 26 October 2026 UTC / offline refresh remains incomplete after isolated bootstrap repair

Exportfixpasses13syntheticfailure/integritychecksinsideanew107-packagecopy,andactualcopiedappflows pass. ThewholeofflinecopyisNOTREADYbecauseitsJupyterchecktimedout;earlierverifiedpackage remainsselected. Do not claimthatolderpackagecontainsnewpatch. See reports/offline_refresh_latest_attempt.json.

## 26 October 2026 UTC / copied notebook recovered with approved local loopback

New451-filecopiedpackageincludingtransactionalexports isnowsoftware-acceptedbyhash-linkedcomponentproofsandsuccessfulcorrected-contextJupytercheck. Previousfailuregatesremainhistoricalfailures;see reports/offline_refresh_recovery_latest.json. No power-loss/physical/manual/newmachineacceptance added.
