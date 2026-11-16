"""Output signatures for supplied-positive misses, never causal model proof."""
import math
from .positive_instances import box_iou,match_positives


ROAD_CLASSES={'car','motorcycle','bus','truck'}


def diagnose(targets,outputs,confidence=.5,iou_threshold=.5):
    """Inspect post-NMS COCO outputs before the app's road/score filters.

    Candidate boxes can explain several overlapping supplied objects; they are
    diagnostic evidence only, not additional true-positive matches.
    """
    if not 0<confidence<1 or not 0<iou_threshold<=1:raise ValueError('Invalid diagnostic thresholds')
    for obj in outputs:
        if not isinstance(obj['label'],str) or not obj['label']:raise ValueError('Missing class')
        if not math.isfinite(obj['score']) or not 0<=obj['score']<=1:raise ValueError('Invalid score')
        box_iou(obj['box'],obj['box'])
    operating=[o for o in outputs if o['label'] in ROAD_CLASSES and o['score']>=confidence]
    matching=match_positives(targets,operating,iou_threshold)
    assigned={m['truth_index'] for m in matching['matches']}
    rows=[]
    for i,target in enumerate(targets):
        evidence=[dict(output_index=j,label=o['label'],score=o['score'],iou=box_iou(target['box'],o['box']),
                       retained_by_product=o['label'] in ROAD_CLASSES and o['score']>=confidence) for j,o in enumerate(outputs)]
        evidence.sort(key=lambda o:(-o['iou'],-o['score'],o['output_index']))
        same=[e for e in evidence if e['label']==target['label']]
        compatible=[e for e in evidence if e['iou']>=iou_threshold]
        same_compatible=[e for e in same if e['iou']>=iou_threshold]
        chosen=None
        if i in assigned:category='matched_at_operating_point'
        elif any(e['score']>=confidence for e in same_compatible):
            category='one_to_one_competition';chosen=next(e for e in same_compatible if e['score']>=confidence)
        elif same_compatible:
            category='same_class_below_operating_threshold';chosen=same_compatible[0]
        elif any(e['score']>=confidence for e in compatible):
            chosen=next(e for e in compatible if e['score']>=confidence)
            category='road_class_disagreement' if chosen['label'] in ROAD_CLASSES else 'outside_product_class_at_operating_point'
        elif any(e['score']>=confidence and e['iou']>=.1 for e in same):
            category='same_class_localization_gap';chosen=next(e for e in same if e['score']>=confidence and e['iou']>=.1)
        elif compatible:category='other_class_below_operating_threshold';chosen=compatible[0]
        else:category='unresolved_after_postprocessing'
        rows.append(dict(target_index=i,track_id=target.get('track_id'),label=target['label'],eligible=target.get('eligible',True),
                         category=category,category_evidence=chosen,best_overlap=evidence[0] if evidence else None,
                         best_same_class_overlap=same[0] if same else None))
    return dict(rows=rows,operating_match=matching,exhaustive_precision_evaluable=False,
                scope='Signatures in final post-NMS outputs only;not raw RPN evidence,causal root causes or a proposal to lower thresholds/remap classes')
