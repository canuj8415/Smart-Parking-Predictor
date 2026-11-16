"""Synthetic selector fixtures check leakage guards, not segmentation accuracy."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.region_data import select_broader_development,evenly_spaced,CAMERAS

def pairs():
    result=[]
    for camera,month in zip(CAMERAS,[1,2,3]):
        for day in range(1,11):
            date=f'2020-{month:02}-{day:02}'
            for frame in range(10):
                stem=f'data/raw/pklot_subset/PKLot/{camera}/sunny/{date}/{date}_08_{frame:02}_00'
                result.append(dict(date=date,image=stem+'.jpg',annotation=stem+'.xml'))
    return result

class RegionDataTests(unittest.TestCase):
    def test_dates_are_disjoint_later_validation_and_before_final(self):
        boundaries={c:'2020-04-01' for c in CAMERAS.values()}
        result=select_broader_development(pairs(),{'2020-01-01'},boundaries)
        self.assertEqual(sum(r['split']=='train' for r in result['frames']),144)
        self.assertEqual(sum(r['split']=='validation' for r in result['frames']),24)
        self.assertNotIn('2020-01-01',{r['date'] for r in result['frames']})
        for camera,split in result['dates'].items():
            self.assertLess(max(split['train']),min(split['validation']))
            self.assertLess(max(split['validation']),boundaries[camera])
    def test_fewer_than_eight_eligible_dates_fails(self):
        with self.assertRaises(ValueError):select_broader_development(pairs(),set(),{c:'2020-01-05' for c in CAMERAS.values()})
    def test_selection_is_deterministic_and_samples_span_timestamps(self):
        boundaries={c:'2021-01-01' for c in CAMERAS.values()}
        a=select_broader_development(pairs(),set(),boundaries);b=select_broader_development(list(reversed(pairs())),set(),boundaries)
        self.assertEqual(a,b);self.assertEqual(evenly_spaced(list(range(10)),4),[0,3,6,9])
    def test_identity_and_path_escapes_rejected(self):
        boundaries={c:'2021-01-01' for c in CAMERAS.values()}
        for field,value in [('image','../outside.jpg'),('annotation','D:/outside.xml'),('annotation','data/other.xml')]:
            rows=pairs();rows[0][field]=value
            with self.assertRaises(ValueError):select_broader_development(rows,set(),boundaries)
    def test_invalid_dates_do_not_get_silently_corrected(self):
        rows=pairs();row=rows[0].copy();row['date']='2020-14-01';rows.append(row)
        result=select_broader_development(rows,set(),{c:'2021-01-01' for c in CAMERAS.values()})
        self.assertEqual(result['rejected_metadata'][0]['reason'],'invalid source date')

if __name__=='__main__':unittest.main()
