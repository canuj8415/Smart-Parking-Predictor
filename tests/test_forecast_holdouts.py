"""Synthetic source/date fixtures test consumption; never open real final labels."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecast_holdouts import evaluate_forecast_once,assert_forecast_dates_closed
from smart_parking.provenance import digest

class ForecastHoldoutTests(unittest.TestCase):
    def setUp(self):
        parent=Path(__file__).resolve().parents[1]/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=parent);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.source=self.root/'synthetic.csv';self.source.write_text('SYNTHETIC SOURCE FIXTURE\n')
        self.checkpoint=self.root/'weights.bin';self.checkpoint.write_bytes(b'SYNTHETIC WEIGHTS')
        self.reservation=self.make_reservation('reserved.json',['2020-01-01','2020-01-02'])
        self.protocol=self.root/'protocol.json';self.selection=self.root/'selection.json';self.bind()
    def make_reservation(self,name,days):
        p=self.root/name
        p.write_text(json.dumps(dict(source_id='SYNTHETIC',reserved_dates=days,source_manifest='synthetic.csv',source_manifest_sha256=digest(self.source),reserved_rows=len(days),metadata=[dict(source_id='SYNTHETIC',source_row=str(i),capture_date=d,timestamp=d+'T12:00:00',split='test') for i,d in enumerate(days)])))
        return p
    def bind(self):
        self.protocol.write_text(json.dumps(dict(checkpoint_sha256=digest(self.checkpoint),reservation_sha256=digest(self.reservation),target_rule='SYNTHETIC TEST ONLY')))
        self.selection.write_text(json.dumps(dict(validation_gate_passed=True,checkpoint_sha256=digest(self.checkpoint),final_protocol_sha256=digest(self.protocol),reservation_sha256=digest(self.reservation))))
    def evaluate(self,callback):
        return evaluate_forecast_once(self.reservation,self.selection,self.checkpoint,self.protocol,'SYNTHETIC-RUN',callback,expected_manifest_sha256=digest(self.reservation),expected_protocol_sha256=digest(self.protocol),root=self.root)
    def test_claim_is_flushed_before_callback_and_repeat_is_blocked(self):
        ordering=[]
        def callback(rows):
            self.assertTrue(ordering);self.assertEqual(len(list((self.root/'data/forecast_holdout_claims').glob('*.claim.json'))),1)
            return len(rows)
        import os
        real_fsync=os.fsync
        with patch('smart_parking.forecast_holdouts.os.fsync',side_effect=lambda fd:(real_fsync(fd),ordering.append('flushed'))):
            self.assertEqual(self.evaluate(callback),2)
        with self.assertRaisesRegex(ValueError,'overlaps'):self.evaluate(lambda _:self.fail('must not read again'))
    def test_failed_callback_consumes_dates_and_saves_failure(self):
        def fail(_):raise RuntimeError('synthetic interruption')
        with self.assertRaisesRegex(RuntimeError,'interruption'):self.evaluate(fail)
        with self.assertRaisesRegex(ValueError,'overlaps'):assert_forecast_dates_closed(self.reservation,root=self.root)
        outcomes=list((self.root/'data/forecast_holdout_claims').glob('*.outcome.json'))
        self.assertIn('failed',json.loads(outcomes[0].read_text())['status'])
    def test_overlapping_date_is_blocked_even_with_other_manifest_and_rows(self):
        self.evaluate(lambda _:None)
        self.reservation=self.make_reservation('other.json',['2020-01-02','2020-01-03']);self.bind()
        with self.assertRaisesRegex(ValueError,'overlaps'):self.evaluate(lambda _:self.fail('overlap'))
        self.reservation=self.make_reservation('disjoint.json',['2020-01-03']);self.bind()
        self.assertEqual(self.evaluate(lambda rows:len(rows)),1)
    def test_failed_gate_or_changed_checkpoint_never_calls_callback(self):
        selected=json.loads(self.selection.read_text());selected['validation_gate_passed']=False;self.selection.write_text(json.dumps(selected))
        with self.assertRaisesRegex(ValueError,'passed'):self.evaluate(lambda _:self.fail('gate'))
        self.bind();self.checkpoint.write_bytes(b'CHANGED')
        with self.assertRaisesRegex(ValueError,'checkpoint'):self.evaluate(lambda _:self.fail('checkpoint'))
        self.assertFalse((self.root/'data/forecast_holdout_claims').exists())
    def test_protocol_binding_and_source_mutation_are_rejected(self):
        self.protocol.write_text(self.protocol.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'bind this final protocol'):self.evaluate(lambda _:self.fail('protocol'))
        self.bind();self.source.write_text('CHANGED SOURCE')
        with self.assertRaisesRegex(ValueError,'source manifest changed'):self.evaluate(lambda _:self.fail('source'))
    def test_source_mutated_during_callback_is_invalid_and_stays_consumed(self):
        with self.assertRaisesRegex(ValueError,'source manifest changed'):
            self.evaluate(lambda _:self.source.write_text('MUTATION'))
        self.source.write_text('SYNTHETIC SOURCE FIXTURE\n')
        with self.assertRaisesRegex(ValueError,'overlaps'):self.evaluate(lambda _:self.fail('consumed'))
