"""Synthetic fixtures test data integrity, not model accuracy."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.data import clean_rows, assign_splits

def sample(day=1,occupancy='4',park='A'):
    return dict(SystemCodeNumber=park,Capacity='10',Occupancy=occupancy,
                LastUpdated=f'2016-10-{day:02d} 10:00:00')

class DataTests(unittest.TestCase):
    def test_invalid_bounds_not_clipped(self):
        accepted,rejected,_=clean_rows([sample(occupancy='11'),sample(2)],'fixture')
        self.assertEqual(len(accepted),1)
        self.assertEqual(rejected[0]['Occupancy'],'11')
        self.assertEqual(accepted[0]['source_row'],3)

    def test_identical_duplicate(self):
        accepted,rejected,quality=clean_rows([sample(),sample()],'fixture')
        self.assertEqual((len(accepted),len(rejected)),(1,1))
        self.assertEqual(quality['identical_duplicate_rows_removed'],1)
        self.assertEqual(rejected[0]['source_row'],3)

    def test_conflicting_duplicate(self):
        accepted,rejected,quality=clean_rows([sample(),sample(occupancy='5')],'fixture')
        self.assertEqual(accepted,[])
        self.assertEqual(len(rejected),2)
        self.assertEqual(quality['conflicting_duplicate_groups'],1)

    def test_bad_timestamp_and_missing_count(self):
        bad=sample()
        bad['LastUpdated']='invalid'
        accepted,rejected,_=clean_rows([bad,sample(occupancy='')],'fixture')
        self.assertEqual(accepted,[])
        self.assertEqual(len(rejected),2)

    def test_global_days_and_chronology(self):
        rows,_,_=clean_rows([sample(day,park=park) for day in range(1,21) for park in ('A','B')],'fixture')
        rows=assign_splits(rows)
        self.assertEqual([sum(r['split']==s for r in rows) for s in ('train','validation','test')],[28,6,6])
        self.assertTrue(all(len({r['split'] for r in rows if r['capture_date']==d})==1 for d in {r['capture_date'] for r in rows}))
        self.assertLess(max(r['timestamp'] for r in rows if r['split']=='train'),min(r['timestamp'] for r in rows if r['split']=='validation'))

    def test_too_few_days_and_invalid_fractions(self):
        rows,_,_=clean_rows([sample()],'fixture')
        with self.assertRaises(ValueError): assign_splits(rows)
        with self.assertRaises(ValueError): assign_splits(rows,.9,.2)

if __name__=='__main__': unittest.main()
