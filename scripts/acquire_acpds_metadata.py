"""Acquire only publisher documents and bounded ZIP metadata, not pixels/labels."""
import json,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,digest
from smart_parking.source_catalog import register_source
from smart_parking.zip_metadata import inventory_tail,validate_range
REV='17da2c8b33055be8019483260f0efbcbdfda0478'
URL='https://pub-e8bbdcbe8f6243b2a9933704a9b1d8bc.r2.dev/parking%2Frois_gopro.zip'
RAW=ROOT/'data/raw/acpds_official'/REV

def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def fetch(url,name,limit,headers=None):
    path=RAW/name
    if path.exists():raise FileExistsError(path)
    started=datetime.now(timezone.utc).isoformat()
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SmartParkingPBL/0.2',**(headers or {})}),timeout=60) as r:
        body=r.read(limit+1)
        if len(body)>limit:raise ValueError('Response exceeds declared byte budget')
        status=r.status;response_headers={k.lower():v for k,v in r.headers.items() if k.lower() in ['content-length','content-range','etag','last-modified','content-type']};final=r.url
    path.write_bytes(body)
    event=receipt('SRC-DS-021',path,url,'ACPDS qualification: opaque archive metadata or author document only',request_started_at=started,retrieval_url=final,status=status,headers=response_headers)
    dump(path.with_suffix(path.suffix+'.receipt.json'),event)
    return body,status,response_headers

def main():
    RAW.mkdir(parents=True,exist_ok=False)
    register_source(ROOT/'data/source_manifest.csv',dict(source_id='SRC-DS-021',resource_type='dataset and publisher documentation',resource='Action-Camera Parking Dataset (ACPDS)',original_creator='Martin Marek',source_url='https://github.com/martin-marek/parking-space-occupancy',download_url=URL,access_date=datetime.now(timezone.utc).isoformat(),access_time_precision='Exact acquisition receipts; research discovery preceded qualification',version=REV,license='MIT;author paper explicitly includes dataset,code and models',permission='Public attributed local dataset research;whole publisher TEST remains closed pending role reservation',purpose='Fresh unseen parking-lot occupancy development and future independent evaluation',local_location=RAW.relative_to(ROOT).as_posix(),attribution='Martin Marek,Image-Based Parking Space Occupancy Classification:Dataset and Baseline,2021,arXiv:2107.12207;retain MIT notice',status='Qualification in progress;no model score',open_issues='Capture dates/pretraining overlap unknown;author reported metrics are not local results'))
    base=f'https://raw.githubusercontent.com/martin-marek/parking-space-occupancy/{REV}/'
    for remote,local in [('README.md','README.md'),('LICENSE','LICENSE'),('dataset/acpds.py','publisher_loader.py')]:fetch(base+remote,local,131072)
    fetch('https://arxiv.org/abs/2107.12207','paper_abstract.html',131072)
    with urllib.request.urlopen(urllib.request.Request(URL,method='HEAD',headers={'User-Agent':'SmartParkingPBL/0.2'}),timeout=60) as r:
        total=int(r.headers['Content-Length'])
        dump(RAW/'head.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),url=URL,status=r.status,total_bytes=total,etag=r.headers.get('ETag'),last_modified=r.headers.get('Last-Modified')))
    tail,status,headers=fetch(URL,'archive_tail.bin',65536,{'Range':f'bytes={total-65536}-{total-1}'})
    validate_range(status,headers.get('content-range'),total-65536,total-1,total,tail)
    inv=inventory_tail(tail,total)
    central=tail[inv['noncentral_prefix_bytes']:]
    (RAW/'central_directory.bin').write_bytes(central)
    receipt('SRC-DS-021',RAW/'central_directory.bin',URL,'Exact derived central directory and end record;no member payload')
    dump(RAW/'directory_inventory.json',dict(inv,archive_url=URL,total_bytes=total,revision=REV,documents_sha256={p.name:digest(p) for p in RAW.iterdir() if p.is_file() and p.suffix in ['.md','.py','.html']},image_pixels_decoded=0,semantic_annotation_bodies_opened=0))
    print(json.dumps(dict(path=str(RAW),total_bytes=total,entries=inv['total_entries'],noncentral_opaque_bytes=inv['noncentral_prefix_bytes'],nonimage_members=[e for e in inv['entries'] if not e['directory'] and not e['name'].lower().endswith(('.jpg','.jpeg','.png'))]),indent=2))

if __name__=='__main__':main()
