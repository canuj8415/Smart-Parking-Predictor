"""Hidden native-widget check of real dated progress display and export methods."""
import csv,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.app import ParkingApp
from smart_parking.progress_reports import load_progress
from smart_parking.provenance import digest


def main():
    evidence=ROOT/'experiments/evidence/HEARTBEAT-20261025T151531Z'
    app=ParkingApp();app.withdraw()
    try:
        app.update_idletasks()
        original=app.source_text.get('1.0','end')
        report=load_progress()
        def unexpected_error(*args):raise AssertionError(str(args))
        with patch('smart_parking.app.messagebox.showerror',side_effect=unexpected_error):
            app.show_progress()
            shown=app.source_text.get('1.0','end')
            assert report['as_of'] in shown and 'Final acceptance remains incomplete' in shown
            assert '32' in shown and '162' in shown and 'zero labelled crossings' in shown
            with patch('smart_parking.app.filedialog.askdirectory',return_value=str(evidence)):
                app.save_progress()
        exported=sorted(evidence.glob('project_progress_*'))[-1]
        saved=json.loads((exported/'progress.json').read_text(encoding='utf-8'));assert saved==report
        final=next(r for r in saved['metrics'] if r['check']=='Final labelled crossing recovery')
        assert final['numerator']==0 and final['denominator']==0 and final['value'] is None
        metadata=json.loads((exported/'export_metadata.json').read_text(encoding='utf-8'))
        assert all(digest(exported/p)==h for p,h in metadata['files'].items())
        with (exported/'sources.csv').open(encoding='utf-8-sig',newline='') as stream:
            assert len(list(csv.DictReader(stream)))==45
        app.load_sources();assert app.source_text.get('1.0','end')==original
        buttons={b.cget('text'):b for b in app.action_buttons}
        app.set_controls_busy(True)
        assert all('disabled' in buttons[name].state() for name in ['View saved progress','Save progress tables'])
        app.set_controls_busy(False)
        assert all('disabled' not in buttons[name].state() for name in ['View saved progress','Save progress tables'])
        result=dict(actual_widget_methods_passed=True,snapshot_as_of=report['as_of'],csv_tables=4,source_rows=45,
            empty_final_score_preserved=True,checksums_verified=True,source_view_round_trip=True,busy_controls_passed=True,
            exported_to=exported.relative_to(ROOT).as_posix(),
            scope='Hidden native Tk widget methods with a mocked folder dialog. No model inference/live refresh/raw holdout read.',
            limitations='No visible screenshot, physical file-dialog acceptance, native Excel session or disconnected rehearsal.')
        (evidence/'native_progress_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,indent=2))
    finally:app.destroy()


if __name__=='__main__':main()
