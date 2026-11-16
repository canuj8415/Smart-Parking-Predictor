"""Rule-specific crossings from publisher object IDs, without tracker association."""
from .flow import GateCounter

def box_iou(a,b):
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
    return intersection/union if union else 0.

def reference_crossings(observations,config):
    geometry=GateCounter(**config)
    if geometry.time_unit!='frames':raise ValueError('Indexed references need frame-index configuration')
    states={};events=[];last=None
    for row in observations:
        frame=row['frame_index']
        if not isinstance(frame,int) or (last is not None and frame<=last):raise ValueError('Reference frame indices must increase')
        if last is not None and frame-last>config['max_gap_frames']:states={}
        last=frame;present=set()
        for obj in row['objects']:
            ident=obj['object_id'];present.add(ident);box=obj['box'];center=((box[0]+box[2])/2,(box[1]+box[3])/2)
            state=states.setdefault(ident,dict(stable_side=0,pending_side=0,pending_count=0,stable_center=None))
            signed=geometry._signed(center);side=1 if signed>config['deadband_pixels'] else -1 if signed< -config['deadband_pixels'] else 0
            if not side:state['pending_side']=0;state['pending_count']=0;continue
            state['pending_count']=state['pending_count']+1 if state['pending_side']==side else 1;state['pending_side']=side
            if state['pending_count']>=config['stable_observations']:
                previous=state['stable_side']
                if previous and previous!=side and geometry._crosses_segment(state['stable_center'],center):
                    direction='negative_to_positive' if previous<side else 'positive_to_negative'
                    events.append(dict(object_id=ident,frame_index=frame,event_type='entry' if direction==config['entry_direction'] else 'exit',direction=direction,center=list(center)))
                state['stable_side']=side;state['stable_center']=center
        states={k:v for k,v in states.items() if k in present}
    return events

def match_reference_events(reference,predicted,frame_track_matches,tolerance_frames=2):
    """Only annotated-object recovery; extra events are not exhaustive false positives."""
    used=set();matches=[]
    for ref in reference:
        options=[]
        for i,pred in enumerate(predicted):
            if i in used or pred['event_type']!=ref['event_type']:continue
            if abs(pred['frame_index']-ref['frame_index'])>tolerance_frames:continue
            if frame_track_matches.get((pred['frame_index'],pred['track_id']))!=ref['object_id']:continue
            options.append((abs(pred['frame_index']-ref['frame_index']),i))
        if options:
            _,i=min(options);used.add(i);matches.append(dict(reference=ref,predicted=predicted[i]))
    return dict(reference_events=len(reference),recovered_events=len(matches),annotated_event_recall=len(matches)/len(reference) if reference else None,
                unmatched_predicted_events=len(predicted)-len(used),precision_evaluable=False,matches=matches)
