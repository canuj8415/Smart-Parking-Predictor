"""Bounded local-demo integration using installed runtime and Python network blocks.

This script is copied into the demo before execution. It never reads raw final
data or measures accuracy. It does not change the computer's network settings.
"""
import copy,csv,gc,hashlib,json,math,os,socket,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
scope=json.loads((ROOT/'BUNDLE_SCOPE.json').read_text(encoding='utf-8'))
ORIGINAL=Path(scope['original_project_root']).resolve()
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/matplotlib')
sys.path.insert(0,str(ROOT/'src'))
blocked=[]


def audit(event,args):
    if event in {'socket.connect','socket.getaddrinfo'}:
        blocked.append(event);raise PermissionError('Python networking blocked by the demo validation process')
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])).resolve()
        if p.is_relative_to(ORIGINAL) and not p.is_relative_to(ROOT):
            raise PermissionError('Original-workspace fallback blocked: '+str(p))


def file_hash(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    sys.addaudithook(audit)
    manifest=json.loads((ROOT/'BUNDLE_MANIFEST.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        if file_hash(ROOT/row['path'])!=row['sha256']:raise ValueError('Bundle asset mismatch: '+row['path'])
    import torch
    torch.set_num_threads(4)
    from smart_parking import app as app_module
    from smart_parking.app import ParkingApp
    from smart_parking.demo_assets import load_demo_assets
    from smart_parking.forecasting import load_forecast
    from smart_parking.forecast_reports import ORIGINAL as ORIGINAL_VIEW,LATER,ORIGINAL_METHOD,LATER_METHOD
    from smart_parking.progress_reports import load_progress
    from smart_parking.convolution import convolution_demo
    from smart_parking.decomposition import image_factors,rank_report
    from smart_parking.live import parse_feed
    from smart_parking.video import process_video
    from smart_parking.provenance import ROOT as imported_root
    assert imported_root.resolve()==ROOT.resolve()
    for name,module in list(sys.modules.items()):
        if name.startswith('smart_parking') and getattr(module,'__file__',None):
            assert Path(module.__file__).resolve().is_relative_to(ROOT)
    app=ParkingApp();app.withdraw();errors=[];outputs=ROOT/'outputs/validation';outputs.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();detectors=[];forecast_exports=[]
    def capture_error(title,message):errors.append(str(title)+': '+str(message))
    def wait_task():
        limit=time.monotonic()+120
        while app.busy and time.monotonic()<limit:
            app.update();time.sleep(.02)
        if app.busy:raise TimeoutError('Bounded demo operation exceeded120seconds')
        if errors:raise RuntimeError('; '.join(errors))
    try:
        with patch('smart_parking.app.messagebox.showerror',side_effect=capture_error):
            app.update_idletasks();app.load_demo()
            if errors:raise RuntimeError('; '.join(errors))
            demo,image,layout=load_demo_assets()
            assert demo['split']=='train' and image.is_relative_to(ROOT) and layout.is_relative_to(ROOT)
            assert 'training example' in app.status.get()
            for kind in ['fasterrcnn','maskrcnn']:
                app.engine=None;gc.collect();app.kind.set(kind);app.analyze();wait_task()
                result=app.result;counts=result['counts']
                assert counts['total']==len(app.layout['slots'])
                assert sum(counts[k] for k in ['occupied','vacant','uncertain'])==counts['total']
                parent=outputs/kind;parent.mkdir()
                with patch('smart_parking.app.filedialog.askdirectory',return_value=str(parent)):app.save_results()
                exported=next(parent.glob('parking_*'))
                metadata=json.loads((exported/'export_metadata.json').read_text(encoding='utf-8'))
                assert file_hash(exported/'analysis.json')==metadata['analysis_record_sha256']
                assert file_hash(exported/'overlay.png')==metadata['analysis_overlay_sha256']
                detectors.append(dict(kind=kind,counts=counts,weight_sha256=result['weight_sha256'],source_image_sha256=demo['image_sha256'],
                    scope='Training-example software check; no ground-truth accuracy or independent evaluation'))
            original_record=app.result;original_overlay=app.analysis_image.copy()
            app.semantic_mask();wait_task();assert app.display_kind=='experimental_semantic_mask' and app.result is original_record
            assert app.analysis_image.tobytes()==original_overlay.tobytes()
            semantic_parent=outputs/'semantic_export';semantic_parent.mkdir()
            with patch('smart_parking.app.filedialog.askdirectory',return_value=str(semantic_parent)):app.save_results()
            semantic=next(semantic_parent.glob('parking_*'))
            assert (semantic/'display_preview.png').exists()
            for view,method in [(ORIGINAL_VIEW,ORIGINAL_METHOD),(LATER,LATER_METHOD)]:
                app.forecast_view.set(view);app.load_parks();app.show_forecast()
                assert view in app.forecast_info.get() and method in app.forecast_info.get()
                displayed=app.forecast_result;assert displayed['report']['method_label']==method
                labels=app.forecast_chart.figure.axes[0].get_legend_handles_labels()[1]
                assert labels==['Actual available',method+' forecast','Last observation']
                parent=outputs/('forecast_original' if view==ORIGINAL_VIEW else 'forecast_later');parent.mkdir()
                with patch('smart_parking.app.filedialog.askdirectory',return_value=str(parent)):app.save_forecast()
                exported=next(parent.glob('forecast_*'))
                metadata=json.loads((exported/'export_metadata.json').read_text(encoding='utf-8'))
                report=json.loads((exported/'forecast_report.json').read_text(encoding='utf-8'))
                with (exported/'forecasts.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
                assert len(rows)==len(displayed['rows']) and metadata['method_id']==displayed['report']['method_id']
                assert report['report']['mae']==displayed['report']['mae'] and 'not newly scored' in report['metrics_scope']
                assert all(file_hash(exported/name)==h for name,h in metadata['files'].items())
                for row,source,value in zip(rows,displayed['rows'],displayed['predicted_available']):
                    assert row['method_label']==method and row['run_id']==displayed['report']['run_id']
                    assert row['car_park_id']==displayed['car_park_id'] and math.isclose(float(row['predicted_available']),value,rel_tol=1e-12)
                    assert row['target_source_time']==str(source.get('target_source_time') or '')
                    assert row['actual_target_lead_minutes']==str(source.get('actual_target_lead_minutes') if source.get('actual_target_lead_minutes') is not None else '')
                forecast_exports.append(dict(view=view,method_label=method,method_id=metadata['method_id'],
                    run_id=metadata['run_id'],selected_windows=len(rows),export=exported.relative_to(ROOT).as_posix(),
                    original_prediction_sha256=metadata['archived_predictions_sha256'],files=metadata['files']))
                app.park.set(list(app.park_picker['values'])[-1]);app.park_picker.event_generate('<<ComboboxSelected>>');app.update()
                assert app.forecast_result is None and app.forecast_chart is None
                with patch('smart_parking.app.filedialog.askdirectory') as no_dialog,patch('smart_parking.app.messagebox.showinfo') as info:
                    app.save_forecast();no_dialog.assert_not_called();info.assert_called_once()
            load_forecast()
            app.refresh_live(False);wait_task()
            assert 'snapshot' in app.live_info.get().lower() and app.live_rows
            demo_math=convolution_demo(app.image)
            assert demo_math['max_2d_error']<1e-5 and demo_math['max_3d_error']<1e-5
            app.show_lab()
            app.svd_rank.set('16');app.show_svd()
            assert app.svd_report['rank']==16 and 'not JPEG size or detection accuracy' in app.status.get()
            app.svd_rank.set('48');app.show_svd();assert app.svd_report['rank']==48
            app.show_lab()
            # Pure numerical lesson in the actual packaged notebook executes in
            # this process: no Jupyter kernel sockets, network or original files.
            notebook=json.loads((ROOT/'notebooks/08_image_patterns_and_svd.ipynb').read_text(encoding='utf-8'))
            namespace={'__name__':'__packaged_lesson__'};notebook_cells=0
            import matplotlib.pyplot as plt
            with patch.object(plt,'show',return_value=None):
                for cell in notebook['cells']:
                    if cell['cell_type']!='code':continue
                    text=''.join(cell['source'])
                    text='\n'.join(line for line in text.splitlines() if not line.startswith('%'))
                    exec(compile(text,'packaged-notebook-cell','exec'),namespace);notebook_cells+=1
            assert notebook_cells==4 and namespace['full']['max_absolute_error']<1e-10
            # Explicit software fixtures, never appended as real observations.
            for malformed in [[],None]:
                try:parse_feed(malformed)
                except ValueError:pass
                else:raise AssertionError('Malformed top-level live input accepted')
            payload=json.loads(next((ROOT/'data/raw/singapore_live').glob('*.json')).read_text(encoding='utf-8'))
            park=copy.deepcopy(payload['items'][0]['carpark_data'][0])
            park['carpark_info']=[dict(total_lots='10',lots_available='3',lot_type='FIXTURE')]
            fixture=dict(items=[dict(timestamp=payload['items'][0]['timestamp'],carpark_data=[park,copy.deepcopy(park)])])
            assert len(parse_feed(fixture))==1
            fixture['items'][0]['carpark_data'][1]['carpark_info'][0]['lots_available']='4'
            try:parse_feed(fixture)
            except ValueError:pass
            else:raise AssertionError('Conflicting duplicate accepted')
            app.show_progress();assert load_progress()['as_of'] in app.source_text.get('1.0','end')
            progress_parent=outputs/'progress';progress_parent.mkdir()
            with patch('smart_parking.app.filedialog.askdirectory',return_value=str(progress_parent)):app.save_progress()
            video=ROOT/scope['video']['local_path']
            video_report=process_video(video,app.get_engine('fasterrcnn'),None,outputs/'video',every_seconds=.5,max_frames=2,
                confidence=.5,flow_config=scope['video_gate'])
            assert video_report['processed_frames']==2
            if errors:raise RuntimeError('; '.join(errors))
        normal_network_attempts=len(blocked);assert normal_network_attempts==0
        try:socket.getaddrinfo('example.invalid',80)
        except PermissionError:pass
        else:raise AssertionError('Network-block probe did not fail')
        for row in manifest['files']:assert file_hash(ROOT/row['path'])==row['sha256']
        report=dict(status='passed',duration_seconds=time.perf_counter()-started,bundle_root=str(ROOT),runtime_executable=sys.executable,
            source_module_root=str(imported_root),manifest_files=len(manifest['files']),training_demo=demo,detectors=detectors,
            archived_forecast_views=2,forecast_method_exports=forecast_exports,
            forecast_plot_export_invalidated_on_selection_change=True,
            cached_live_rows=len(app.live_rows),cached_live_label=app.live_info.get(),
            semantic_preview_separate_from_analysis=True,convolution_arithmetic_passed=True,progress_export_passed=True,
            svd_app_rank_switching_passed=True,packaged_notebook_python_cells=notebook_cells,
            notebook_check_scope='Executed Python cells in copied process with inline magic/show suppressed; full Jupyter kernel acceptance was performed in main project only',
            strict_live_fixture_checks_passed=True,
            video_processed_frames=video_report['processed_frames'],normal_python_network_attempts=normal_network_attempts,
            explicit_network_block_probe_passed=True,original_workspace_fallback_blocked=True,all_bundle_hashes_unchanged=True,
            scope='Relocated local bundle using existing installed Python runtime. Hidden native widgets and mocked save dialogs; actual inference/exports on a training example and already-seen licensed video.',
            limitations=['No model accuracy scored','No raw final image/date/sequence read','No visible/manual-dialog acceptance',
                'Python-level networking blocked; OS networking and unrelated apps untouched','Not a fresh offline install or new-machine/hardware-disconnected rehearsal'])
        (ROOT/'VALIDATION_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2),flush=True)
    finally:app.destroy()


if __name__=='__main__':main()
