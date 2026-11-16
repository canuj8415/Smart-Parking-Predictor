"""Durable, overlap-aware claims before a frozen final evaluation reads labels.

A failed/interrupted evaluation consumes its holdout too. Claims are never
released automatically. This module reads manifests/checkpoints, not images.
"""
import hashlib,json,os
from datetime import date,datetime,timezone
from pathlib import Path
from .provenance import ROOT,digest

def reservation_frames(manifest,root=ROOT):
    rows=json.loads(Path(manifest).read_text(encoding='utf-8'))['frames']
    if not rows:raise ValueError('Empty final reservation')
    base=Path(root).resolve();identities=[]
    for row in rows:
        path=(base/row['image']).resolve()
        if not path.is_relative_to(base):raise ValueError('Final frame outside project root')
        identities.append(path.relative_to(base).as_posix().casefold())
    if len(set(identities))!=len(identities):raise ValueError('Duplicate final frame identities')
    for row in rows:
        if not row.get('camera_id') or not row.get('date') or date.fromisoformat(row['date']).isoformat()!=row['date']:
            raise ValueError('Final reservations require camera and capture-date groups')
    return rows,identities

def assert_holdout_closed(manifest,receipt_dir=None,root=ROOT):
    rows,identities=reservation_frames(manifest,root)
    folder=Path(receipt_dir or ROOT/'data/holdout_claims')
    groups={(r['camera_id'].casefold(),r['date']) for r in rows}
    for path in folder.glob('*.claim.json'):
        claim=json.loads(path.read_text(encoding='utf-8'))
        if set(identities)&set(claim['frame_ids']):raise ValueError('Final reservation overlaps an already started evaluation: '+path.name)
        if groups&{tuple(g) for g in claim.get('source_groups',[])}:raise ValueError('Final camera/date overlaps an already started evaluation: '+path.name)
    return rows

def evaluate_final_once(manifest,selection,checkpoint,run_id,evaluate,*,expected_manifest_sha256,receipt_dir=None,root=ROOT):
    """Call evaluate(rows) only after validating selection and flushing a claim."""
    manifest=Path(manifest);checkpoint=Path(checkpoint)
    if digest(manifest)!=expected_manifest_sha256:raise ValueError('Final reservation checksum changed')
    chosen=json.loads(Path(selection).read_text(encoding='utf-8'))
    if chosen.get('validation_gate_passed') is not True:raise ValueError('Final evaluation requires a passed frozen validation gate')
    checkpoint_sha=digest(checkpoint)
    if checkpoint_sha!=chosen['checkpoint_sha256']:raise ValueError('Selected checkpoint checksum changed')
    folder=Path(receipt_dir or ROOT/'data/holdout_claims');folder.mkdir(parents=True,exist_ok=True)
    lock=folder/'claim.lock';descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(descriptor)
    try:
        rows=assert_holdout_closed(manifest,folder,root);_,identities=reservation_frames(manifest,root)
        identity=hashlib.sha256('\n'.join(sorted(identities)).encode()).hexdigest()
        marker=folder/(identity+'.claim.json')
        claim=dict(run_id=run_id,started_at=datetime.now(timezone.utc).isoformat(),status='started; holdout consumed even if evaluation fails',manifest=str(manifest),manifest_sha256=expected_manifest_sha256,checkpoint_sha256=checkpoint_sha,frame_ids=identities,
            source_groups=sorted({(r['camera_id'].casefold(),r['date']) for r in rows}))
        # Exclusive create + fsync happens BEFORE the callback can open an image.
        with marker.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(claim,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    finally:lock.unlink(missing_ok=True)
    try:
        result=evaluate(rows)
    except BaseException as error:
        outcome=dict(status='failed; original claim remains consumed',error=type(error).__name__,detail=str(error),finished_at=datetime.now(timezone.utc).isoformat())
        marker.with_suffix('.outcome.json').write_text(json.dumps(outcome,indent=2),encoding='utf-8')
        raise
    marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='completed; holdout consumed',finished_at=datetime.now(timezone.utc).isoformat()),indent=2),encoding='utf-8')
    return result
