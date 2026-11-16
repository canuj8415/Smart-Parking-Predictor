"""Synthetic source-access fixtures; no publisher videos or final labels read."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.uvg import require_development


class UVGAccessTests(unittest.TestCase):
    def setUp(self):
        self.parent = (ROOT/'outputs/test_fixtures').resolve(); self.parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.parent); self.root = Path(self.temp.name).resolve()
        self.path = self.root/'roles.json'; self.path.write_text(json.dumps(dict(canonical_collection='https://ultravideo.fi/UVG-VCM/',
            sequences=[dict(name='HighwayView', role='development', assets=['HighwayView.mp4']),
                       dict(name='HighwayDrive', role='reserved_final', assets=['HighwayDrive.mp4'])])))
        self.sha = digest(self.path)

    def tearDown(self):
        assert self.root != self.parent and self.root.is_relative_to(self.parent); self.temp.cleanup()

    def test_declared_publisher_development_asset_is_admitted(self):
        result = require_development(self.path, self.sha, 'https://ultravideo.fi/UVG-VCM/HighwayView/HighwayView.mp4')
        self.assertEqual(result['role'], 'development')

    def test_final_sequence_aliases_and_all_representations_are_blocked(self):
        for name in ['HighwayDrive/HighwayDrive.mp4', 'highwaydrive/raw.yuv', '%48ighwayDrive/annotations.json']:
            with self.assertRaises(ValueError): require_development(self.path, self.sha, 'https://ultravideo.fi/UVG-VCM/'+name)

    def test_mirrors_credentials_queries_and_traversal_are_blocked(self):
        for url in ['http://ultravideo.fi/UVG-VCM/HighwayView/HighwayView.mp4',
                    'https://mirror.invalid/UVG-VCM/HighwayView/HighwayView.mp4',
                    'https://user@ultravideo.fi/UVG-VCM/HighwayView/HighwayView.mp4',
                    'https://ultravideo.fi/UVG-VCM/HighwayView/../HighwayDrive/raw.yuv',
                    'https://ultravideo.fi/UVG-VCM/HighwayView/HighwayView.mp4?other=1']:
            with self.assertRaises(ValueError): require_development(self.path, self.sha, url)

    def test_unknown_and_visualization_assets_are_not_model_inputs(self):
        for asset in ['HighwayView_vis.mp4', 'unknown.mp4']:
            with self.assertRaises(ValueError): require_development(self.path, self.sha, 'https://ultravideo.fi/UVG-VCM/HighwayView/'+asset)

    def test_changed_reservation_never_reopens_a_sequence(self):
        value=json.loads(self.path.read_text());value['sequences'][1]['role']='development';self.path.write_text(json.dumps(value))
        with self.assertRaises(ValueError): require_development(self.path, self.sha, 'https://ultravideo.fi/UVG-VCM/HighwayDrive/HighwayDrive.mp4')
