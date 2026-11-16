"""Synthetic phase offsets verify as-of timing and unchanged zero offset."""
import csv,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecasting import build_windows

class ForecastPhaseTests(unittest.TestCase):
    def test_shifted_grid_uses_prior_real_readings_and_retains_target_timing(self):
        parent=Path(__file__).resolve().parents[1]/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root=Path(temporary);p=root/'data/splits/birmingham-global-days-v1/manifest.csv';p.parent.mkdir(parents=True)
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['car_park_id','capture_date','split','capacity','timestamp','occupancy','source_row']);w.writeheader()
                for i in range(8):w.writerow(dict(car_park_id='SYNTHETIC',capture_date='2020-01-01',split='train',capacity=100,timestamp=(datetime(2020,1,1,8,4)+timedelta(minutes=30*i)).isoformat(),occupancy=10+i,source_row=i))
            self.assertEqual(build_windows(root,splits=('train',))['train'],[])
            rows=build_windows(root,splits=('train',),grid_offset_minutes=5)['train'];self.assertTrue(rows)
            for r in rows:
                self.assertTrue(all(age==1 for age in r['input_ages_minutes']))
                self.assertEqual(r['actual_target_lead_minutes'],29)
                self.assertEqual(r['target_age_minutes'],1)
                self.assertNotIn(r['target_source_row'],r['input_source_rows'])
    def test_invalid_offsets_fail_before_any_source_read(self):
        for phase in [-1,30,True,2.5,float('nan')]:
            with self.assertRaisesRegex(ValueError,'offset'):build_windows('nonexistent',splits=('train',),grid_offset_minutes=phase)
