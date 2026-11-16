"""Acquire a pinned PKLot-portion annotation archive for metadata/rights audit.

No annotation JSON is parsed and no image is downloaded or decoded. Operational
use waits for matching/annotation-scope and per-file rights checks.
"""
import hashlib,json,sys,tarfile,urllib.request
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,digest

REVISION='9218800c4eb2b7c1b17b51c8cdb07ad51686f8a2'
SOURCE='SRC-DS-010'
FILES=[('annotations/original/cars/PKLot/ufpr04_cars.tar.xz',1426408,'a208873ead0b4907ec56f601e815ecbe55d1ee05'),
       ('README.md',16119,'b76c65408cd3deb97d3eea9028582206567d363c'),
       ('CITATION.cff',1086,'1a99abf7516089251c93d0f82b365ff02b204f29')]

if __name__=='__main__':
    folder=ROOT/'data/raw/metapklot_inspection';folder.mkdir(parents=True,exist_ok=True);assets=[]
    for relative,size,blob_sha in FILES:
        path=folder/Path(relative).name;url=f'https://raw.githubusercontent.com/DSBD-Research/MetaPKLot-Dataset/{REVISION}/{relative}'
        if path.exists():raw=path.read_bytes()
        else:
            request=urllib.request.Request(url,headers={'User-Agent':'SmartParkingPBL/0.4 metadata inspection'})
            with urllib.request.urlopen(request,timeout=25) as response:raw=response.read(size+1)
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if len(raw)!=size or actual!=blob_sha:raise ValueError('Pinned publisher Git blob mismatch: '+relative)
        if not path.exists():
            path.write_bytes(raw)
            receipt(SOURCE,path,url,'Metadata/rights inspection only; no annotation JSON parsing or model use',revision=REVISION,publisher_git_blob_sha1=blob_sha,license_scope='Publisher declares PKLot portion CC BY4.0; mixed repository has no blanket licence; operational use pending file/scope checks')
        assets.append(dict(path=path.relative_to(ROOT).as_posix(),url=url,bytes=size,sha256=digest(path),publisher_git_blob_sha1=blob_sha))
    archive=folder/'ufpr04_cars.tar.xz'
    with tarfile.open(archive,'r:xz') as tar:
        members=[dict(name=m.name,bytes=m.size,is_file=m.isfile()) for m in tar.getmembers()]
    metadata=dict(source_id=SOURCE,recorded_at=datetime.now(timezone.utc).isoformat(),revision=REVISION,creator='DSBD-Research; Paulo Lisboa de Almeida and collaborators',source_url='https://github.com/DSBD-Research/MetaPKLot-Dataset',paper_doi='10.1007/s00521-026-12398-0',
        status='Pinned inspection archive acquired; no annotation documents parsed or used',archive_members=members,assets=assets,annotation_json_documents_parsed=0,images_downloaded=0,images_decoded=0,
        rights='PKLot portion declared CC BY4.0 in publisher README; do not assume this licence covers CNRPark-EXT or PLds; inspect exact file metadata/scope before operational use',
        next_step='Use only approved development frame IDs; verify source-image and ROI matching. Do not expose reserved final frames/labels or equate spot polygons with vehicle masks.')
    acquisition=folder/'acquisition.json'
    if not acquisition.exists():acquisition.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    else:metadata=json.loads(acquisition.read_text())
    print(json.dumps(metadata,indent=2),flush=True)
