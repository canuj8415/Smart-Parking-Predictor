"""Paired frozen-score fusion diagnostics; uncertainty is never a correct decision."""
import math
from collections import defaultdict


def state_from_probability(probability, low=.25, high=.75):
    if not 0 <= low < high <= 1 or not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError('Finite probability and ordered thresholds required')
    return 'vacant' if probability <= low else 'occupied' if probability >= high else 'uncertain'


def state_metrics(rows, key):
    matrix=[[0,0,0],[0,0,0]]
    for row in rows:
        if row['label'] not in (0,1) or row[key] not in ('vacant','occupied','uncertain'):
            raise ValueError('Binary truth and explicit three-way state required')
        matrix[int(row['label'])][('vacant','occupied','uncertain').index(row[key])]+=1
    n=len(rows);tn,fp,uv=matrix[0];fn,tp,uo=matrix[1];decided=tn+fp+fn+tp
    def ratio(a,b):return a/b if b else None
    return dict(samples=n,actual_vacant=tn+fp+uv,actual_occupied=fn+tp+uo,
                confusion=matrix,columns=['vacant','occupied','uncertain'],
                false_vacant=fn,false_occupied=fp,correct_vacant=tn,correct_occupied=tp,
                uncertainty=uv+uo,uncertainty_fraction=ratio(uv+uo,n),
                vacancy_precision=ratio(tn,tn+fn),vacancy_recall=ratio(tn,tn+fp+uv),
                fraction_of_occupied_called_vacant=ratio(fn,fn+tp+uo),
                decided=decided,decision_coverage=ratio(decided,n),
                accuracy_on_decided=ratio(tn+tp,decided),correct_fraction_of_all=ratio(tn+tp,n))


def paired_fusion_metrics(rows):
    rows=list(rows);seen=set();groups=defaultdict(list)
    for row in rows:
        identity=(row['image'],row['slot_id'])
        if identity in seen:raise ValueError('Duplicate image/slot identity')
        seen.add(identity);groups[row['image']].append(row)
        expected=state_from_probability(row['probability_occupied'])
        if row['classifier_state']!=expected:raise ValueError('Baseline state differs from frozen probability')
        fused='uncertain' if expected=='vacant' and row['vehicle_id'] is not None else expected
        if row['fusion_state']!=fused:raise ValueError('Fusion violates fixed application disagreement rule')
    baseline=state_metrics(rows,'classifier_state');fusion=state_metrics(rows,'fusion_state')
    def retention(values):
        correct=[r for r in values if r['label']==0 and r['classifier_state']=='vacant']
        kept=sum(r['fusion_state']=='vacant' for r in correct)
        return dict(eligible=len(correct),retained=kept,fraction=kept/len(correct) if correct else None)
    per_image=[dict(image=image,classifier=state_metrics(values,'classifier_state'),
                    fusion=state_metrics(values,'fusion_state'),correct_vacancy_retention=retention(values))
               for image,values in sorted(groups.items())]
    return dict(classifier=baseline,fusion=fusion,correct_vacancy_retention=retention(rows),
                unsafe_vacancies_flagged=baseline['false_vacant']-fusion['false_vacant'],
                correct_vacancies_sent_to_review=baseline['correct_vacant']-fusion['correct_vacant'],
                per_image=per_image)


def fusion_gates(metrics,gates):
    f=metrics['fusion'];ret=metrics['correct_vacancy_retention']['fraction']
    per=[r['correct_vacancy_retention']['fraction'] for r in metrics['per_image'] if r['correct_vacancy_retention']['eligible']]
    return dict(false_vacancy_limit=f['fraction_of_occupied_called_vacant'] is not None and f['fraction_of_occupied_called_vacant']<=gates['occupied_false_vacancy_max'],
                uncertainty_limit=f['uncertainty_fraction'] is not None and f['uncertainty_fraction']<=gates['uncertainty_max'],
                correct_vacancy_retention=ret is not None and ret>=gates['correct_vacancy_retention_min'],
                every_image_vacancy_retention=bool(per) and min(per)>=gates['image_correct_vacancy_retention_min'])
