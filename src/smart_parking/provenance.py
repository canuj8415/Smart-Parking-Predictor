"""Append-only resource receipts: original URLs, real timestamps, bytes and hashes."""
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def receipt(source_id, path, url, purpose, **metadata):
    path=Path(path).resolve()
    record=dict(source_id=source_id,accessed_at=now(),source_url=url,
        local_path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
        sha256=digest(path),purpose=purpose,**metadata)
    log=ROOT/'data/resource_receipts.jsonl'
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('a',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(record)+'\n')
    return record

def download(source_id, url, destination, purpose, hash_prefix=None):
    path=ROOT/destination
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if hash_prefix and not digest(path).startswith(hash_prefix):
            raise ValueError(f'Cached asset hash mismatch: {path.name}')
        return path
    partial=path.with_suffix(path.suffix+'.partial')
    request=urllib.request.Request(url,headers={'User-Agent':'SmartParkingPBL/0.2'})
    with urllib.request.urlopen(request,timeout=90) as response, partial.open('wb') as output:
        expected=response.headers.get('Content-Length')
        final_url=response.url
        while chunk:=response.read(1024*1024):
            output.write(chunk)
        if expected and output.tell()!=int(expected):
            raise ValueError('Incomplete download')
    if hash_prefix and not digest(partial).startswith(hash_prefix):
        raise ValueError('Asset checksum prefix does not match publisher filename')
    os.replace(partial,path)
    receipt(source_id,path,url,purpose,retrieval_url=final_url)
    return path
