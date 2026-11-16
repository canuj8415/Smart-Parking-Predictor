"""One-use canonical CNR whole-date claims; aliases cannot free consumed dates."""
import csv,hashlib,json,os
from datetime import date,datetime,timezone
from pathlib import Path
from .cnrpark_metadata import COLLECTION
from .provenance import digest
def reservation(path,root):
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    if value['collection']!=COLLECTION:raise ValueError('Unsupported canonical collection')
    days=value['reserved_dates']
    if not days or len(set(days))!=len(days) or any(date.fromisoformat(d).isoformat()!=d for d in days):raise ValueError('Invalid reserved dates')
    root=Path(root).resolve()
    for key in ['parent_manifest','source_metadata','source_archive']:
        source=(root/value[key]).resolve()
        if not source.is_relative_to(root) or digest(source)!=value[key+'_sha256']:raise ValueError('Reserved source changed/outside project')
    with (root/value['parent_manifest']).open(encoding='utf-8',newline='') as stream:
        rows=[r for r in csv.DictReader(stream) if r['split']=='reserved_final']
    if len(rows)!=value['reserved_rows'] or {r['capture_date'] for r in rows}!=set(days) or any(r['collection']!=COLLECTION for r in rows):
        raise ValueError('Reservation does not match complete parent final-date membership')
    return value,{(COLLECTION,day) for day in days}
def assert_closed(path,root,receipts):
    value,keys=reservation(path,root)
    for claim in Path(receipts).glob('*.claim.json'):
        prior=json.loads(claim.read_text(encoding='utf-8'))
        if keys & {tuple(k) for k in prior['canonical_date_groups']}:raise ValueError('Final canonical date already consumed')
    return value
def evaluate_once(path,selection,protocol,checkpoint,run_id,evaluate,*,root,receipts,expected_reservation_sha256,expected_protocol_sha256):
    if digest(path)!=expected_reservation_sha256 or digest(protocol)!=expected_protocol_sha256:raise ValueError('Frozen reservation/protocol changed')
    chosen=json.loads(Path(selection).read_text(encoding='utf-8'));config=json.loads(Path(protocol).read_text(encoding='utf-8'));weight=digest(checkpoint)
    for value in [chosen,config]:
        if value['reservation_sha256']!=expected_reservation_sha256 or value['checkpoint_sha256']!=weight:raise ValueError('Selection binding mismatch')
    if chosen.get('validation_gate_passed') is not True or chosen['protocol_sha256']!=expected_protocol_sha256:raise ValueError('A passed frozen development gate is required')
    if config.get('image_analysis_authorized') is not True:raise ValueError('Image-content use has not been qualified')
    folder=Path(receipts);folder.mkdir(parents=True,exist_ok=True);lock=folder/'claim.lock'
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(descriptor)
    try:
        value=assert_closed(path,root,folder);_,keys=reservation(path,root)
        marker=folder/(hashlib.sha256(json.dumps(sorted(keys)).encode()).hexdigest()+'.claim.json')
        record=dict(run_id=run_id,started_at=datetime.now(timezone.utc).isoformat(),canonical_date_groups=sorted(keys),
            reservation_sha256=expected_reservation_sha256,protocol_sha256=expected_protocol_sha256,checkpoint_sha256=weight,
            status='Consumed before callback;failure/cancellation does not reopen dates')
        with marker.open('x',encoding='utf-8') as stream:json.dump(record,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    finally:lock.unlink(missing_ok=True)
    try:
        result=evaluate(value)
        if digest(path)!=expected_reservation_sha256 or digest(protocol)!=expected_protocol_sha256 or digest(checkpoint)!=weight:raise ValueError('Frozen inputs changed during evaluation')
        reservation(path,root)
    except BaseException as error:
        marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='failed;dates remain consumed',error=type(error).__name__)),encoding='utf-8');raise
    marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='completed;dates consumed')),encoding='utf-8');return result
