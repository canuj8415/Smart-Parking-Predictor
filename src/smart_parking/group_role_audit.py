"""Conservative metadata-only recheck of previously provisional date groups."""
from datetime import date


def identity(camera,day):
    if not isinstance(camera,str) or not camera.strip():raise ValueError('Canonical camera ID required')
    if not isinstance(day,str) or date.fromisoformat(day).isoformat()!=day:raise ValueError('Canonical capture date required')
    return camera.strip().casefold(),day


def audit_groups(candidates,development_rows,claims):
    groups=[identity(r['camera_id'],r['capture_date']) for r in candidates]
    if len(groups)!=len(set(groups)):raise ValueError('Duplicate provisional group')
    development={identity(r['camera_id'],r['date']) for r in development_rows}
    consumed={}
    for claim in claims:
        if not claim.get('run_id') or not claim.get('source_groups'):raise ValueError('Complete durable claim metadata required')
        for camera,day in claim['source_groups']:consumed.setdefault(identity(camera,day),set()).add(claim['run_id'])
    rows=[]
    for camera,day in groups:
        used=sorted(consumed.get((camera,day),set()))
        status='consumed_final' if used else ('development_exposed' if (camera,day) in development else 'not_accounted_for')
        rows.append(dict(camera_id=camera,capture_date=day,status=status,claim_runs=used,development_exposed=(camera,day) in development))
    return dict(groups=rows,provisional_candidates=len(rows),development_exposed=sum(r['status']=='development_exposed' for r in rows),
        consumed_final=sum(r['status']=='consumed_final' for r in rows),not_accounted_for=sum(r['status']=='not_accounted_for' for r in rows),
        newly_qualified_final_groups=0,qualification_policy='Unaccounted metadata is NOT automatically a qualified final set;source/lineage/leakage/rights still require admission')
