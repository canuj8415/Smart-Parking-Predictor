# Python and Jupyter workflow

The user explicitly requested Python/Jupyter on 24 October 2026. This supersedes
the original C/C++/Java instruction for current engineering. The missing
university documents have not verified which language the faculty accepts.

## Current components

The main product is now `run_app.py`, and its executed teaching notebook is
`notebooks/02_parking_product.ipynb`. See USER_GUIDE.md and TEST_RESULTS.md for
current model training, live source, video and experimental limits. The data-only
notes below describe the first component. Full test execution now needs the
existing model environment because tests include the vision/MLP modules:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

`src/smart_parking/data.py` provides standard-library Python acquisition, hash
validation, record checks, quarantine and chronological splitting. The scripts
`acquire_birmingham.py` and `prepare_birmingham.py` are its command-line entry points.
`tests/test_data.py` has six passing integrity tests using synthetic fixtures.
The dataset statistics come from genuine records, not those fixtures.

`notebooks/01_real_data_audit.ipynb` teaches the process using actual acquired
records. Its execution status is recorded in TEST_RESULTS.md. Notebooks call
reusable `.py` modules so the same code can be tested and later used in the app.
The planned baseline will use explicit NumPy gradients. Larger models are
proposed in Python PyTorch. No model has been trained.

## Run from this project folder in PowerShell

```powershell
python scripts/prepare_birmingham.py
python -m unittest discover -s tests -v
```

Use the existing notebook environment to open JupyterLab:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/start_jupyter.py
```

Or execute and save notebook outputs without opening its interface:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/execute_notebook.py
```

The launcher creates a project-local kernel for its interpreter and stores
runtime/cache files here. It does not modify the existing environment or other
labs. Stop the local Jupyter server when finished. On another computer use that
environment's Python. `requirements-notebooks.txt` pins tested direct notebook
dependencies; a full offline transitive wheel cache has not been prepared.

## Inspected environment

Python 3.12.10; JupyterLab 4.6.3; NumPy 2.5.3; Matplotlib 3.11.2; nbformat 5.11.1;
nbclient 0.11.0; ipykernel 7.3.0. Existing PyTorch is 2.14.0+cpu with torchvision
0.29.0. An actual runtime check returned CUDA unavailable; the GPU exists but
this installation cannot use it. No packages were installed or upgraded.

## Understand and modify the first module

Input: immutable UCI CSV plus saved split configuration. Outputs: row-level
manifest, train/validation/test files, quarantine, car-park coverage and report.
`sha256` checks bytes; `acquire` validates cached/downloaded files; `clean_rows`
checks observations; `assign_splits` assigns whole dates; `prepare` coordinates.

To experiment with split fractions, use a new split ID/output directory in the
configuration and rerun. Never change the final holdout to tune a model. The raw
hash pin deliberately rejects changed source bytes until provenance is reviewed.


Third notebook:03_region_transfer_and_live_coverage.ipynb, six executed code cells, zero saved errors. Replay uses only local weights/validation images. Execute with scripts/execute_notebook.py and that filename. If a restricted local kernel stalls, cancel the owned attempt before a permitted host retry; do not stack kernels or claim unexecuted output.

## Singapore forecasting lesson

`notebooks/10_singapore_forecast_study.ipynb` explains the frozen aggregate-count
study using completed historical development evidence. Seven code cells have
executed in the shared Python environment. Tables use standard Python and
Jupyter display tools; no pandas installation is required.

From the project folder, the existing notebook executor accepts this filename:

```powershell
& 'D:\deep learning\.venv\Scripts\python.exe' scripts/execute_notebook.py 10_singapore_forecast_study.ipynb
```

The separate `scripts/validate_singapore_lesson.py` runs the actual kernel with
bounded project-file and Python socket audits. It is a software validation,
not a new scientific evaluation. The first restricted attempt timed out and a
host attempt exposed the removed pandas dependency; both were preserved before
the successful retry. Original frozen study inputs and final claims were not
changed. A new-machine/physical-offline/manual-browser run is still separate.
