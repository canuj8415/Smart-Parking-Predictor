"""Execute full real-data image analysis, semantic masks and a video-codec smoke test."""
import argparse,csv,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.layout import load_layout
from smart_parking.vision import VisionEngine
from smart_parking.training import ParkingUNet
from smart_parking.convolution import plot_convolutions
from smart_parking.video import process_video
from smart_parking.provenance import digest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--skip-video',action='store_true');args=parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    run='PRODUCT-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    with (ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8',newline='') as stream:frames=list(csv.DictReader(stream))
    frame=next(f for f in frames if f['split']=='test');image=Image.open(ROOT/frame['image']).convert('RGB');layout=load_layout(ROOT/frame['layout_path'],image.size)
    results={}
    for kind in ['fasterrcnn','maskrcnn']:
        engine=VisionEngine(kind);result,overlay=engine.analyze(image,layout)
        if result['counts']['total']!=sum(result['counts'][k] for k in ['occupied','vacant','uncertain']):raise RuntimeError('Count conservation failed')
        if kind=='maskrcnn' and any(not d['has_instance_mask'] for d in result['detections']):raise RuntimeError('Missing actual instance masks')
        overlay.save(folder/(kind+'_overlay.png'));(folder/(kind+'_result.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
        results[kind]=dict(detections=len(result['detections']),counts=result['counts'],latency_seconds=result['latency_seconds'])
        print(kind,results[kind],flush=True)
    fig,demo=plot_convolutions(image);fig.savefig(folder/'convolution_lab.png',dpi=140)
    results['convolution']=dict(max_2d_error=demo['max_2d_error'],max_3d_error=demo['max_3d_error'])
    if args.skip_video:
        results.update(run_id=run,sample_frame=frame['image'],sample_sha256=digest(ROOT/frame['image']),source_id='SRC-DS-001',
            video_smoke='Not run in this invocation; video dependency setup pending',
            detector_accuracy='unmeasured: no box ground truth',instance_mask_iou='unmeasured: no vehicle mask ground truth')
        (folder/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        (ROOT/'models/product_smoke_summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(json.dumps(results,indent=2),flush=True);raise SystemExit(0)
    # This deliberately constructed clip verifies codec/frame plumbing only.
    # It is not presented as real vehicle-motion evidence.
    import cv2
    clip=folder/'codec_fixture.avi';writer=cv2.VideoWriter(str(clip),cv2.VideoWriter_fourcc(*'MJPG'),5,image.size)
    if not writer.isOpened():raise RuntimeError('Video writer did not open')
    for _ in range(3):writer.write(cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR))
    writer.release()
    video_result=process_video(str(clip),engine,layout,folder/'video',every_n=1,max_frames=2)
    results['video_smoke']=dict(**video_result,fixture_type='Repeated still-frame codec fixture; not real traffic or flow evaluation')
    results.update(run_id=run,sample_frame=frame['image'],sample_sha256=digest(ROOT/frame['image']),source_id='SRC-DS-001',
        detector_accuracy='unmeasured: no box ground truth',instance_mask_iou='unmeasured: no vehicle mask ground truth')
    (folder/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    (ROOT/'models/product_smoke_summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2),flush=True)
