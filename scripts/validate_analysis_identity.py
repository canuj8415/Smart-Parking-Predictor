"""One real-input, local-only provenance/export integration trial; not accuracy."""
import csv,json,socket,sys,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.error import URLError
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.vision import VisionEngine
from smart_parking.layout import load_layout
from smart_parking.exports import export_analysis
from smart_parking.analysis_identity import image_identity,layout_identity
from smart_parking.live import get_live
from smart_parking.forecasting import load_forecast
from smart_parking.provenance import digest

if __name__=='__main__':
    started=datetime.now(timezone.utc);run='PROVENANCE-OFFLINE-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    with (ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8',newline='') as stream:frame=next(r for r in csv.DictReader(stream) if r['split']=='train')
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-DS-001',source_frame=frame['image'],source_file_sha256=digest(ROOT/frame['image']),source_split='training image used for software integration, not accuracy scoring',
        hypothesis='Real analysis exports preserve the actual processed-pixel, geometry, detector and classifier identities while cached product paths work with HTTP/socket connection creation blocked.',
        detector='fasterrcnn_resnet50_fpn_v2',resolution=640,threshold=.5,
        code_sha256=digest(Path(__file__)),vision_code_sha256=digest(ROOT/'src/smart_parking/vision.py'),identity_code_sha256=digest(ROOT/'src/smart_parking/analysis_identity.py'),exports_code_sha256=digest(ROOT/'src/smart_parking/exports.py'),
        scope='Local cached integration; no physical disconnect, fresh installation, detector/occupancy accuracy or native dialog claim')
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8');clock=time.perf_counter()
    with patch('urllib.request.urlopen',side_effect=URLError('HTTP disabled by this verification process')) as http,patch('socket.create_connection',side_effect=OSError('Connection creation disabled by this verification process')) as connections:
        image=Image.open(ROOT/frame['image']).convert('RGB');geometry=load_layout(ROOT/frame['layout_path'],image.size);engine=VisionEngine('fasterrcnn')
        result,overlay=engine.analyze(image,geometry,confidence=.5)
        assert result['input_image']==image_identity(image) and result['layout_identity']==layout_identity(geometry)
        assert result['classifier_checkpoint_sha256']==digest(ROOT/'models/checkpoints/occupancy_resnet18.pt')
        exported=export_analysis(folder/'exports',result,overlay)
        saved=json.loads((exported/'analysis.json').read_text());metadata=json.loads((exported/'export_metadata.json').read_text())
        assert saved==result and metadata['analysis_record_sha256']==digest(exported/'analysis.json') and metadata['analysis_overlay_sha256']==digest(exported/'overlay.png')
        assert Image.open(exported/'overlay.png').convert('RGB').tobytes()==overlay.convert('RGB').tobytes()
        model,bundle=load_forecast();rows,cache=get_live(False)
        implicit_calls=http.call_count+connections.call_count
        assert implicit_calls==0,'Cached inference attempted an unexpected download/connection'
        failure_message=None
        try:
            with patch('smart_parking.live.latest_snapshot',side_effect=FileNotFoundError):get_live(True)
        except ConnectionError as error:failure_message=str(error)
        assert failure_message and 'Load saved snapshot' in failure_message
    report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,real_vehicle_predictions=len(result['detections']),counts=result['counts'],
        processed_input_identity=result['input_image'],inference_geometry_identity=result['layout_identity'],detector_weight_sha256=result['weight_sha256'],classifier_checkpoint_sha256=result['classifier_checkpoint_sha256'],classifier_run_id=result['classifier_run_id'],
        export_path=str(exported.relative_to(ROOT)),overlay_pixels_and_record_match=True,implicit_download_or_connection_attempts=implicit_calls,planned_online_failure_probe='Cache lookup forced missing only for this blocked-HTTP error-guidance check',online_failure_guidance=failure_message,
        cached_live_records=len(rows),cached_provider_timestamp=rows[0]['feed_timestamp'],historical_model_loaded=True,accuracy_evaluated=False,production_models_changed=False)
    (folder/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run;state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
