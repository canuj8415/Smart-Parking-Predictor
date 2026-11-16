"""Measure real-motion detection plumbing, without inventing parking labels."""
import csv,hashlib,json,statistics,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.vision import VisionEngine
from smart_parking.video import process_video
from smart_parking.provenance import digest
import cv2
import numpy as np
from PIL import Image

if __name__=='__main__':
    source=ROOT/'data/raw/wikimedia_street_traffic/Street_traffic.webm';metadata=json.loads(source.with_name('acquisition.json').read_text())
    if digest(source)!=metadata['sha256']:raise ValueError('Source checksum changed')
    run='REAL-VIDEO-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    cap=cv2.VideoCapture(str(source))
    if not cap.isOpened():raise ValueError('Original video cannot be decoded')
    fps=cap.get(cv2.CAP_PROP_FPS);reported_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));cap.release()
    if fps<=0:raise ValueError('Need valid video timestamps/frame rate')
    protocol=dict(run_id=run,source_id=metadata['source_id'],started_at=datetime.now(timezone.utc).isoformat(),source_sha256=metadata['sha256'],
        source_page=metadata['source_page'],attribution=metadata['attribution'],license_url=metadata['license_url'],hypothesis='Real moving recorded traffic can be decoded, timestamped and analyzed consistently by the existing local detector',
        detector='fasterrcnn_resnet50_fpn_v2',threshold=.5,sample_interval_seconds=2.,max_processed_frames=20,
        occupancy_evaluated=False,vehicle_accuracy_evaluated=False,flow_evaluated=False,
        code_sha256=digest(Path(__file__)),video_code_sha256=digest(ROOT/'src/smart_parking/video.py'),vision_code_sha256=digest(ROOT/'src/smart_parking/vision.py'))
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    start=time.perf_counter();engine=VisionEngine('fasterrcnn');load_seconds=time.perf_counter()-start
    result=process_video(str(source),engine,None,folder/'video',every_n=1,every_seconds=2.,max_frames=20,confidence=.5)
    log=[json.loads(line) for line in (folder/'video/detections.jsonl').read_text().splitlines()]
    times=[r['video_time_seconds'] for r in log]
    if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Non-increasing real video timestamps')
    latencies=[r['result']['latency_seconds'] for r in log];counts=[len(r['result']['detections']) for r in log]
    # Validate actual source motion using two original decoded frames, not overlay differences.
    capture=cv2.VideoCapture(str(source));original=[];hashes=[]
    wanted=[0.,5.,10.];index=0
    while wanted:
        ok,frame=capture.read()
        if not ok:raise ValueError('Missing motion-check source frame')
        at=capture.get(cv2.CAP_PROP_POS_MSEC)/1000
        if at+1e-6>=wanted[0]:
            wanted.pop(0);small=cv2.resize(frame,(192,108));original.append(small);hashes.append(hashlib.sha256(small.tobytes()).hexdigest())
            Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).save(folder/f'source_frame_{index:05}.jpg')
        index+=1
    capture.release();difference=float(np.mean(np.abs(original[0].astype(float)-original[1].astype(float))))
    if len(set(hashes))<2 or difference==0:raise ValueError('No verified source-frame variation')
    report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),video_metadata=dict(reported_fps=fps,reported_frames=reported_frames,width=width,height=height),
        metrics=dict(processed_frames=result['processed_frames'],decoded_frames=result['decoded_frames'],video_last_processed_second=max(times),
            detector_load_seconds=load_seconds,median_inference_seconds=statistics.median(latencies),p95_inference_seconds=float(np.percentile(latencies,95)),
            processed_throughput_fps=result['processed_frames']/result['processing_seconds'],min_vehicles_per_frame=min(counts),max_vehicles_per_frame=max(counts),
            timestamp_strictly_increasing=True,original_frame_difference_mean_pixel=difference,unique_motion_check_hashes=len(set(hashes))),
        video_result=result,weight_sha256=engine.weight_sha256,device='cpu',
        limitations=['One short street-traffic recording, not a parking camera or full deployment benchmark','No supplied boxes/tracks/slot/flow ground truth: detector mAP, occupancy accuracy and flow accuracy unmeasured','Decoded changing frames establish motion input, not correct tracking or counting','Throughput is offline processing and includes output writing; no real-time claim','Only one pretrained detector in this video run'])
    (folder/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text());state.setdefault('completed_run_ids',[]).append(run);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run;state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
