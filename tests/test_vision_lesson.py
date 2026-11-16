import unittest
from smart_parking.vision_lesson import allowed_paths,load


class VisionLessonTests(unittest.TestCase):
    def test_manifest_excludes_raw_growing_and_final_sources(self):
        paths=allowed_paths();self.assertEqual(len(paths),11)
        self.assertTrue(all(p.startswith('experiments/results/UVG-') for p in paths))
        self.assertFalse(any('HighwayDrive' in p or p.startswith('data/') for p in paths))

    def test_non_development_kind_rejected_before_reads(self):
        with self.assertRaises(ValueError):load('.',dict(data_kind='final',inputs={p:'x' for p in allowed_paths()}))

    def test_unlisted_alias_or_path_cannot_be_added(self):
        for extra in ['data/raw/secret.json','../outside.json','reports/singapore_final_latest.json']:
            inputs={p:'x' for p in allowed_paths()};inputs[extra]='x'
            with self.assertRaises(ValueError):load('.',dict(data_kind='archived_development_only',inputs=inputs))

    def test_missing_archive_is_not_silently_skipped(self):
        paths={p:'x' for p in allowed_paths()};paths.pop(next(iter(paths)))
        with self.assertRaises(ValueError):load('.',dict(data_kind='archived_development_only',inputs=paths))
