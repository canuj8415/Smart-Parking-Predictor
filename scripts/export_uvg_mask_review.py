"""Derive review flags without changing saved predictions or recording a new trial."""
import json
from datetime import datetime,timezone
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.mask_review import review_candidates


def main():
    study=ROOT/'experiments/results/UVG-MASK-DEDUP-20261026T144351078557Z';trial=json.loads((study/'run.json').read_text());source=ROOT/trial['native_folder'];ref=ROOT/trial['reference_folder'];rows=[];hashes={}
    assert not trial['component_gates_passed'],'Review-only fallback documents the actual failed candidate'
    for f in trial['frames']:
        prediction_path=source/f'maskrcnn_{f:04d}.json';mask_path=source/f'maskrcnn_{f:04d}_masks.npz';reference=ref/f'maskrcnn_{f:04d}.json'
        for p in [prediction_path,mask_path,reference]:
            relative=p.relative_to(ROOT).as_posix();assert digest(p)==trial['input_hashes'][relative];hashes[relative]=digest(p)
        old=json.loads(prediction_path.read_text());count=len(json.loads(reference.read_text())['predictions']);packed=np.load(mask_path,allow_pickle=False);masks=np.unpackbits(packed['packed'],axis=-1,count=960).astype(bool)
        pred_bytes=json.dumps(old['predictions'],sort_keys=True).encode();mask_bytes=masks.tobytes();review=review_candidates(old['predictions'],masks,count)
        assert review['retained_indices']==list(range(len(old['predictions']))) and review['automatic_removals']==0
        assert json.dumps(old['predictions'],sort_keys=True).encode()==pred_bytes and masks.tobytes()==mask_bytes
        rows.append(dict(frame=f,source_predictions=prediction_path.relative_to(ROOT).as_posix(),source_masks=mask_path.relative_to(ROOT).as_posix(),review=review))
    protected=trial['protected_hashes'];assert all(digest(ROOT/p)==h for p,h in protected.items())
    # Research deletion outputs remain immutable; review records refer to the original native candidate.
    report=dict(created_at=datetime.now(timezone.utc).isoformat(),source_trial=trial['run_id'],kind='derived_inspection_only_no_new_experiment',
        input_hashes=hashes,implementation_hashes={p:digest(ROOT/p) for p in ['scripts/export_uvg_mask_review.py','src/smart_parking/mask_review.py','tests/test_mask_review.py']},rows=rows,
        retained_predictions=sum(row['review']['output_prediction_count'] for row in rows),review_records=sum(len(row['review']['review_items']) for row in rows),
        unique_flagged_predictions=sum(len({i for item in row['review']['review_items'] for i in item['indices']}) for row in rows),
        automatic_removals=0,prediction_and_mask_bytes_unchanged=True,new_model_inference=False,new_trial_counted=False,overall_vision_admission_passed=False,production_integrated=False,
        scope='Possible conflicts only;not verified duplicates/false positives,new model accuracy,occupancy answers or final validation')
    (study/'review_only.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['retained_predictions','review_records','unique_flagged_predictions','automatic_removals','prediction_and_mask_bytes_unchanged']},indent=2))


if __name__=='__main__':main()
