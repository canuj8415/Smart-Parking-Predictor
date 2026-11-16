"""Regression for a pending poll callback surviving native-window shutdown."""
import sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.app import ParkingApp


class ShutdownTests(unittest.TestCase):
    def test_close_cancels_the_registered_poll_once_and_requests_video_stop(self):
        app=ParkingApp.__new__(ParkingApp)
        app._closed=False;app._poll_after='synthetic-pending-poll';app.after_cancel=Mock();app.cancel_video=False
        with patch('tkinter.Tk.destroy') as native_destroy:
            app.destroy();app.destroy()
        app.after_cancel.assert_called_once_with('synthetic-pending-poll')
        native_destroy.assert_called_once();self.assertTrue(app.cancel_video);self.assertIsNone(app._poll_after)

    def test_poll_after_close_never_schedules_or_touches_widgets(self):
        app=ParkingApp.__new__(ParkingApp);app._closed=True;app.after=Mock()
        app._poll()
        app.after.assert_not_called()
