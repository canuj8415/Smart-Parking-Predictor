# A separate copy of the Singapore lesson

The lesson folder is
`outputs/singapore_lesson_packages/SG-LESSON-PACK-20261026T114219733927Z/`.
It contains **22 payload files, 10,100,681 bytes**, plus its checksum manifest.
The original full app/demo package is retained separately.

This is a lesson copy, **not a Python installer**. It includes the executed
notebook, ten archived study inputs, a small statistical checkpoint, helper code
and attribution with the original 46 acquisition receipts. It includes no raw
snapshots, growing history, future forecast batches, production neural weights,
trainer, live collector or final scorer.

Read `notebooks/10_singapore_forecast_study.ipynb` inside that folder. Its chart
and explanations are already saved. To execute it, use a Python environment
with Jupyter, ipykernel, nbclient, nbformat and matplotlib already installed.
Pandas is not required. From the main project folder, the existing verified
offline environment can be used as follows:

```powershell
$parkingLessonRoot = Join-Path (Get-Location) 'outputs/singapore_lesson_packages/SG-LESSON-PACK-20261026T114219733927Z'
$parkingLessonPython = Join-Path (Get-Location) 'outputs/installation_checks/JUPYTER-OFFLINE-20261025T212313313839Z/venv/Scripts/python.exe'
& $parkingLessonPython (Join-Path $parkingLessonRoot 'scripts/verify_lesson_package.py')
& $parkingLessonPython (Join-Path $parkingLessonRoot 'run_lesson.py')
```

The launcher saves a new executed notebook and chart under `outputs/executions`
inside the lesson folder. It preserves the original payload bytes. On another
computer, select its own compatible installed Python/Jupyter environment; the
path above belongs to this computer and is not an included runtime.

The relocated copy was actually executed with the previously offline-installed
Jupyter environment. All seven original cells passed; the helper came from the
copied folder, and five dependency modules came from that selected environment.
All payload checksums matched before and after execution. Expected protected
read/write and external-DNS probes were blocked by Python audits. The copied
chart was visually inspected. The verifier and launcher help also passed.

These checks do not establish a new-machine installation, physical network
disconnection, manual browser layout or student mastery. The real future study
is still unscored. Development MAE 6.31 versus 6.96 spaces is an archived paired
comparison at nine collection times, not a learned live or camera-accuracy claim.

Attribution: HDB/data.gov.sg,
[official availability feed](https://api.data.gov.sg/v1/transport/carpark-availability),
[Singapore Open Data Licence 1.0](https://data.gov.sg/open-data-licence), under the
accepted terms. Exact source rows, URLs, acquisition times and checksums are in
`sources/ATTRIBUTION.json`; the two teaching examples remain explicitly synthetic.

Evidence: `reports/singapore_lesson_package_latest.json`. The previous full app
bundle and original lesson files were not replaced.
