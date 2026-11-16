"""Reusable partial-foreground sequence scoring, in original frame units."""
from collections import Counter
from .sequence_reference import box_iou,reference_crossings,match_reference_events


def evaluate_cached_sequence(records, image_size, config, tracker_factory, *, scored_from=5, cancel_file=None):
    tracker=tracker_factory(**config)
    refs,predicted,match_map,track_ids,recalls,journal=[],[],{},[],[],[]
    for row in records:
        if cancel_file is not None and cancel_file.exists():raise InterruptedError('Cancellation requested')
        frame=row['frame_index']
        tracking=tracker.update(row['result']['detections'],frame,image_size=image_size)
        refs.append(dict(frame_index=frame,objects=row['reference_objects']))
        predicted.extend(tracking['events'])
        ident=None;detected=False;visible=bool(row['reference_objects'])
        if visible:
            # The declared experiment targets publisher object1 only; other
            # road users are not exhaustive negatives or extra labelled cars.
            objects=[o for o in row['reference_objects'] if o['object_id']==1]
            if len(objects)!=1:raise ValueError('This protocol requires selected foreground object1')
            box=objects[0]['box']
            detected=any(box_iou(d['box'],box)>=.5 for d in row['result']['detections'])
            ranked=sorted([(box_iou(t['box'],box),t['track_id']) for t in tracking['tracks']],reverse=True)
            if ranked and ranked[0][0]>=.5:
                ident=ranked[0][1];match_map[(frame,ident)]=1
            if frame>=scored_from:recalls.append(detected);track_ids.append(ident)
        journal.append(dict(frame_index=frame,visible=visible,detected=detected,matched_track_id=ident,tracking=tracking))
    # Reference geometry is independent of the candidate's identity policy.
    reference_config={k:v for k,v in config.items() if k!='continuation_confidence'}
    ref_events=[e for e in reference_crossings(refs,reference_config) if e['frame_index']>=scored_from]
    pred_events=[e for e in predicted if e['frame_index']>=scored_from]
    metrics=match_reference_events(ref_events,pred_events,match_map)
    ids=[i for i in track_ids if i is not None];counts=Counter(ids)
    metrics.update(scored_visible_car_frames=len(recalls),annotated_car_box_recall=sum(recalls)/len(recalls) if recalls else None,
        matched_track_coverage=len(ids)/len(recalls) if recalls else None,
        dominant_track_fraction=max(counts.values())/len(recalls) if counts and recalls else None)
    return dict(metrics=metrics,reference_events=ref_events,predicted_events=pred_events,
                weak_continuations=getattr(tracker,'weak_continuations',0)),journal
