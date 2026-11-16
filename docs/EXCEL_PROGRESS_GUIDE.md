# Read the project progress report

Open `outputs/01a16cf3-1f03-7631-8fac-d3d382c5b25c/smart_parking_progress_20261025.xlsx`.
The earlier `smart_parking_training_run_001.xlsx` is preserved separately.

Start with **Progress**. Each row says what works, what was demonstrated and what
remains. There is no invented single completion percentage. **Results** contains
actual measured scores, their test population and limitations. Recorded inputs
and original/frozen evidence locations are to the right of that table.

**Sources** lists all 45 catalog entries, including original creators, URLs,
licence records, local data locations and unresolved issues. A candidate marked
unacquired was not downloaded. **Experiments** preserves all 43 historical rows:
32 counted trials, nine earlier records and two interrupted attempts. A frame,
epoch, routine software test or report rebuild is not an extra experiment.

Think of occupancy as asking whether a numbered chair has someone sitting in it.
Vehicle detection finds the person, slot geometry identifies the chair, and the
classifier helps decide whether it is occupied. Forecasting asks how many chairs
may be occupied later. Its MAE is the average size of the count error in spaces;
smaller is better. Persistence simply assumes the count will stay the same.

Mask overlap (IoU) compares the predicted parking region with the labelled
region. Our conditional result uses stored geometry in two known camera views,
so its score must not be described as a new neural model finding every slot.

The car-tracking final has **zero reference crossings** of its frozen line.
“Not evaluable” means there was no labelled crossing to grade. It is neither
zero accuracy nor perfect counting. The overall final gate failed. The whole
sequence is used up for final comparisons; a changed method needs fresh data.

The live-feed error is a separate Singapore persistence study. The snapshot
contains 19,256 matched later outcomes, MAE 4.407 spaces, as of 15:17 UTC on
25 October 2026. Its 75.4% target-matching coverage is not model accuracy.
Missing targets remain unscored. This feed cannot grade camera detections.

Data paths are relative to `D:\deep learning\project001` unless shown in full:

- Original downloaded material: `data/raw/`.
- Latest report's live JSON: `data/raw/singapore_live/20261025T151744856149Z.json`.
- Normalized live CSV: `data/processed/singapore_live_observations.csv`.
- Forecast issue/score history: `data/processed/singapore_prospective/`.
- Exact experiment reports and observation CSVs: `experiments/results/`.
- Every acquisition's actual URL, timestamp and checksum: `data/resource_receipts.jsonl`.
- Original source register: `data/source_manifest.csv`.
- Dated report inputs and copies: `reports/progress/`; `latest.json` identifies
  the saved snapshot shown by the app.

In the Python app, choose **Sources & guide**, then **View saved progress**.
**Save progress tables** writes a new folder containing JSON, four CSV tables
and export checksums. **Refresh source records** returns to the source view.
These actions display/export saved evidence; they do not rerun models or refresh
the network. The original detector/tracker defaults and checkpoints are retained.

The workbook is a dated report. Editing its cells does not train a model or edit
the original data. Its formulas and unavailable-score boundary were checked,
all four sheets were rendered, and the saved XLSX package was inspected. Native
Microsoft Excel interaction remains untested. The app methods were checked in
a hidden native window with a mocked folder chooser; visible/manual save and
physically disconnected acceptance remain unfinished.
