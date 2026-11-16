"""Bounded hidden-native validation of archived report labels and exports.

No training, final re-scoring, raw/processed data access or network requests.
"""
import csv
import json
import math
import io
import unittest
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,value):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    state_path=ROOT/'data/automation_state.json';state=read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    started=datetime.now(timezone.utc);rid='FORECAST-DISPLAY-EXPORT-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    output=ROOT/'outputs/forecast_display_checks'/rid;output.mkdir(parents=True,exist_ok=False)
    paths=['scripts/validate_forecast_display_exports.py','src/smart_parking/forecast_reports.py','src/smart_parking/app.py','src/smart_parking/exports.py','tests/test_export_transactions.py']
    source_hashes={p:digest(ROOT/p) for p in paths}
    original=read('models/lstm_30min_model_card.json');later=read('models/forecast_final_evaluation.json')
    protected_paths=['models/lstm_30min_model_card.json','models/forecast_final_evaluation.json',
        f'experiments/results/{original["run_id"]}/test_predictions.json',
        f'experiments/results/{later["run_id"]}/test_predictions.json',f'experiments/results/{later["run_id"]}/run.json',
        'models/checkpoints/lstm_30min.pt','models/checkpoints/occupancy_resnet18.pt','models/checkpoints/parking_unet.pt']
    protected_paths += [p.relative_to(ROOT).as_posix() for name in ['holdout_claims','forecast_holdout_claims','sequence_holdout_claims'] for p in (ROOT/'data'/name).glob('*.json')]
    protected={p:digest(ROOT/p) for p in protected_paths}
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=145,
        source_ids=['SRC-DS-003'],source_hashes=source_hashes,protected_hashes=protected,
        hypothesis='Transactional exports preserve archived method/count provenance and earlier saves, reject inconsistent or nonfinite records before publication, and leave no partial published directory under controlled save failures.',
        gates=['Original LSTM versus group-relative residual LSTM named correctly',
            'Legend/text/CSV/JSON agree on method,run,park and displayed values',
            'Report/car-park changes clear old plot and export state',
            'Export before showing is refused before opening a directory dialog',
            'Normal Python raw/processed/split and network attempts zero; explicit negative raw-file probe blocked',
            'Archived prediction/card/checkpoint/holdout bytes unchanged',
            'Synthetic fault/cancellation/collision/invalid-data cases preserve prior exports and clean owned staging files',
            'Successful image preview and forecast exports have complete checksum manifests'],
        limits=dict(wall_seconds=180,reports=2,windows_per_report='All saved rows for first selected park'),
        fixture_kind='Synthetic test data explicitly separate from real archived Birmingham prediction display',
        accuracy_evaluated=False,limitations=['Hidden native Tk widgets and real plot export; not visible/manual usability',
            'Archived output display,not a new forecast evaluation or live/camera validation','Python audit covers Python opens/sockets,not all native system I/O'])
    dump(folder/'protocol.json',protocol)
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in source_hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'),deadline_seconds=180)]
    dump(state_path,state);timer=time.perf_counter();app=None;denied=[];probe=False
    forbidden=[(ROOT/'data'/name).resolve() for name in ['raw','processed','splits']]
    def audit(event,args):
        if event in {'socket.connect','socket.getaddrinfo'}:
            denied.append(dict(event=event,probe=probe));raise PermissionError('Archived forecast check is offline')
        if event=='open' and isinstance(args[0],(str,bytes)):
            path=Path(args[0].decode() if isinstance(args[0],bytes) else args[0]).resolve()
            if any(path.is_relative_to(base) for base in forbidden):
                denied.append(dict(event=event,path=str(path),probe=probe));raise PermissionError('Raw/processed/split data forbidden during archived display')
    sys.addaudithook(audit)
    try:
        sys.path.insert(0,str(ROOT))
        suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_export_transactions');test_output=io.StringIO()
        test_result=unittest.TextTestRunner(stream=test_output,verbosity=2).run(suite)
        (folder/'fault_tests.txt').write_text(test_output.getvalue(),encoding='utf-8')
        assert test_result.wasSuccessful() and test_result.testsRun==13
        from smart_parking.app import ParkingApp
        from smart_parking.forecast_reports import ORIGINAL,LATER,ORIGINAL_METHOD,LATER_METHOD,load_forecast_report
        app=ParkingApp();app.withdraw();app.tabs.select(app.forecast);app.update_idletasks()
        reports=[]
        def modal_error(title,message):raise AssertionError(f'Unexpected modal error: {title}: {message}')
        with patch('smart_parking.app.messagebox.showerror',side_effect=modal_error),patch('smart_parking.app.messagebox.showinfo') as info:
            with patch('smart_parking.app.filedialog.askdirectory') as no_dialog:
                app.save_forecast();no_dialog.assert_not_called()
            assert info.call_count==1
            for name,expected in [(ORIGINAL,ORIGINAL_METHOD),(LATER,LATER_METHOD)]:
                if (folder/'CANCEL').exists() or time.perf_counter()-timer>180:raise InterruptedError('Bounded report check cancelled')
                app.forecast_view.set(name);app.load_parks();app.update_idletasks()
                assert app.forecast_chart is None and app.forecast_result is None
                assert expected in app.forecast_info.get()
                selected_park=app.park.get();app.show_forecast();app.update_idletasks()
                view=app.forecast_result;assert view and view['report']['method_label']==expected
                axes=app.forecast_chart.figure.axes[0]
                labels=axes.get_legend_handles_labels()[1]
                assert labels==['Actual available',expected+' forecast','Last observation']
                assert list(axes.lines[1].get_ydata())==view['predicted_available']
                assert f"Overall report MAE: {expected} " in app.forecast_info.get()
                assert 'MAE: LSTM ' not in app.forecast_info.get()
                before=set(output.iterdir())
                with patch('smart_parking.app.filedialog.askdirectory',return_value=str(output)) as dialog:
                    app.save_forecast();dialog.assert_called_once()
                created=set(output.iterdir())-before;assert len(created)==1;export=created.pop()
                metadata=read(export/'export_metadata.json');snapshot=read(export/'forecast_report.json')
                with (export/'forecasts.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
                assert len(rows)==len(view['rows']) and all(r['method_label']==expected and r['car_park_id']==selected_park for r in rows)
                assert metadata['method_id']==view['report']['method_id'] and metadata['run_id']==view['report']['run_id']
                assert metadata['complete'] and all(digest(export/p)==h for p,h in metadata['files'].items())
                assert snapshot['report']['mae']==view['report']['mae'] and 'not newly scored' in snapshot['metrics_scope']
                for row,source,pred in zip(rows,view['rows'],view['predicted_available']):
                    assert math.isclose(float(row['predicted_available']),pred,rel_tol=1e-12)
                    assert row['target_source_time']==str(source.get('target_source_time') or '')
                    assert row['actual_target_lead_minutes']==str(source.get('actual_target_lead_minutes') if source.get('actual_target_lead_minutes') is not None else '')
                reports.append(dict(report=name,method=expected,run_id=view['report']['run_id'],car_park_id=selected_park,
                    selected_windows=len(rows),saved_report_mae=view['report']['mae'],saved_baseline_mae=view['report']['baseline_mae'],
                    legend=labels,info_text=app.forecast_info.get(),export=export.relative_to(ROOT).as_posix(),
                    original_prediction_sha256=view['report']['predictions_sha256'],plot_sha256=digest(export/'forecast.png')))
                # Exercise real combobox event binding, not just the helper.
                choices=list(app.park_picker['values']);app.park.set(choices[-1]);app.park_picker.event_generate('<<ComboboxSelected>>');app.update()
                assert app.forecast_result is None and app.forecast_chart is None
                with patch('smart_parking.app.filedialog.askdirectory') as no_dialog:
                    app.save_forecast();no_dialog.assert_not_called()
        assert not denied
        probe=True
        try:(ROOT/'data/raw/NEGATIVE_CONTROL_DO_NOT_READ').read_bytes()
        except PermissionError:pass
        else:raise AssertionError('Negative raw-data control was not blocked')
        assert len(denied)==1 and denied[0]['probe']
        assert all(digest(ROOT/p)==h for p,h in source_hashes.items())
        assert all(digest(ROOT/p)==h for p,h in protected.items())
        app.destroy();app=None
        outcome=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-timer,
            integration_gate_passed=True,reports=reports,normal_forbidden_attempts=0,negative_control=denied,
            synthetic_transaction_tests=13,transactional_export_gate_passed=True,
            source_predictions_models_and_holdouts_unchanged=True,visible_desktop_or_manual_validation=False)
        dump(folder/'run.json',outcome);dump(ROOT/'models/forecast_display_export_validation.json',outcome)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Transactional analysis/forecast exports;synthetic faults plus real archived hidden-native integration',started_at=started.isoformat(),
            finished_at=outcome['finished_at'],source_ids='SRC-DS-003',split_ids='Archived existing reports only; no raw final reads or scoring',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Actual hidden native Tk + real saved-report plot/CSV/JSON',
            epochs=0,random_seed=145,hardware='CPU',execution_environment=sys.version.split()[0],
            training_duration=outcome['duration_seconds'],evaluation_metrics=json.dumps(dict(integration_gate_passed=True,transactional_export_gate_passed=True,synthetic_transaction_tests=13,reports=reports,normal_forbidden_attempts=0,accuracy_evaluated=False)),
            logs=folder.relative_to(ROOT).as_posix(),checkpoints='All original model weights unchanged',code_revision_basis='352a260 plus sealed transactional export changes',
            implementation_sha256=source_hashes[paths[0]],conclusions='13syntheticfault/integritycases and2realarchivedmethodexports pass;no new accuracy/raw-data reads/model promotion;notpower-loss/physicaloffline/manualUIcertification')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,integration_gate_passed=True,reports=reports,normal_forbidden_attempts=0),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False,denied=denied))
        state=read(state_path);raise
    finally:
        if app is not None:app.destroy()
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
