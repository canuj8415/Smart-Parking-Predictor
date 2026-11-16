"""Bounded official-archive metadata inspection before sequence rights are accepted."""
import io,json,struct,sys,urllib.request,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt
URL='https://data.vision.ee.ethz.ch/csergi/share/davis/DAVIS-2017-trainval-480p.zip'

class RemoteZip(io.RawIOBase):
    def __init__(self,url=URL,budget=50*1024*1024):
        self.url=url;self.position=0;self.received=0;self.budget=budget
        with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=20) as r:
            self.size=int(r.headers['Content-Length']);self.etag=r.headers.get('ETag');self.modified=r.headers.get('Last-Modified')
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.position
    def seek(self,offset,whence=0):
        self.position=offset if whence==0 else self.position+offset if whence==1 else self.size+offset
        if not 0<=self.position<=self.size:raise ValueError('ZIP seek outside archive')
        return self.position
    def read(self,n=-1):
        n=min(self.size-self.position,n if n>=0 else self.size-self.position)
        if not n:return b''
        if n>8*1024*1024 or self.received+n>self.budget:raise ValueError('Bounded archive read limit exceeded')
        start=self.position;end=start+n-1
        request=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}','User-Agent':'SmartParkingPBL/0.2'})
        with urllib.request.urlopen(request,timeout=20) as r:
            if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.size}':raise ValueError('Server did not honor exact byte range')
            if self.etag and r.headers.get('ETag')!=self.etag:raise ValueError('Archive ETag changed')
            data=r.read(n+1)
        if len(data)!=n:raise ValueError('Incomplete range')
        self.position+=n;self.received+=n;return data
    def entry(self,info):
        self.seek(info.header_offset);header=self.read(30)
        if header[:4]!=b'PK\x03\x04':raise ValueError('Invalid local ZIP header')
        fields=struct.unpack('<4s5H3I2H',header);name_size,extra_size=fields[-2:]
        self.seek(info.header_offset+30);name=self.read(name_size).decode('utf-8')
        if name!=info.filename or info.flag_bits&1:raise ValueError('Entry identity/encryption unsupported')
        self.seek(info.header_offset+30+name_size+extra_size);compressed=self.read(info.compress_size)
        data=zlib.decompress(compressed,-15) if info.compress_type==8 else compressed if info.compress_type==0 else None
        if data is None or len(data)!=info.file_size or zlib.crc32(data)&0xffffffff!=info.CRC:raise ValueError('Entry size/CRC mismatch')
        return data

if __name__=='__main__':
    from smart_parking.source_catalog import require_source_identity
    require_source_identity(ROOT/'data/source_manifest.csv','SRC-DS-012','DAVIS2017 car-turn and car-roundabout original JPEG frames / publisher foreground masks','https://davischallenge.org/davis2017/code.html')
    folder=ROOT/'data/raw/davis2017_metadata';folder.mkdir(parents=True,exist_ok=True)
    remote=RemoteZip();archive=zipfile.ZipFile(remote);infos=archive.infolist()
    docs=[i for i in infos if Path(i.filename).name.lower() in {'readme.md','sources.md','license','license.txt','readme.txt'}]
    result=dict(url=URL,size=remote.size,etag=remote.etag,last_modified=remote.modified,entry_count=len(infos),metadata_entries=[i.filename for i in docs],
        candidate_sequence_entries=[dict(name=i.filename,size=i.file_size,compressed=i.compress_size,crc32=i.CRC,offset=i.header_offset) for i in infos if '/car-roundabout/' in i.filename or '/car-turn/' in i.filename])
    for info in docs:
        target=folder/Path(info.filename).name
        data=remote.entry(info)
        if target.exists() and target.read_bytes()!=data:raise ValueError('Preserve existing metadata revision')
        if not target.exists():
            target.write_bytes(data);receipt('SRC-DS-012',target,URL,'Original DAVIS metadata/rights inspection only',archive_entry=info.filename,archive_etag=remote.etag,crc32=info.CRC)
        print(info.filename+'\n'+data.decode('utf-8',errors='replace'),flush=True)
    result['metadata_range_bytes_received']=remote.received
    (folder/'archive_index_inspection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='candidate_sequence_entries'},indent=2),flush=True)
