"""Run explicitly configured local-video gate predictions without desktop input."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.flow import GateCounter
from smart_parking.vision import VisionEngine
from smart_parking.video import process_video
from smart_parking.provenance import digest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,help='An authorized local video file; no camera opened')
    parser.add_argument('--gate-config',required=True,help='JSON: image_size, line and explicit entry_direction; optional tracker settings')
    parser.add_argument('--attribution',required=True,help='JSON recording creator, original URL/ownership and permission/licence')
    parser.add_argument('--output',required=True,help='New empty output directory')
    parser.add_argument('--interval',type=float,default=.5)
    parser.add_argument('--max-frames',type=int,default=120)
    args=parser.parse_args();source=Path(args.source).resolve();output=Path(args.output).resolve()
    if not source.is_file():parser.error('Source must be an existing authorized local video file')
    config=GateCounter(**json.loads(Path(args.gate_config).read_text(encoding='utf-8'))).config
    if config.get('time_unit')=='frames':parser.error('This video-file CLI needs seconds-based settings, not frame-index settings')
    if not 0<args.interval<=config['max_gap_seconds']:parser.error('Sampling interval must be positive and no greater than max_gap_seconds')
    if args.max_frames<1:parser.error('Choose a positive bounded number of processed frames')
    if output.exists() and any(output.iterdir()):parser.error('Output directory must be new or empty to preserve prior evidence')
    attribution=json.loads(Path(args.attribution).read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=True)
    metadata=dict(source_path=str(source),source_sha256=digest(source),gate_config=config,attribution=attribution,
        interval_seconds=args.interval,max_processed_frames=args.max_frames,accuracy_evaluated=False,
        limitations='Predicted crossings only; configure the actual view and direction. Same image dimensions do not establish camera identity. No occupancy or live availability inferred.')
    (output/'source_and_gate.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    engine=VisionEngine('fasterrcnn')
    result=process_video(str(source),engine,None,output,every_seconds=args.interval,max_frames=args.max_frames,confidence=.5,
        flow_config=config,cancel=lambda:(output/'CANCEL').exists())
    print(json.dumps(dict(counts=result['flow_diagnostics'],processed_frames=result['processed_frames'],accuracy_evaluated=False),indent=2))
