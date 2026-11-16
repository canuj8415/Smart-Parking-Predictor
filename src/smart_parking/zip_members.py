"""Bounded selective JPEG member validation; no archive-wide extraction."""
import struct
import zlib
from pathlib import PurePosixPath


def image_member_span(name,admitted_names,inventory,maximum_bytes=8_000_000):
    # Enforce admission before returning offsets to a network caller.
    if name not in admitted_names:raise ValueError('Image is not admitted development content')
    p=PurePosixPath(name)
    if len(p.parts)!=2 or p.parts[0]!='images' or '\\' in name or p.name in ('.','..') or not p.name.lower().endswith('.jpg'):raise ValueError('Unsafe JPEG member name')
    rows=inventory['entries'];matches=[e for e in rows if e['name']==name]
    if len(matches)!=1:raise ValueError('Missing or ambiguous archive member')
    e=matches[0]
    if e['directory'] or e['method']!=8 or not 0<e['size']<=maximum_bytes or not 0<e['compressed_size']<=maximum_bytes:raise ValueError('Unsupported JPEG or expansion budget')
    start=e['header_offset'];following=[r['header_offset'] for r in rows if r['header_offset']>start]
    end=min(following+[inventory['central_offset']])-1
    if not 0<=start<end<inventory['total_bytes'] or end-start+1>maximum_bytes:raise ValueError('Invalid or oversized member range')
    return e,start,end


def validate_member_range(status,content_range,start,end,total,body,etag,expected_etag):
    if not expected_etag or etag!=expected_etag:raise ValueError('Archive identity changed')
    if status!=206 or content_range!=f'bytes {start}-{end}/{total}' or len(body)!=end-start+1:raise ValueError('Not the exact requested archive member range')


def decode_jpeg_member(body,entry,maximum_bytes=8_000_000):
    if len(body)<30 or len(body)>maximum_bytes or not 0<entry['size']<=maximum_bytes:raise ValueError('Member byte budget exceeded')
    sig,version,flags,method,mt,md,crc,size,expanded,nlen,xlen=struct.unpack_from('<4s5H3I2H',body)
    if sig!=b'PK\x03\x04' or flags not in (0,8) or method!=8 or method!=entry['method']:raise ValueError('Unsupported local JPEG header')
    name=entry['name'].encode('ascii');begin=30+nlen+xlen;end=begin+entry['compressed_size']
    if nlen!=len(name) or body[30:30+nlen]!=name:raise ValueError('JPEG local/central names differ')
    if flags==0 and (crc,size,expanded)!=(entry['crc32'],entry['compressed_size'],entry['size']):raise ValueError('JPEG local/central metadata differ')
    if flags==8 and (crc!=0 or size!=0 or expanded not in (0,entry['size'])):raise ValueError('Invalid streamed JPEG placeholders')
    if flags==8:
        if len(body)!=end+16 or struct.unpack('<4s3I',body[end:])!=(b'PK\x07\x08',entry['crc32'],entry['compressed_size'],entry['size']):raise ValueError('JPEG descriptor mismatch')
    elif len(body)!=end:raise ValueError('Unexpected bytes after JPEG member')
    d=zlib.decompressobj(-15);image=d.decompress(body[begin:end],entry['size']+1)
    if len(image)!=entry['size'] or not d.eof or d.unused_data or d.unconsumed_tail or zlib.crc32(image)!=entry['crc32']:raise ValueError('JPEG expansion/CRC mismatch')
    if not image.startswith(b'\xff\xd8') or not image.endswith(b'\xff\xd9'):raise ValueError('Not a complete JPEG')
    return image
