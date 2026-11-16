"""Paired labelled prediction changes with strict identities and fixed thresholds."""
import math


def paired_changes(before,after,key_fields=('image_sha256','slot_id')):
    def index(rows):
        result={}
        for row in rows:
            key=tuple(str(row[k]) for k in key_fields)
            if any(not k for k in key) or key in result:raise ValueError('Missing or duplicate observation identity')
            p=row['probability_occupied']
            if type(row['label']) is not int or row['label'] not in {0,1} or not math.isfinite(p) or not 0<=p<=1:raise ValueError('Invalid target or probability')
            result[key]=row
        return result
    first,last=index(before),index(after)
    if not first or set(first)!=set(last):raise ValueError('Paired cohorts differ or are empty')
    rows=[]
    for key in sorted(first):
        b,a=first[key],last[key]
        if b['label']!=a['label']:raise ValueError('Paired target changed')
        y=b['label'];pb=b['probability_occupied'];pa=a['probability_occupied']
        old_bad=int(pb>=.5)!=y;new_bad=int(pa>=.5)!=y
        rows.append(dict(identity=list(key),label=y,camera_id=b.get('camera_id'),date=b.get('date'),
            probability_before=pb,probability_after=pa,probability_delta=pa-pb,
            hard_error_before=old_bad,hard_error_after=new_bad,regressed=(not old_bad and new_bad),corrected=(old_bad and not new_bad),
            false_vacant_before=(y==1 and pb<=.25),false_vacant_after=(y==1 and pa<=.25),
            correct_confident_vacant_before=(y==0 and pb<=.25),correct_confident_vacant_after=(y==0 and pa<=.25),
            review_before=(.25<pb<.75),review_after=(.25<pa<.75)))
    summary=dict(observations=len(rows),regressed=sum(r['regressed'] for r in rows),corrected=sum(r['corrected'] for r in rows),
        errors_before=sum(r['hard_error_before'] for r in rows),errors_after=sum(r['hard_error_after'] for r in rows),
        new_false_vacant=sum(r['false_vacant_after'] and not r['false_vacant_before'] for r in rows),
        removed_false_vacant=sum(r['false_vacant_before'] and not r['false_vacant_after'] for r in rows))
    assert summary['errors_after']-summary['errors_before']==summary['regressed']-summary['corrected']
    return rows,summary
