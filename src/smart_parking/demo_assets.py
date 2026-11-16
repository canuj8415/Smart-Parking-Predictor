"""A hash-bound training example for demonstrations, never a final exam image."""
import csv,json
from pathlib import Path
from .provenance import ROOT,digest


def inside(root,relative):
    base=Path(root).resolve();path=(base/relative).resolve()
    if not path.is_relative_to(base):raise ValueError('Demo asset outside project folder')
    return path


def select_training_demo(root=ROOT):
    root=Path(root)
    with (root/'data/manifests/pklot_frames.csv').open(encoding='utf-8-sig',newline='') as stream:
        training=[r for r in csv.DictReader(stream) if r['split']=='train']
    if not training:raise ValueError('No training example available for demonstration')
    # Fixed camera preference when present; otherwise use the first training row.
    # No image outcomes or occupancy answers influence this selection.
    row=next((r for r in training if r['camera_id']=='ufpr05'),training[0])
    image=inside(root,row['image']);layout=inside(root,row['layout_path'])
    if digest(image)!=row['image_sha256']:raise ValueError('Original training image checksum changed')
    geometry=json.loads(layout.read_text(encoding='utf-8'))
    if any('occupied' in s or 'state' in s for s in geometry['slots']):raise ValueError('Demo layout must contain geometry, not occupancy answers')
    return dict(schema_version=1,source_id='SRC-DS-001',split='train',camera_id=row['camera_id'],capture_date=row['date'],
        image=row['image'],layout=row['layout_path'],image_sha256=row['image_sha256'],layout_sha256=digest(layout),
        purpose='Training-split demonstration only, not an independent accuracy evaluation',
        selection='First training row for ufpr05 if available, otherwise first training row; no outcome-based selection')


def load_demo_assets(root=ROOT):
    root=Path(root);config=root/'configs/demo_sample.json'
    record=json.loads(config.read_text(encoding='utf-8')) if config.exists() else select_training_demo(root)
    if record.get('schema_version')!=1 or record.get('split')!='train':raise ValueError('Demo must use an explicitly recorded training example')
    image=inside(root,record['image']);layout=inside(root,record['layout'])
    if digest(image)!=record['image_sha256'] or digest(layout)!=record['layout_sha256']:
        raise ValueError('Demo image or layout checksum changed')
    return record,image,layout
