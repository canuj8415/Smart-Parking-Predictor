"""Authorized Singapore live feed with immutable snapshots and explicit freshness."""
import csv
import json
import urllib.request
from urllib.error import URLError
from datetime import datetime,timezone,timedelta
from .provenance import ROOT,receipt

URL='https://api.data.gov.sg/v1/transport/carpark-availability'
SOURCE_ID='SRC-LIVE-001'

def _observation_key(park,lot,observed):
    at=datetime.fromisoformat(observed)
    if at.tzinfo is None:at=at.replace(tzinfo=timezone(timedelta(hours=8)))
    return park,lot,at.astimezone(timezone.utc).isoformat()


def _count(value):
    # Booleans/floats must not silently become integer parking counts.
    if isinstance(value,bool) or not isinstance(value,(str,int)):
        raise ValueError('Parking counts must be integer values')
    try:return int(value)
    except (ValueError,TypeError) as error:raise ValueError('Parking counts must be integer values') from error


def parse_feed(payload):
    if not isinstance(payload,dict):raise ValueError('Live feed must contain a JSON object')
    items=payload.get('items',[])
    if not items:raise ValueError('Live feed contains no timestamped items')
    rows=[];seen={}
    for item in items:
        feed_time=item['timestamp'];datetime.fromisoformat(feed_time)
        for park in item.get('carpark_data',[]):
            park_id=park['carpark_number']
            if not isinstance(park_id,str) or not park_id.strip():raise ValueError('Missing car-park identity')
            updated=park.get('update_datetime',feed_time)
            datetime.fromisoformat(updated)
            for info in park.get('carpark_info',[]):
                lot=info['lot_type']
                if not isinstance(lot,str) or not lot.strip():raise ValueError('Missing lot-type identity')
                capacity=_count(info['total_lots']);available=_count(info['lots_available'])
                if capacity<=0 or not 0<=available<=capacity:continue
                key=_observation_key(park_id,lot,updated);counts=(capacity,available)
                if key in seen:
                    if seen[key]!=counts:raise ValueError('Conflicting duplicate parking observation')
                    continue
                seen[key]=counts
                rows.append(dict(source_id=SOURCE_ID,car_park_id=park_id,
                    lot_type=lot,capacity=capacity,available=available,occupied=capacity-available,
                    observed_at=updated,feed_timestamp=feed_time))
    if not rows:raise ValueError('No valid capacity/availability observations')
    return rows

def latest_snapshot():
    folder=ROOT/'data/raw/singapore_live'
    files=sorted(folder.glob('*.json')) if folder.exists() else []
    if not files:raise FileNotFoundError('No saved live data; press Refresh while connected.')
    return files[-1]

def get_live(refresh=False):
    if not refresh:
        path=latest_snapshot()
    else:
        try:
            previous=latest_snapshot()
            # Respect the publisher's one-minute polling recommendation.
            age=datetime.now(timezone.utc).timestamp()-previous.stat().st_mtime
            if age<60:return parse_feed(json.loads(previous.read_text(encoding='utf-8'))),dict(cached=True,path=str(previous),reason='One-minute cache')
        except FileNotFoundError:pass
        request=urllib.request.Request(URL,headers={'User-Agent':'SmartParkingPBL/0.2'})
        try:
            with urllib.request.urlopen(request,timeout=20) as response:
                raw=response.read(10*1024*1024+1)
                if len(raw)>10*1024*1024:raise ValueError('Feed exceeds size limit')
        except (URLError,TimeoutError) as error:
            raise ConnectionError('Could not reach the official Singapore feed. Check your internet connection, or choose Load saved snapshot to view previously recorded data.') from error
        try:
            payload=json.loads(raw);rows=parse_feed(payload)
        except (ValueError,TypeError,KeyError) as error:
            # Retain rejected public bytes as evidence without making them the
            # latest usable snapshot or appending them to normalized history.
            rejected=ROOT/'data/raw/singapore_live_rejected';rejected.mkdir(parents=True,exist_ok=True)
            path=rejected/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
            with path.open('xb') as stream:stream.write(raw)
            receipt(SOURCE_ID,path,URL,'Rejected official payload; excluded from app/history/prospective scoring',
                license='Singapore Open Data Licence 1.0',validation_error=str(error))
            raise ValueError('Official feed failed validation; rejected bytes saved separately. Load a saved snapshot to continue.') from error
        folder=ROOT/'data/raw/singapore_live';folder.mkdir(parents=True,exist_ok=True)
        name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'
        path=folder/name
        with path.open('xb') as stream:stream.write(raw)
        receipt(SOURCE_ID,path,URL,'Authorized real public car-park snapshot',license='Singapore Open Data Licence 1.0',
            provider_timestamp=payload['items'][0]['timestamp'])
        history=ROOT/'data/processed/singapore_live_observations.csv';history.parent.mkdir(parents=True,exist_ok=True)
        existing=set()
        if history.exists():
            with history.open(encoding='utf-8',newline='') as stream:
                existing={_observation_key(r['car_park_id'],r['lot_type'],r['observed_at']) for r in csv.DictReader(stream)}
        additions=[r for r in rows if _observation_key(r['car_park_id'],r['lot_type'],r['observed_at']) not in existing]
        new=not history.exists()
        with history.open('a',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            if new:writer.writeheader()
            writer.writerows(additions)
    payload=json.loads(path.read_text(encoding='utf-8'));rows=parse_feed(payload)
    return rows,dict(cached=not refresh,path=str(path),provider_timestamp=payload['items'][0]['timestamp'])
