"""Inspection-only mask conflicts after automatic suppression failed validation."""
from .mask_duplicates import deduplicate as _research_plan


def review_candidates(predictions,masks,reference_count):
    """Keep every detection; suspected duplicates are not confirmed identities."""
    plan=_research_plan(predictions,masks,reference_count,16,.85,.8)
    items=[]
    for row in plan['suppressed']:
        items.append(dict(indices=[row['retained_index'],row['removed_index']],reason='possible_same_class_duplicate',
                          label=row['label'],box_containment=row['box_containment'],mask_containment=row['mask_containment'],
                          min_mask_pixels=row['min_mask_pixels'],action='review_only'))
    items.extend(dict(row,action='review_only') for row in plan['reviews'])
    return dict(retained_indices=list(range(len(predictions))),review_items=items,automatic_removals=0,
                source_prediction_count=len(predictions),output_prediction_count=len(predictions),classes_remapped=False,
                policy='Inspection only;no prediction,mask,confidence,occupancy-state or model change',
                reason='Automatic same-class containment suppression lost correctly matched cars in the archived development trial')
