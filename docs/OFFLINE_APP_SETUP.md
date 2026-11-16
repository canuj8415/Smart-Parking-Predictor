# Verified offline app environment

The app-only offline installation passed on this laptop in a **new virtual
environment**. The original working Python installation was left unchanged.
All184existing software tests also passed inside the new environment, with
networking blocked. This verifies app dependencies and representative functions;
it does not establish vehicle accuracy or student understanding.

The exact verified interpreter is:

`outputs/installation_checks/OFFLINE-INSTALL-20261025T210141239920Z/venv/Scripts/python.exe`

From the project folder, use it explicitly if needed:

```powershell
& '.\outputs\installation_checks\OFFLINE-INSTALL-20261025T210141239920Z\venv\Scripts\python.exe' run_app.py
```

The normal launcher still uses your selected/current Python. It was not switched
automatically. `reports/offline_runtime_latest.json` identifies the verified
environment,hash-locked requirements,installer archive manifest and evidence.

The local installer set is `dependencies/offline_app/v1/`:24original wheels,
208,542,037bytes total. Publisher SHA256,archive CRC and embedded licence/notice
checks passed. Complete original archives/notices are retained. Each package and
version is listed in `WHEELHOUSE_MANIFEST.json`; hashes are enforced by
`requirements-app-cpu-lock.txt`. This is a Windows64/Python3.12 CPU profile.

To reproduce into another **new** folder on a machine with compatible Python and
these project files already available, the tested install uses:

```powershell
python -m venv '.\outputs\my_offline_app\venv'
& '.\outputs\my_offline_app\venv\Scripts\python.exe' -m pip install --no-index --require-hashes --find-links '.\dependencies\offline_app\v1\wheels' -r '.\dependencies\offline_app\v1\requirements-app-cpu-lock.txt'
& '.\outputs\my_offline_app\venv\Scripts\python.exe' -m pip check
& '.\outputs\my_offline_app\venv\Scripts\python.exe' run_app.py --check-environment
```

Use a new folder; do not overwrite the existing `.venv`. The base Python/Tk and
current Windows installation are still reused. This is not a new-machine or
physically disconnected demonstration. App tests used hidden native windows and
mocked save dialogs. The decoder was explicitly preloaded from the fresh venv;
the ordinary source package can prefer its identical bundled decoder instead.

The fresh check exercised both frozen detectors on the existing training-only
example,paired exports,separate semantic preview,two archived forecast views,
cached live data,SVD and two already-seen licensed video samples. Counts agreed
with the fixed software example; they are not new ground-truth accuracy scores.
Consumed final image/date/sequence groups were not opened again.

Jupyter packages are **not** included in this app-only profile. The eight
notebooks remain executed/verified in the original notebook environment. A fresh
offline notebook environment is a separate next step. The older189-file demo is
also a dated copy and does not include this208MBinstaller set automatically.

Provenance correction: pip's earlier `--dry-run` downloaded/cache-stored complete
wheels even though it installed no packages. The initial plan's no-acquisition
flag was inaccurate. Original plan/logs remain; version2and
`data/provenance_corrections/RUNTIME_DRYRUN_CACHE_20261025.json` record the correction.
Staging then recovered and verified those cached originals without downloading
them again. Sources: SRC-PKG-002official metadata and SRC-PKG-003original wheels;
per-file URLs,hashes,creators/licences and local-copy timing are retained.

## 25 October 2026 / fresh offline Jupyter kernels verified

A separate app+Jupyter profile now passes actual fresh kernel checks. See docs/OFFLINE_JUPYTER_SETUP.md. The app-only installation described above remains unchanged; its184software tests retain their original scope/date.
