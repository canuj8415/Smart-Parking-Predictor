"""Core product failure modes; synthetic fixtures are never reported as model scores."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from PIL import Image
from smart_parking.layout import validate_layout,slot_mask
from smart_parking.vision import assign_occupancy
from smart_parking.events import OccupancyEvents
from smart_parking.live import parse_feed
from smart_parking.convolution import convolution_demo

def layout():return dict(camera_id='fixture',image_size=[100,60],slots=[
    dict(id='A',polygon=[[0,0],[45,0],[45,50],[0,50]]),
    dict(id='B',polygon=[[50,0],[99,0],[99,50],[50,50]])])

class ProductTests(unittest.TestCase):
    def test_bad_polygon_and_duplicate_ids(self):
        value=layout();value['slots'][0]['polygon']=[[0,0],[40,40],[0,40],[40,0]]
        with self.assertRaises(ValueError):validate_layout(value)
        value=layout();value['slots'][1]['id']='A'
        with self.assertRaises(ValueError):validate_layout(value)

    def test_wrong_camera_dimensions_fail(self):
        with self.assertRaises(ValueError):validate_layout(layout(),(200,120))

    def test_missing_detection_does_not_imply_vacancy(self):
        observations=assign_occupancy((100,60),layout(),[],[])
        self.assertTrue(all(o['state']=='uncertain' for o in observations))

    def test_one_detection_not_counted_twice(self):
        detections=[dict(id=0,score=.9,box=[0,0,99,50])]
        observations=assign_occupancy((100,60),layout(),detections,[None])
        self.assertEqual(sum(o['vehicle_id'] is not None for o in observations),1)

    def test_classifier_detector_disagreement_is_uncertain(self):
        detections=[dict(id=0,score=.9,box=[0,0,40,40])]
        observations=assign_occupancy((100,60),layout(),detections,[None],[.1,.1])
        self.assertEqual(observations[0]['state'],'uncertain');self.assertEqual(observations[1]['state'],'vacant')

    def test_event_debounce_and_reset(self):
        events=OccupancyEvents(2)
        row=lambda state:[dict(slot_id='A',state=state)]
        events.update(row('vacant'),0);events.update(row('vacant'),1)
        self.assertEqual(events.update(row('occupied'),2),[])
        self.assertEqual(len(events.update(row('occupied'),3)),1)
        events.reset();self.assertEqual(events.update(row('vacant'),4),[])

    def test_live_feed_validates_counts_and_lot_types(self):
        payload=dict(items=[dict(timestamp='2026-10-24T17:00:00+08:00',carpark_data=[dict(carpark_number='TEST',
            update_datetime='2026-10-24T16:59:00',carpark_info=[dict(total_lots='10',lots_available='3',lot_type='C'),
            dict(total_lots='5',lots_available='7',lot_type='Y')])])])
        rows=parse_feed(payload);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['occupied'],7)
        with self.assertRaises(ValueError):parse_feed({'items':[]})

    def test_manual_2d_3d_arithmetic(self):
        demo=convolution_demo(Image.new('RGB',(50,30),'gray'))
        self.assertLess(demo['max_2d_error'],1e-6);self.assertLess(demo['max_3d_error'],1e-6)

if __name__=='__main__':unittest.main()
