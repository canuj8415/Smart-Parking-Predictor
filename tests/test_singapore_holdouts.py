"""Synthetic future intervals/issuance receipts;no real final claims or data."""
import json,sys,tempfile,unittest
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.singapore_holdouts import validate_reservation,assert_history_allowed,final_once
from smart_parking.singapore_history import aware_utc
from smart_parking.provenance import digest
class SingaporeHoldoutTests(unittest.TestCase):
    def setUp(self):
        self.parent=(Path(__file__).resolve().parents[1]/'outputs/test_fixtures').resolve();self.parent.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=self.parent);self.root=Path(self.temp.name).resolve();assert self.root.is_relative_to(self.parent)
        self.checkpoint=self.root/'checkpoint.pt';self.checkpoint.write_bytes(b'synthetic-checkpoint');self.snapshot=self.root/'snapshot.json';self.snapshot.write_text('synthetic-snapshot')
        self.claims=self.root/'claims';self.prepare()
    def tearDown(self):
        assert self.root!=self.parent and self.root.is_relative_to(self.parent);self.temp.cleanup()
    def write(self,path,value):path.write_text(json.dumps(value),encoding='utf-8')
    def prepare(self,start='2026-01-01T01:00:00+00:00',end='2026-01-01T02:00:00+00:00'):
        a=aware_utc(start);b=aware_utc(end)
        self.value=dict(source_id='SRC-LIVE-001',carparks_scope='ALL',created_at='2026-01-01T00:10:00+00:00',historical_cutoff='2026-01-01T00:00:00+00:00',final_origin_start=start,final_origin_end=end,final_target_end=(b+timedelta(minutes=51)).isoformat())
        self.res=self.root/'reservation.json';self.write(self.res,self.value);self.rh=digest(self.res)
        issue=a+timedelta(minutes=15);self.ledger=self.root/'forecasts.jsonl'
        self.forecast=dict(forecast_id='synthetic-id',source_id='SRC-LIVE-001',car_park_id='synthetic',lot_type='C',capacity=10,predicted_available=3.5,
            issued_at=issue.isoformat(),committed_at=(issue+timedelta(seconds=1)).isoformat(),checkpoint_sha256=digest(self.checkpoint),reservation_sha256=self.rh,
            earliest_target=(issue+timedelta(minutes=20)).isoformat(),latest_target=(issue+timedelta(minutes=45)).isoformat(),
            origin_observed_at=(issue-timedelta(seconds=30)).isoformat(),origin_provider_time=(issue-timedelta(seconds=10)).isoformat(),
            origin_receipt=dict(source_id='SRC-LIVE-001',local_path='snapshot.json',sha256=digest(self.snapshot),accessed_at=(issue-timedelta(seconds=5)).isoformat()))
        self.ledger.write_text(json.dumps(self.forecast)+'\n',encoding='utf-8');self.selection=self.root/'selection.json';self.choice=dict(development_gate_passed=True,reservation_sha256=self.rh,checkpoint_sha256=digest(self.checkpoint),frozen_at='2026-01-01T00:30:00+00:00',forecast_ledger='forecasts.jsonl',forecast_ledger_sha256=digest(self.ledger));self.write(self.selection,self.choice)
    def call(self,callback,as_of='2026-01-01T06:00:00+00:00'):
        return final_once(self.res,self.selection,self.checkpoint,'synthetic-run',callback,as_of=as_of,receipts=self.claims,expected_reservation_sha256=self.rh,root=self.root)
    def test_history_bound_and_global_scope(self):
        assert_history_allowed(self.value,'2025-12-31T23:00:00+00:00','2025-12-31T23:00:00+00:00')
        with self.assertRaises(ValueError):assert_history_allowed(self.value,'2026-01-01T00:01:00+00:00','2026-01-01T00:00:00+00:00')
        with self.assertRaises(ValueError):validate_reservation(dict(self.value,carparks_scope='one-lot'))
    def test_callback_failure_consumes_global_interval_and_alias_overlap(self):
        def broken(value):raise RuntimeError('Synthetic scoring failure')
        with self.assertRaises(RuntimeError):self.call(broken)
        self.prepare('2026-01-01T01:30:00+00:00','2026-01-01T03:00:00+00:00')
        with self.assertRaises(ValueError):self.call(lambda value:'not called')
    def test_early_peeking_late_freeze_and_fabricated_issuance_flag_fail(self):
        with self.assertRaises(ValueError):self.call(lambda value:'not called',as_of='2026-01-01T02:00:00+00:00')
        self.write(self.selection,dict(self.choice,frozen_at='2026-01-01T01:30:00+00:00'))
        with self.assertRaises(ValueError):self.call(lambda value:'not called')
        self.write(self.selection,dict(self.choice,forecast_ledger_sha256='wrong',prospective_issuance_verified=True))
        with self.assertRaises(ValueError):self.call(lambda value:'not called')
        self.assertFalse(list(self.claims.glob('*.claim.json')) if self.claims.exists() else [])
    def test_target_outcomes_in_issuance_ledger_rejected(self):
        self.ledger.write_text(json.dumps(dict(self.forecast,actual_available=5))+'\n');self.write(self.selection,dict(self.choice,forecast_ledger_sha256=digest(self.ledger)))
        with self.assertRaises(ValueError):self.call(lambda value:'not called')
    def test_inputs_changed_during_callback_fail_and_remain_consumed(self):
        def mutate(value):self.checkpoint.write_bytes(b'mutated-fixture');return {'fixture':1}
        with self.assertRaises(ValueError):self.call(mutate)
        self.assertEqual(len(list(self.claims.glob('*.claim.json'))),1)
    def test_successful_bound_callback_runs_once_after_complete_window(self):
        calls=[]
        result=self.call(lambda value:(calls.append(value['source_id']) or {'synthetic_score':2}))
        self.assertEqual(result,{'synthetic_score':2});self.assertEqual(calls,['SRC-LIVE-001'])
        with self.assertRaises(ValueError):self.call(lambda value:'must not repeat')
if __name__=='__main__':unittest.main()
