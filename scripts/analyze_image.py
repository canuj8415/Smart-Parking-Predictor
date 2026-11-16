"""Run real local vision models and save overlays/counts; no network access."""
import argparse,json,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.layout import load_layout
from smart_parking.vision import VisionEngine

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('image');parser.add_argument('--layout');parser.add_argument('--detector',choices=['fasterrcnn','maskrcnn'],default='fasterrcnn');parser.add_argument('--confidence',type=float,default=.5);parser.add_argument('--output',default='outputs/image_analysis')
    args=parser.parse_args()
    try:
        image=Image.open(args.image).convert('RGB');layout=load_layout(args.layout,image.size) if args.layout else None
    except (OSError,ValueError) as error:parser.error(str(error))
    result,overlay=VisionEngine(args.detector).analyze(image,layout,args.confidence)
    folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True)
    overlay.save(folder/'overlay.png');(folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(detections=len(result['detections']),counts=result['counts'],latency_seconds=result['latency_seconds'],output=str(folder)),indent=2))
