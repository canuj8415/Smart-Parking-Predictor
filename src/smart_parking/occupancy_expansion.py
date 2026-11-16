"""Metadata-only selection of extra occupancy training data with date isolation."""
from datetime import date
from pathlib import PurePosixPath


def member_name(path):
    text=str(path).replace('\\','/')
    prefixes=('data/raw/pklot_subset/','data/raw/pklot_fresh_v1/',
              'data/raw/pklot_occupancy_expansion_v1/')
    for prefix in prefixes:
        if text.startswith(prefix):
            text=text[len(prefix):]
            break
    parts=PurePosixPath(text).parts
    if len(parts)!=5 or parts[0]!='PKLot' or any(p in {'.','..'} or ':' in p for p in parts):
        raise ValueError('Unrecognized or unsafe original archive identity')
    day=parts[-2]
    if date.fromisoformat(day).isoformat()!=day or parts[-1][:10]!=day:
        raise ValueError('Source calendar/filename date mismatch')
    if PurePosixPath(text).suffix not in {'.jpg','.xml'}:
        raise ValueError('Unsupported source member')
    return '/'.join(parts)


def select_frames(inventory,original,broader,fresh,plan,claims,per_group=4):
    """Keep original train frames; add fixed chronological positions per train date.

    Only previously designated training dates can be added. Earlier test dates,
    consumed image-final dates, new final dates and every proposed validation
    date are excluded globally, even if another camera/path alias is supplied.
    No image pixels, occupancy labels or model outputs are consulted here.
    """
    if not isinstance(per_group,int) or per_group<1:
        raise ValueError('Positive integer sample cap required')
    index={}
    for row in inventory:
        name=member_name(row['image_member'])
        annotation=member_name(row['annotation_member'])
        if PurePosixPath(name).with_suffix('.xml').as_posix()!=annotation:
            raise ValueError('Image/annotation identity mismatch')
        if PurePosixPath(name).parent.name!=row['capture_date']:
            raise ValueError('Inventory capture date mismatch')
        if name in index:raise ValueError('Duplicate original member identity')
        index[name]=row
    protected={r['date'] for r in original if r['split']=='test'}
    protected.update(g['date'] for g in plan['reserved_groups'])
    protected.update(day for claim in claims for _,day in claim.get('source_groups',[]))
    validation=[r for r in original if r['split']=='validation']
    validation += [r for r in broader['frames'] if r['split']=='validation']
    validation += fresh['frames']
    validation_days={r['date'] for r in validation}
    # Reject a bad input plan; do not silently reassign reserved groups.
    if protected & validation_days:raise ValueError('Validation overlaps a protected final date')
    train_days={r['date'] for r in original if r['split']=='train'}
    train_days.update(d for splits in broader['dates'].values() for d in splits['train'])
    if train_days & (protected|validation_days):
        raise ValueError('Training overlaps a validation or protected final date')
    selected={}
    original_train=set()
    def add(row,role,additional=False):
        name=member_name(row['image'])
        if name not in index:raise ValueError('Frame absent from qualified archive inventory')
        meta=index[name]
        if row['camera_id']!=meta['camera_id'] or row['date']!=meta['capture_date']:
            raise ValueError('Canonical source camera/date mismatch')
        if member_name(row['annotation'])!=meta['annotation_member']:
            raise ValueError('Annotation absent from canonical image pair')
        if name in selected:
            if selected[name]['role']!=role:raise ValueError('Same image in two roles')
            return
        selected[name]=dict(camera_id=meta['camera_id'],date=meta['capture_date'],
            image_archive_member=name,annotation_archive_member=meta['annotation_member'],
            image='data/raw/pklot_occupancy_expansion_v1/'+name,
            annotation='data/raw/pklot_occupancy_expansion_v1/'+meta['annotation_member'],
            role=role,additional_training_frame=additional,
            expected_image_bytes=int(meta['image_bytes']),expected_annotation_bytes=int(meta['annotation_bytes']))
    for row in original:
        if row['split']=='train':
            add(row,'train')
            original_train.add(member_name(row['image']))
    for row in validation:add(row,'validation')
    groups=sorted({(r['camera_id'],r['capture_date']) for r in inventory if r['capture_date'] in train_days})
    for camera,day in groups:
        choices=sorted((r for r in inventory if r['camera_id']==camera and r['capture_date']==day
            and r['image_member'] not in original_train),
            key=lambda r:(PurePosixPath(r['image_member']).stem,r['image_member']))
        count=min(per_group,len(choices))
        positions=sorted({int(i*(len(choices)-1)/(count-1)) if count>1 else 0 for i in range(count)})
        for position in positions:
            meta=choices[position]
            add(dict(camera_id=camera,date=day,image=meta['image_member'],annotation=meta['annotation_member']),
                'train',True)
    frames=sorted(selected.values(),key=lambda r:(r['role'],r['camera_id'],r['date'],r['image_archive_member']))
    train_actual={r['date'] for r in frames if r['role']=='train'}
    validation_actual={r['date'] for r in frames if r['role']=='validation'}
    if train_actual & validation_actual or (train_actual|validation_actual)&protected:
        raise ValueError('Final split isolation failed')
    return dict(frames=frames,protected_global_dates=sorted(protected),
        training_global_dates=sorted(train_actual),validation_global_dates=sorted(validation_actual),
        policy='Original train frames plus up to4additional chronological metadata positions per previously designated training camera/date; original/broader/fresh development kept as validation; all final dates excluded globally',
        pixels_or_labels_read=False)
