"""Inventory actual product assets/runs and extend the permanent source registry."""
import csv,json,platform,sys
from datetime import datetime,timezone
from pathlib import Path
import importlib.metadata as metadata
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def csv_rows(path):
    with path.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))

if __name__=='__main__':
    manifest=ROOT/'data/source_manifest.csv';rows=csv_rows(manifest);fields=list(rows[0]);ids={r['source_id'] for r in rows}
    access=datetime.now(timezone.utc).isoformat()
    additions=[
      ('SRC-LIVE-001','dataset/API','Singapore Carpark Availability','HDB; data.gov.sg','https://api.data.gov.sg/v1/transport/carpark-availability','Singapore Open Data Licence 1.0; user explicitly authorized its terms','data/raw/singapore_live/','Live availability snapshot, stored raw and normalized separately from image/history domains'),
      ('SRC-MOD-001','pretrained model','Faster R-CNN ResNet50 FPN V2 COCO_V1','TorchVision contributors','https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn_v2.html','TorchVision code BSD-3-Clause; upstream warns weights may inherit dataset terms; local academic use only, no weight redistribution','models/pretrained/fasterrcnn_resnet50_fpn_v2.pth','Real vehicle boxes; externally pretrained on COCO, no project detector fine-tuning'),
      ('SRC-MOD-002','pretrained model','Mask R-CNN ResNet50 FPN COCO_V1','TorchVision contributors','https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn.html','TorchVision code BSD-3-Clause; dataset-derived model terms retained; no weight redistribution','models/pretrained/maskrcnn_resnet50_fpn.pth','Real predicted vehicle instance masks; not slot polygons or project-trained instance model'),
      ('SRC-MOD-003','pretrained model','ResNet18 ImageNet1K V1','TorchVision contributors','https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html','TorchVision code BSD-3-Clause; ImageNet-derived pretrained-weight terms; local academic use only','models/pretrained/resnet18_imagenet.pth','Frozen pretrained features plus project-trained occupancy head'),
      ('SRC-DOC-013','documentation/license','TorchVision repository and pretrained-model disclaimer','TorchVision contributors','https://github.com/pytorch/vision','BSD-3-Clause code; separate pretrained model disclaimer','not downloaded','Architecture API and rights review; do not treat code license as universal dataset rights'),
      ('SRC-DOC-014','documentation/license','Singapore live API and licence','Singapore Government; HDB','https://data.gov.sg/open-data-licence','Singapore Open Data Licence 1.0','not downloaded','Attribution and access conditions, including explicitly approved indemnity clause'),
      ('SRC-PKG-001','package','opencv-python-headless 4.13.0.92 Windows wheel','OpenCV contributors and wheel maintainers','https://pypi.org/project/opencv-python-headless/4.13.0.92/','Apache 2.0 package; retain bundled third-party notices','dependencies/wheels/opencv_python_headless-4.13.0.92-cp37-abi3-win_amd64.whl','Optional project-local video decoder; exact published PyPI SHA-256 pin'),
      ('SRC-DOC-015','documentation','PKLot original laboratory page','UFPR VRI laboratory','https://web.inf.ufpr.br/vri/databases/parking-lot-database/','CC BY 4.0 dataset; cite Almeida et al. 2015','not downloaded','Verify original archive link and slot-label scope'),
      ('SRC-PAP-010','paper','Mask R-CNN','Kaiming He; Georgia Gkioxari; Piotr Dollar; Ross Girshick','https://arxiv.org/abs/1703.06870','Metadata/abstract reviewed; full-text redistribution rights not asserted','not downloaded','Verified instance-segmentation architecture citation; he2017mask')]
    receipts_path=ROOT/'data/resource_receipts.jsonl'
    receipts=[json.loads(line) for line in receipts_path.read_text(encoding='utf-8').splitlines()] if receipts_path.exists() else []
    by_source={}
    for item in receipts:by_source.setdefault(item['source_id'],[]).append(item)
    for sid,kind,name,creator,url,license,local,purpose in additions:
        existing=by_source.get(sid,[]);path=ROOT/local
        measured=path.is_file() and path.stat().st_size>0
        if sid in ids:
            row=next(r for r in rows if r['source_id']==sid)
            if measured or existing:
                row.update(status='used',original_size=str(path.stat().st_size)+' bytes' if measured else str(len(existing))+' actual acquisition receipts',
                    local_location=local,sha256=digest(path) if measured else 'See actual per-file resource receipts',
                    access_date=existing[-1]['accessed_at'] if existing else row['access_date'])
            continue
        status='downloaded' if measured or existing else 'used' if kind.startswith('documentation') else 'candidate'
        row={field:'not applicable/unverified' for field in fields}
        row.update(source_id=sid,resource_type=kind,resource=name,original_creator=creator,source_url=url,
            download_url=existing[-1]['source_url'] if existing else '',access_date=existing[-1]['accessed_at'] if existing else access,
            access_time_precision='Exact acquisition time in resource receipts; documentation review date only',version=name,
            license=license,permission='Local attributed academic evaluation; no publication/redistribution of raw weights or private footage',
            original_size=str(path.stat().st_size)+' bytes' if measured else str(len(existing))+' acquisition receipts',
            local_location=local,sha256=digest(path) if measured else 'See per-asset resource receipts',purpose=purpose,
            used_by='Smart Parking local application; Jupyter product notebook',modifications='Raw preserved; transformations recorded by module/run',
            attribution=creator+'; see THIRD_PARTY_SOURCES.md',status=status,
            open_issues='No detector mAP/vehicle mask accuracy claimed without matching ground truth' if kind=='pretrained model' else 'See implementation and licensing records')
        rows.append(row);ids.add(sid)
    for row in rows:
        if row['source_id']=='SRC-DS-001' and (ROOT/'data/raw/pklot_subset/PKLot.tar.gz').exists():
            row.update(status='downloaded',local_location='data/raw/pklot_subset/PKLot.tar.gz',
                original_size=str((ROOT/'data/raw/pklot_subset/PKLot.tar.gz').stat().st_size)+' bytes full original archive',
                sha256=digest(ROOT/'data/raw/pklot_subset/PKLot.tar.gz'),used_by='Occupancy ResNet18 head; parking-region U-Net; image inference',
                modifications='Original archive preserved; subset selection, date grouping, masked crops and union masks in data/manifests/',
                open_issues='Convenience development subset, invalid dates/polygons quarantined; not full-dataset benchmark')
    with manifest.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    registry=ROOT/'docs/SOURCE_REGISTRY.md'
    registry.write_text('# Source registry\n\nCanonical complete fields: `data/source_manifest.csv`. Actual asset-level access times, retrieval URLs, bytes, hashes and local paths: `data/resource_receipts.jsonl`.\n\n| ID | Resource | Status | Local storage |\n|---|---|---|---|\n'+'\n'.join(f"| {r['source_id']} | [{r['resource']}]({r['source_url']}) | {r['status']} | {r['local_location']} |" for r in rows)+'\n\nDocumentation consulted in earlier sessions has date-only precision; acquisition receipts preserve actual times. Unknowns are not filled with guesses. See LICENSING_RECORD.md and THIRD_PARTY_SOURCES.md for use limits.\n',encoding='utf-8')
    inventory=json.loads((ROOT/'data/dataset_inventory.json').read_text(encoding='utf-8'))
    inventory['inventoried_at']=access
    if (ROOT/'data/raw/pklot_subset/acquisition.json').exists():
        acquisition=json.loads((ROOT/'data/raw/pklot_subset/acquisition.json').read_text())
        item=dict(source_id='SRC-DS-001',status='downloaded',full_archive_downloaded=acquisition['full_archive_downloaded'],
            original_archive='data/raw/pklot_subset/PKLot.tar.gz',archive_sha256=next(r['sha256'] for r in rows if r['source_id']=='SRC-DS-001'),
            paired_frames=len(acquisition['pairs']),capture_date_folder_labels=len({p['date'] for p in acquisition['pairs']}),
            source_folder_dates_not_all_valid=True,subset_manifest='data/raw/pklot_subset/acquisition.json',asset_receipts='data/resource_receipts.jsonl')
        inventory['datasets']=[d for d in inventory['datasets'] if d['source_id']!='SRC-DS-001']+[item]
    from smart_parking.live import get_live
    try:
        live,info=get_live(False)
        item=dict(source_id='SRC-LIVE-001',status='downloaded_snapshot',car_parks=len({r['car_park_id'] for r in live}),observations=len(live),
            provider_timestamp=live[0]['feed_timestamp'],raw_path=str(Path(info['path']).relative_to(ROOT)),
            used_for_training=False,derived_history='data/processed/singapore_live_observations.csv')
        inventory['datasets']=[d for d in inventory['datasets'] if d['source_id']!='SRC-LIVE-001']+[item]
    except FileNotFoundError:pass
    inventory['not_acquired']=[n for n in inventory.get('not_acquired',[]) if n!='PKLot']
    (ROOT/'data/dataset_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    deps={}
    for name in ['torch','torchvision','numpy','Pillow','matplotlib','jupyterlab','nbformat','nbclient','ipykernel']:
        distribution=metadata.distribution(name)
        deps[name]=dict(version=distribution.version,license=distribution.metadata.get('License-Expression') or distribution.metadata.get('License','unverified'),
            creator=distribution.metadata.get('Author') or distribution.metadata.get('Author-email','not specified'),
            homepage=distribution.metadata.get('Home-page') or distribution.metadata.get('Project-URL','not specified'))
    (ROOT/'docs/DEPENDENCY_INVENTORY.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),direct_packages=deps,
        standard_library=['tkinter','urllib','json','csv','pathlib','hashlib','threading','queue','xml.etree.ElementTree'],
        local_optional_package='OpenCV wheel with exact receipt if installation succeeds'),indent=2),encoding='utf-8')
    experiment_path=ROOT/'experiments/EXPERIMENT_REGISTRY.csv';experiments=csv_rows(experiment_path);efields=list(experiments[0]);eids={e['experiment_id'] for e in experiments}
    for runfile in sorted([*(ROOT/'experiments/results').glob('*/run.json'),*(ROOT/'experiments/results').glob('PRODUCT-*/summary.json')]):
        run=json.loads(runfile.read_text());rid=run['run_id']
        if rid in eids:continue
        record={field:'not applicable / see run.json' for field in efields}
        record.update(experiment_id=rid,run_type='synthetic educational baseline' if rid.startswith('MLP') else 'real-data inference/integration' if rid.startswith('PRODUCT') else 'real-data training and held-out evaluation',
            source_ids=run.get('source_id',run.get('data_type','not specified')),split_ids=run.get('split_id','see run.json'),
            configuration=runfile.relative_to(ROOT).as_posix(),architecture=run.get('architecture','see run.json and model card'),
            model_version=rid,optimizer=run.get('optimizer','see run.json'),learning_rate=run.get('learning_rate','see run.json'),
            epochs=run.get('epochs',run.get('head_epochs','see run.json')),batch_size=run.get('batch_size','see run.json'),random_seed=run.get('seed','not specified'),
            hardware='i9-14900HX; CPU',execution_environment='Python '+platform.python_version()+'; Torch '+metadata.version('torch'),
            training_duration=run.get('training_seconds',run.get('metrics',{}).get('training_seconds','not separately measured')),
            evaluation_metrics=json.dumps(run.get('metrics',run.get('classifier_metrics',{'synthetic_loss':run.get('final_loss')}))),
            logs=runfile.parent.relative_to(ROOT).as_posix(),checkpoints='models/checkpoints/',implementation_sha256=run.get('code_sha256','see run.json'),
            conclusions='Actual run; interpret limitations and baseline comparisons in run.json')
        experiments.append(record);eids.add(rid)
    with experiment_path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=efields);writer.writeheader();writer.writerows(experiments)
    print(json.dumps(dict(sources=len(rows),acquisition_receipts=len(receipts),experiment_records=len(experiments)),indent=2))
