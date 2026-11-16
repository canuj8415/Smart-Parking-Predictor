"""Synthetic guarded-membership parser and pure window extraction checks."""
import csv,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecast_final_data import reserved_groups
from smart_parking.forecasting import windows_from_groups

class FinalDataTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        for i in range(9):
            stamp=(datetime(2020,1,1,8,4)+timedelta(minutes=30*i)).isoformat()
            rows.append(dict(source_id='SYNTHETIC',source_row=str(i),car_park_id='A',capture_date='2020-01-01',timestamp=stamp,split='test',capacity='100',occupancy=str(10+i),available=str(90-i)))
        metadata=[{k:r[k] for k in ['source_id','source_row','car_park_id','capture_date','timestamp','split']} for r in rows]
        return rows,metadata
    def write(self,root,rows):
        p=root/'synthetic.csv'
        with p.open('w',newline='') as s:
            w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        return p
    def test_exact_rows_build_causal_windows_without_parsing_unreserved_bad_values(self):
        parent=Path(__file__).resolve().parents[1]/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            rows,metadata=self.fixture();extra=dict(rows[0],source_row='UNRESERVED',occupancy='DO NOT PARSE')
            p=self.write(Path(tmp),rows+[extra]);groups=reserved_groups(p,metadata)
            windows=windows_from_groups(groups,splits=('test',),grid_offset_minutes=10)['test']
            self.assertEqual(len(windows),2)
            self.assertTrue(all(r['actual_target_lead_minutes']==24 for r in windows))
            self.assertTrue(all(set(r['input_source_rows']+[r['target_source_row']])<=set(range(9)) for r in windows))
    def test_identity_bounds_missing_or_duplicate_rows_fail(self):
        parent=Path(__file__).resolve().parents[1]/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            root=Path(tmp)
            for kind in ['identity','bounds','missing','duplicate']:
                rows,metadata=self.fixture()
                if kind=='identity':rows[0]['car_park_id']='WRONG'
                if kind=='bounds':rows[0]['occupancy']='101'
                if kind=='missing':rows=rows[1:]
                if kind=='duplicate':rows=rows+[rows[0]]
                with self.subTest(kind=kind):
                    with self.assertRaises(ValueError):reserved_groups(self.write(root,rows),metadata)
