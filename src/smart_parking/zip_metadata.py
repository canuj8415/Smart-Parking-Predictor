"""Bounded ZIP metadata validation; no image/annotation extraction API."""
import io
import struct
import zipfile
import zlib


def validate_range(status,content_range,start,end,total,body):
    if not (0<=start<=end<total) or end-start+1>131072:raise ValueError('Range outside metadata byte budget')
    if status!=206 or content_range!=f'bytes {start}-{end}/{total}' or len(body)!=end-start+1:
        raise ValueError('Server did not return the exact bounded range')


def inventory_tail(tail,total):
    if not isinstance(tail,bytes) or len(tail)>131072 or len(tail)>total:raise ValueError('Invalid bounded ZIP tail')
    index=tail.rfind(b'PK\x05\x06');fields=None
    while index>=0:
        if index+22<=len(tail):
            value=struct.unpack_from('<4s4H2IH',tail,index)
            if index+22+value[7]==len(tail):fields=value;break
        index=tail.rfind(b'PK\x05\x06',0,index)
    if fields is None:raise ValueError('Complete ZIP end record missing')
    _,disk,central_disk,disk_entries,entries,size,offset,comment=fields
    if disk or central_disk or disk_entries!=entries or entries==65535 or size==0xffffffff or offset==0xffffffff:
        raise ValueError('Multidisk/ZIP64 metadata needs a separate bounded plan')
    start=total-len(tail)
    if offset<start or offset+size!=start+index:raise ValueError('Central directory not completely contained in tail')
    # Supply zipfile a canonical metadata-only end record. Its own signature
    # search otherwise mistakes a signature inside a valid ZIP comment.
    central=tail[offset-start:offset-start+size]+struct.pack('<4s4H2IH',b'PK\x05\x06',0,0,entries,entries,size,0,0)
    with zipfile.ZipFile(io.BytesIO(central)) as archive:
        infos=archive.infolist()
        if len(infos)!=entries:raise ValueError('ZIP entry count mismatch')
        rows=[dict(name=i.filename,size=i.file_size,compressed_size=i.compress_size,method=i.compress_type,
                   crc32=i.CRC,header_offset=i.header_offset,directory=i.is_dir()) for i in infos]
    return dict(entries=rows,total_entries=entries,central_size=size,central_offset=offset,
                acquired_tail_bytes=len(tail),noncentral_prefix_bytes=offset-start,
                tail_is_exclusively_metadata=offset==start,whole_archive_integrity_verified=False)


def require_document_member(name):
    # Fixed source plan: never interpret a filename extension as general permission.
    if name!='README.pdf':raise ValueError('Only the declared root README document may be opened')


def decode_document_member(header,name_extra,compressed,entry):
    """Validate a fixed README local header and bound expansion before CRC check."""
    require_document_member(entry['name'])
    if len(header)!=30:raise ValueError('Exact ZIP local header required')
    signature,version,flags,method,mtime,mdate,crc,size,expanded,nlen,xlen=struct.unpack('<4s5H3I2H',header)
    if signature!=b'PK\x03\x04' or flags!=0 or method!=8:raise ValueError('Only unencrypted explicit-size DEFLATE README supported')
    if len(name_extra)!=nlen+xlen or name_extra[:nlen]!=b'README.pdf':raise ValueError('Local name or extra-field length differs')
    if size!=len(compressed) or size>131072 or expanded>131072:raise ValueError('Document byte budget exceeded or incomplete range')
    if (size,expanded,crc,method)!=(entry['compressed_size'],entry['size'],entry['crc32'],entry['method']):raise ValueError('Local and central README metadata differ')
    decoder=zlib.decompressobj(-15);body=decoder.decompress(compressed,expanded+1)
    if len(body)!=expanded or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:raise ValueError('Unexpected expansion or trailing compressed content')
    if zlib.crc32(body)!=crc:raise ValueError('README CRC mismatch')
    return body


def require_image_admission(qualification):
    if qualification.get('individual_content_rights_qualified') is not True:
        raise ValueError('Individual image/annotation content rights remain unqualified')
    if not qualification.get('role_manifest_sha256'):
        raise ValueError('A separate whole-group role reservation is required before semantic access')
