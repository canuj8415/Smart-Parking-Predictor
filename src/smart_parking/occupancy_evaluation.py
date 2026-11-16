"""Frozen-score occupancy diagnostics with explicit uncertainty and denominators."""
import math

def occupancy_metrics(labels,probabilities,low=.25,high=.75):
    if not 0<=low<high<=1:raise ValueError('Invalid uncertainty thresholds')
    labels=list(labels);probabilities=list(probabilities)
    if len(labels)!=len(probabilities):raise ValueError('Label/score lengths differ')
    if any(y not in (0,1) for y in labels):raise ValueError('Labels must be binary')
    labels=[int(y) for y in labels]
    if any(not math.isfinite(p) or not 0<=p<=1 for p in probabilities):raise ValueError('Scores must be finite probabilities')
    n=len(labels)
    hard=[[0,0],[0,0]];selective=[[0,0,0],[0,0,0]];bins=[[] for _ in range(10)]
    for y,p in zip(labels,probabilities):
        hard[y][int(p>=.5)]+=1
        state=0 if p<=low else 1 if p>=high else 2
        selective[y][state]+=1;bins[min(9,int(p*10))].append((y,p))
    def ratio(a,b):return a/b if b else None
    def summary(matrix,covered):
        tn,fp=matrix[0][:2];fn,tp=matrix[1][:2]
        return dict(covered=covered,coverage=ratio(covered,n),accuracy_on_covered=ratio(tn+tp,covered),
            predicted_vacant=tn+fn,false_vacant=fn,vacancy_precision=ratio(tn,tn+fn),
            false_vacancy_fraction_of_vacant_predictions=ratio(fn,tn+fn),
            fraction_of_occupied_called_vacant=ratio(fn,sum(labels)),correct_decision_fraction=ratio(tn+tp,n))
    calibration=[];ece=0.
    for i,values in enumerate(bins):
        mean_p=sum(p for _,p in values)/len(values) if values else None
        occupied=sum(y for y,_ in values)/len(values) if values else None
        if values:ece+=len(values)/n*abs(mean_p-occupied)
        calibration.append(dict(bin_lower=i/10,bin_upper=(i+1)/10,count=len(values),mean_occupied_score=mean_p,observed_occupied_fraction=occupied))
    return dict(samples=n,actual_vacant=n-sum(labels),actual_occupied=sum(labels),
        hard_threshold=.5,uncertainty_thresholds=[low,high],hard_confusion=hard,
        selective_confusion=selective,confusion_rows=['actual_vacant','actual_occupied'],selective_columns=['predicted_vacant','predicted_occupied','uncertain'],
        hard=summary(hard,n),selective={**summary(selective,n-selective[0][2]-selective[1][2]),'uncertain':selective[0][2]+selective[1][2]},
        brier_score=sum((p-y)**2 for y,p in zip(labels,probabilities))/n if n else None,
        probability_calibration_ece=ece if n else None,calibration_bins=calibration)
