"""Video-file or explicitly selected camera processing with timestamped events."""
import csv
import json
import time
import math
from pathlib import Path
from PIL import Image,ImageDraw
from .events import OccupancyEvents
from .layout import validate_layout
from .flow import GateCounter

def process_video(source,engine,layout,output,*,every_n=15,every_seconds=None,max_frames=0,confidence=.5,callback=None,cancel=None,flow_config=None):
    if not 0<confidence<1:raise ValueError('Detection threshold must be strictly between zero and one')
    if every_seconds is not None and (not math.isfinite(every_seconds) or every_seconds<=0):raise ValueError('Time sampling interval must be positive and finite')
    flow=GateCounter(**flow_config) if flow_config is not None else None
    if flow is not None and flow.time_unit!='seconds':raise ValueError('Timestamped video processing requires a seconds-based gate configuration')
    try:import cv2
    except ImportError as error:raise RuntimeError('OpenCV is missing; run scripts/setup_video.py once online.') from error
    if every_n<1:raise ValueError('Frame interval must be positive')
    capture=cv2.VideoCapture(source)
    if not capture.isOpened():raise ValueError('Unable to open this video/camera')
    folder=Path(output);folder.mkdir(parents=True,exist_ok=True);events=OccupancyEvents(2);records=[];changes=[];processed=0;decoded=0;index=0;start=time.perf_counter()
    detection_log=(folder/'detections.jsonl').open('w',encoding='utf-8',newline='\n')
    first_time=None;last_time=None;next_sample=None;flow_events=[];flow_result=None
    try:
        fps=capture.get(cv2.CAP_PROP_FPS)
        if fps<=0:fps=None
        while True:
            if cancel and cancel():break
            ok,frame=capture.read()
            if not ok:break
            decoded+=1
            timestamp=capture.get(cv2.CAP_PROP_POS_MSEC)/1000 if not isinstance(source,int) else time.perf_counter()-start
            if every_seconds is not None:
                if not math.isfinite(timestamp) or (last_time is not None and timestamp<last_time):raise ValueError('Video timestamps are invalid for time sampling; use frame sampling')
                if decoded>5 and first_time==timestamp:raise ValueError('Video timestamps do not advance; use frame sampling')
            if first_time is None:first_time=timestamp
            last_time=timestamp
            selected=index%every_n==0 if every_seconds is None else next_sample is None or timestamp+1e-6>=next_sample
            if selected:
                image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
                if layout is not None:validate_layout(layout,image.size)
                result,overlay=engine.analyze(image,layout,confidence=confidence)
                if flow is not None:
                    flow_result=flow.update(result.get('detections',[]),timestamp,image_size=image.size)
                    result['flow']=flow_result;flow_events.extend(flow_result['events'])
                    draw=ImageDraw.Draw(overlay);draw.line([flow.a,flow.b],fill='cyan',width=4)
                    for track in flow_result['tracks']:
                        draw.text(tuple(track['center']),str(track['track_id']),fill='cyan')
                records.append(dict(frame=index,video_time_seconds=timestamp,detected_vehicles=len(result.get('detections',[])),**(result['counts'] if layout is not None else {}),
                    **(flow_result['counts'] if flow is not None else {}),latency_seconds=result['latency_seconds']))
                detection_log.write(json.dumps(dict(frame=index,video_time_seconds=timestamp,occupancy_evaluated=layout is not None,result=result))+'\n');detection_log.flush()
                if layout is not None:changes.extend(events.update(result['slots'],timestamp))
                processed+=1
                overlay.save(folder/f'frame_{index:07d}.jpg')
                if callback:callback(overlay,result,timestamp)
                if every_seconds is not None:next_sample=timestamp+every_seconds
                if max_frames and processed>=max_frames:break
            index+=1
    finally:capture.release();detection_log.close()
    if not records:raise ValueError('Video contained no decodable processed frames')
    with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    observed_fps=(decoded-1)/(last_time-first_time) if decoded>1 and last_time>first_time else None
    summary=dict(processed_frames=processed,decoded_frames=decoded,source_fps=observed_fps if observed_fps is not None else fps,reported_source_fps=fps,
                 observed_timestamp_fps=observed_fps,fps_metadata_consistent=abs(fps-observed_fps)/observed_fps<.05 if fps is not None and observed_fps is not None else None,
                 sample_interval_seconds=every_seconds,detection_threshold=confidence,processing_seconds=time.perf_counter()-start,
                 occupancy_evaluated=layout is not None,events=changes,flow_enabled=flow is not None,
                 flow_config=flow.config if flow is not None else None,flow_events=flow_events,
                 flow_diagnostics={k:flow_result[k] for k in ['counts','gap_resets','ambiguous_matches','discarded_duplicates']} if flow_result is not None else None,
                 claims='Configured gate crossings are predictions; entrance/exit accuracy not evaluated. Occupancy requires a matching layout.' if flow is not None else 'Occupancy transitions only, not entrance/exit vehicle-flow counts' if layout is not None else 'Vehicle detections only; parking occupancy and entrance/exit flow not evaluated')
    (folder/'events.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');return summary
