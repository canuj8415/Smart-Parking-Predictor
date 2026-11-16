"""Evaluate categorical occupancy decisions without inventing probabilities."""
def decision_metrics(labels,states):
    labels=list(labels);states=list(states)
    if len(labels)!=len(states):raise ValueError('Label/state lengths differ')
    if any(y not in (0,1) for y in labels):raise ValueError('Labels must be binary')
    columns={'vacant':0,'occupied':1,'uncertain':2}
    if any(s not in columns for s in states):raise ValueError('Unknown occupancy decision')
    matrix=[[0,0,0],[0,0,0]]
    for y,state in zip(labels,states):matrix[int(y)][columns[state]]+=1
    n=len(labels);tn,fp,uv=matrix[0];fn,tp,uo=matrix[1];covered=n-uv-uo
    ratio=lambda a,b:a/b if b else None
    return dict(samples=n,confusion=matrix,rows=['actual_vacant','actual_occupied'],columns=list(columns),
        covered=covered,coverage=ratio(covered,n),uncertain=uv+uo,accuracy_on_covered=ratio(tn+tp,covered),
        predicted_vacant=tn+fn,false_vacant=fn,vacancy_precision=ratio(tn,tn+fn),
        false_vacancy_fraction_of_vacant_predictions=ratio(fn,tn+fn),
        fraction_of_occupied_called_vacant=ratio(fn,fn+tp+uo),correct_decision_fraction=ratio(tn+tp,n))
