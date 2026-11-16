"""Separate corrective development trial; preserve the failed RGB assumption."""
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.uvg import instance_pixels, require_development, validate_annotations


def dump(path,value): path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    started=datetime.now(timezone.utc);timer=time.monotonic()
    run_id='UVG-MASK-CHANNELS-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/results'/run_id;out.mkdir(parents=True,exist_ok=False)
    reservation=ROOT/'data/manifests/uvg_source_roles_v1.json'
    sha='68599fe2e3f8206acf96626f25777af97bafa2351195a0cc76a613f49d35535e'
    folder=ROOT/'data/raw/uvg_vcm_official/HighwayView'
    names=['HighwayView_annotations.json','HighwayView_masks.zip']
    for name in names: require_development(reservation,sha,'https://ultravideo.fi/UVG-VCM/HighwayView/'+name)
    frames=[61,121,181,241,361,421,481,541]  # fixed before these pixel planes are decoded
    sources=['scripts/validate_uvg_mask_channels.py','src/smart_parking/uvg.py','tests/test_uvg_mask_channels.py']
    protocol=dict(run_id=run_id,started_at=started.isoformat(),seed=137,source_ids=['SRC-DS-019','SRC-DOC-021'],
        data_kind='real_development_label_consistency_no_model',
        hypothesis='Explicit JSON-BGR to PNG-RGB conversion recovers supplied instance colors within fixed two-pixel box tolerance on eight additional development frames.',
        gates=['All supplied instance colors present inside their normalized boxes within two pixels on all eight prespecified frames',
               'Reservation unchanged; no final access; no inference or score-based channel selection'],
        frames=frames,initial_failure='UVG-QUALIFICATION-20261026T125634879459Z',
        reservation_sha256=sha,input_hashes={name:digest(folder/name) for name in names},
        implementation_hashes={p:digest(ROOT/p) for p in sources},maximum_seconds=180)
    dump(out/'protocol.json',protocol);dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in sources})
    annotations=json.loads((folder/names[0]).read_text());validate_annotations(annotations,600)
    results=[]
    with zipfile.ZipFile(folder/names[1]) as z:
        for frame in frames:
            if time.monotonic()-timer>180 or (folder/'CANCEL').exists(): raise InterruptedError('Bounded channel validation stopped')
            with Image.open(io.BytesIO(z.read(f'UVG-VCM/HighwayView/HighwayView_masks/mask_{frame:04d}.png'))) as im:
                array=np.array(im)
            for obj in annotations[str(frame)]:
                yy,xx=np.where(instance_pixels(array,obj['mask_color']))
                bounds=None if not len(xx) else [int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]
                contained=bool(bounds and bounds[0]>=obj['x_min']*3840-2 and bounds[2]<=obj['x_max']*3840+2
                               and bounds[1]>=obj['y_min']*2160-2 and bounds[3]<=obj['y_max']*2160+2)
                results.append(dict(frame=frame,track_id=obj['track_id'],pixels=len(xx),decoded_bounds=bounds,
                                    supplied_bounds=[obj[k] for k in ['x_min','y_min','x_max','y_max']],passes=contained))
    checks=dict(all_supplied_instances_consistent=all(r['passes'] for r in results),
                reservation_unchanged=digest(reservation)==sha,final_data_unopened=True)
    report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,
        instances_checked=len(results),instances_passing=sum(r['passes'] for r in results),results=results,checks=checks,
        all_gates_passed=all(checks.values()),model_inference=False,exhaustiveness_established=False,
        scope='Annotation adapter consistency, not model mask IoU, detection/count/occupancy accuracy or final performance.')
    dump(out/'run.json',report)
    dump(ROOT/'reports/uvg_mask_channels_latest.json',dict(run_id=run_id,report=(out/'run.json').relative_to(ROOT).as_posix(),
        instances_checked=len(results),instances_passing=report['instances_passing'],checks=checks,all_gates_passed=report['all_gates_passed']))
    print(json.dumps({k:report[k] for k in ['run_id','duration_seconds','instances_checked','instances_passing','all_gates_passed']},indent=2))


if __name__=='__main__': main()
