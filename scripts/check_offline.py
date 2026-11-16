"""Verify the real image path with outbound HTTP disabled in this process.

Windows networking is not changed. This is not a physically disconnected demo.
"""
import csv,json,sys,urllib.request
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.vision import VisionEngine
from smart_parking.layout import load_layout
from smart_parking.live import get_live
from smart_parking.forecasting import load_forecast

if __name__=='__main__':
    with (ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8',newline='') as stream:frame=next(r for r in csv.DictReader(stream) if r['split']=='test')
    with patch('urllib.request.urlopen',side_effect=RuntimeError('Outbound HTTP disabled by verification harness')):
        image=Image.open(ROOT/frame['image']).convert('RGB');layout=load_layout(ROOT/frame['layout_path'],image.size)
        result,_=VisionEngine('fasterrcnn').analyze(image,layout)
        model,bundle=load_forecast();live,metadata=get_live(False)
        report=dict(scope='Outbound urllib HTTP blocked in this Python process; OS network remains connected',
            image_inference='pass',model=result['model'],counts=result['counts'],historical_checkpoint_load='pass',
            cached_live_observations=len(live),provider_timestamp=live[0]['feed_timestamp'],
            status='pass; no implicit model or data download',limitations='Not a fresh offline install or physically disconnected rehearsal')
    folder=ROOT/'experiments/evidence/OFFLINE-PROCESS';folder.mkdir(parents=True,exist_ok=True)
    (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
