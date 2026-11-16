"""Synthetic archived results test display routing, not forecasting accuracy."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecast_reports import available_forecast_reports,load_forecast_report,build_forecast_view,ORIGINAL,LATER,ORIGINAL_METHOD,LATER_METHOD
from smart_parking.provenance import digest

class ForecastReportTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[1]/'.cache/test_tmp';base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'models').mkdir();self.folder=self.root/'experiments/results/SYNTHETIC';self.folder.mkdir(parents=True)
        self.predictions=self.folder/'test_predictions.json';self.predictions.write_text(json.dumps([dict(car_park_id='FIXTURE',
            origin='2016-12-12T10:00:00',target_time='2016-12-12T10:30:00',capacity=100,actual_occupied=15,
            candidate_occupied=12,predicted_occupied=88,persistence_occupied=18)]))
        self.result=self.folder/'run.json';self.result.write_text(json.dumps(dict(final_evaluation=dict(final_gate_passed=True,metrics=dict(candidate_mae_spaces=2,persistence_mae_spaces=3),actual_target_lead_minutes=dict(min=10,max=29)))))
        (self.root/'models/forecast_final_evaluation.json').write_text(json.dumps(dict(run_id='SYNTHETIC',run_json_sha256=digest(self.result),predictions_sha256=digest(self.predictions))))
    def test_later_report_uses_its_own_prediction_column_metrics_and_timing(self):
        report=load_forecast_report(LATER,self.root)
        self.assertEqual(report['rows'][0]['predicted_occupied'],12);self.assertEqual(report['mae'],2)
        self.assertEqual(report['method_label'],LATER_METHOD)
        self.assertIn('residual LSTM',report['architecture']);self.assertEqual(report['predictions_sha256'],digest(self.predictions))
        self.assertIn('10.0–29.0',report['horizon_note']);self.assertIn('not live',report['horizon_note'])
        self.assertEqual(available_forecast_reports(self.root),[ORIGINAL,LATER])
    def test_changed_saved_report_is_rejected_without_silent_fallback(self):
        self.predictions.write_text('[]')
        with self.assertRaisesRegex(ValueError,'checksum'):load_forecast_report(LATER,self.root)
    def test_unknown_view_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):load_forecast_report('UNAVAILABLE',self.root)

    def test_original_and_later_keep_distinct_methods_and_saved_metrics(self):
        original=self.root/'experiments/results/ORIGINAL_SYNTHETIC';original.mkdir()
        (original/'test_predictions.json').write_text(json.dumps([dict(car_park_id='FIXTURE',predicted_occupied=33)]))
        (self.root/'models/lstm_30min_model_card.json').write_text(json.dumps(dict(run_id='ORIGINAL_SYNTHETIC',metrics=dict(mae_slots=7,persistence_mae_slots=4))))
        old=load_forecast_report(ORIGINAL,self.root);later=load_forecast_report(LATER,self.root)
        self.assertEqual(old['method_label'],ORIGINAL_METHOD);self.assertNotEqual(old['method_id'],later['method_id'])
        self.assertEqual(old['rows'][0]['predicted_occupied'],33);self.assertEqual(old['mae'],7);self.assertEqual(later['mae'],2)

    def test_view_owns_displayed_selection_and_does_not_invent_source_times(self):
        report=load_forecast_report(LATER,self.root);view=build_forecast_view(report,'FIXTURE')
        report['rows'][0]['predicted_occupied']=99;report['method_label']='different later selection'
        self.assertEqual(view['predicted_available'],[88]);self.assertEqual(view['rows'][0]['predicted_occupied'],12)
        self.assertEqual(view['report']['method_label'],LATER_METHOD)
        self.assertEqual(view['forecast_legend'],LATER_METHOD+' forecast')
        self.assertIn(LATER_METHOD+' 2.00',view['info_text']);self.assertNotIn('MAE: LSTM ',view['info_text'])
        self.assertNotIn('target_source_time',view['rows'][0])
        with self.assertRaisesRegex(ValueError,'No archived'):build_forecast_view(report,'UNKNOWN')

    def test_invalid_archived_counts_do_not_become_plausible_available_spaces(self):
        report=load_forecast_report(LATER,self.root)
        for bad in [True,float('nan'),-1,101,None]:
            report['rows'][0]['predicted_occupied']=bad
            with self.subTest(value=bad),self.assertRaises(ValueError):build_forecast_view(report,'FIXTURE')
