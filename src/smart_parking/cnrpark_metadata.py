"""Label-blind CNR-EXT metadata validation and global-date partitions.

No PIL/torch/image decompression. A public database licence is recorded separately
from permission to use its individual image contents for a model experiment.
"""
import csv,re
from datetime import date
from pathlib import PurePosixPath
COLLECTION='cnrpark-ext-official'
FIELDS={'camera','datetime','day','hour','image_url','minute','month','occupancy','slot_id','weather','year','occupant_changed'}
WEATHER={'S':'SUNNY','O':'OVERCAST','R':'RAINY'}
def canonical_row(row,source_row):
    camera=row['camera']
    if camera in ('A','B'):return None
    if camera not in {f'{i:02}' for i in range(1,10)}:raise ValueError('Unknown CNR camera')
    day=date(int(row['year']),int(row['month']),int(row['day'])).isoformat()
    hour=int(row['hour']);minute=int(row['minute']);slot=row['slot_id'];weather=row['weather']
    if not 0<=hour<24 or not 0<=minute<60 or weather not in WEATHER:raise ValueError('Invalid calendar/weather')
    if not re.fullmatch(r'[1-9]\d*',slot):raise ValueError('Invalid slot identity')
    clock=f'{hour:02}.{minute:02}'
    if row['datetime']!=day+'_'+clock:raise ValueError('Conflicting source datetime fields')
    expected=f'CNR-EXT/PATCHES/{WEATHER[weather]}/{day}/camera{int(camera)}/{weather}_{day}_{clock}_C{camera}_{slot}.jpg'
    path=PurePosixPath(row['image_url'])
    if path.is_absolute() or '..' in path.parts or row['image_url']!=expected:raise ValueError('Unsafe or inconsistent image metadata path')
    return dict(source_id='SRC-DS-002',collection=COLLECTION,source_row=source_row,camera_id='cnrpark-ext:'+camera,
        capture_date=day,capture_clock=clock,slot_id=slot,weather=weather,archive_member=expected.removeprefix('CNR-EXT/'))
def read_metadata(path):
    rows=[];rejected=[];base=0;seen=set()
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if set(reader.fieldnames or [])!=FIELDS:raise ValueError('Unexpected official CSV schema')
        for index,row in enumerate(reader,2):
            try:
                record=canonical_row(row,index)
                if record is None:base+=1;continue
                key=record['archive_member']
                if key in seen:raise ValueError('Duplicate image record')
                seen.add(key);rows.append(record)
            except (ValueError,KeyError,TypeError) as error:rejected.append(dict(source_row=index,error=str(error)))
    return rows,rejected,base
def global_date_split(rows):
    days=sorted({r['capture_date'] for r in rows})
    if len(days)<10:raise ValueError('At least10global dates required')
    a=int(len(days)*.6);b=int(len(days)*.8)
    mapping={day:('train' if i<a else 'validation' if i<b else 'reserved_final') for i,day in enumerate(days)}
    return [dict(r,split=mapping[r['capture_date']]) for r in rows],mapping
