"""Acquire two author-owned DAVIS sequences via bounded, verified archive ranges."""
import json,struct,sys,zlib,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inspect_davis_archive import RemoteZip,URL
from smart_parking.provenance import receipt,download,digest
SEQUENCES={'car-turn':'development','car-roundabout':'reserved_final'}

def decode(info,block,start):
    at=info.header_offset-start;header=block[at:at+30]
    if header[:4]!=b'PK\x03\x04':raise ValueError('Bad local archive member header')
    fields=struct.unpack('<4s5H3I2H',header);name_len,extra_len=fields[-2:]
    if block[at+30:at+30+name_len].decode('utf-8')!=info.filename or info.flag_bits&1:raise ValueError('Member name/encryption mismatch')
    at+=30+name_len+extra_len;compressed=block[at:at+info.compress_size]
    if len(compressed)!=info.compress_size or info.file_size>2*1024*1024:raise ValueError('Member bounds exceeded')
    if info.compress_type==8:
        decoder=zlib.decompressobj(-15);data=decoder.decompress(compressed,info.file_size+1)
        if not decoder.eof or decoder.unconsumed_tail:raise ValueError('Deflate entry length inconsistent')
    elif info.compress_type==0:data=compressed
    else:raise ValueError('Unsupported ZIP compression')
    if len(data)!=info.file_size or zlib.crc32(data)&0xffffffff!=info.CRC:raise ValueError('Member CRC/size mismatch')
    return data

def main():
    from smart_parking.source_catalog import require_source_identity
    require_source_identity(ROOT/'data/source_manifest.csv','SRC-DS-012','DAVIS2017 car-turn and car-roundabout original JPEG frames / publisher foreground masks','https://davischallenge.org/davis2017/code.html')
    metadata=ROOT/'data/raw/davis2017_metadata';sources=(metadata/'SOURCES.md').read_text()
    for name in SEQUENCES:
        if any(line.split()[1]==name for line in sources.splitlines() if line.startswith('* ')):raise ValueError('External footage exception needs a separate rights review')
    readme=(metadata/'README.md').read_text()
    assert 'All sequences if not stated differently are owned by the authors' in readme and 'CC BY-NC' in readme
    for url,target,purpose in [
        ('https://davischallenge.org/','data/raw/davis2017_metadata/official_home.html','Official dataset creator/license schema'),
        ('https://davischallenge.org/davis2017/code.html','data/raw/davis2017_metadata/official_downloads.html','Official archive link and human-annotation description'),
        ('https://creativecommons.org/licenses/by-nc/4.0/','data/raw/davis2017_metadata/cc_by_nc_4.html','Dataset noncommercial attribution licence deed')]:
        download('SRC-DS-012',url,target,purpose)
    remote=RemoteZip(budget=50*1024*1024);pinned=json.loads((metadata/'archive_index_inspection.json').read_text());assert remote.etag==pinned['etag'] and remote.size==pinned['size']
    archive=zipfile.ZipFile(remote);all_infos=archive.infolist();entries=[];block_records=[]
    for sequence,role in SEQUENCES.items():
        for kind in ['JPEGImages','Annotations']:
            chosen=sorted([i for i in all_infos if i.filename.startswith(f'DAVIS/{kind}/480p/{sequence}/') and not i.is_dir()],key=lambda i:i.header_offset)
            groups=[];current=[]
            for info in chosen:
                if current and info.header_offset+info.compress_size+70000-current[0].header_offset>7*1024*1024:groups.append(current);current=[]
                current.append(info)
            if current:groups.append(current)
            for group in groups:
                last=group[-1];remote.seek(last.header_offset);header=remote.read(30);name_len,extra_len=struct.unpack('<4s5H3I2H',header)[-2:]
                start=group[0].header_offset;end=last.header_offset+30+name_len+extra_len+last.compress_size-1
                block_path=ROOT/f'data/raw/davis2017_ranges/{start}_{end}.bin';block_path.parent.mkdir(parents=True,exist_ok=True)
                if block_path.exists():block=block_path.read_bytes()
                else:
                    remote.seek(start);block=remote.read(end-start+1);block_path.write_bytes(block)
                    receipt('SRC-DS-012',block_path,URL,'Bounded original archive byte range; not the full ZIP',range_start=start,range_end=end,archive_etag=remote.etag,archive_size=remote.size)
                if len(block)!=end-start+1:raise ValueError('Cached archive range has wrong length')
                block_records.append(dict(path=block_path.relative_to(ROOT).as_posix(),start=start,end=end,sha256=digest(block_path)))
                for info in group:
                    data=decode(info,block,start);relative=Path(info.filename)
                    target=(ROOT/'data/raw/davis2017_subset'/relative).resolve()
                    if not target.is_relative_to((ROOT/'data/raw/davis2017_subset').resolve()):raise ValueError('Archive path escapes subset directory')
                    target.parent.mkdir(parents=True,exist_ok=True)
                    if target.exists() and target.read_bytes()!=data:raise ValueError('Preserve existing original member bytes')
                    if not target.exists():
                        target.write_bytes(data);receipt('SRC-DS-012',target,URL,'Original sequence member; CRC verified; no pixel transformation',archive_entry=info.filename,archive_etag=remote.etag,crc32=info.CRC,parent_range=block_path.relative_to(ROOT).as_posix())
                    entries.append(dict(sequence=sequence,role=role,kind=kind,member=info.filename,path=target.relative_to(ROOT).as_posix(),bytes=len(data),sha256=digest(target),crc32=info.CRC))
                print(f'Acquired {sequence}/{kind}: {len(group)} original members',flush=True)
    result=dict(acquired_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-012',archive_url=URL,archive_etag=remote.etag,archive_size=remote.size,
        archive_fully_downloaded=False,full_archive_sha256=None,range_bytes_received_this_execution=remote.received,blocks=block_records,entries=entries,
        licence='DAVIS aggregate CC BY-NC4.0; README default author-owned sequences; selected sequences absent from external SOURCES exceptions; local noncommercial academic use only',
        source_docs=dict(readme_sha256=digest(metadata/'README.md'),sources_sha256=digest(metadata/'SOURCES.md')),
        role_plan=SEQUENCES,frame_rate='Not established from the acquired metadata; do not invent physical timestamps',
        reserved_pixels_decoded=False,reserved_annotation_values_decoded=False)
    path=metadata/'subset_acquisition.json'
    if path.exists():raise FileExistsError('Original successful acquisition manifest already exists')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(files=len(entries),original_member_bytes=sum(r['bytes'] for r in entries),network_bytes_this_execution=remote.received,roles=SEQUENCES),indent=2),flush=True)

if __name__=='__main__':main()
