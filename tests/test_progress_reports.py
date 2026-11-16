"""Synthetic saved-report isolation and meaningful export edge cases."""
import csv,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.progress_reports import load_progress,progress_text,export_progress
from smart_parking.provenance import digest


class ProgressTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[1]/'.cache/test_tmp';base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.base=self.root/'reports/progress';self.base.mkdir(parents=True)
        self.report=dict(schema_version=1,as_of='2020-01-01T00:00:00+00:00',completed_trials=1,software_tests=1,
            features=[dict(feature='Fixture',status='Incomplete',result='No scored crossing',next_action='Fresh labels')],
            metrics=[dict(check='Zero references',numerator=0,denominator=0,value=None,note='Not evaluable')],
            sources=[dict(source_id='SYNTHETIC',resource='=UNTRUSTED()',url='https://example.invalid')],experiments=[])
        self.path=self.base/'snapshot.json';self.path.write_text(json.dumps(self.report))
        self.pointer=self.base/'latest.json';self.pointer.write_text(json.dumps(dict(path='reports/progress/snapshot.json',sha256=digest(self.path))))

    def test_display_keeps_dated_incomplete_scope(self):
        report=load_progress(self.root);text=progress_text(report)
        self.assertIn('Final acceptance remains incomplete',text)
        self.assertIn('2020-01-01',text);self.assertIn('Fresh labels',text)

    def test_tampered_or_escaping_report_is_rejected(self):
        self.path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'checksum'):load_progress(self.root)
        self.pointer.write_text(json.dumps(dict(path='outside.json',sha256='irrelevant')))
        with self.assertRaisesRegex(ValueError,'inside the report'):load_progress(self.root)

    def test_exports_preserve_zero_unavailable_and_prevent_formula_execution(self):
        folder=export_progress(self.root,self.report)
        with (folder/'metrics.csv').open(encoding='utf-8-sig',newline='') as f:row=next(csv.DictReader(f))
        self.assertEqual(row['numerator'],'0');self.assertEqual(row['denominator'],'0');self.assertEqual(row['value'],'')
        with (folder/'sources.csv').open(encoding='utf-8-sig',newline='') as f:source=next(csv.DictReader(f))
        self.assertTrue(source['resource'].startswith("'=UNTRUSTED"))
        metadata=json.loads((folder/'export_metadata.json').read_text())
        for name,checksum in metadata['files'].items():self.assertEqual(digest(folder/name),checksum)
