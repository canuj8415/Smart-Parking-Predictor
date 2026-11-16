"""Select an already packaged pre-reservation feed snapshot using metadata only."""
from datetime import datetime,timezone
import json
from pathlib import Path
from .provenance import digest


def _utc(value):
    stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
    if stamp.tzinfo is None:raise ValueError('Timezone-aware snapshot evidence required')
    return stamp.astimezone(timezone.utc)


def select_snapshot(root,manifest,scope,reservation,receipts):
    root=Path(root).resolve();start=_utc(reservation['final_origin_start'])
    candidates=[r for r in manifest['files'] if r['path'].startswith('data/raw/singapore_live/')]
    if len(candidates)!=1:raise ValueError('Exactly one prior immutable demo snapshot required')
    row=candidates[0];path=(root/row['path']).resolve();base=(root/'data/raw/singapore_live').resolve()
    if path.parent!=base or path.suffix!='.json' or row.get('source_id')!='SRC-LIVE-001':raise ValueError('Invalid prior snapshot identity')
    if row['path']!=scope['cached_live_snapshot'] or row['sha256']!=scope['cached_live_sha256'] or digest(path)!=row['sha256']:
        raise ValueError('Prior manifest/scope/snapshot hash changed')
    matches=[r for r in receipts if r.get('source_id')=='SRC-LIVE-001' and r.get('local_path')==row['path'] and r.get('sha256')==row['sha256']]
    if len(matches)!=1:raise ValueError('Unique original snapshot acquisition receipt required')
    receipt=matches[0];received=_utc(receipt['accessed_at']);provider=_utc(receipt['provider_timestamp'])
    if not provider<=received<start or not provider<start:raise ValueError('Snapshot overlaps or arrives after protected future origins')
    if _utc(scope['cached_live_provider_timestamp'])!=provider:raise ValueError('Saved provider timestamp differs from receipt')
    return dict(path=row['path'],sha256=row['sha256'],provider_timestamp=receipt['provider_timestamp'],received_at=receipt['accessed_at'],
                protected_origin_start=start.isoformat(),selection='Exact prior-demo snapshot,receipt and provider strictly before reserved origins',raw_body_decoded_during_selection=False)
