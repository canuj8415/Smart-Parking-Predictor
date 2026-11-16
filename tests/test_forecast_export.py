"""Synthetic metadata/CSV lifecycle tests, not new forecasting evaluation."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecast_reports import build_forecast_view,LATER,LATER_METHOD
from smart_parking.exports import export_forecast
from smart_parking.provenance import digest
from smart_parking.app import ParkingApp


class FixtureFigure:
    def savefig(self,path,**kwargs):Image.new('RGB',(12,8),'navy').save(path)


class ForecastExportTests(unittest.TestCase):
    def view(self):
        return build_forecast_view(dict(name=LATER,run_id='SYNTHETIC',method_id='trend_guarded_group_relative_residual_lstm',
            method_label=LATER_METHOD,architecture='Synthetic report fixture',source_id='SYNTHETIC',predictions_sha256='fixture-hash',
            mae=2,baseline_mae=3,horizon_note='Source lead not recorded in this synthetic fixture',
            rows=[dict(car_park_id='FIXTURE',origin='2016-12-12T10:00:00',target_time='2016-12-12T10:30:00',
                capacity=100,actual_occupied=15,predicted_occupied=12,persistence_occupied=18)]),'FIXTURE')

    def test_saved_graph_csv_and_metadata_describe_same_archived_method(self):
        base=Path(__file__).resolve().parents[1]/'outputs/test_fixtures';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temporary:
            self.assertTrue(Path(temporary).resolve().is_relative_to(base.resolve()))
            folder=export_forecast(temporary,self.view(),FixtureFigure())
            with (folder/'forecasts.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
            self.assertEqual(rows[0]['method_label'],LATER_METHOD);self.assertEqual(rows[0]['predicted_available'],'88')
            self.assertEqual(rows[0]['target_source_time'],'');self.assertEqual(rows[0]['actual_target_lead_minutes'],'')
            metadata=json.loads((folder/'export_metadata.json').read_text());report=json.loads((folder/'forecast_report.json').read_text())
            self.assertEqual(metadata['method_id'],'trend_guarded_group_relative_residual_lstm')
            self.assertEqual(report['original_occupied_prediction_column'],'candidate_occupied')
            self.assertIn('not newly scored',report['metrics_scope'])
            self.assertTrue(all(digest(folder/name)==sha for name,sha in metadata['files'].items()))

    def test_export_requires_actual_displayed_forecast_before_creating_folder(self):
        with self.assertRaisesRegex(ValueError,'Show an archived'):export_forecast('unused-forecast',None,None)
        state=SimpleNamespace(forecast_result=None,forecast_chart=None)
        with patch('smart_parking.app.filedialog.askdirectory') as dialog,patch('smart_parking.app.messagebox.showinfo') as info:
            ParkingApp.save_forecast(state);dialog.assert_not_called();info.assert_called_once()

    def test_changed_car_park_invalidates_old_plot_and_export_snapshot(self):
        child=Mock();info=Mock()
        state=SimpleNamespace(forecast_plot=SimpleNamespace(winfo_children=lambda:[child]),forecast_chart=object(),
            forecast_result=self.view(),forecast_info=info)
        state.clear_forecast=lambda:ParkingApp.clear_forecast(state)
        ParkingApp.forecast_selection_changed(state)
        self.assertIsNone(state.forecast_chart);self.assertIsNone(state.forecast_result);child.destroy.assert_called_once()
        self.assertIn('Car park changed',info.set.call_args.args[0])

    def test_mixed_car_park_rows_are_rejected(self):
        view=self.view();view['rows'][0]['car_park_id']='OTHER'
        with self.assertRaisesRegex(ValueError,'does not match'):export_forecast('unused-forecast',view,FixtureFigure())
