"""Recover a bounded official archive prefix using verified HTTP byte ranges.

The archive is shuffled. Retain only image/XML pairs actually present in the
prefix; this is a convenience development subset, never a full benchmark.
"""
import concurrent.futures
import json
import sys
import tarfile
import time
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,now,digest
URL='https://www.inf.ufpr.br/lesoliveira/download/PKLot.tar.gz'
FOLDER=ROOT/'data/raw/pklot_subset'
CHUNK=8*1024*1024
TOTAL=3860376865

def get_chunk(index):
    start=index*CHUNK;end=min(TOTAL,start+CHUNK)-1
    path=FOLDER/f'parts/{index:04d}.part';path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size==end-start+1:return path
    for attempt in range(3):
        try:
            request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}','User-Agent':'SmartParkingPBL/0.2'})
            with urllib.request.urlopen(request,timeout=60) as response:
                expected=f'bytes {start}-{end}/'
                if response.status!=206 or not response.headers.get('Content-Range','').startswith(expected):
                    raise ValueError('Server did not honor the exact public byte range')
                data=response.read(end-start+2)
                if len(data)!=end-start+1:raise ValueError('Truncated range')
            path.write_bytes(data);print('Downloaded range',index+1,'of',(TOTAL+CHUNK-1)//CHUNK,flush=True);return path
        except Exception:
            if attempt==2:raise
            time.sleep(1)

if __name__=='__main__':
    FOLDER.mkdir(parents=True,exist_ok=True);started=now()
    cached=FOLDER/'PKLot.tar.gz'
    ledger=ROOT/'data/resource_receipts.jsonl'
    if cached.exists() and cached.stat().st_size==TOTAL and ledger.exists():
        receipts=[json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
        matches=[r for r in receipts if r['local_path']=='data/raw/pklot_subset/PKLot.tar.gz' and r.get('full_archive_downloaded')]
        if matches and digest(cached)==matches[-1]['sha256']:
            print('Full original archive already cached and hash-verified; no download requested.');raise SystemExit(0)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        parts=list(pool.map(get_chunk,range((TOTAL+CHUNK-1)//CHUNK)))
    prefix=FOLDER/'PKLot.tar.gz'
    with prefix.open('wb') as stream:
        for part in parts:stream.write(part.read_bytes())
    extracted=0
    try:
        with tarfile.open(prefix,mode='r|gz') as archive:
            for member in archive:
                if not member.isfile() or Path(member.name).suffix.lower() not in {'.jpg','.xml'}:continue
                target=(FOLDER/member.name).resolve()
                if not target.is_relative_to(FOLDER.resolve()) or member.size>10*1024*1024:raise ValueError('Unsafe member')
                # Keep the already acquired prefix images; read matching XML from the full archive.
                if target.suffix.lower()=='.jpg' and not target.exists():continue
                raw=archive.extractfile(member).read()
                if len(raw)!=member.size:continue
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);extracted+=1
    except (tarfile.ReadError,EOFError):
        print('Expected end of deliberately partial archive prefix.',flush=True)
    pairs=[]
    for image in sorted(FOLDER.glob('PKLot/**/*.jpg')):
        xml=image.with_suffix('.xml')
        if xml.exists():pairs.append(dict(date=image.parent.name,image=image.relative_to(ROOT).as_posix(),annotation=xml.relative_to(ROOT).as_posix()))
    record=dict(source_id='SRC-DS-001',url=URL,started_at=started,finished_at=now(),
        full_archive_downloaded=True,compressed_bytes_acquired=TOTAL,extracted_entries=extracted,pairs=pairs,
        policy='Full original archive acquired; working images come from its first 512 MiB compressed prefix; matching XML verified across archive. Date-grouped convenience subset, not representative full benchmark.')
    info=FOLDER/'acquisition.json';info.write_text(json.dumps(record,indent=2),encoding='utf-8')
    receipt('SRC-DS-001',prefix,URL,'Full original PKLot archive',full_archive_downloaded=True,byte_range=f'0-{TOTAL-1}')
    for pair in pairs:
        for key in ('image','annotation'):receipt('SRC-DS-001',ROOT/pair[key],URL,'Original paired research subset',archive_member=Path(pair[key]).relative_to('data/raw/pklot_subset').as_posix())
    print('PAIRS',len(pairs),'DAYS',len({p['date'] for p in pairs}),flush=True)
