"""Durable whole-source/date claims before any final forecast outcome is parsed."""
import hashlib,json,os
from datetime import date,datetime,timezone
from pathlib import Path
from .provenance import ROOT,digest


def reservation_dates(manifest,root=ROOT):
    reservation=json.loads(Path(manifest).read_text(encoding='utf-8'))
    source=reservation['source_id'];days=reservation['reserved_dates'];rows=reservation['metadata']
    if not source or not days or len(days)!=len(set(days)) or any(date.fromisoformat(d).isoformat()!=d for d in days):
        raise ValueError('Invalid source/date reservation')
    if len(rows)!=reservation['reserved_rows'] or len({r['source_row'] for r in rows})!=len(rows):
        raise ValueError('Final row membership is empty, duplicated or inconsistent')
    if not rows or {r['capture_date'] for r in rows}!=set(days):raise ValueError('Final dates and row metadata differ')
    for r in rows:
        if r['source_id']!=source or r['split']!='test' or r['timestamp'][:10]!=r['capture_date']:
            raise ValueError('Final row metadata has inconsistent source/date/split')
    base=Path(root).resolve();path=(base/reservation['source_manifest']).resolve()
    if not path.is_relative_to(base):raise ValueError('Source manifest is outside the project')
    if digest(path)!=reservation['source_manifest_sha256']:raise ValueError('Reserved source manifest changed')
    return reservation,sorted([[source,d] for d in days])


def assert_forecast_dates_closed(manifest,receipt_dir=None,root=ROOT):
    reservation,keys=reservation_dates(manifest,root)
    folder=Path(receipt_dir or Path(root)/'data/forecast_holdout_claims')
    requested={tuple(k) for k in keys}
    for path in folder.glob('*.claim.json'):
        claimed=json.loads(path.read_text(encoding='utf-8'))
        if requested & {tuple(k) for k in claimed['source_dates']}:
            raise ValueError('Final source/date overlaps an already started evaluation: '+path.name)
    return reservation


def evaluate_forecast_once(manifest,selection,checkpoint,protocol,run_id,evaluate,*,expected_manifest_sha256,expected_protocol_sha256,receipt_dir=None,root=ROOT):
    """Validate bindings, fsync an exclusive claim, then call evaluate(metadata)."""
    manifest=Path(manifest);checkpoint=Path(checkpoint);protocol=Path(protocol)
    if digest(manifest)!=expected_manifest_sha256:raise ValueError('Final reservation checksum changed')
    if digest(protocol)!=expected_protocol_sha256:raise ValueError('Final protocol checksum changed')
    chosen=json.loads(Path(selection).read_text(encoding='utf-8'))
    if chosen.get('validation_gate_passed') is not True:raise ValueError('A passed frozen validation gate is required')
    checkpoint_sha=digest(checkpoint)
    if checkpoint_sha!=chosen['checkpoint_sha256']:raise ValueError('Selected checkpoint changed')
    if chosen['final_protocol_sha256']!=expected_protocol_sha256:raise ValueError('Selection does not bind this final protocol')
    if chosen['reservation_sha256']!=expected_manifest_sha256:raise ValueError('Selection does not bind this reservation')
    config=json.loads(protocol.read_text(encoding='utf-8'))
    if config['checkpoint_sha256']!=checkpoint_sha or config['reservation_sha256']!=expected_manifest_sha256:
        raise ValueError('Final protocol does not bind the selected model/reservation')
    folder=Path(receipt_dir or Path(root)/'data/forecast_holdout_claims');folder.mkdir(parents=True,exist_ok=True)
    lock=folder/'claim.lock';descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(descriptor)
    try:
        reservation=assert_forecast_dates_closed(manifest,folder,root);_,keys=reservation_dates(manifest,root)
        identity=hashlib.sha256(json.dumps(keys,separators=(',',':')).encode()).hexdigest()
        marker=folder/(identity+'.claim.json')
        claim=dict(run_id=run_id,started_at=datetime.now(timezone.utc).isoformat(),status='started; consumed even on failure',
            manifest_sha256=expected_manifest_sha256,checkpoint_sha256=checkpoint_sha,protocol_sha256=expected_protocol_sha256,
            source_manifest_sha256=reservation['source_manifest_sha256'],source_dates=keys)
        with marker.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(claim,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    finally:lock.unlink(missing_ok=True)
    try:
        result=evaluate(reservation['metadata'])
        # A mutation invalidates the attempt, but never releases its consumed dates.
        if digest(checkpoint)!=checkpoint_sha or digest(protocol)!=expected_protocol_sha256 or digest(manifest)!=expected_manifest_sha256:
            raise ValueError('Frozen model/protocol/reservation changed during evaluation')
        reservation_dates(manifest,root)
    except BaseException as error:
        marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='failed; dates remain consumed',error=type(error).__name__,detail=str(error),finished_at=datetime.now(timezone.utc).isoformat()),indent=2),encoding='utf-8')
        raise
    marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='completed; dates consumed',finished_at=datetime.now(timezone.utc).isoformat()),indent=2),encoding='utf-8')
    return result
