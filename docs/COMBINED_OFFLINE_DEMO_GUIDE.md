# Open the combined offline demonstration

The latest combined package is recorded in `reports/offline_demo_latest.json`.
It contains selected app data, original saved models, notebook08, saved live
readings, the licensed video demonstration and all107app+Jupyter installers.
`BUNDLE_MANIFEST.json` lists the exact copied payload and its checksums; generated
environment and validation outputs are separate. The full training datasets and
the other ten notebooks remain in the original project.

From PowerShell in the original project folder:

```powershell
$parkingDemo = Get-Content '.\reports\offline_demo_latest.json' -Raw | ConvertFrom-Json
Set-Location $parkingDemo.path
& '.\.venv\Scripts\python.exe' run_app.py
```

Choose **Load real sample**, then either detector and **Analyze**. Try saving
results, the separate region preview, archived forecasts, saved live readings
and the convolution/image-pattern lessons. The sample is a training image;
its100space predictions demonstrate the software and do not provide an accuracy
mark. Singapore readings are official aggregate counts and cannot grade the
camera. The 3D convolution example uses an explicitly labelled teaching volume.
The copied snapshot is intentionally dated; its exact file/provider timestamp is
in `reports/offline_demo_latest.json`. Current main-project live history can be
newer. A saved snapshot is not a claim that the offline copy has live internet.

To open the included notebook from the copied folder:

```powershell
& '.\.venv\Scripts\python.exe' scripts/start_jupyter.py --offline --notebook '08_image_patterns_and_svd.ipynb'
```

The default launcher still opens notebook01 in a full project. This selected
package includes only notebook08, so use the explicit command above. The usual
**launch_parking.cmd** also finds the package's `.venv`; the explicit command
avoids a separately configured environment variable selecting another Python.

## Build a new environment from the included installers

The original Windows/base Python/Tk is reused; it is not bundled. On this laptop,
the recorded package already has a checked `.venv`. Do not reinstall over it.
For a new setup, use an existing64-bit Windows Python3.12 from the copied folder:

```powershell
python scripts/setup_offline_bundle.py --destination '.venv_rebuild'
& '.\.venv_rebuild\Scripts\python.exe' run_app.py
& '.\.venv_rebuild\Scripts\python.exe' scripts/start_jupyter.py --offline --notebook '08_image_patterns_and_svd.ipynb'
```

Choose a destination that does not exist. Setup refuses to overwrite one. It
checks payload hashes, installs only included wheels using `--no-index` and
`--require-hashes`, then checks dependency compatibility. Installation logs remain
under `outputs/setup/` and the resulting interpreter is in
`OFFLINE_ENVIRONMENT.json`. Earlier environments and project files are preserved.
Setup rechecks the original payload; keep a pristine copy if you later record
new live data or edit bundled inputs.

A virtual environment contains absolute installation paths. If you move this
folder to another location or computer, create a new environment at that location
instead of assuming the old `.venv` will still work. New-machine compatibility
has not been tested. Keep original installer archives and their embedded notices;
this local academic package does not establish external redistribution rights.

## What the check proves

`READY.json` points to `COMBINED_VALIDATION.json`. Its stages cover a fresh copied
environment, actual hidden native app/model/export routes, cached data, archived
forecasts, a bounded already-seen video check, and a genuine notebook kernel with
an inline plot. Original payload bytes are checked again afterwards. Software
fixtures used for feed checks are labelled and never added as real observations.
`VALIDATION_REPORT.json` covers only the app-check stage; use the combined report
for the installation-plus-app-plus-notebook result.

Python file-open/network guards reject reads into the main project and external
connections during the guarded checks. These guards do not isolate all native
extension operations or physically disconnect the laptop. Hidden windows and
mocked save dialogs do not replace manual/browser testing. Student explanation,
physical offline rehearsal, full-training reproducibility and official university
document checks remain separate. No new scientific accuracy is measured.

The source register describes the wider project. A path in that register is not
a promise that the full dataset is included here. Use the bundle manifest for
included files and the original `data/resource_receipts.jsonl` for acquisition
URLs/timestamps/hashes. Per-wheel publisher metadata, creator/licence declarations
and complete original embedded notices are included with the installer set.

## 26 October 2026 / forecast exports verified in the refreshed offline copy

Current checked folder: `outputs/offline_demo_packages/COMBINED-DEMO-20261026T025712811956Z`. It already has the verified `.venv`;skip installation on this laptop and use the launch commands above. The fresh107-package install,both detector routes and genuine notebook08kernel passed. Choose **Original experiment** or **Later-date check**,then **Show held-out forecast** and **Save forecast results**. The legend/export identifies **Original LSTM** or **Group-relative residual LSTM**. Saving writes PNG,CSV,report JSON and checksum metadata for the displayed selection;changing report/park clears it. These are saved Birmingham results. See `docs/FORECAST_REPORTS_GUIDE.md`. Only notebook08ofnine is included. The cached Singapore reading is provider `2026-10-26T10:29:36+08:00`,so it can show STALE. The earlier419-file demo remains intact. Full-training/physical/new-machine/manual/student acceptance remains separate.

## 26 October: newer working-source export fix

Thetransactionalexportfixand382-testregressionaredatedAFTERthisoldercombinedpackage. Its424payloadfilesandoriginalbytesremainunchanged;itdoesnotyetcontainthenewsourcepatch. Buildaseparatenewversionedpayloadandvalidatebeforeclaimingupdatedofflinecoverage. Neverreopenconsumedrawholdoutsforsmokechecks;usearchivedoutputs/syntheticfixtures. See RESULT_EXPORTS_GUIDE.md.

## 26 October 2026 UTC / offline refresh remains incomplete after isolated bootstrap repair

Currentlatestpointerintentionally remainsoldverifiedpackage. New451-file refreshedcopyinstall/app/exportfaultchecks pass,butJupytertimeoutleavesitINCOMPLETE;do not useasREADYreplacement. See reports/offline_refresh_latest_attempt.json. Preservefailedoutputsanddiagnoseexistingfreshvenvwithoutreinstall. Tenothernotebooks/fulltrainingdata/basePythonareabsentfromnewselectedpayload;physical/manual/newmachine/studentacceptance stillopen.

## 26 October 2026 UTC / copied notebook recovered with approved local loopback

Latestpointer nowselects451-filecopywithnewREVALIDATION_ACCEPTANCE.json/READY.json. InitialCOMBINED_VALIDATION.jsonremainsfailedhistory;itsINCOMPLETEmarkerretainedasINCOMPLETE.initial_failed_build. Managedautomationmustpermitlocal-loopbacksocketsforJupyter;Pythonexternal/fallbackguardsstayactive. No newinstall/detectorreplay. Onlynotebook08included;10others/fulltrainingdata/basePythonabsent. Physical/manual/newmachine/student/officialacceptance remainopen.

27Oct2026:Current selected copy is468files/809047000bytes with107original hash-locked wheels/full notices and actual fresh environment/app/notebook/export checks. Pointer reports/offline_demo_latest.json;guide CURRENT_OFFLINE_PACKAGE.md. Old451-fileaccepted/failed records preserved. Sourcecatalog63 unchanged,no new package acquisition or external publication. Codex-assisted implementation/tests/docs;student mastery not assessed. Physical/manual/newmachine/university gates remainopen.
