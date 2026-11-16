"""Synthetic irregular-source fixtures verify timing provenance, not accuracy."""
import csv,sys,tempfile,unittest
from datetime import datetime,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecasting import build_windows

class ForecastTimingTests(unittest.TestCase):
    def fixture(self, observations, length=2, horizon_steps=1):
        parent=Path(__file__).resolve().parents[1]/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root=Path(temporary);folder=root/'data/splits/birmingham-global-days-v1';folder.mkdir(parents=True)
            with (folder/'manifest.csv').open('w',newline='',encoding='utf-8') as stream:
                writer=csv.DictWriter(stream,fieldnames=['car_park_id','capture_date','split','capacity','timestamp','occupancy','source_row']);writer.writeheader()
                for i,at in enumerate(observations):writer.writerow(dict(car_park_id='SYNTHETIC',capture_date='2020-01-01',split='train',capacity=100,timestamp=at,occupancy=10+i,source_row=i+1))
            return build_windows(root,length=length,horizon_steps=horizon_steps,splits=('train',))['train']

    def test_target_grid_and_actual_sensor_lead_are_distinct(self):
        rows=self.fixture(['2020-01-01T08:20:00','2020-01-01T08:50:00','2020-01-01T09:10:00','2020-01-01T09:40:00'])
        self.assertEqual(len(rows),1);r=rows[0]
        self.assertEqual(r['origin'],'2020-01-01T09:00:00');self.assertEqual(r['target_time'],'2020-01-01T09:30:00')
        self.assertEqual(r['input_source_times'],['2020-01-01T08:20:00','2020-01-01T08:50:00'])
        self.assertEqual(r['target_source_time'],'2020-01-01T09:10:00')
        self.assertEqual(r['target_age_minutes'],20);self.assertEqual(r['actual_target_lead_minutes'],10)
        self.assertEqual(r['source_to_source_horizon_minutes'],20)

    def test_exact_grid_readings_have_exact_horizon(self):
        r=self.fixture(['2020-01-01T08:00:00','2020-01-01T08:30:00','2020-01-01T09:00:00'])[0]
        self.assertEqual(r['actual_target_lead_minutes'],30)
        self.assertEqual(r['source_to_source_horizon_minutes'],30)
        self.assertEqual(r['target_age_minutes'],0);self.assertEqual(r['input_ages_minutes'],[0,0])

    def test_expired_source_gap_drops_window_instead_of_filling_future(self):
        self.assertEqual(self.fixture(['2020-01-01T08:00:00','2020-01-01T08:35:00','2020-01-01T09:00:00']),[])

    def test_every_input_is_asof_and_actual_target_is_future(self):
        start=datetime(2020,1,1,8,20)
        rows=self.fixture([(start+timedelta(minutes=30*i)).isoformat() for i in range(7)],horizon_steps=2)
        self.assertTrue(rows)
        for row in rows:
            for at,source,age in zip(row['input_grid_times'],row['input_source_times'],row['input_ages_minutes']):
                self.assertEqual((datetime.fromisoformat(at)-datetime.fromisoformat(source)).total_seconds()/60,age)
                self.assertTrue(0<=age<=20)
            self.assertGreater(row['actual_target_lead_minutes'],0)
            self.assertEqual(row['actual_target_lead_minutes'],60-row['target_age_minutes'])

if __name__=='__main__':unittest.main()
