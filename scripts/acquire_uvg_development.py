"""Acquire only bounded publisher development assets; never fetch final bodies."""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest, receipt
from smart_parking.uvg import require_development

RESERVATION = ROOT/'data/manifests/uvg_source_roles_v1.json'
RESERVATION_SHA = '68599fe2e3f8206acf96626f25777af97bafa2351195a0cc76a613f49d35535e'
ASSETS = [
    ('HighwayView.mp4', 34779312, '"212b0b0-655272bd92300"'),
    ('HighwayView_annotations.json', 6552268, '"63facc-6562880de5940"'),
    ('HighwayView_masks.zip', 6338514, '"60b7d2-65588e418aec0"')]


def main():
    start = datetime.now(timezone.utc); folder = ROOT/'data/raw/uvg_vcm_official/HighwayView'; folder.mkdir(parents=True, exist_ok=True)
    plan = dict(started_at=start.isoformat(), source_id='SRC-DS-019', reservation_sha256=RESERVATION_SHA,
        total_planned_bytes=sum(size for _, size, _ in ASSETS), maximum_each_bytes=64*1024*1024,
        scope='Development inspection only; original publisher unannotated MP4, annotations and masks. No model score, no reserved final body.')
    evidence = ROOT/'data/raw/uvg_vcm_official/acquisition_plan_v1.json'
    if not evidence.exists(): evidence.write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
    for name, expected_size, expected_etag in ASSETS:
        url = 'https://ultravideo.fi/UVG-VCM/HighwayView/'+name
        require_development(RESERVATION, RESERVATION_SHA, url)
        final = folder/name
        if final.exists():
            raise FileExistsError('Preserve existing original asset; no implicit overwrite or duplicate acquisition')
        partial = folder/(name+'.'+start.strftime('%Y%m%dT%H%M%S%fZ')+'.partial')
        request = urllib.request.Request(url, headers={'User-Agent': 'SmartParkingPBL/0.2', 'If-Match': expected_etag})
        timer = time.monotonic(); total = 0
        with urllib.request.urlopen(request, timeout=25) as response, partial.open('xb') as stream:
            require_development(RESERVATION, RESERVATION_SHA, response.url)
            if response.status != 200 or int(response.headers['Content-Length']) != expected_size or response.headers.get('ETag') != expected_etag:
                raise ValueError('Publisher asset revision or declared length changed; retain partial evidence')
            while chunk := response.read(1024*1024):
                if time.monotonic()-timer > 120 or (folder/'CANCEL').exists():
                    raise InterruptedError('Bounded acquisition stopped; original partial retained')
                total += len(chunk)
                if total > min(expected_size, 64*1024*1024):
                    raise ValueError('Bounded source size exceeded')
                stream.write(chunk)
            metadata = dict(response_etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'), retrieval_url=response.url)
        if total != expected_size:
            raise ValueError('Incomplete original asset; partial retained')
        assert final.resolve().is_relative_to((ROOT/'data/raw/uvg_vcm_official').resolve()) and not final.exists()
        os.replace(partial, final)
        record = receipt('SRC-DS-019', final, url, 'Official UVG HighwayView development asset, bounded unmodified acquisition',
            license='CC BY 4.0; publisher dataset-level declaration', publisher='Tampere University / Ultra Video Group',
            reservation_sha256=RESERVATION_SHA, semantic_final_data_opened=False, **metadata)
        print(json.dumps(dict(path=record['local_path'], bytes=record['bytes'], sha256=record['sha256'])), flush=True)


if __name__ == '__main__': main()
