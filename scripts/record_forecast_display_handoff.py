"""Save forecast-identity/export evidence without changing scientific results."""
import csv
import json
import shutil
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import get_live,URL,_observation_key
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T022042Z'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    p=ROOT/p;old=p.read_text(encoding='utf-8');assert title not in old
    p.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')


def main():
    assert not (E/'handoff_checks.json').exists()
    state=read('data/automation_state.json');study=read('models/forecast_display_export_validation.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==53
    assert state['scheduled_wakeups_completed']==35 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert study['integration_gate_passed'] and study['normal_forbidden_attempts']==0 and not study['accuracy_evaluated']
    assert all(digest(ROOT/p)==h for p,h in {**study['source_hashes'],**study['protected_hashes']}.items())
    software=read(E/'regressions.json');assert software['tests_run']==213 and software['success']
    assert [r['method'] for r in study['reports']]==['Original LSTM','Group-relative residual LSTM']
    for item,role in zip(study['reports'],['original','later']):
        source=ROOT/item['export'];target=E/'native_exports'/role;target.mkdir(parents=True,exist_ok=False)
        for name in ['forecast.png','forecasts.csv','forecast_report.json','export_metadata.json']:
            shutil.copyfile(source/name,target/name);assert digest(source/name)==digest(target/name)
    live_rows,meta=get_live(refresh=False);raw=Path(meta['path']);live=read('data/processed/singapore_prospective/summary.json')
    assert Path(live['snapshot_path'])==raw
    records=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(records) if r['local_path']==raw.relative_to(ROOT).as_posix())
    assert receipt['source_url']==URL and receipt['sha256']==digest(raw)
    with (ROOT/'data/processed/singapore_live_observations.csv').open(encoding='utf-8',newline='') as stream:history=list(csv.DictReader(stream))
    keys=[_observation_key(r['car_park_id'],r['lot_type'],r['observed_at']) for r in history]
    assert len(keys)==len(set(keys)) and all(0<=r['available']<=r['capacity'] and r['capacity']>0 for r in live_rows)
    with (ROOT/'data/source_manifest.csv').open(encoding='utf-8-sig',newline='') as stream:assert len(list(csv.DictReader(stream)))==57
    snapshots=len(list(raw.parent.glob('*.json')))
    write(E/'live_checkpoint.json',dict(**live,snapshot_count=snapshots,raw_sha256=digest(raw),receipt=receipt,
        valid_rows=len(live_rows),car_parks=len({r['car_park_id'] for r in live_rows}),history_duplicates=0,
        scope='Singapore persistence baseline only;not neural or camera accuracy',separate_100_run_checkpoint=False))
    brief=dict(run_id=study['run_id'],integration_gate_passed=True,scientific_accuracy_evaluated=False,
        actual_hidden_native_widgets=True,visible_or_manual_validation=False,normal_raw_processed_or_network_attempts=0,
        models_and_predictions_unchanged=True,reports=study['reports'],software_tests_passed=213,
        guide='docs/FORECAST_REPORTS_GUIDE.md',older_offline_package_updated=False)
    write('reports/forecast_display_exports_latest.json',brief)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=datetime.now(timezone.utc).isoformat()
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-003':item['archived_forecast_display_validation']=brief
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in live_rows}),observations=len(live_rows),
            provider_timestamp=meta['provider_timestamp'],raw_path=raw.relative_to(ROOT).as_posix(),snapshot_count=snapshots,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state.update(scheduled_wakeups_completed=36,last_updated_at=datetime.now(timezone.utc).isoformat(),forecast_display_exports=brief,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;no neural/camera accuracy',coverage=live['forecast_coverage']))
    next_poll=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    state['next_actions']=[
        'Main app forecast labels/exports are fixed and actual hidden native checks pass. Both are LSTM variants:Original LSTM versus trend-guarded group-relative residual LSTM. Report text/legend/CSV/JSON use actual method,own cohort/MAE/timing. Save forecast results exports displayed snapshot;park/report changes invalidate old plot/export. No new training or holdout scoring.',
        'Next meaningful integration milestone:refresh the SELECTED combined offline demo for this actual app/export change,not merely the counter. Extend scripts/verify_relocated_demo.py to assert method labels and forecast PNG/CSV/JSON exports under copied-folder guard. Update build_offline_demo.py hard-coded other7notebooks wording:current project has9,selected payloadstillonly08unless deliberately expanded. Preserve earlier package bytes. Run fresh package-local no-index install/native/new export/Jupyter checks;do not claim new-machine/physical/visible acceptance.',
        'Preserve occupancy candidate failed final gate13/14rainy-view retention<95percent,original app model retained. All6latest final photos/3whole groups/171sourceframes CONSUMED,plus older image/Birmingham/DAVIS finals. No tuning/re-evaluating changed methods there. Archived displays/exports allowed. Models/predictions/final claims remain unchanged.',
        'Then verify authoritative individual-image usage permission for CNR or acquire another legitimate labelled source. CNR144965metadata records qualified,32079reserved images remain unopened/image-use-unqualified. Do not use unknown image rights or private CCTV/accounts/bypass. Reserve fresh canonical source groups before any new occupancy candidate final.',
        f'Counter53; next separate100-run checkpoint100;no active jobs.213full software tests pass. Singapore{live["checked_at"]}:41snapshots,{live["scores_total"]}matched persistence outcomes,MAE{live["baseline_mae_spaces"]:.6f}spaces;next sensible collection after{next_poll}. Missing targets unscored;no neural/camera live accuracy.',
        'Source57 unchanged;new derived forecast exports carrySRC-DS-003/run/checkpoint/prediction hashes and preserve missing source timestamps. Newguide docs/FORECAST_REPORTS_GUIDE.md. Physical/manual/browser/student mastery/official university-doc completion still pending;earlier Excel/PDF/slides/offline package remain dated snapshots.'
    ];write('data/automation_state.json',state)
    title='## 26 October 2026 / precise forecast variant labels and owned-snapshot exports'
    note='Both archived methods are LSTM variants. Display now distinguishes Original LSTM from Group-relative residual LSTM(trend-guarded/group-relative training),instead of using an ambiguous generic LSTM label for every report. Each keeps its own stored cohort,MAE,persistence comparison and actual source-time limitations. New Save forecast results route writes actual displayed PNG,CSV,reportJSON and checksum manifest;all identify method/run/park and sourceprediction SHA. Missing sensor timestamps/leads remain blank,not fabricated from grid targets. Plot and export snapshot are cleared on report or car-park changes. Actual hidden native Tk checks exercised both real archived reports:8original/75later windows for selectedBHMBCCMKT01;plot lines,text,CSV/JSON/export hashes agree. Normal raw/processed/split/network attempts0under Python audit;explicit raw-file negative probe blocked. No model inference/training/new scientific scoring;original204rowreportMAE121.210vs61.142persistence,and later1853rowreport31.724vs39.072remainunchanged,differentcohorts. All protected model/card/prediction/holdout hashes unchanged.213full software tests pass;new test fixtures are synthetic. One integration trial advances52->53,not perplot/test/export. Latest officialSingapore41snapshots adds1150matched later baseline outcomes,35100total,MAE4.804530spaces;1237newforecasts frozen. Source57unchanged. No occupancy model promotion:failed rainy-view final gate retained and all final groups remain consumed. Old combined offline package remains an older snapshot;nextrefresh is justified by this concrete application feature change. Visible/manual/physical/new-machine/student/official acceptance unclaimed. Guide:docs/FORECAST_REPORTS_GUIDE.md;pointer:reports/forecast_display_exports_latest.json.'
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md']:append(p,title,note)
    append('docs/UI_TEST_LOG.md',title,'Actual hidden native forecast widgets,real matplotlib plots and mocked export-folder dialogs checked for both saved reports. Real combobox park-change event invalidates old plot/export;save-before-show refused before directory dialog. Both export PNGs visually inspected;source curves/timestamps/metrics preserved. No visible window/manual dialog typing or new forecast score.')
    append('docs/DATASET_PROVENANCE.md',title,'Only archived experiment output JSON read for forecast display/export. DerivedCSV includesSRC-DS-003,run/method/park,grid target and separately recorded real sensor time/lead,occupied and available values. Sidecar records archived prediction/checkpoint hashes;export manifest bindsPNG/CSV/reportJSON. No raw/processed/split holdout reads under audit,no new source acquisition. Separate Singapore receipt/raw/normalized/prospective history remains authoritative.')
    guide='''# Read and save the right forecast

The app has two saved forecasting reports. **Both use an LSTM**, a model that learns from sequences. The original predicts the occupancy level. The later variant learns a bounded change from the last count, limits it using the recent trend, and was trained with a group-relative objective so parking locations receive more balanced attention.

## Use the app

1. Open **Availability forecast**.
2. Choose **Original experiment** or **Later-date check**, then a car park.
3. Select **Show held-out forecast**. The legend and score name the actual variant.
4. Select **Save forecast results**, then choose a folder. It saves the displayed graph, a CSV, a report description and checksum records.
5. Changing the report or car park clears the old graph. Show the new forecast before saving again.

The original report says **Original LSTM**. The later one says **Group-relative residual LSTM**. These are saved historical Birmingham forecasts, not a newly generated live forecast.

| Saved report | Evaluation dates | Recorded windows | Model MAE (spaces) | Persistence MAE (spaces) |
|---|---|---:|---:|---:|
| Original LSTM | 8–11 December 2016 | 204 | 121.21 | 61.14 |
| Group-relative residual LSTM | 12–19 December 2016 | 1,853 | 31.72 | 39.07 |

These rows use different dates and windows. Compare each model with its persistence value on the same row. The score in the app describes the whole saved report, even when its graph shows only one car park.

Think of persistence as saying “there were 100 cars at the last reading, so expect 100 again.” MAE is the mean absolute counting error. An MAE of five spaces means errors average five spaces; it is not a five-percent accuracy score.

The grid targets are half an hour apart. Real matched readings in the later report occur about 10.0–29.1 minutes after the forecast origin. The original report did not save the exact sensor lead. Missing sensor times remain blank in exports rather than being filled with the grid time.

## What is saved

| File in your chosen export folder | Meaning |
|---|---|
| `forecast.png` | The displayed graph with the correct method in its legend |
| `forecasts.csv` | The displayed car park's actual, forecast and persistence counts, with method/run IDs and recorded timestamps |
| `forecast_report.json` | Method, source, archived prediction/checkpoint hashes, whole-report score and timing scope |
| `export_metadata.json` | Checksums connecting the graph, CSV and report description |

Tested examples are under `outputs/forecast_display_checks/FORECAST-DISPLAY-EXPORT-20261026T023007776153Z/`. The exact integration pointer is `reports/forecast_display_exports_latest.json`. Source records are in `data/source_manifest.csv` and `data/resource_receipts.jsonl`;SRC-DS-003 is the UCI Birmingham dataset. Immutable parent predictions stay under their unique `experiments/results/` run folders.

This fix changes names, display and exports. It does not retrain models, recalculate their old scores or reopen raw final-test data. The Singapore feed is separate aggregate availability data. The earlier copied offline demo remains a dated snapshot until the next package update.
'''
    p=ROOT/'docs/FORECAST_REPORTS_GUIDE.md';assert not p.exists();p.write_text(guide,encoding='utf-8')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;requirements=list(r)
    for item in requirements:
        if item['requirement_id'] in {'APP-01','APP-02','SEQ-02','QA-02'}:
            item['actual_evidence']+='; models/forecast_display_export_validation.json; tests/test_forecast_export.py; docs/FORECAST_REPORTS_GUIDE.md'
            item['test_result']+=';213software tests;both actual hidden-native report labels/plots/PNG-CSV-JSON exports verified;no raw final reads/scoring;protected bytes unchanged'
            item['open_problems']+=';earlier copied offline package remains dated;visible/manual export dialog and physical/new-machine use unverified'
    with req.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(requirements)
    write(E/'handoff_checks.json',dict(completed_trials=53,wakeups_completed=36,software_tests_passed=213,
        no_active_jobs=True,normal_forbidden_read_or_network_attempts=0,negative_raw_probe_blocked=True,
        archived_predictions_models_and_holdout_claims_unchanged=True,forecast_variants_correctly_identified=True,
        native_widget_plot_export_checks_passed=True,scientific_accuracy_evaluated=False,
        occupancy_failed_final_retained=True,old_offline_package_updated=False,source_records=57,next_live_milestone=100))
    print(json.dumps(dict(completed_trials=53,methods=[r['method'] for r in study['reports']],tests=213,original_predictions_unchanged=True),indent=2))


if __name__=='__main__':main()
