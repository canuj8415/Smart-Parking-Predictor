# Current offline app and Jupyter installation update

The fresh app-only offline installation passes;see docs/OFFLINE_APP_SETUP.md and reports/offline_runtime_latest.json. A separate app+Jupyter installation now also passes actual fresh kernel checks for lesson08 and a training-only product check;see docs/OFFLINE_JUPYTER_SETUP.md and reports/offline_jupyter_latest.json. All-eight fresh notebooks,Lab server/browser,new-machine,physical-offline and manual acceptance remain separate. The prior failure/readiness snapshot below is preserved as history.

## Historical readiness snapshot before the complete wheelhouse

# Starting on this laptop or setting up another environment

The working app uses the existing project Python installation. A copied demo
folder includes model/data examples but does not include that Python environment.
The launcher now checks that its main components can be found before importing
the heavy image-model code. If they are missing, it explains the setup problem
instead of showing a long Python traceback. It never installs or downloads files.

For an optional technical diagnostic, run from the main project folder:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' run_app.py --check-environment
```

This only discovers modules/versions. It does not test binary compatibility,
load detector weights, open a desktop window or prove offline installation.
`video_decoder_discovered` also means discovery only. Compatible components and
the exact model/configuration files must still work together in an actual run.

The observed app dependencies are pinned in `requirements-app.txt`; Jupyter
dependencies are separately listed in `requirements-notebooks.txt`. Python3.12
is the tested series. Tkinter comes with the base Python installation; a new
virtual environment still reuses that base interpreter and desktop support.
Use `SMART_PARKING_PYTHON` with the launcher to select the intended interpreter.

For a genuinely fresh offline setup, compatible wheels for **all** app packages
and their dependencies must be available beforehand, with source/licence/byte
checks, plus a suitable Python installation. The project currently keeps the
verified OpenCV wheel under `dependencies/wheels/`; that alone cannot install
PyTorch, TorchVision, NumPy, Pillow, Matplotlib and their dependencies. A missing
offline wheel does not establish that its release is unavailable online.

The readiness audit creates a separate empty virtual environment under
`outputs/installation_checks/`, disables system site packages, blocks networking
inside its probes, and compares the old/new launcher. Its offline pip command is
a dry-run with `--no-index`; it does not download or install app packages. Original
Python, data, weights and prior demo packages remain unchanged. Results are in
`models/installation_readiness.json` and its recorded experiment folder.

A successful prerequisite check is not full acceptance. Fresh installation,
new-machine behaviour, visible/manual dialogs, physical disconnection and student
rehearsal remain separate checks. The last copied demo is a dated snapshot and
does not automatically receive later launcher changes.

The new launcher also passed a separate existing-runtime hidden-window startup/close check without loading model engines. That integration check supplements discovery; it does not turn the failed clean offline install into a pass. Official release metadata for five core packages and CPU wheel hashes is saved in data/manifests/runtime_core_candidates_v1.json; no installer wheel was downloaded by this preparation step and transitive closure remains unresolved.
