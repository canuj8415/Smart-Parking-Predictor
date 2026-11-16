"""Create a reproducible read-only lesson from the frozen development evidence."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN='FORECAST-GROUP-ROBUST-20261025T094258007427Z'
def md(text):return dict(cell_type='markdown',metadata={},source=text.splitlines(keepends=True))
def code(text):return dict(cell_type='code',metadata={},source=text.splitlines(keepends=True),outputs=[],execution_count=None)
cells=[md('''# Lesson 5: a fairer forecast score

If a sign says 20 free spaces but the later reading is 14, the error is six
spaces. MAE averages these error sizes. Persistence means predicting the current
count again. Lower MAE is better; it is not an accuracy percentage.

This lesson reads completed real-data results. It does not train, tune, download
data or open the reserved future numeric outcomes. See the source table below.
'''),code('''import json, hashlib, html
from pathlib import Path
from IPython.display import display, HTML
ROOT = Path.cwd()
if not (ROOT / "src/smart_parking").exists():
    ROOT = ROOT.parent
RUN = "FORECAST-GROUP-ROBUST-20261025T094258007427Z"
folder = ROOT / "experiments/results" / RUN
result = json.loads((folder / "run.json").read_text())
assert hashlib.sha256((folder / "candidate.pt").read_bytes()).hexdigest() == result["checkpoint_sha256"]
def table(headers, rows):
    body = "".join("<tr>" + "".join("<td>" + html.escape(str(v)) + "</td>" for v in row) + "</tr>" for row in rows)
    display(HTML("<table border='1' cellpadding='6'><tr>" + "".join("<th>" + html.escape(h) + "</th>" for h in headers) + "</tr>" + body + "</table>"))
print("Frozen completed trial:", RUN)
'''),md('''## Why pay attention to each car park?

A good class average can hide struggling students. Likewise, large car parks can
dominate a forecast's error total. The new loss gives half its weight to the
average relative car-park error and half to the worst relative car-park error.
Difficulty scales come from each fitting prefix's persistence errors only, with
a floor of one space. Unseen parks use the median fitted scale.

Three earlier-to-later training blocks choose a common epoch count. All-training
refitting uses that fixed count. Later development outcomes are opened only
after saving the candidate. This model retains the existing bounded trend LSTM.
'''),code('''audit = json.loads((folder / "training_fold_audit.json").read_text())
table(["Training block", "Fit windows", "Later tuning windows", "Latest fit date", "Earliest tuning date"],
      [[r["fold"], r["fit_windows"], r["tuning_windows"], max(r["fit_dates"]), min(r["tuning_dates"])] for r in audit])
for r in audit:
    assert not set(r["fit_source_rows"]) & set(r["tuning_source_rows"])
    assert max(r["fit_dates"]) < min(r["tuning_dates"])
print("Selected epochs:", result["selected_epoch"], "out of", result["max_epochs"])
'''),md('''## What happened on the later development windows?

The new model reduces MAE relative to persistence, and passes the existing
overall/per-park gate. The earlier trend candidate has lower aggregate error but
fails that gate. All are development comparisons, with reused dates. Correlated
overlapping windows are not hundreds of independent days. Historical numerical
reporting differences below 0.001 spaces do not explain the displayed gap.
'''),code('''old = json.loads((ROOT / "experiments/results/FORECAST-TREND-GUARD-20261024T164720136309Z/run.json").read_text())
m = result["metrics"]
table(["Method", "MAE in spaces", "Development gate"], [
    ["Persistence", f"{m['persistence_mae_spaces']:.2f}", "Comparator"],
    ["Earlier trend LSTM", f"{old['metrics']['candidate_validation_mae_slots']:.2f}", old['metrics']['validation_gate_passed']],
    ["Group-relative LSTM", f"{m['candidate_mae_spaces']:.2f}", m['validation_gate_passed']]])
print(f"Observed improvement relative to persistence: {100*m['improvement_vs_persistence']:.1f}%")
table(["Car park", "Windows", "Candidate MAE", "Persistence MAE", "Enough windows for park gate?"],
      [[r['car_park_id'], r['windows'], f"{r['candidate_mae']:.2f}", f"{r['persistence_mae']:.2f}", r['windows'] >= 10] for r in result['per_park']])
'''),md('''## What is still unproven?

The app's original model is unchanged. No independent final result or Singapore
neural accuracy is available. Eight later dates are reserved by identifiers and
timestamps only. Their original fixed-grid coverage may be inadequate. A causal
window protocol and one-time final guard must be fixed and tested before final
scoring. Legacy test-window loading is now blocked while this reservation exists.
'''),code('''reservation = json.loads((ROOT / "data/manifests/forecast_fresh_dates_v1.json").read_text())
print("Reserved dates:", reservation["reserved_dates"])
print("Reserved source rows:", reservation["reserved_rows"], "— no numeric final outcomes read in this lesson")
live = json.loads((folder / "live_summary_snapshot.json").read_text())
table(["Separate live checkpoint", "Value"], [["Retrieved at", live['checked_at']], ["Persistence matched outcomes", live['scores_total']], ["Persistence MAE, spaces", round(live['baseline_mae_spaces'],3)]])
print("These Singapore results do not score the Birmingham neural model or camera.")
'''),md('''## Real sources and local files

UCI Parking Birmingham, source SRC-DS-003:
https://archive.ics.uci.edu/dataset/482/parking+birmingham

- Original archive: `data/raw/uci_parking_birmingham/parking-birmingham.zip`.
- Prepared source rows: `data/splits/birmingham-global-days-v1/manifest.csv`.
- Candidate predictions, source row IDs and actual target timestamps:
  `experiments/results/FORECAST-GROUP-ROBUST-20261025T094258007427Z/observations.csv`.
- Singapore original JSON: `data/raw/singapore_live/20261025T093811785068Z.json`.
- Singapore normalized readings: `data/processed/singapore_live_observations.csv`.
- URLs, licences and acquisition checksums: `data/source_manifest.csv` and
  `data/resource_receipts.jsonl`.

Try explaining: why can a model with 30.20-space MAE pass the development gate
when an earlier model with 20.90-space MAE fails it? Why is neither number a
universal accuracy percentage? An answer in your own words is still needed;
saved notebook output does not demonstrate independent mastery.
''')]
if __name__=='__main__':
    destination=ROOT/'experiments/results'/RUN/'live_summary_snapshot.json'
    if not destination.exists():shutil.copyfile(ROOT/'data/processed/singapore_prospective/summary.json',destination)
    notebook=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.12.10')),nbformat=4,nbformat_minor=5)
    # Stable unique cell IDs make the generated lesson valid with current nbformat.
    for i,cell in enumerate(cells):cell['id']=f'forecast-lesson-{i:02d}'
    (ROOT/'notebooks/05_forecast_robustness.ipynb').write_text(json.dumps(notebook,indent=1)+'\n',encoding='utf-8')
