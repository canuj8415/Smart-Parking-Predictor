"""Read publisher development partitions while keeping TEST semantics opaque.

The structural scan finds top-level object spans only. It does not establish
the semantic validity of the skipped TEST value and never deserializes it.
"""
import json
import math
from pathlib import PurePosixPath


def development_only(body):
    if not isinstance(body,bytes) or len(body)>2_000_000:raise ValueError('Annotation byte budget exceeded')
    text=body.decode('utf-8');n=len(text);i=0;spans={}
    def white(pos):
        while pos<n and text[pos] in ' \t\r\n':pos+=1
        return pos
    def quoted(pos):
        if pos>=n or text[pos]!='"':raise ValueError('Expected quoted key')
        pos+=1
        while pos<n:
            if text[pos]=='\\':pos+=2
            elif text[pos]=='"':return pos+1
            else:pos+=1
        raise ValueError('Unclosed string')
    i=white(i)
    if i>=n or text[i]!='{':raise ValueError('Expected top-level object')
    i=white(i+1)
    while i<n and text[i]!='}':
        end=quoted(i);key=json.loads(text[i:end]);i=white(end)
        if key not in ('train','valid','test') or key in spans:raise ValueError('Unknown or repeated publisher partition')
        if i>=n or text[i]!=':':raise ValueError('Missing colon')
        i=white(i+1);start=i
        if i>=n or text[i]!='{':raise ValueError('Each partition must be an object')
        stack=['}'];i+=1
        while stack and i<n:
            c=text[i]
            if c=='"':i=quoted(i);continue
            if c in '{[':
                stack.append('}' if c=='{' else ']')
                if len(stack)>128:raise ValueError('Nesting budget exceeded')
            elif c in '}]':
                if c!=stack.pop():raise ValueError('Mismatched partition structure')
            i+=1
        if stack:raise ValueError('Truncated partition')
        spans[key]=(start,i);i=white(i)
        if i<n and text[i]==',':
            i=white(i+1)
            if i>=n or text[i]=='}':raise ValueError('Trailing comma')
        elif i>=n or text[i]!='}':raise ValueError('Missing partition separator')
    if i>=n or text[i]!='}' or white(i+1)!=n or set(spans)!=set(('train','valid','test')):raise ValueError('Incomplete top-level partitions or trailing data')
    return {k:json.loads(text[s:e]) for k,(s,e) in spans.items() if k!='test'}


def validate_development(partitions,archive_names):
    if set(partitions)!=set(('train','valid')):raise ValueError('Only development partitions admitted')
    seen=set();summary={}
    for role,data in partitions.items():
        if set(data)!=set(('file_names','rois_list','occupancy_list')):raise ValueError('Unknown annotation schema')
        names,regions,labels=(data[k] for k in ('file_names','rois_list','occupancy_list'))
        if not names or len(names)!=len(regions) or len(names)!=len(labels):raise ValueError('Unaligned image lists')
        occupied=0;spaces=0;min_coordinate=math.inf;max_coordinate=-math.inf
        for name,rois,ys in zip(names,regions,labels):
            if not isinstance(name,str) or PurePosixPath(name).name!=name or '\\' in name or not name.lower().endswith('.jpg'):raise ValueError('Unsafe or unexpected image name')
            if name in seen or 'images/'+name not in archive_names:raise ValueError('Duplicate, cross-partition or missing image')
            seen.add(name)
            if not rois or len(rois)!=len(ys):raise ValueError('Unaligned space labels')
            for polygon,y in zip(rois,ys):
                if type(y) not in (int,bool) or y not in (0,1):raise ValueError('Occupancy must be explicit binary integer or publisher boolean')
                if len(polygon)!=4 or any(len(p)!=2 for p in polygon):raise ValueError('Expected four two-dimensional ROI corners')
                coords=[c for p in polygon for c in p]
                if any(type(c) not in (int,float) or not math.isfinite(c) or c<0 for c in coords):raise ValueError('Invalid ROI coordinates')
                area=abs(sum(polygon[j][0]*polygon[(j+1)%4][1]-polygon[(j+1)%4][0]*polygon[j][1] for j in range(4)))/2
                if area<=0:raise ValueError('Degenerate ROI')
                min_coordinate=min(min_coordinate,*coords);max_coordinate=max(max_coordinate,*coords);spaces+=1;occupied+=y
        summary[role]=dict(images=len(names),spaces=spaces,occupied_label1=occupied,vacant_label0=spaces-occupied,min_coordinate=min_coordinate,max_coordinate=max_coordinate)
    return summary
