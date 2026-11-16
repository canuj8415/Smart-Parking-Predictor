"""Synthetic setup-only fixtures; no camera accuracy evidence."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from smart_parking.sequence_setup import setup_gate


class SequenceSetupTests(unittest.TestCase):
    def rows(self, xs):
        return [dict(frame_index=i, objects=[dict(object_id=1, box=[x-5, 40, x+5, 60])])
                for i, x in enumerate(xs)]

    def test_setup_direction_and_timebase(self):
        config, setup = setup_gate(self.rows([70, 73, 76, 79, 82]), [200, 100])
        self.assertEqual(config['line'], [[100, 24], [100, 75]])
        self.assertEqual(config['time_unit'], 'frames')
        self.assertNotIn('max_gap_seconds', config)
        self.assertTrue(setup['uses_labelled_setup'])
        other, _ = setup_gate(self.rows([82, 79, 76, 73, 70]), [200, 100])
        self.assertEqual(other['line'][0][0], 52)

    def test_future_missing_or_stationary_setup_is_rejected(self):
        rows = self.rows([70, 73, 76, 79, 82])
        with self.assertRaisesRegex(ValueError, 'later frames forbidden'):
            setup_gate(rows + [dict(frame_index=5, objects=[])], [200, 100])
        rows[1]['objects'] = []
        with self.assertRaisesRegex(ValueError, 'same labelled object'):
            setup_gate(rows, [200, 100])
        with self.assertRaisesRegex(ValueError, 'motion below'):
            setup_gate(self.rows([70]*5), [200, 100])
