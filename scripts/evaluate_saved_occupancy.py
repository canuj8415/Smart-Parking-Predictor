"""Evaluate saved slot predictions against original labels, never feed labels to inference."""
import csv,json,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.layout import read_pklot_xml
from smart_parking.provenance import digest

if __name__=='__main__':
    summary=json.loads((ROOT/'models/product_smoke_summary.json').read_text())
    with (ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8',newline='') as stream:frame=next(f for f in csv.DictReader(stream) if f['image']==summary['sample_frame'])
    image=Image.open(ROOT/frame['image']);labels=read_pklot_xml(ROOT/frame['annotation'],image.size)
    truth={s['id']:s['ground_truth_occupied'] for s in labels['slots']};folder=ROOT/'experiments/results'/summary['run_id'];evaluation={}
    for kind in ['fasterrcnn','maskrcnn']:
        result_path=folder/(kind+'_result.json');result=json.loads(result_path.read_text())
        decided=[s for s in result['slots'] if s['state']!='uncertain']
        correct=sum((s['state']=='occupied')==bool(truth[s['slot_id']]) for s in decided)
        false_free=sum(s['state']=='vacant' and truth[s['slot_id']]==1 for s in decided)
        evaluation[kind]=dict(actual_occupied=sum(truth.values()),actual_vacant=len(truth)-sum(truth.values()),
            predicted_counts=result['counts'],decided_slots=len(decided),decision_coverage=len(decided)/len(truth),
            accuracy_on_decided=correct/max(1,len(decided)),false_vacant_slots=false_free,
            prediction_file_sha256=digest(result_path),scope='One real frame only; not aggregate system accuracy or detector mAP')
    (folder/'occupancy_evaluation.json').write_text(json.dumps(evaluation,indent=2),encoding='utf-8')
    print(json.dumps(evaluation,indent=2))
