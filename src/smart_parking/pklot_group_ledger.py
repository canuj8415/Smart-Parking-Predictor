"""Conservative whole-archive metadata roles, never automatic final admission."""
from collections import Counter,defaultdict
from datetime import date
from pathlib import PurePosixPath

ALIASES={'pucpr':'pucpr','parking2':'pucpr','ufpr04':'ufpr04','parking1a':'ufpr04','ufpr05':'ufpr05','parking1b':'ufpr05'}

def identity(camera,day):
    if not isinstance(camera,str) or camera.strip().casefold() not in ALIASES:raise ValueError('Unknown camera alias')
    if not isinstance(day,str) or date.fromisoformat(day).isoformat()!=day:raise ValueError('Canonical date required')
    return ALIASES[camera.strip().casefold()],day

def member_identity(value):
    if not isinstance(value,str):raise ValueError('Member path required')
    path=PurePosixPath(value.replace('\\','/'));parts=path.parts
    if path.is_absolute() or '..' in parts or any(':' in part for part in parts):raise ValueError('Unsafe member path')
    positions=[i for i,p in enumerate(parts) if p.casefold()=='pklot']
    if not positions or positions[-1]+1>=len(parts):raise ValueError('Missing PKLot camera folder')
    camera=parts[positions[-1]+1];day=path.parent.name
    if path.stem[:10]!=day:raise ValueError('Member date mismatch')
    return identity(camera,day)

def build_ledger(pairs,exposures,claims,historical):
    counts=Counter();members=set();roles=defaultdict(set);references=defaultdict(set);hash_groups=defaultdict(set)
    for row in pairs:
        group=identity(row['camera_id'],row['capture_date'])
        if member_identity(row['image_member'])!=group or member_identity(row['annotation_member'])!=group:raise ValueError('Index/member identity mismatch')
        image=PurePosixPath(row['image_member'].replace('\\','/'));annotation=PurePosixPath(row['annotation_member'].replace('\\','/'))
        if image.suffix.casefold()!='.jpg' or annotation.suffix.casefold()!='.xml' or image.with_suffix('').as_posix().casefold()!=annotation.with_suffix('').as_posix().casefold():raise ValueError('Unsafe or unpaired index row')
        key=image.as_posix().casefold()
        if key in members:raise ValueError('Duplicate index member alias')
        members.add(key);counts[group]+=1
    for row in exposures:
        group=identity(row['camera_id'],row['date'])
        if group not in counts:raise ValueError('Exposure group absent from validated archive index')
        role=row['role'];role={'development':'validation'}.get(role,role)
        if role not in {'train','validation','test'}:raise ValueError('Unrecognized historical role')
        roles[group].add(role);references[group].add((row['source'],role))
        if row.get('image_sha256'):hash_groups[row['image_sha256']].add(group)
    claim_runs=defaultdict(set)
    for claim in claims:
        if not claim.get('run_id') or not claim.get('source_groups'):raise ValueError('Complete claim metadata required')
        for camera,day in claim['source_groups']:
            group=identity(camera,day)
            if group not in counts:raise ValueError('Claim group absent from validated index')
            claim_runs[group].add(claim['run_id'])
    old_refs=defaultdict(set)
    for record in historical:
        for day in record['excluded_dates']:
            for group in counts:
                if group[1]==day:old_refs[group].add(record['path'])
    protected={g for g in counts if claim_runs[g] or 'test' in roles[g]}
    aliases=[];aliased_to_protected=set(protected)
    changed=True
    while changed:
        changed=False
        for groups in hash_groups.values():
            if len(groups)>1 and groups&aliased_to_protected and not groups<=aliased_to_protected:
                aliased_to_protected.update(groups);changed=True
    groups_on_alias_edges=set()
    for sha,groups in sorted(hash_groups.items()):
        if len(groups)>1:
            touches=bool(groups&aliased_to_protected)
            aliases.append(dict(image_sha256=sha,groups=[list(g) for g in sorted(groups)],touches_protected=touches))
            if touches:groups_on_alias_edges.update(groups)
    rows=[]
    for group,n in sorted(counts.items()):
        used=roles[group];old=old_refs[group];claim=sorted(claim_runs[group]);alias=group in groups_on_alias_edges
        if claim:status='consumed_durable_final'
        elif 'test' in used:status='historical_test_protected'
        elif alias:status='byte_alias_to_protected_quarantine'
        elif 'validation' in used:status='development_exposed'
        elif 'train' in used:status='training_exposed'
        elif old:status='historical_metadata_excluded'
        else:status='unaccounted_quarantine'
        conflict=bool(('test' in used or claim) and used&{'train','validation'})
        rows.append(dict(camera_id=group[0],capture_date=group[1],paired_frames=n,status=status,historical_roles=sorted(used),durable_claim_runs=claim,
            role_overlap_with_protected=conflict,byte_alias_to_protected=alias,exposure_references=[dict(path=p,role=r) for p,r in sorted(references[group])],
            historical_exclusion_references=sorted(old),new_training_admitted=False,new_final_admitted=False))
    return dict(groups=rows,paired_frames=sum(counts.values()),camera_date_groups=len(counts),status_counts=dict(Counter(r['status'] for r in rows)),
                durable_consumed_groups=sum(bool(claim_runs[g]) for g in counts),
                historical_test_groups=sum('test' in roles[g] for g in counts),protected_role_overlap_groups=sum(r['role_overlap_with_protected'] for r in rows),
                known_cross_group_byte_aliases=aliases,new_training_groups_admitted=0,new_final_groups_admitted=0,
                qualification='Unaccounted or metadata-excluded is not automatically fresh. Closed historical test roles and durable claims override later train/DEV roles;all known aliases remain protected. No pixels/XML labels read.')
