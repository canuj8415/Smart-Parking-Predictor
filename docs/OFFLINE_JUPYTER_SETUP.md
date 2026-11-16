# Jupyter from the saved offline installers

The parking app acts like an attendant: it looks at a picture and reports which
spaces appear occupied. A notebook is the exercise book behind that answer: it
shows the calculations, pictures and explanations one step at a time.

The separate app+Jupyter environment is identified by
`reports/offline_jupyter_latest.json`. Its acceptance record covers a new virtual
environment on this laptop, built from local installer files. It reuses the
existing Windows/base Python installation and the project's saved images/models.
The original working environment and earlier app-only environment are preserved.

## Open the notebook workspace

From PowerShell in the project folder:

```powershell
$parkingNotebook = Get-Content '.\reports\offline_jupyter_latest.json' -Raw | ConvertFrom-Json
& $parkingNotebook.python '.\scripts\start_jupyter.py' --offline --notebook '08_image_patterns_and_svd.ipynb'
```

This opens the image-pattern lesson directly. Without `--notebook`, the launcher
still defaults to notebook01. Select **Python (Smart Parking)** if prompted for a kernel. A kernel is simply
the Python process running that notebook. This command explicitly uses the new
environment; normal app launch settings were not switched automatically.

Actual automated kernel checks cover lesson08, including its inline picture and
table, plus a separate training-only product check with both saved detectors and
the 2D/3D convolution examples. Lesson08's original code cells were retained,
with one diagnostic setup cell in the separately saved output copy. Original
notebooks were not overwritten. The latest JSON points to both executed copies.
The product check agrees with the fixed training example; that agreement is not
new real-world accuracy. The 3D example is a labelled numeric teaching volume.

The local JupyterLab server now also passes authenticated HTTP/JavaScript-asset,
notebook-delivery and WebSocket kernel checks. The project kernel points to the
verified Python and returned an inline plot. Anonymous kernel API access was
rejected and the temporary server/kernel stopped cleanly. See
`reports/jupyter_server_latest.json` for exact evidence. A visible browser's
JavaScript execution and manual kernel selection remain unverified. All eight notebooks
were previously executed in the original environment; only the specified two
notebook checks were executed in this fresh environment. Do not rerun notebook02
on its old held-out image to claim a new independent accuracy result.

## Rebuild another separate environment without package downloads

Use a new destination folder and compatible Windows64/Python3.12:

```powershell
python -m venv '.\outputs\my_offline_notebooks\venv'
& '.\outputs\my_offline_notebooks\venv\Scripts\python.exe' -m pip install --no-index --only-binary=:all: --require-hashes --find-links '.\dependencies\offline_app\v1\wheels' --find-links '.\dependencies\offline_jupyter\v1\wheels' -r '.\dependencies\offline_jupyter\v1\requirements-app-jupyter-lock.txt'
& '.\outputs\my_offline_notebooks\venv\Scripts\python.exe' -m pip check
& '.\outputs\my_offline_notebooks\venv\Scripts\python.exe' '.\scripts\start_jupyter.py' --offline --notebook '08_image_patterns_and_svd.ipynb'
```

There are 24 app installer archives plus 83 Jupyter extension archives: 107
packages, 257,829,508 bytes altogether. The extra Jupyter archives use
49,287,471 bytes. Both directories are needed. Exact versions, original URLs,
publisher SHA256, creators, licence declarations and embedded notice hashes are
in `reports/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json` and its referenced app
manifest. Source IDs: SRC-PKG-003 and SRC-PKG-004. Full original notices remain
inside the local wheel archives; local academic use was the acquisition scope.

The acquisition used official PyPI. The resolver can download full archives
even with `--dry-run`; it installs no packages during that step. Size was checked
after resolution. Verified archives were recovered from that cache without
another transfer. Receipts retain exact local copy times and original resolver
operation bounds; exact per-file original network times were not captured.
Restricted DNS, an initial UTF-8 handling failure, and an interrupted bundled-pip
bootstrap are preserved in the evidence, rather than erased.

The initial installation succeeded with Python socket access denied, including
a harmless IPv6 localhost capability probe. That strict acceptance gate failed
and remains recorded. The continuation reused this new environment without
reinstalling, allowed localhost communication, and denied other Python socket
connections during the checks. Native ZeroMQ is outside Python audit coverage. This is a software
offline check, not a physical network-disconnection or new-machine demonstration.
The freshly installed decoder was preloaded explicitly; ordinary project imports
can prefer the identical older bundled decoder. Browser/manual/offline rehearsal,
student explanation and missing university-document checks remain separate.

`--offline` disables the server's update checker and makes extension management
read-only. The server binds to `127.0.0.1` on this laptop and keeps its usual
authentication. `--no-browser` starts without opening a browser; `--port 8889`
chooses another port if needed. Automated validation used `--state-dir` with a
separate temporary settings folder; it did not overwrite the usual project
kernel settings or leave a server running.

Implementation references: [nbclient execution documentation](https://nbclient.readthedocs.io/en/latest/client.html)
and [pip hash-checking documentation](https://pip.pypa.io/en/stable/topics/secure-installs/).
