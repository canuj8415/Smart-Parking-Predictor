"""Real-data acquisition and preparation. No training, resampling or invented times."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

URL = 'https://archive.ics.uci.edu/static/public/482/parking+birmingham.zip'
ARCHIVE_HASH = 'AF7D1B1B5BB85AA6CBF0E5212D06E76470A7FBE6C42C86EA01BF4C36D3A56AD8'
CSV_HASH = 'F1E28B9C697769A1A05CD20148241B60B1A73FEE4907611163EFC6FD9D12770A'
RAW_FIELDS = ['SystemCodeNumber', 'Capacity', 'Occupancy', 'LastUpdated']
FIELDS = ['source_id', 'source_row', 'car_park_id', 'timestamp', 'capture_date', 'capacity', 'occupancy', 'available', 'split']

def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()

def acquire(root, allow_download=False):
    folder = Path(root) / 'data/raw/uci_parking_birmingham'
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / 'parking-birmingham.zip'
    if not archive.exists():
        if not allow_download:
            raise FileNotFoundError('Run scripts/acquire_birmingham.py online first.')
        partial = archive.with_suffix('.zip.partial')
        with urllib.request.urlopen(URL, timeout=90) as response, partial.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if sha256(partial) != ARCHIVE_HASH:
            raise ValueError('Archive version changed; inspect before changing the hash pin.')
        partial.replace(archive)
    if sha256(archive) != ARCHIVE_HASH:
        raise ValueError('Archive checksum mismatch.')
    with zipfile.ZipFile(archive) as zipped:
        if zipped.namelist() != ['dataset.csv'] or zipped.testzip() is not None:
            raise ValueError('Unexpected archive contents or failed ZIP integrity check.')
        destination = folder / 'dataset.csv'
        if not destination.exists():
            destination.write_bytes(zipped.read('dataset.csv'))
    if sha256(destination) != CSV_HASH:
        raise ValueError('CSV checksum mismatch.')
    return destination

def clean_rows(rows, source_id):
    groups, rejected, invalid = defaultdict(list), [], 0
    for line, raw in enumerate(rows, 2):
        try:
            if not raw['SystemCodeNumber'].strip():
                raise ValueError('missing_car_park')
            capacity, occupancy = int(raw['Capacity']), int(raw['Occupancy'])
            time = datetime.strptime(raw['LastUpdated'], '%Y-%m-%d %H:%M:%S')
            if capacity <= 0 or not 0 <= occupancy <= capacity:
                raise ValueError('invalid_capacity_or_occupancy_bounds')
        except (ValueError, TypeError, KeyError) as error:
            rejected.append(dict(source_id=source_id, source_row=line, **raw, reason=str(error)))
            invalid += 1
            continue
        groups[(raw['SystemCodeNumber'], raw['LastUpdated'])].append(dict(
            source_id=source_id, source_row=line, car_park_id=raw['SystemCodeNumber'],
            timestamp=raw['LastUpdated'], capture_date=time.date().isoformat(),
            capacity=capacity, occupancy=occupancy, available=capacity-occupancy))
    accepted, duplicate_groups, duplicate_rows, conflicts = [], 0, 0, 0
    for records in groups.values():
        if len({(r['capacity'], r['occupancy']) for r in records}) > 1:
            conflicts += 1
            removed, reason = records, 'conflicting_duplicate_key'
        else:
            accepted.append(records[0])
            removed, reason = records[1:], 'identical_duplicate_key_and_values'
            duplicate_rows += len(removed)
            duplicate_groups += bool(removed)
        rejected.extend(dict(source_id=source_id, source_row=r['source_row'],
                             **rows[r['source_row']-2], reason=reason) for r in removed)
    return (sorted(accepted, key=lambda r: (r['timestamp'], r['car_park_id'], r['source_row'])),
            sorted(rejected, key=lambda r: r['source_row']),
            dict(invalid_rows=invalid, identical_duplicate_groups=duplicate_groups,
                 identical_duplicate_rows_removed=duplicate_rows, conflicting_duplicate_groups=conflicts))

def assign_splits(rows, train_fraction=.7, validation_fraction=.15):
    if not (0 < train_fraction < 1 and 0 < validation_fraction < 1 and train_fraction+validation_fraction < 1):
        raise ValueError('Invalid split fractions.')
    dates = sorted({r['capture_date'] for r in rows})
    ntrain, nval = math.floor(len(dates)*train_fraction), math.floor(len(dates)*validation_fraction)
    if min(ntrain, nval, len(dates)-ntrain-nval) < 1:
        raise ValueError('Insufficient dates for three nonempty splits.')
    mapping = {day: 'train' if i < ntrain else 'validation' if i < ntrain+nval else 'test'
               for i, day in enumerate(dates)}
    return [dict(r, split=mapping[r['capture_date']]) for r in rows]

def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)

def prepare(root):
    root = Path(root).resolve()
    config_path = root / 'configs/birmingham_split.json'
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    raw_path = root / config['raw_csv']
    if sha256(raw_path) != config['expected_csv_sha256']:
        raise ValueError('Raw CSV checksum mismatch.')
    with raw_path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != RAW_FIELDS:
            raise ValueError('Unexpected CSV schema.')
        raw = list(reader)
    clean, rejected, quality = clean_rows(raw, config['source_id'])
    prepared = assign_splits(clean, config['train_fraction'], config['validation_fraction'])
    output = (root / config['output_directory']).resolve()
    if not output.is_relative_to((root / 'data/splits').resolve()):
        raise ValueError('Output must stay inside data/splits.')
    if len(prepared)+len(rejected) != len(raw):
        raise ValueError('Row conservation failed.')
    keys = [(r['car_park_id'], r['timestamp']) for r in prepared]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate output key.')
    summaries = []
    for split in ('train', 'validation', 'test'):
        subset = [r for r in prepared if r['split'] == split]
        summaries.append(dict(split=split, rows=len(subset), days=len({r['capture_date'] for r in subset}),
                              first_timestamp=subset[0]['timestamp'], last_timestamp=subset[-1]['timestamp']))
    if not (summaries[0]['last_timestamp'] < summaries[1]['first_timestamp'] and
            summaries[1]['last_timestamp'] < summaries[2]['first_timestamp']):
        raise ValueError('Chronological split overlap.')
    parks, intervals, park_summary = defaultdict(list), [], []
    for row in prepared:
        parks[row['car_park_id']].append(row)
    for name, records in sorted(parks.items()):
        times = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S') for r in records]
        gaps = [(b-a).total_seconds()/60 for a,b in zip(times,times[1:])]
        intervals.extend(gaps)
        counts = Counter(r['split'] for r in records)
        park_summary.append(dict(car_park_id=name, rows=len(records),
             capacity=';'.join(map(str,sorted({r['capacity'] for r in records}))),
             **{f'{s}_rows': counts[s] for s in ('train','validation','test')},
             gaps_over_45_minutes=sum(g > config['gap_warning_minutes'] for g in gaps)))
    intervals.sort()
    summary = dict(split_id=config['split_id'], source_id=config['source_id'],
         input_sha256=sha256(raw_path), config_sha256=sha256(config_path),
         preparation_script_sha256=sha256(Path(__file__)), raw_rows=len(raw),
         accepted_rows=len(prepared), quarantine_rows=len(rejected), **quality,
         car_parks=len(parks), capture_days=len({r['capture_date'] for r in prepared}),
         timezone=config['timezone'], resampling='none', windows_created=0,
         interval_minutes=dict(min=intervals[0], median=intervals[(len(intervals)-1)//2],
                               p95=intervals[math.floor((len(intervals)-1)*.95)], max=intervals[-1]),
         checks=dict(row_conservation='pass', duplicate_keys='none', global_day_overlap='none',
                     valid_count_bounds='pass', chronological_boundaries='pass'),
         splits=summaries, car_park_coverage=park_summary,
         limitations=['Source timezone unspecified; no UTC conversion',
                      'Irregular/overnight gaps; no sequence-window eligibility established',
                      'Potential physical overlap across entities; never sum capacities',
                      'Some car parks lack validation/test coverage', 'No model trained or evaluated'])
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output/'manifest.csv', prepared, FIELDS)
    for split in ('train','validation','test'):
        write_csv(output/f'{split}.csv', [r for r in prepared if r['split']==split], FIELDS)
    write_csv(output/'quarantine.csv', rejected, ['source_id','source_row',*RAW_FIELDS,'reason'])
    write_csv(output/'car_park_summary.csv', park_summary, list(park_summary[0]))
    (output/'validation_report.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary
