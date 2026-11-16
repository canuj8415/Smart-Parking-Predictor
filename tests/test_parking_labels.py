"""Synthetic label and partition fixtures;no real images or accuracy scores."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from smart_parking.parking_labels import parse_space_labels, parse_space_polygons, training_inspection_selection


class SpacePolygonTests(unittest.TestCase):
    def test_closed_ring_and_original_coordinates_preserved(self):
        row = parse_space_polygons('1 .1 .1 .8 .1 .8 .8 .1 .8 .1 .1')[0]
        self.assertTrue(row['closing_vertex_removed'])
        self.assertEqual(len(row['normalized_polygon']), 4)
        self.assertEqual(len(row['source_normalized_xy']), 10)
        self.assertAlmostEqual(row['normalized_area'], .49)

    def test_open_triangle_allowed_and_box_format_distinct(self):
        self.assertEqual(len(parse_space_polygons('0 .1 .1 .8 .1 .5 .8')[0]['normalized_polygon']), 3)
        self.assertEqual(parse_space_polygons(''), [])
        with self.assertRaises(ValueError):
            parse_space_polygons('0 .5 .5 .2 .2')

    def test_crossing_touching_and_degenerate_rings_rejected(self):
        for body in ['.1 .1 .8 .8 .8 .1 .1 .8', '.1 .1 .8 .1 .5 .1 .5 .8',
                     '.1 .1 .2 .2 .3 .3', '.1 .1 .8 .1 .8 .8 .8 .1 .1 .8']:
            with self.subTest(body=body), self.assertRaises(ValueError):
                parse_space_polygons('0 '+body)

    def test_nonfinite_malformed_or_outside_vertices_rejected(self):
        for row in ['2 .1 .1 .8 .1 .8 .8', '0 .1 .1 .8 .1 .8',
                    '0 nan .1 .8 .1 .8 .8', '0 -.1 .1 .8 .1 .8 .8']:
            with self.subTest(row=row), self.assertRaises(ValueError):
                parse_space_polygons(row)

    def test_rotated_or_reversed_duplicate_ring_rejected(self):
        for other in ['1 .8 .1 .8 .8 .1 .1', '0 .8 .8 .8 .1 .1 .1']:
            with self.assertRaises(ValueError):
                parse_space_polygons('0 .1 .1 .8 .1 .8 .8\n'+other)

    def test_rounding_tolerance_reported_without_silent_large_clipping(self):
        row = parse_space_polygons('0 -.0000001 .1 .8 .1 .8 .8')[0]
        self.assertTrue(row['rounding_clipped'])
        self.assertEqual(row['normalized_polygon'][0][0], 0)
        with self.assertRaises(ValueError):
            parse_space_polygons('0 -.00001 .1 .8 .1 .8 .8')


class SpaceLabelTests(unittest.TestCase):
    def test_source_values_classes_and_blank_file_are_preserved(self):
        rows = parse_space_labels('\n0 .5 .5 .2 .4\n1 .2 .2 .1 .1\n')
        self.assertEqual(rows[0]['source_line'], 2)
        self.assertEqual(rows[0]['normalized_xyxy'], [.4, .3, .6, .7])
        self.assertEqual(rows[1]['class_name'], 'space-vacant')
        self.assertEqual(rows[0]['source_text'], '0 .5 .5 .2 .4')
        self.assertEqual(parse_space_labels('\n'), [])

    def test_classes_and_row_width_are_strict(self):
        for row in ['2 .5 .5 .2 .2', '0.0 .5 .5 .2 .2', '1 .5 .5 .2',
                    '1 .5 .5 .2 .2 .99', 'occupied .5 .5 .2 .2']:
            with self.subTest(row=row), self.assertRaises(ValueError):
                parse_space_labels(row)

    def test_nonfinite_negative_and_outside_coordinates_rejected(self):
        for values in ['nan .5 .2 .2', '.5 inf .2 .2', '.5 .5 0 .2',
                       '.5 .5 -.2 .2', '1.1 .5 .2 .2', '.05 .5 .2 .2']:
            with self.subTest(values=values), self.assertRaises(ValueError):
                parse_space_labels('0 '+values)

    def test_only_tiny_rounding_overflow_is_explicitly_clipped(self):
        row = parse_space_labels('0 .1 .5 .2000001 .2')[0]
        self.assertTrue(row['rounding_clipped'])
        self.assertEqual(row['normalized_xyxy'][0], 0)
        self.assertEqual(row['normalized_center_size'][2], .2000001)
        with self.assertRaises(ValueError):
            parse_space_labels('0 .1 .5 .20001 .2')

    def test_duplicate_and_conflicting_rectangles_rejected(self):
        for second_class in ['0', '1']:
            with self.assertRaises(ValueError):
                parse_space_labels('0 .5 .5 .2 .2\n'+second_class+' .5 .5 .2 .2')


class InspectionSelectionTests(unittest.TestCase):
    def fixture(self):
        return [dict(path=f'{split}/images/image_{i:03}.jpg', type='blob', sha=f'{i:040x}', size=100)
                for split in ['train', 'valid', 'test'] for i in range(10)]

    def test_selection_is_order_invariant_train_only_and_label_blind(self):
        rows = self.fixture()
        actual = training_inspection_selection(rows)
        self.assertEqual([x['selected_index'] for x in actual], [0, 3, 6, 9])
        self.assertEqual(actual, training_inspection_selection(list(reversed(rows))))
        self.assertTrue(all(x['annotation'].startswith('train/labels/') for x in actual))

    def test_aliases_unsafe_paths_duplicates_and_bad_identity_rejected(self):
        for change in [dict(path='train/images/../final.jpg'), dict(path='train\\images\\x.jpg'),
                       dict(sha='not-a-blob'), dict(size=-1), dict(path='train/images/sub/x.jpg')]:
            rows = self.fixture()
            rows[0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                training_inspection_selection(rows)
        with self.assertRaises(ValueError):
            training_inspection_selection(self.fixture()+[self.fixture()[0]])

    def test_small_or_invalid_selection_size_fails(self):
        for count in [0, -1, True, 100]:
            with self.subTest(count=count), self.assertRaises(ValueError):
                training_inspection_selection(self.fixture(), count)


if __name__ == '__main__':
    unittest.main()
