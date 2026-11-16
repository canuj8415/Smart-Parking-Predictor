import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.prospective import freeze_baseline,score_baseline,record_snapshot,ledger_status

def row(at,available=40,capacity=100):
    return dict(source_id='SRC-LIVE-001',car_park_id='FIXTURE',lot_type='C',capacity=capacity,available=available,observed_at=at,feed_timestamp=at)

class ProspectiveTests(unittest.TestCase):
    def test_stale_snapshot_cannot_create_retrospective_forecast(self):
        self.assertEqual(freeze_baseline([row('2026-10-24T08:00:00+00:00')],'2026-10-24T09:00:00+00:00'),[])
    def test_early_or_wrong_capacity_observation_not_scored(self):
        forecast=freeze_baseline([row('2026-10-24T08:00:00+00:00')],'2026-10-24T08:00:05+00:00')
        self.assertEqual(score_baseline(forecast,[row('2026-10-24T08:10:00+00:00')],'2026-10-24T08:10:05+00:00'),[])
        self.assertEqual(score_baseline(forecast,[row('2026-10-24T08:30:00+00:00',35,99)],'2026-10-24T08:30:05+00:00'),[])
    def test_later_target_is_scored_once_with_actual_horizon(self):
        forecast=freeze_baseline([row('2026-10-24T08:00:00+00:00')],'2026-10-24T08:00:05+00:00')
        scores=score_baseline(forecast,[row('2026-10-24T08:30:00+00:00',35)],'2026-10-24T08:30:05+00:00')
        self.assertEqual(scores[0]['absolute_error_spaces'],5)
        self.assertAlmostEqual(scores[0]['actual_horizon_minutes'],29+55/60)
        self.assertEqual(score_baseline(forecast,[row('2026-10-24T08:30:00+00:00',35)],'2026-10-24T08:30:05+00:00',[scores[0]['forecast_id']]),[])
    def test_duplicate_collection_does_not_reissue_forecasts(self):
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            first=record_snapshot([row('2026-10-24T08:00:00+00:00')],{'path':'synthetic-fixture.json'},'2026-10-24T08:00:05+00:00',temporary)
            second=record_snapshot([row('2026-10-24T08:00:00+00:00')],{'path':'synthetic-fixture.json'},'2026-10-24T08:00:06+00:00',temporary)
            self.assertEqual(first['forecasts_added'],1);self.assertEqual(second['forecasts_added'],0)
            self.assertIsNone(second['baseline_mae_spaces'])
    def test_naive_provider_time_is_interpreted_in_singapore(self):
        forecasts=freeze_baseline([row('2026-10-24T16:00:00')],'2026-10-24T08:00:05+00:00')
        self.assertEqual(forecasts[0]['origin_observed_at'],'2026-10-24T08:00:00+00:00')
    def test_ledger_coverage_separates_scores_expiry_and_pending_states(self):
        forecasts=[freeze_baseline([row(f'2026-10-24T{time}:00+00:00')],f'2026-10-24T{time}:00+00:00')[0] for time in ['07:50','08:00','08:12','08:35','08:55']]
        score=dict(forecast_id=forecasts[0]['forecast_id'],scored_at='2026-10-24T08:22:00+00:00')
        status=ledger_status(forecasts,[score],'2026-10-24T09:00:00+00:00')
        for key in ['scored','expired_missing_target','awaiting_late_delivery','pending_in_window','pending_before_window']:self.assertEqual(status[key],1)
        self.assertEqual(status['resolved_forecasts'],2);self.assertEqual(status['matched_fraction_of_resolved_forecasts'],.5)
    def test_late_delivery_grace_avoids_premature_missing_target_claim(self):
        forecast=freeze_baseline([row('2026-10-24T08:00:00+00:00')],'2026-10-24T08:00:00+00:00')
        at_boundary=ledger_status(forecast,[],'2026-10-24T08:51:00+00:00')
        self.assertEqual(at_boundary['awaiting_late_delivery'],1);self.assertIsNone(at_boundary['matched_fraction_of_resolved_forecasts'])
        expired=ledger_status(forecast,[],'2026-10-24T08:51:01+00:00')
        self.assertEqual(expired['expired_missing_target'],1);self.assertEqual(expired['matched_fraction_of_resolved_forecasts'],0)
    def test_coverage_is_as_of_time_and_rejects_duplicate_ledger_ids(self):
        first=freeze_baseline([row('2026-10-24T08:00:00+00:00')],'2026-10-24T08:00:00+00:00')[0]
        future=freeze_baseline([row('2026-10-24T10:00:00+00:00')],'2026-10-24T10:00:00+00:00')[0]
        late_score=dict(forecast_id=first['forecast_id'],scored_at='2026-10-24T10:10:00+00:00')
        status=ledger_status([first,future],[late_score],'2026-10-24T09:00:00+00:00')
        self.assertEqual(status['scored'],0);self.assertEqual(status['excluded_future_forecasts'],1)
        with self.assertRaisesRegex(ValueError,'Duplicate forecast'):ledger_status([first,first],[],'2026-10-24T09:00:00+00:00')
if __name__=='__main__':unittest.main()
