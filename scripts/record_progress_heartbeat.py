"""Record report/UI work without inflating the scientific trial counter."""
import csv,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
from smart_parking.progress_reports import load_progress
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T151531Z'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('Dated report work already recorded')
    report=load_progress();state=read('data/automation_state.json');now=datetime.now(timezone.utc).isoformat()
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==report['completed_trials']==32
    assert not state['active_validation_jobs'] and not state['active_training_jobs']
    tests=(E/'unit_tests.txt').read_text(encoding='utf-8-sig');assert 'Ran 162 tests' in tests and tests.rstrip().endswith('OK')
    native=read(E.relative_to(ROOT)/'native_progress_checks.json');workbook=read(E.relative_to(ROOT)/'workbook_verification.json')
    package=read(E.relative_to(ROOT)/'export_package_checks.json')
    assert native['actual_widget_methods_passed'] and native['snapshot_as_of']==report['as_of']
    assert workbook['snapshot_as_of']==report['as_of'] and workbook['counted_trials']==32 and workbook['source_rows']==45
    artifact=ROOT/'outputs/01a16cf3-1f03-7631-8fac-d3d382c5b25c/smart_parking_progress_20261025.xlsx'
    assert digest(artifact)==package['workbook_sha256']
    inputs=report['input_snapshots']
    for record in inputs:assert digest(ROOT/record['snapshot'])==record['sha256']
    assert len(report['sources'])==45 and len(report['experiments'])==43
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert receipt['local_path']=='data/raw/singapore_live/20261025T151744856149Z.json'
    payload=read(receipt['local_path']);rows=parse_feed(payload);live=read('data/processed/singapore_prospective/summary.json')
    assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    assert len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})==len(rows)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        interpretation='1235previously frozen persistence forecasts matched later observations; no model/neural/camera accuracy'))
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in production.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    state['last_updated_at']=now;state['scheduled_wakeups_completed']+=1
    state['progress_report']=dict(path=artifact.relative_to(ROOT).as_posix(),sha256=digest(artifact),snapshot_as_of=report['as_of'],
        pointer='reports/progress/latest.json',worksheets=4,sources=45,experiment_rows=43,completed_trials=32,software_tests=162,
        guide='docs/EXCEL_PROGRESS_GUIDE.md',app_view_export_methods_checked=True,native_excel_opened=False)
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Keep all consumed final groups closed: DAVIS car-roundabout whole sequence; original image camera/date finals; Birmingham temporal finals. Current flow final lacks positive crossings and fails acceptance; no line move or changed-method reuse. Seek fresh legitimate labelled positive-crossing sequences/protocol.',
        'Continue product correctness/native-visible/folder-dialog and fresh physically offline acceptance without changing frozen model claims. New Sources & guide buttons View saved progress / Save progress tables have hidden-widget/mocked-dialog checks only. Excel report native application check pending.',
        'Report now includes four-tab XLSX, all45catalog sources/43historical records,32counted trials and12scoped metrics. Snapshot is dated15:32UTC; input copies/checksums preserved. Report edits,162software checks and UI export validation are not additional model experiments.',
        'Finish final report/PDF compilation/presentation/student explanations. Missing university documents block official compliance, not independent work. Original pretrained/project checkpoints and experimental candidates retained.',
        'Next official collection at a sensible30mincadence. At15:17UTC:19256matched persistence outcomes,MAE4.406730,6290expired/1442pending,75.38%resolved matching. No neural/camera live accuracy. Counter32; separate100-run checkpoint100.'
    ]
    write('data/automation_state.json',state)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    records=dict(report=state['progress_report'],snapshot_inputs=inputs,authoring='Codex using bundled @oai/artifact-tool and runtime26.1024.11018; main product/Jupyter remain Python',
        source_catalog='data/source_manifest.csv',scope='Derived dated report; no raw observations edited, training or holdout rescoring',
        builder='outputs/01a16cf3-1f03-7631-8fac-d3d382c5b25c/progress_build/build_progress.mjs')
    write('reports/progress/artifact_inventory.json',records)
    write(E.relative_to(ROOT)/'checks.json',dict(tests_passed=162,completed_recorded_trials=32,new_scientific_experiments=0,
        workbook_sha256=digest(artifact),worksheets=4,source_rows=45,historical_experiment_rows=43,metrics=12,
        input_copies_verified=True,zero_vs_unavailable_formula_test_passed=True,formula_errors=0,rendered_all_sheets=True,
        native_widget_methods_passed=True,physical_dialog_or_native_excel_check=False,production_flow_and_weights_unchanged=True,
        no_final_raw_pixel_read_or_rescoring=True,active_jobs=[]))
    note='''Added Python archived-progress loading with checksum/path validation, readable
dated display and JSON/four-CSV export. Sources & guide has View saved progress
and Save progress tables; source-view round-trip, busy controls and actual export
files/checksums pass hidden native Tk method checks with mocked folder chooser.
Zero-reference crossing numerator0/denominator0/valueNone stays unavailable;
CSV guards avoid spreadsheet-formula execution from source strings. No model
inference, raw-final decoding, training, candidate promotion or default tracker change.

162software tests pass. New four-tab Excel report contains11capabilities,12scoped
metrics,45source entries and43historical experiment rows (32scheduled completed,
9earlier,2interrupted). All source creators/URLs/licences/local paths and failed
experiments retained. Dated snapshots and exact input copies/checksums are in
reports/progress; original first-training workbook preserved. The new XLSX is
outputs/01a16cf3-1f03-7631-8fac-d3d382c5b25c/smart_parking_progress_20261025.xlsx.
Guide:docs/EXCEL_PROGRESS_GUIDE.md. Formula metrics match saved reports; positive
denominator zero-result and zero-reference unavailable boundaries checked. All
four sheets rendered/reviewed; native tables/freeze panes/cached unavailable
text/no-error cells verified in exported package. Native Excel use not checked.

Initial workbook build rejected non-date literals in7older registry rows. Builder
now preserves unknown date text and converts only genuine timestamps; no registry
dates invented. Authoring recovery recorded, not counted as a model experiment.
Main/Jupyter remain Python; bundled artifact-tool JS used only for Excel authoring.
These report/UI checks are not a new scientific trial:counter remains32, next
100-run checkpoint100, no active jobs. All final holdouts remain consumed.

Actual15:17UTC Singapore snapshot25matches1235earlier frozen persistence forecasts:
19256matched total,MAE4.406730spaces;6290expired/1442pending;75.38%resolved
matching, not accuracy. Raw JSON/normalized observations/URL/time/SHA saved.
No neural/camera accuracy. Remaining work:visible/native/offline acceptance,
fresh positive-crossing evidence, report compilation/presentation and student
explanations. No universal accuracy or full project completion claimed.'''
    title='## 25 October 2026 / dated Excel report and Python progress exports'
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        p=ROOT/name;text=p.read_text(encoding='utf-8')
        if title not in text:p.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    p=ROOT/'docs/UI_TEST_LOG.md';p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nNew saved-progress/source buttons:actual hidden native Tk display/export methods, JSON/CSV equality/checksums, source round-trip and busy-state checks pass. Folder chooser mocked; no visible screenshot/manual dialog/physical-offline/native Excel claim. Evidence:experiments/evidence/HEARTBEAT-20261025T151531Z/native_progress_checks.json.\n',encoding='utf-8')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=p.read_text(encoding='utf-8').replace('159 tests pass; network-disabled-process','162 tests pass; network-disabled-process').replace('Twenty-four authorized public snapshots acquired','Twenty-five authorized public snapshots acquired').replace('Sixteen prospective persistence cohorts scored','Seventeen prospective persistence cohorts scored').replace('18,021 matched later outcomes, MAE4.425','19,256 matched later outcomes, MAE4.407')
    text+='\n\nSaved progress report:four-tab XLSX with11capabilities/12scoped metrics/45sources/43historical entries;32counted trials. Python app has dated progress display and JSON/four-CSV export.162software tests and hidden-native method checks pass; visible/native Excel/dialog/physical-offline acceptance pending. See docs/EXCEL_PROGRESS_GUIDE.md.\n';p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/REQUIREMENTS.csv'
    with p.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id'] in ['APP-02','QA-02','DOC-02']:
            row['actual_evidence']+='; docs/EXCEL_PROGRESS_GUIDE.md; reports/progress/artifact_inventory.json; experiments/evidence/HEARTBEAT-20261025T151531Z/'
            row['test_result']+=';162software tests; archived progress/four-CSV exports and four-sheet XLSX calculation/render/package checks pass'
    with p.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    print(json.dumps(dict(tests=162,completed_trials=32,workbook=str(artifact),source_rows=45,metrics=12),indent=2))


if __name__=='__main__':main()
