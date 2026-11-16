"""Synthetic archived-byte corruption check; never touches real study files."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from smart_parking.vision_lesson import allowed_paths,load


class VisionLessonIntegrityTests(unittest.TestCase):
    def test_changed_archived_bytes_rejected_before_interpretation(self):
        root=Path(__file__).resolve().parents[1]
        scratch=(root/'outputs/test_fixtures/vision_lesson_integrity').resolve()
        assert scratch.is_relative_to(root)
        scratch.mkdir(parents=True,exist_ok=True)
        with TemporaryDirectory(dir=scratch) as folder:
            assert Path(folder).resolve().is_relative_to(scratch)
            inputs={p:hashlib.sha256(b'{}').hexdigest() for p in sorted(allowed_paths())}
            for relative in inputs:
                path=Path(folder)/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'{}')
            (Path(folder)/next(iter(inputs))).write_bytes(b'changed fixture')
            with self.assertRaisesRegex(ValueError,'Archived lesson input changed'):
                load(folder,dict(data_kind='archived_development_only',inputs=inputs))
