"""Strict membership parsing for a guarded final callback; no automatic access."""
import csv
from collections import defaultdict
from datetime import datetime


def reserved_groups(source,metadata):
    """Call only inside a durable final claim; parse exactly the pinned row IDs."""
    expected={r['source_row']:r for r in metadata}
    if not expected or len(expected)!=len(metadata):raise ValueError('Empty or duplicate reserved row IDs')
    groups=defaultdict(list);seen=set()
    with source.open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            ident=row['source_row']
            if ident not in expected:continue
            reference=expected[ident]
            if ident in seen or any(row[k]!=reference[k] for k in ['source_id','car_park_id','capture_date','timestamp','split']):
                raise ValueError('Reserved row identity differs from original metadata')
            seen.add(ident)
            if row['split']!='test':raise ValueError('Reserved source row is not assigned to test')
            capacity=int(row['capacity']);occupied=int(row['occupancy']);available=int(row['available'])
            if capacity<=0 or not 0<=occupied<=capacity or available+occupied!=capacity:raise ValueError('Invalid final capacity/occupancy')
            groups[(row['car_park_id'],row['capture_date'],'test',capacity)].append((datetime.fromisoformat(row['timestamp']),occupied,int(ident)))
    if seen!=set(expected):raise ValueError('Some reserved rows are absent from the source manifest')
    return groups
