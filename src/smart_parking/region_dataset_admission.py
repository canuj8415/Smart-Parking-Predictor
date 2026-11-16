"""Byte-only split qualification before any selected image/annotation decode."""
import random
from collections import defaultdict


def group_key(camera,day):return camera+'|'+day


def select_frames(pairs,groups,seed=168,train_per_group=4,development_per_group=2):
    roles={group_key(g['camera_id'],g['capture_date']):g['status'] for g in groups};bygroup=defaultdict(list)
    for pair in pairs:bygroup[group_key(pair['camera_id'],pair['capture_date'])].append(pair)
    rng=random.Random(seed);selected=[]
    for key in sorted(bygroup):
        status=roles[key]
        if status not in {'training_exposed','development_exposed'}:continue
        role='train' if status=='training_exposed' else 'development';limit=train_per_group if role=='train' else development_per_group
        rows=sorted(bygroup[key],key=lambda r:r['image_member']);rows=rng.sample(rows,min(limit,len(rows)))
        selected.extend(dict(row,role=role,group_id=key) for row in sorted(rows,key=lambda r:r['image_member']))
    return [dict(row,index=i) for i,row in enumerate(selected)]


def qualify_hashes(records,selected,roles):
    parent={};byhash=defaultdict(set);record_index={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def join(a,b):
        x,y=find(a),find(b)
        if x!=y:parent[max(x,y)]=min(x,y)
    for record in records:
        key=record['member'].casefold()
        if key in record_index:raise ValueError('Duplicate archive member hash record')
        record_index[key]=record;byhash[record['sha256']].add(record['group_id']);find(record['group_id'])
    for groups in byhash.values():
        ordered=sorted(groups)
        for other in ordered[1:]:join(ordered[0],other)
    protected_roots={find(g) for g in parent if roles.get(g) not in {'training_exposed','development_exposed'}}
    dev_roots={find(g) for g,status in roles.items() if status=='development_exposed' and g in parent}
    accepted=[];rejected=[];seen=set()
    for frame in selected:
        record=record_index[frame['image_member'].casefold()];root=find(frame['group_id']);reason=None
        if record['group_id']!=frame['group_id']:raise ValueError('Selected member/group hash mismatch')
        if root in protected_roots:reason='Whole-group byte alias to closed/quarantined/unindexed metadata'
        elif frame['role']=='train' and root in dev_roots:reason='Whole-group byte alias to development group'
        elif (frame['role'],record['sha256']) in seen:reason='Duplicate selected JPEG bytes within role'
        if reason:rejected.append(dict(frame,reason=reason,image_sha256=record['sha256']))
        else:seen.add((frame['role'],record['sha256']));accepted.append(dict(frame,image_sha256=record['sha256']))
    return dict(accepted=accepted,rejected=rejected,jpeg_records=len(records),unique_jpeg_hashes=len(byhash),cross_group_hash_edges=sum(len(g)>1 for g in byhash.values()),
                policy='Closed/quarantined/unknown groups protect entire hash-connected components;TRAIN components touching DEV are excluded. No replacement sampling or final admission.')
