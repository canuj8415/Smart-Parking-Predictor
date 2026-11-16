"""Synthetic coverage/similarity fixtures,not real data or accuracy evidence."""
import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from smart_parking.annotation_quality import UNKNOWN, occupancy_support, difference_hash, similar_pairs


def polygon(label, x0, x1):
    return dict(class_id=label, normalized_polygon=[[x0,.2],[x1,.2],[x1,.8],[x0,.8]])


class AnnotationQualityTests(unittest.TestCase):
    def test_unlabelled_and_empty_annotations_stay_unknown(self):
        target, report = occupancy_support([polygon(0,.1,.4)], (31,21))
        self.assertEqual(target[0,0], UNKNOWN)
        self.assertEqual(target[10,6], 1)
        self.assertEqual(report['known_vacant_pixels'], 0)
        blank, summary = occupancy_support([], (31,21))
        self.assertTrue(np.all(blank == UNKNOWN))
        self.assertEqual(summary['supplied_union_pixels'], 0)

    def test_source_class_mapping_and_conflicts_are_order_independent(self):
        rows = [polygon(0,.1,.6), polygon(1,.4,.9)]
        first, summary = occupancy_support(rows, (31,21))
        reverse, other = occupancy_support(list(reversed(rows)), (31,21))
        np.testing.assert_array_equal(first, reverse)
        self.assertEqual(summary, other)
        self.assertEqual(first[10,6], 1)
        self.assertEqual(first[10,24], 0)
        self.assertEqual(first[10,15], UNKNOWN)
        self.assertGreater(summary['conflict_pixels'], 0)
        self.assertEqual(sum(summary[k] for k in ['known_occupied_pixels','known_vacant_pixels','unknown_pixels']), summary['pixels'])

    def test_bad_dimensions_classes_and_vertices_rejected(self):
        for size in [(1,20),(20,False),(10000,10000)]:
            with self.assertRaises(ValueError):occupancy_support([],size)
        for row in [dict(class_id=2,normalized_polygon=[[.1,.1],[.2,.1],[.2,.2]]),
                    dict(class_id=0,normalized_polygon=[[.1,.1],[float('nan'),.1],[.2,.2]])]:
            with self.assertRaises(ValueError):occupancy_support([row],(20,20))

    def test_difference_hash_is_fixed_width_and_deterministic(self):
        pixels=np.tile(np.arange(17,dtype=np.uint8),(16,1))
        image=Image.fromarray(pixels)
        actual=difference_hash(image)
        self.assertEqual(len(actual),64)
        self.assertEqual(actual,difference_hash(image.copy()))
        self.assertEqual(actual,'f'*64)

    def test_similarity_pairs_are_unordered_reproducible_candidates(self):
        rows=[dict(image='c',difference_hash256='f'*64),dict(image='a',difference_hash256='0'*64),dict(image='b',difference_hash256='0'*63+'1')]
        expected=[dict(left='a',right='b',hamming_distance=1)]
        self.assertEqual(similar_pairs(rows,1),expected)
        self.assertEqual(similar_pairs(list(reversed(rows)),1),expected)
        self.assertEqual(similar_pairs(rows,0),[])

    def test_duplicate_identity_malformed_hash_and_invalid_limit_rejected(self):
        row=dict(image='a',difference_hash256='0'*64)
        with self.assertRaises(ValueError):similar_pairs([row,row])
        with self.assertRaises(ValueError):similar_pairs([dict(row,difference_hash256='bad')])
        for limit in [-1,257,True]:
            with self.assertRaises(ValueError):similar_pairs([row],limit)


if __name__ == '__main__':unittest.main()
