"""Synthetic public-feed chronology and target-window fixtures only."""
import sys,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.singapore_history import canonical_observation,deduplicate_observations,causal_examples
def fixture(minute,capacity=100,available=50):
    at=datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(minutes=minute)
    row=dict(source_id='SRC-LIVE-001',car_park_id='synthetic',lot_type='C',capacity=capacity,available=available,
        observed_at=at.isoformat(),feed_timestamp=(at+timedelta(seconds=36)).isoformat())
    return canonical_observation(row,(at+timedelta(seconds=50)).isoformat(),'synthetic/'+str(minute)+'.json','fixture-sha')
class SingaporeHistoryTests(unittest.TestCase):
    def test_source_naive_time_is_singapore_but_receipt_must_be_aware(self):
        row=dict(source_id='SRC-LIVE-001',car_park_id='synthetic',lot_type='C',capacity=100,available=50,observed_at='2026-01-01T08:00:00',feed_timestamp='2026-01-01T08:00:36+08:00')
        value=canonical_observation(row,'2026-01-01T00:00:50+00:00','fixture','sha');self.assertEqual(value['observed_at'],'2026-01-01T00:00:00+00:00')
        with self.assertRaises(ValueError):canonical_observation(row,'2026-01-01T00:00:50','fixture','sha')
    def test_duplicates_first_available_and_conflicting_revisions_quarantined(self):
        row=fixture(0);later=dict(row,available_at='2026-01-01T00:01:00+00:00')
        rows,bad,dup=deduplicate_observations([later,row]);self.assertEqual(rows[0]['available_at'],row['available_at']);self.assertEqual(dup,1)
        rows,bad,dup=deduplicate_observations([row,dict(later,available=51)]);self.assertEqual(rows,[]);self.assertEqual(len(bad),1)
    def test_global_cutoff_excludes_train_labels_arriving_after_it(self):
        records=[fixture(i) for i in [0,30,60,90,120]]
        examples,reasons=causal_examples(records,'2026-01-01T02:10:00+00:00','2026-01-01T00:50:00+00:00')
        self.assertEqual(reasons['training_label_arrived_after_train_cutoff'],1)
        self.assertTrue(all(r['role']=='development' for r in examples));self.assertEqual(len(examples),2)
        for r in examples:self.assertLess(r['previous_available_at'],r['issued_at']);self.assertNotIn('target_available',{'origin_fraction':r['origin_fraction']})
    def test_capacity_changes_cannot_be_skipped_to_reuse_old_regime(self):
        records=[fixture(0),fixture(30,120),fixture(60),fixture(90),fixture(120)]
        examples,reasons=causal_examples(records,'2026-01-01T02:10:00+00:00','2026-01-01T00:50:00+00:00')
        self.assertEqual(reasons['previous_capacity_changed'],2);self.assertEqual(len(examples),1)
    def test_post_cutoff_inputs_and_stale_or_wrong_source_rejected(self):
        with self.assertRaises(ValueError):causal_examples([fixture(120)],'2026-01-01T01:00:00+00:00','2026-01-01T00:30:00+00:00')
        row=dict(source_id='wrong',car_park_id='synthetic',lot_type='C',capacity=100,available=50,observed_at='2026-01-01T00:00:00+00:00',feed_timestamp='2026-01-01T00:00:36+00:00')
        with self.assertRaises(ValueError):canonical_observation(row,'2026-01-01T00:00:50+00:00','fixture','sha')
        row['source_id']='SRC-LIVE-001'
        with self.assertRaises(ValueError):canonical_observation(row,'2026-01-01T01:00:00+00:00','fixture','sha')
if __name__=='__main__':unittest.main()
