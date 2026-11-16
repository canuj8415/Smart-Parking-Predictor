"""Fault-injected local exports; synthetic images/reports,not model evaluation."""
import json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from smart_parking.exports import export_analysis,export_forecast
from smart_parking.forecast_reports import build_forecast_view
from smart_parking.provenance import digest


class Figure:
    def savefig(self,path,**kwargs):Image.new('RGB',(12,8),'navy').save(path)


class InterruptedImage:
    def save(self,path):
        Path(path).write_bytes(b'partial synthetic image');raise OSError('Injected storage interruption')


def fixture_view():
    return build_forecast_view(dict(name='SYNTHETIC',run_id='SYNTHETIC',method_id='fixture',method_label='Synthetic fixture',
        architecture='Software test only',source_id='SYNTHETIC',predictions_sha256='fixture',mae=2,baseline_mae=3,horizon_note='Synthetic',
        rows=[dict(car_park_id='FIXTURE',origin='2020-01-01T00:00:00',target_time='2020-01-01T00:30:00',capacity=10,actual_occupied=3,predicted_occupied=4,persistence_occupied=5)]),'FIXTURE')


class ExportTransactionTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[1]/'outputs/test_fixtures';base.mkdir(parents=True,exist_ok=True)
        self.temporary=tempfile.TemporaryDirectory(dir=base);self.addCleanup(self.temporary.cleanup);self.parent=Path(self.temporary.name).resolve()
        assert self.parent.is_relative_to(base.resolve())
        self.earlier=self.parent/'previous_export';self.earlier.mkdir();(self.earlier/'keep.txt').write_bytes(b'previous genuine export must survive')
        self.prior=digest(self.earlier/'keep.txt');self.image=Image.new('RGB',(8,8),'green')

    def assert_prior_only(self):
        self.assertEqual(set(self.parent.iterdir()),{self.earlier});self.assertEqual(digest(self.earlier/'keep.txt'),self.prior)

    def test_interrupted_analysis_cleans_partial_png_and_preserves_previous(self):
        with self.assertRaisesRegex(OSError,'Injected'):export_analysis(self.parent,{'kind':'SYNTHETIC'},InterruptedImage())
        self.assert_prior_only()

    def test_interrupted_preview_cleans_already_written_analysis(self):
        with self.assertRaises(OSError):export_analysis(self.parent,{'kind':'SYNTHETIC'},self.image,preview_image=InterruptedImage(),preview_kind='mask')
        self.assert_prior_only()

    def test_nonfinite_or_unsupported_json_is_rejected_before_parent_creation(self):
        for value in [float('nan'),float('inf'),float('-inf'),object()]:
            parent=self.parent/'must_not_exist'
            with self.assertRaises(ValueError):export_analysis(parent,{'value':value},self.image)
            self.assertFalse(parent.exists())
        self.assert_prior_only()

    def test_invalid_png_cannot_be_published(self):
        class InvalidImage:
            def save(self,path):Path(path).write_bytes(b'not a PNG')
        with self.assertRaises(ValueError):export_analysis(self.parent,{'kind':'SYNTHETIC'},InvalidImage())
        self.assert_prior_only()

    def test_metadata_write_failure_removes_every_owned_file(self):
        original=Path.write_text
        def fail(path,text,*args,**kwargs):
            if path.name=='export_metadata.json':path.write_bytes(b'{');raise OSError('Injected metadata interruption')
            return original(path,text,*args,**kwargs)
        with patch.object(Path,'write_text',new=fail):
            with self.assertRaises(OSError):export_analysis(self.parent,{'kind':'SYNTHETIC'},self.image)
        self.assert_prior_only()

    def test_hash_failure_leaves_no_published_or_staging_folder(self):
        with patch('smart_parking.exports.digest',side_effect=OSError('Injected checksum read failure')):
            with self.assertRaises(OSError):export_analysis(self.parent,{'kind':'SYNTHETIC'},self.image)
        self.assert_prior_only()

    def test_forecast_plot_interruption_cleans_its_partial_file(self):
        class InterruptedFigure:
            def savefig(self,path,**kwargs):Path(path).write_bytes(b'partial');raise OSError('Injected plot interruption')
        with self.assertRaises(OSError):export_forecast(self.parent,fixture_view(),InterruptedFigure())
        self.assert_prior_only()

    def test_cancellation_cleans_owned_partial_files(self):
        class CancelledImage:
            def save(self,path):Path(path).write_bytes(b'partial');raise KeyboardInterrupt('Synthetic cancellation')
        with self.assertRaises(KeyboardInterrupt):export_analysis(self.parent,{'kind':'SYNTHETIC'},CancelledImage())
        self.assert_prior_only()

    def test_mismatched_displayed_forecast_vectors_create_nothing(self):
        for key,value in [('actual_available',[]),('predicted_available',[9]),('persistence_available',[float('nan')])]:
            view=fixture_view();view[key]=value
            with self.assertRaises(ValueError):export_forecast(self.parent,view,Figure())
            self.assert_prior_only()

    def test_nonfinite_report_metrics_create_nothing(self):
        view=fixture_view();view['report']['mae']=float('nan')
        with self.assertRaises(ValueError):export_forecast(self.parent,view,Figure())
        self.assert_prior_only()

    def test_timestamp_collision_never_overwrites_prior_export(self):
        when=datetime(2026,1,1,tzinfo=timezone.utc)
        existing=self.parent/'parking_20260101T000000000000Z';existing.mkdir();(existing/'sentinel.txt').write_bytes(b'existing')
        with patch('smart_parking.exports.datetime') as clock:
            clock.now.return_value=when
            with self.assertRaises(FileExistsError):export_analysis(self.parent,{'kind':'SYNTHETIC'},self.image)
        self.assertEqual((existing/'sentinel.txt').read_bytes(),b'existing');self.assertEqual(set(self.parent.iterdir()),{self.earlier,existing})

    def test_success_hashes_analysis_record_overlay_and_separate_preview(self):
        result={'kind':'SYNTHETIC','counts':{'occupied':1}}
        folder=export_analysis(self.parent,result,self.image,preview_image=Image.new('RGB',(8,8),'purple'),preview_kind='mask')
        metadata=json.loads((folder/'export_metadata.json').read_text());self.assertTrue(metadata['complete'])
        self.assertEqual(set(metadata['files']),{'overlay.png','analysis.json','display_preview.png'})
        self.assertTrue(all(digest(folder/n)==h for n,h in metadata['files'].items()))
        self.assertEqual(metadata['display_preview_sha256'],digest(folder/'display_preview.png'))
        self.assertEqual(json.loads((folder/'analysis.json').read_text()),result)
        self.assertFalse(any('staging' in p.name for p in self.parent.iterdir()));self.assertEqual(digest(self.earlier/'keep.txt'),self.prior)

    def test_forecast_csv_json_and_plot_publish_together(self):
        folder=export_forecast(self.parent,fixture_view(),Figure());metadata=json.loads((folder/'export_metadata.json').read_text())
        self.assertEqual(set(p.name for p in folder.iterdir()),{'forecast.png','forecasts.csv','forecast_report.json','export_metadata.json'})
        self.assertTrue(metadata['complete']);self.assertTrue(all(digest(folder/n)==h for n,h in metadata['files'].items()))
        self.assertFalse(any('staging' in p.name for p in self.parent.iterdir()))
