"""Bounded range recovery for the verified PyPI wheel, installed only locally."""
import concurrent.futures,hashlib,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt
URL='https://files.pythonhosted.org/packages/4a/90/b338326131ccb2aaa3c2c85d00f41822c0050139a4bfe723cfd95455bd2d/opencv_python_headless-4.13.0.92-cp37-abi3-win_amd64.whl'
SIZE=40070414;SHA='77a82fe35ddcec0f62c15f2ba8a12ecc2ed4207c17b0902c7a3151ae29f37fb6';CHUNK=1024*1024
folder=ROOT/'dependencies/wheels/opencv_parts';folder.mkdir(parents=True,exist_ok=True)
def retrieve(i):
    start=i*CHUNK;end=min(SIZE,start+CHUNK)-1;p=folder/f'{i:03d}.part'
    if p.exists() and p.stat().st_size==end-start+1:return p
    request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}','User-Agent':'SmartParkingPBL/0.2'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request,timeout=30) as response:
                if response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {start}-{end}/'):raise ValueError('Wheel range not honored')
                data=response.read(end-start+2)
            break
        except (TimeoutError,OSError):
            if attempt==3:raise
    if len(data)!=end-start+1:raise ValueError('Incomplete wheel range')
    p.write_bytes(data);print('Video wheel range',i+1,flush=True);return p
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:parts=list(pool.map(retrieve,range((SIZE+CHUNK-1)//CHUNK)))
    wheel=ROOT/'dependencies/wheels/opencv_python_headless-4.13.0.92-cp37-abi3-win_amd64.whl'
    data=b''.join(p.read_bytes() for p in parts)
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('Publisher SHA-256 mismatch')
    wheel.write_bytes(data);receipt('SRC-PKG-001',wheel,URL,'Project-local video decoder; exact PyPI digest verified')
    subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps','--target',str(ROOT/'dependencies/python'),str(wheel)],check=True)
