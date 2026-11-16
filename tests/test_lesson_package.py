"""Synthetic file-integrity fixtures, not a relocated notebook execution."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/'src'))
from smart_parking.lesson_package import safe_path, verify_payload, file_hash


class LessonPackageTests(unittest.TestCase):
    def setUp(self):
        self.parent = (ROOT/'outputs/test_fixtures').resolve(); self.parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.parent); self.root = Path(self.temp.name).resolve()
        self.file = self.root/'archived.csv'; self.file.write_bytes(b'synthetic,input\r\n1,2\r\n')
        self.manifest = dict(entries=[dict(path='archived.csv', bytes=self.file.stat().st_size, sha256=file_hash(self.file))])
        (self.root/'PACKAGE_MANIFEST.json').write_text(json.dumps(self.manifest))

    def tearDown(self):
        assert self.root != self.parent and self.root.is_relative_to(self.parent); self.temp.cleanup()

    def test_traversal_absolute_and_parent_paths_are_rejected(self):
        for value in ['../outside', str(self.root/'absolute'), 'nested/../../outside']:
            with self.assertRaises(ValueError):
                safe_path(self.root, value)

    def test_exact_bytes_survive_and_generated_outputs_are_separate(self):
        outputs = self.root/'outputs/run'; outputs.mkdir(parents=True); (outputs/'cache.json').write_text('{}')
        self.assertEqual(verify_payload(self.root, self.manifest)['files'], 1)
        self.assertEqual(self.file.read_bytes(), b'synthetic,input\r\n1,2\r\n')

    def test_tampered_payload_is_rejected(self):
        self.file.write_bytes(b'synthetic,input\n1,2\n')
        with self.assertRaises(ValueError):
            verify_payload(self.root, self.manifest)

    def test_duplicate_or_unexpected_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            verify_payload(self.root, dict(entries=self.manifest['entries']*2))
        (self.root/'unexpected.json').write_text('{}')
        with self.assertRaises(ValueError):
            verify_payload(self.root, self.manifest)
