# Current selected offline demonstration

The verified copy is `outputs/offline_demo_packages/COMBINED-DEMO-20261027T044747395249Z`. It contains 468 payload files (809,047,000
bytes), including 107 original installer wheels and their notices. A new local
environment was installed from those wheels using hash locks and no index.
Existing Windows, 64-bit Python 3.12 and Tk were reused; they are not distributed.

In PowerShell opened inside that copied folder, launch the already installed app:

```powershell
& '.\.venv\Scripts\python.exe' run_app.py
& '.\.venv\Scripts\python.exe' scripts/start_jupyter.py --offline --notebook '08_image_patterns_and_svd.ipynb'
```

Keep the copy at its verified location. Moving installed environments can break
absolute kernel paths; use the included setup instructions to create a new local
environment rather than overwriting a verified one. Only notebook 08 and selected
demo assets are included; full training datasets and ten other notebooks are absent.

Both actual detector routes retain the fixed TRAIN example counts of 68 occupied,
32 vacant and 0 uncertain out of 100. Those are reproducibility checks, not a new
accuracy score. The bounded assignment helper is included and its import was
verified. The actual copied-folder Jupyter kernel produced one inline PNG.
Thirteen synthetic export fault cases, all 107 locked dependency versions and
separate deliberate fallback/DNS probes passed. Normal audit records have no
denials. Localhost transport was allowed for Jupyter; external/fallback guards
were retained. Python audits do not isolate native extension I/O.

The copy intentionally retains the earlier cached Singapore snapshot
`data/raw/singapore_live/20261026T023005168368Z.json`, before the reserved prospective period. Its age
and provider timestamp remain visible. Current main-project live history is
separate; pending learned forecast targets were not copied into the demo.

The older 451-file accepted copy, its original failed build report and its later
REVALIDATION_ACCEPTANCE chain are unchanged. Earlier selection pointers are in
`reports/demo_package_history/COMBINED-DEMO-20261027T044747395249Z`. The new authoritative pointer is
`reports/offline_demo_latest.json`; READY.json and COMBINED_VALIDATION.json inside
the copy bind its actual validation. It passed in 299.063 seconds.

The separate 100-run live checkpoint accepted 2,423 rows from 2,005 car parks,
excluded five invalid bound records, verified duplicates/freshness/CSV integrity,
and exercised the hidden native live table/filter/status callback with actual
fresh rows. It is aggregate feed/software validation, not camera accuracy.
Learned Singapore forecasts remain unscored until their separate final closure.

Physical network disconnection, a different computer, visible manual/browser
rehearsal, student independent explanation and official university acceptance
remain unverified. Local academic use does not authorize external redistribution.
For reproducible project tests, use `python scripts/run_project_tests.py`; it keeps
temporary files and imports inside the workspace. The current full suite passes
446 tests. The initial temporary-folder cleanup failure is retained as evidence.
