"""Metadata-only selection for a broader known-camera development study."""
from collections import defaultdict
from datetime import datetime
from pathlib import PurePosixPath

CAMERAS={'parking1a':'ufpr04','parking1b':'ufpr05','parking2':'pucpr'}

def evenly_spaced(values,count):
    if not values or count<1:raise ValueError('Need values and a positive sample count')
    if len(values)<=count:return list(values)
    if count==1:return [values[0]]
    return [values[round(i*(len(values)-1)/(count-1))] for i in range(count)]

def select_broader_development(pairs,excluded_dates,final_boundaries):
    """Six train/two later validation dates per camera, chosen before decoding.

    Select eight evenly spaced unused valid dates with at least four indexed
    pairs each. Sample up to eight train/four validation timestamps per date.
    Every date precedes the existing camera's sealed final date. No final rows
    enter the returned development manifest.
    """
    groups=defaultdict(lambda:defaultdict(list));rejected=[]
    for row in pairs:
        path=PurePosixPath(row['image'].replace('\\','/'));annotation=PurePosixPath(row['annotation'].replace('\\','/'))
        if path.is_absolute() or annotation.is_absolute() or '..' in path.parts or '..' in annotation.parts or ':' in row['image'] or ':' in row['annotation']:
            raise ValueError('Only project-relative source paths are allowed')
        try:
            if datetime.strptime(row['date'],'%Y-%m-%d').strftime('%Y-%m-%d')!=row['date']:raise ValueError('Noncanonical date')
        except ValueError:
            rejected.append(dict(image=row['image'],reason='invalid source date'));continue
        camera=CAMERAS.get(path.parts[4] if len(path.parts)>4 else None)
        if camera is None:raise ValueError('Unknown source camera')
        if row['date'] in excluded_dates:continue
        if camera not in final_boundaries:raise ValueError('Missing final boundary')
        if row['date']>=final_boundaries[camera]:continue
        if path.parent.name!=row['date'] or annotation.parent!=path.parent or annotation.stem!=path.stem:
            raise ValueError('Image/annotation/date identity mismatch')
        groups[camera][row['date']].append(row)
    selected=[];dates={}
    for camera in sorted(CAMERAS.values()):
        eligible=sorted(d for d,values in groups[camera].items() if len(values)>=4)
        if len(eligible)<8:raise ValueError('Need eight unused earlier development dates for '+camera)
        chosen=evenly_spaced(eligible,8);dates[camera]=dict(train=chosen[:6],validation=chosen[6:])
        for i,date in enumerate(chosen):
            split='train' if i<6 else 'validation'
            options=sorted(groups[camera][date],key=lambda r:(PurePosixPath(r['image']).stem,r['image']))
            for row in evenly_spaced(options,8 if split=='train' else 4):selected.append(dict(**row,camera_id=camera,split=split))
    paths=[r['image'] for r in selected]
    if len(paths)!=len(set(paths)):raise ValueError('Duplicate indexed source images')
    train_days={r['date'] for r in selected if r['split']=='train'};val_days={r['date'] for r in selected if r['split']=='validation'}
    if train_days&val_days:raise ValueError('Global capture dates overlap development splits')
    return dict(frames=selected,dates=dates,rejected_metadata=rejected)
