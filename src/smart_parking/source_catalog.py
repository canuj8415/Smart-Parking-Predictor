"""Append new permanent source identities; reject reuse for another resource."""
import csv
from pathlib import Path

def require_source_identity(path,source_id,resource,source_url):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    matches=[r for r in rows if r['source_id']==source_id]
    if len(matches)!=1 or matches[0]['resource']!=resource or matches[0]['source_url']!=source_url:
        raise ValueError('Register the correct permanent source identity before acquisition')
    return matches[0]

def register_source(path,record):
    path=Path(path)
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    if not record.get('source_id') or not record.get('resource') or not record.get('source_url'):
        raise ValueError('A source needs an ID, resource name and original URL')
    if len({r['source_id'] for r in rows})!=len(rows):raise ValueError('Source registry already contains duplicate IDs')
    existing=[r for r in rows if r['source_id']==record['source_id']]
    if existing:
        if any(existing[0][key]!=record[key] for key in ['resource','source_url']):
            raise ValueError('Permanent source ID already belongs to a different resource')
        return False
    if set(record)-set(fields):raise ValueError('Unknown source-record fields')
    with path.open('a',encoding='utf-8',newline='') as stream:
        csv.DictWriter(stream,fieldnames=fields).writerow({key:record.get(key,'') for key in fields})
    return True
