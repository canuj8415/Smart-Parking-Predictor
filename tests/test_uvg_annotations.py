import copy
import unittest
from smart_parking.uvg import validate_annotations


def fixture():
    obj = dict(class_name='car', class_id=3, track_id=1, mask_color=[155,255,255],
               x_min=.1, y_min=.2, x_max=.4, y_max=.5, polygon=[.1,.2,.4,.2,.4,.5,.1,.5])
    return {'version':'1.0', '1':[obj], '2':[copy.deepcopy(obj)]}


class AnnotationTests(unittest.TestCase):
    def test_valid_normalized_persistent_objects(self):
        result = validate_annotations(fixture(), 2)
        self.assertEqual((result['frames'], result['object_observations'],result['unique_tracks']), (2,2,1))
        self.assertFalse(result['exhaustive_ground_truth_established'])

    def test_frame_gaps_and_unknown_schema(self):
        for change in ('gap', 'version', 'extra'):
            data = fixture()
            if change=='gap': del data['2']
            elif change=='version': data['version']='0.9'
            else: data['1'][0]['confidence']=1
            with self.assertRaises(ValueError): validate_annotations(data,2)

    def test_nonfinite_bounds_and_polygon_mismatch(self):
        for value in (float('nan'),float('inf'),-.1,1.1,True):
            data=fixture(); data['1'][0]['polygon'][0]=value
            with self.assertRaises(ValueError): validate_annotations(data,2)
        data=fixture(); data['1'][0]['x_max']=.3
        with self.assertRaises(ValueError): validate_annotations(data,2)

    def test_duplicate_or_changed_identity(self):
        for change in ('duplicate','color','class','id'):
            data=fixture()
            if change=='duplicate': data['1'].append(copy.deepcopy(data['1'][0]))
            elif change=='color': data['2'][0]['mask_color']=[1,2,3]
            elif change=='class': data['2'][0]['class_name']='truck'
            else: data['1'][0]['track_id']=True
            with self.assertRaises(ValueError): validate_annotations(data,2)

    def test_empty_frame_is_not_negative_certification(self):
        data=fixture(); data['2']=[]
        self.assertEqual(validate_annotations(data,2)['object_observations'],1)
