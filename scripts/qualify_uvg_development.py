"""Bounded format/identity audit of the reserved UVG development sequence only.

No model inference, parking truth, final-data access or automatic promotion.
Run using the existing offline-installed environment which already contains cv2.
"""
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.uvg import require_development, validate_annotations

RESERVATION = ROOT/'data/manifests/uvg_source_roles_v1.json'
SHA = '68599fe2e3f8206acf96626f25777af97bafa2351195a0cc76a613f49d35535e'


def dump(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    start = datetime.now(timezone.utc); timer = time.monotonic()
    run_id = 'UVG-QUALIFICATION-'+start.strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT/'experiments/results'/run_id; out.mkdir(parents=True, exist_ok=False)
    assets = ROOT/'data/raw/uvg_vcm_official/HighwayView'
    names = ['HighwayView.mp4', 'HighwayView_annotations.json', 'HighwayView_masks.zip']
    for name in names:
        require_development(RESERVATION, SHA, 'https://ultravideo.fi/UVG-VCM/HighwayView/'+name)
    implementation = ['scripts/qualify_uvg_development.py', 'src/smart_parking/uvg.py',
                      'tests/test_uvg_access.py', 'tests/test_uvg_annotations.py']
    protected = json.loads((ROOT/'models/singapore_trend_development.json').read_text())['protected_hashes']
    scoring = json.loads((ROOT/'data/manifests/singapore_trend_scoring_v1.json').read_text())
    protected.update(scoring['implementation_hashes'])
    protocol = dict(run_id=run_id, started_at=start.isoformat(), seed=137,
        source_ids=['SRC-DS-019','SRC-DOC-021'], data_kind='real_publisher_development_only',
        hypothesis='Publisher preview, annotation frames and mask bundle agree structurally and supplied object identities/coordinates are internally consistent; alignment remains provisional pending visual review.',
        gates=['600 contiguous one-based annotation and mask frame IDs',
               'Normalized finite polygon/bounding-box consistency and persistent class/color identities',
               'All mask members CRC-valid, PNG geometry matches video metadata',
               'Actual bounded decode reaches 600 frames at 3840x2160; metadata60fps',
               'Supplied colors present within two-pixel bounding-box tolerance on frames1,300,600',
               'All protected production/frozen-study hashes unchanged; final sequence unopened'],
        selected_frames=[1,300,600], maximum_seconds=240,
        reservation_sha256=SHA, input_hashes={name:digest(assets/name) for name in names},
        implementation_hashes={p:digest(ROOT/p) for p in implementation}, protected_hashes=protected,
        model_inference=False, final_data_opened=False, exhaustive_truth_established=False)
    dump(out/'protocol.json', protocol)
    dump(out/'implementation_sources.json', {p:(ROOT/p).read_text(encoding='utf-8') for p in implementation})
    def bounded():
        if time.monotonic()-timer > 240 or (assets/'CANCEL').exists():
            raise InterruptedError('Qualification duration/cancellation boundary reached')
    try:
        annotations = json.loads((assets/names[1]).read_text())
        summary = validate_annotations(annotations,600)
        mask_summary, panels, samples = {}, [], []
        with zipfile.ZipFile(assets/names[2]) as archive:
            members = [i for i in archive.infolist() if not i.is_dir()]
            expected = {f'UVG-VCM/HighwayView/HighwayView_masks/mask_{i:04d}.png' for i in range(1,601)}
            assert len(members)==600 and {i.filename for i in members}==expected
            assert sum(i.file_size for i in members) < 64*1024*1024
            for item in members:
                bounded()
                content=archive.read(item)  # zipfile checks each CRC; never extract paths
                with Image.open(io.BytesIO(content)) as image:
                    assert image.format=='PNG' and image.size==(3840,2160) and image.mode in ('RGB','RGBA')
            mask_summary=dict(files=600,crc_checked=600,png_headers_checked=600,
                              uncompressed_bytes=sum(i.file_size for i in members), all_pixels_decoded=False)
            cap = cv2.VideoCapture(str(assets/names[0]))
            assert cap.isOpened()
            metadata=dict(declared_frames=cap.get(cv2.CAP_PROP_FRAME_COUNT),width=cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                          height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT),fps=cap.get(cv2.CAP_PROP_FPS),decoder=cv2.__version__)
            assert metadata['declared_frames']==600 and metadata['width']==3840 and metadata['height']==2160 and abs(metadata['fps']-60)<1e-6
            count=0
            try:
                while True:
                    bounded(); ok, frame=cap.read()
                    if not ok: break
                    count+=1
                    assert frame.shape[:2]==(2160,3840) and count<=600
                    if count not in (1,300,600): continue
                    with Image.open(io.BytesIO(archive.read(f'UVG-VCM/HighwayView/HighwayView_masks/mask_{count:04d}.png'))) as image:
                        rgb=np.asarray(image.convert('RGB'),dtype=np.uint32)
                    packed=(rgb[:,:,0]<<16)|(rgb[:,:,1]<<8)|rgb[:,:,2]
                    checks=[]
                    for obj in annotations[str(count)]:
                        r,g,b=obj['mask_color']; yy,xx=np.where(packed==((r<<16)|(g<<8)|b))
                        present=bool(len(xx)); contained=False
                        if present:
                            contained=(xx.min()>=obj['x_min']*3840-2 and xx.max()<=obj['x_max']*3840+2
                                       and yy.min()>=obj['y_min']*2160-2 and yy.max()<=obj['y_max']*2160+2)
                        checks.append(dict(track_id=obj['track_id'],color_present=present,
                                           within_bbox_two_pixels=bool(contained),mask_pixels=len(xx)))
                    samples.append(dict(frame=count,objects=checks))
                    panel=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((960,540))
                    draw=ImageDraw.Draw(panel)
                    for obj in annotations[str(count)]:
                        points=list(zip(obj['polygon'][::2],obj['polygon'][1::2]))
                        draw.line([(int(x*960),int(y*540)) for x,y in points+[points[0]]],fill=(255,60,60),width=2)
                    draw.rectangle((0,0,960,24),fill='black')
                    draw.text((8,6),f'UVG HighwayView DEVELOPMENT frame {count}; publisher polygons; no model predictions',fill='white')
                    panels.append(panel)
            finally: cap.release()
        assert count==600
        montage=Image.new('RGB',(960,1620))
        for i,panel in enumerate(panels): montage.paste(panel,(0,i*540))
        montage.save(out/'development_alignment.png')
        checks=dict(complete_annotation_frames=summary['frames']==600,complete_mask_frames=mask_summary['files']==600,
            video_decodes_600=count==600, sampled_supplied_masks_consistent=all(o['color_present'] and o['within_bbox_two_pixels'] for s in samples for o in s['objects']),
            protected_hashes_unchanged=all(digest(ROOT/p)==h for p,h in protected.items()),
            source_reservation_unchanged=digest(RESERVATION)==SHA, final_data_unopened=True)
        report=dict(protocol, finished_at=datetime.now(timezone.utc).isoformat(), duration_seconds=time.monotonic()-timer,
            annotations=summary,masks=mask_summary,video=dict(metadata,decoded_frames=count),sampled_masks=samples,
            checks=checks,all_structural_gates_passed=all(checks.values()),visual_alignment_review='pending',
            scope='Format and supplied-label consistency only. No model score/exhaustiveness/parking-region or occupancy accuracy. Unknown capture dates/pretraining overlap. All600 video frames development exposed; only3 mask pixel planes decoded.')
        dump(out/'run.json',report)
        dump(ROOT/'reports/uvg_qualification_latest.json',dict(run_id=run_id,report=(out/'run.json').relative_to(ROOT).as_posix(),
             checks=checks,all_structural_gates_passed=all(checks.values()),final_sequence='HighwayDrive RESERVED unopened', model_inference=False))
        print(json.dumps(dict(run_id=run_id,duration_seconds=report['duration_seconds'],annotations=summary,checks=checks),indent=2))
    except BaseException as error:
        dump(out/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False))
        raise


if __name__=='__main__': main()
