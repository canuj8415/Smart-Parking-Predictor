import unittest
import sys
from pathlib import Path
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.occupancy_expansion import member_name,select_frames


def frame(day,clock='08_00_00',camera='pucpr',split='train'):
    folder='parking2' if camera=='pucpr' else 'parking1b'
    base=f'PKLot/{folder}/sunny/{day}/{day}_{clock}'
    return dict(camera_id=camera,date=day,image=base+'.jpg',annotation=base+'.xml',split=split)


class ExpansionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.old=[frame('2012-10-01'),frame('2012-10-02',split='validation'),frame('2012-10-03',split='test')]
        examples=self.old+[frame('2012-10-01',clock=f'{h:02d}_00_00') for h in range(9,15)]
        self.inventory=[dict(image_member=f['image'],annotation_member=f['annotation'],
            camera_id=f['camera_id'],capture_date=f['date'],image_bytes=100,annotation_bytes=50) for f in examples]
        self.broader=dict(frames=[],dates={})
        self.fresh=dict(frames=[])
        self.plan=dict(reserved_groups=[])

    def call(self,claims=()):
        return select_frames(self.inventory,self.old,self.broader,self.fresh,self.plan,claims)

    def test_fixed_metadata_positions_keep_old_training_and_no_test(self):
        a=self.call();b=self.call()
        self.assertEqual(a,b)
        self.assertEqual(sum(r['role']=='train' for r in a['frames']),5)
        self.assertEqual(sum(r['additional_training_frame'] for r in a['frames']),4)
        self.assertFalse(a['pixels_or_labels_read'])
        self.assertNotIn('2012-10-03',{r['date'] for r in a['frames']})

    def test_reserved_date_blocks_training_even_under_another_camera(self):
        self.plan['reserved_groups']=[dict(camera_id='ufpr05',date='2012-10-01')]
        with self.assertRaises(ValueError):self.call()

    def test_consumed_whole_date_blocks_training(self):
        with self.assertRaises(ValueError):
            self.call([dict(source_groups=[['ufpr05','2012-10-01']])])

    def test_training_cannot_take_development_date(self):
        self.broader['dates']={'pucpr':dict(train=['2012-10-02'])}
        with self.assertRaises(ValueError):self.call()

    def test_path_and_calendar_rejections(self):
        for path in ['PKLot/../sunny/2012-10-01/2012-10-01_08_00_00.jpg',
            '/PKLot/parking2/sunny/2012-10-01/2012-10-01_08_00_00.jpg',
            'PKLot/parking2/sunny/2012-14-01/2012-14-01_08_00_00.jpg',
            'PKLot/parking2/sunny/2012-10-01/2012-10-02_08_00_00.jpg']:
            with self.subTest(path=path),self.assertRaises(ValueError):member_name(path)

    def test_canonical_camera_and_duplicate_inventory_rejected(self):
        original=deepcopy(self.old)
        self.old[0]['camera_id']='ufpr05'
        with self.assertRaises(ValueError):self.call()
        self.old=original;self.inventory.append(deepcopy(self.inventory[0]))
        with self.assertRaises(ValueError):self.call()
