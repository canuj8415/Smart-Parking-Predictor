"""Hash-bound archived development reader; no inference or acquisition API."""
import hashlib
import json
from pathlib import Path

BASE='UVG-DETECTORS-20261026T131246880705Z'
CANDIDATE='UVG-DETECTORS-20261026T131820602234Z'
AUDIT='UVG-OUTPUT-AUDIT-20261026T134257858034Z'


def allowed_paths():
    paths=[f'experiments/results/{name}/run.json' for name in [BASE,CANDIDATE,AUDIT]]
    paths.extend(f'experiments/results/{AUDIT}/{kind}_{f:04d}.json' for kind in ['fasterrcnn','maskrcnn'] for f in [121,300,541])
    paths.extend(f'experiments/results/{CANDIDATE}/{name}' for name in ['development_comparison.png','fixed_frame_mask_comparison.png'])
    return set(paths)


def load(root,manifest):
    root=Path(root).resolve()
    if manifest.get('data_kind')!='archived_development_only' or set(manifest.get('inputs',{}))!=allowed_paths():
        raise ValueError('Only exact archived development lesson inputs are admitted')
    documents={};hashes={}
    for relative,expected in manifest['inputs'].items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root):raise ValueError('Lesson input path escaped root')
        content=path.read_bytes();actual=hashlib.sha256(content).hexdigest()
        if actual!=expected:raise ValueError('Archived lesson input changed: '+relative)
        hashes[relative]=actual
        if path.suffix=='.json':documents[relative]=json.loads(content)
    runs=[documents[f'experiments/results/{name}/run.json'] for name in [BASE,CANDIDATE,AUDIT]]
    first,second,audit=runs
    if first.get('final_evaluation') is not False or second.get('final_evaluation') is not False:
        raise ValueError('Actual final results cannot enter this development lesson')
    if first['frames']!=second['frames'] or first['input_hashes']!=second['input_hashes'] or first['weight_hashes']!=second['weight_hashes']:
        raise ValueError('Compared development cohorts/weights must be identical')
    if first['all_gates_passed'] or second['all_gates_passed']:
        raise ValueError('Lesson must retain the archived absolute admission failures')
    signatures={}
    for kind in ['fasterrcnn','maskrcnn']:
        rows=[row for f in [121,300,541] for row in documents[f'experiments/results/{AUDIT}/{kind}_{f:04d}.json']['diagnosis']['rows'] if row['eligible']]
        counts={}
        for row in rows:counts[row['category']]=counts.get(row['category'],0)+1
        if counts!=audit['summary'][kind]['eligible_signatures'] or len(rows)!=audit['summary'][kind]['eligible']:
            raise ValueError('Archived signature counts disagree')
        signatures[kind]=counts
    return dict(baseline=first,candidate=second,audit=audit,signatures=signatures,input_hashes=hashes,
                real_source_raw_loaded=False,final_result_loaded=False,model_inference=False)
