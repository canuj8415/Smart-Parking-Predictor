import sys,unittest,tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.segmentation_experiment import reserve_frames,mask_metrics
from smart_parking.layout import read_pklot_xml
class SegmentationStudyTests(unittest.TestCase):
    def test_date_reservation_excludes_prior_data_and_separates_splits(self):
        pairs=[]
        for folder,month in [('parking1a',1),('parking1b',2),('parking2',3)]:
            for day in range(1,11):
                date=f'2020-{month:02}-{day:02}'
                for n in [0,1]:pairs.append(dict(date=date,image=f'data/raw/pklot_subset/PKLot/{folder}/sunny/{date}/{n}.jpg',annotation='fixture.xml'))
        excluded={'2020-01-01','2020-02-01','2020-03-01'}
        rows=reserve_frames(pairs,excluded)
        self.assertEqual(len(rows),48);self.assertFalse({r['date'] for r in rows}&excluded)
        for camera in {r['camera_id'] for r in rows}:
            dates={s:{r['date'] for r in rows if r['camera_id']==camera and r['split']==s} for s in ['train','validation','test']}
            self.assertLess(max(dates['train']),min(dates['validation']));self.assertLess(max(dates['validation']),min(dates['test']))
    def test_pixel_iou_uses_intersection_and_union_not_background_accuracy(self):
        self.assertEqual(mask_metrics([True,False],[True,True])['pixel_iou'],.5)
        self.assertEqual(mask_metrics([False,False],[False,False])['pixel_iou'],1)
    def test_insufficient_fresh_dates_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'Insufficient fresh'):reserve_frames([],set())
    def test_single_frame_dates_cannot_supply_artificial_duplicate_pairs(self):
        pairs=[dict(date=f'2020-01-{day:02}',image=f'data/raw/pklot_subset/PKLot/parking1a/sunny/2020-01-{day:02}/0.jpg',annotation='fixture.xml') for day in range(1,10)]
        with self.assertRaisesRegex(ValueError,'Insufficient fresh'):reserve_frames(pairs,set())
    def test_original_xml_point_capitalization_preserves_same_polygon(self):
        root=Path(__file__).resolve().parents[1]/'.cache/test_tmp';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            outputs=[]
            for tag in ['point','Point']:
                p=Path(temporary)/(tag+'.xml');p.write_text('<parking id="fixture"><space id="1" occupied="1"><contour>'+''.join(f'<{tag} x="{x}" y="{y}"/>' for x,y in [(1,1),(8,1),(8,8),(1,8)])+'</contour></space></parking>')
                outputs.append(read_pklot_xml(p,(10,10)))
            self.assertEqual(outputs[0]['slots'],outputs[1]['slots']);self.assertEqual(outputs[0]['slots'][0]['polygon'],[[1,1],[8,1],[8,8],[1,8]])
if __name__=='__main__':unittest.main()
