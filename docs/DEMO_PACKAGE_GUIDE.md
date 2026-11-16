# Current combined offline package

The latest selected demo now includes its107-wheel installer set and a freshly verified package-local environment. See docs/COMBINED_OFFLINE_DEMO_GUIDE.md and reports/offline_demo_latest.json. The older runtime-only package below is retained as history.

## Historical runtime-only demo

# Run the relocated local demo

The latest checked folder is:

`D:\deep learning\project001\outputs\demo_packages\DEMO-BUNDLE-20261025T194803443600Z`

It contains 189 hash-verified files, about545MB, including the Python app, both
pretrained detectors, original occupancy/region/forecast checkpoints, one real
training image and geometry-only layout, an already-seen licensed traffic clip,
the Windows video decoder, a saved Singapore snapshot and archived reports.
Original project data and weights were copied without being moved or edited.
The full training datasets and Python environment are not included.

1. Read `START_HERE.md` inside the folder.
2. Use an installed Python environment with the app dependencies. On this laptop:

   ```powershell
   cd 'D:\deep learning\project001\outputs\demo_packages\DEMO-BUNDLE-20261025T194803443600Z'
   & 'D:\deep learning\.venv\Scripts\python.exe' run_app.py
   ```

3. For the launcher, optionally set `SMART_PARKING_PYTHON` to that environment's
   `python.exe`, then run `launch_parking.cmd`. The launcher also recognizes a
   `.venv` in its own folder or its parent. It never installs packages itself.
4. Click **Load real sample**. This is a recorded training-split PKLot view with
   100 configured spaces. It demonstrates behavior; it does not supply a new
   independent accuracy mark. Changing the default sample does not change any
   recorded model evaluation or training split.
5. Try Faster R-CNN and Mask R-CNN, then save results. The actual analysis overlay
   stays paired with its JSON. A learned-region preview is exported separately.
6. Show the two archived forecast views, cached live readings, convolution/SVD lab and selected notebook08
   and Sources & guide progress tables. Display saved timestamps and limits.

`BUNDLE_MANIFEST.json` lists the copied files, roles, source IDs, sizes and hashes.
`BUNDLE_SCOPE.json` records the original project, selected training image and
street-video creator/licence. The project-wide source register includes more
data than this selected demo contains. `READY.json` points to the actual
`VALIDATION_REPORT.json`; it does not mean the whole research project is finished.

The check ran from the copied folder in a separate process, using the already
installed runtime. Reads back into the original project were denied. Normal
Python networking attempts were blocked and no normal task attempted one. An
explicit blocked-network probe verified the guard. Windows networking was not
changed, and unrelated apps were untouched.

Actual checks covered both detector routes and real exports, separate semantic
preview, archived forecast charts, cached live display, 2D/3D arithmetic, saved
progress exports and two bounded samples of the licensed street video. Widgets
were hidden and folder dialogs mocked. The first bundle passed those checks but
revealed a pending-callback shutdown warning; it is preserved. The new version
cancels the poll on close and passes the stricter warning-free shutdown check.

This proves a relocated local software path using the existing runtime. It does
not prove a fresh offline install, a new computer, physical network disconnection,
manual native dialogs or broad accuracy. No raw final image/sequence/date was
read or rescored. All previously consumed holdouts remain consumed. The copied
Windows video decoder does not establish cross-platform support.

The Excel/progress snapshot bundled here is intentionally dated15:32UTC. Newer
technical progress is in the original project's continuation log. The sample,
weights and source records retain their original attribution and restrictions;
this work did not publish the bundle externally.


## 25 October 2026 / refreshed relocated demo with live guards and Jupyter lesson

Latest package includes the live.pyguards,SVD module,guide and executed notebook08. Its4Python cells were checked inside the copy with inline magic/show suppressed; no copied-folder Jupyter-kernel acceptance. Use reports/demo_package_latest.json for exact byte hashes. Main-project8notebooks remain separate; old package versions preserved.

## 26 October 2026 / forecast exports verified in the refreshed offline copy

The latest pointer now selects COMBINED-DEMO-20261026T025712811956Z (424files),including the forecast export fix. Use docs/COMBINED_OFFLINE_DEMO_GUIDE.md;only notebook08ofnine is included. Historical package counts below describe previous dated copies.
