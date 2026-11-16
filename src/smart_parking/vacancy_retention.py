"""Retain the identities of correct baseline vacancies, not just their count."""
import math
from collections import defaultdict


def vacancy_retention(baseline,candidate,minimum=.95,threshold=.25):
    if not 0<=minimum<=1 or not 0<=threshold<=1:raise ValueError('Invalid retention settings')
    def index(rows):
        result={}
        for r in rows:
            key=tuple(r[k] for k in ('source_id','camera_id','date','frame','slot_id'))
            if key in result:raise ValueError('Duplicate occupancy identity')
            p=r['probability_occupied']
            if r['label'] not in (0,1) or not math.isfinite(p) or not 0<=p<=1:raise ValueError('Invalid target/probability')
            result[key]=r
        return result
    b,c=index(baseline),index(candidate)
    if not b or b.keys()!=c.keys():raise ValueError('Retention requires identical nonempty cohorts')
    if any(b[k]['label']!=c[k]['label'] for k in b):raise ValueError('Targets changed between paired predictions')
    groups=defaultdict(lambda:dict(baseline_correct_vacant=0,retained_same_vacant=0))
    for key,row in b.items():
        group=groups[(row['camera_id'],row['date'])]
        if row['label']==0 and row['probability_occupied']<=threshold:
            group['baseline_correct_vacant']+=1
            group['retained_same_vacant']+=int(c[key]['probability_occupied']<=threshold)
    values=[]
    for (camera,date),g in sorted(groups.items()):
        n=g['baseline_correct_vacant'];retained=g['retained_same_vacant'];values.append(dict(camera_id=camera,date=date,**g,fraction=retained/n if n else None,gate_passed=retained>=minimum*n))
    return dict(minimum=minimum,vacant_threshold=threshold,dates=values,gate_passed=all(v['gate_passed'] for v in values))
