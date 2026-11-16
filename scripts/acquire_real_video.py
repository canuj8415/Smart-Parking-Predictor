"""Acquire one publisher-attributed real traffic recording with immutable receipts."""
import csv,hashlib,json,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,digest

PAGE='https://commons.wikimedia.org/wiki/File:Street_traffic.webm'
PERMALINK='https://commons.wikimedia.org/w/index.php?title=File:Street_traffic.webm&oldid=1273823111'
URL='https://upload.wikimedia.org/wikipedia/commons/7/70/Street_traffic.webm'
SOURCE='SRC-VID-001'
if __name__=='__main__':
    folder=ROOT/'data/raw/wikimedia_street_traffic';folder.mkdir(parents=True,exist_ok=True)
    asset=folder/'Street_traffic.webm'
    if not asset.exists():
        request=urllib.request.Request(URL,headers={'User-Agent':'SmartParkingPBL/0.3 academic source validation'})
        with urllib.request.urlopen(request,timeout=40) as response:
            if response.headers.get('Content-Length') and int(response.headers['Content-Length'])>100_000_000:raise ValueError('Unexpectedly large video')
            raw=response.read(100_000_001)
        if len(raw)!=26490572 or hashlib.sha1(raw).hexdigest()!='7f916030f14d84a65aa92077339f472897915fef':raise ValueError('Publisher size/SHA-1 mismatch; do not accept this asset')
        asset.write_bytes(raw)
        receipt(SOURCE,asset,URL,'Original real moving traffic video for detection/video integration; no parking-slot ground truth',license='CC BY 3.0 Unported',creator='Editor (YouTube user Editor)',source_page=PAGE,description_page_revision=1273823111,publisher_sha1='7f916030f14d84a65aa92077339f472897915fef')
    if asset.stat().st_size!=26490572 or hashlib.sha1(asset.read_bytes()).hexdigest()!='7f916030f14d84a65aa92077339f472897915fef':raise ValueError('Cached source video differs from verified publisher asset')
    info=dict(source_id=SOURCE,title='Street traffic',creator='Editor (YouTube user Editor)',original_recording_date='2011-05-28',source_page=PAGE,source_page_permalink=PERMALINK,download_url=URL,
        accessed_at=datetime.now(timezone.utc).isoformat(),license='Creative Commons Attribution 3.0 Unported',license_url='https://creativecommons.org/licenses/by/3.0/',
        original_source='https://www.youtube.com/watch?v=_7sCYyxw4Ic',attribution='Street traffic, Editor, via Wikimedia Commons, CC BY 3.0. Derived frames/overlays are modified for academic model evaluation. No endorsement.',
        source_license_review='Wikimedia description records license review by McZusatz on 2013-02-03',
        local_path=asset.relative_to(ROOT).as_posix(),bytes=asset.stat().st_size,sha256=digest(asset),publisher_sha1='7f916030f14d84a65aa92077339f472897915fef',
        intended_use='Real-motion detection/video integration only; no supplied vehicle boxes, slot labels, entrance/exit ground truth or parking occupancy benchmark')
    acquisition=folder/'acquisition.json'
    if acquisition.exists():
        original_info=json.loads(acquisition.read_text(encoding='utf-8'))
        if original_info['sha256']!=info['sha256']:raise ValueError('Existing acquisition receipt conflicts with verified source')
        info=original_info  # Reusing a local file is not a new retrieval.
    else:acquisition.write_text(json.dumps(info,indent=2),encoding='utf-8')
    registry=ROOT/'data/source_manifest.csv'
    with registry.open(encoding='utf-8',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;records=list(reader)
    if SOURCE not in {r['source_id'] for r in records}:
        record={k:'' for k in fields};record.update(source_id=SOURCE,resource_type='real recorded video',resource='Street traffic, San Francisco',original_creator=info['creator'],source_url=PAGE,download_url=URL,access_date=info['accessed_at'],access_time_precision='Actual UTC retrieval timestamp recorded in receipts',version='Wikimedia file publisher SHA-1 pinned; description revision1273823111',license='CC BY 3.0 Unported',permission='User-authorized public-data research; adaptation with attribution under displayed CC BY licence',original_size=str(info['bytes']),local_location=info['local_path'],sha256=info['sha256'],purpose=info['intended_use'],used_by='Real traffic video detection/integration evaluation',modifications='Original unchanged; derived sampled frames/overlays separately labelled',attribution=info['attribution'],status='downloaded',open_issues='No ground-truth vehicle boxes or parking-slot occupancy labels; no detector accuracy or parking-video benchmark claim')
        records.append(record)
        with registry.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(records)
    print(json.dumps(info,indent=2))
