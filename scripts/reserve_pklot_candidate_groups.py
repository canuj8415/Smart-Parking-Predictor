"""Seal a metadata-only group plan;future pixel/duplicate audit still required."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
def main():
    run=json.loads((ROOT/'models/pklot_unused_date_inventory.json').read_text(encoding='utf-8'));summary=run['summary']
    source=ROOT/summary['manifest'];assert digest(source)==summary['manifest_sha256']
    path=ROOT/'data/manifests/pklot_fresh_group_plan_v1.json'
    if path.exists():raise FileExistsError('Preserve sealed plan')
    with source.open(encoding='utf-8',newline='') as stream:rows=[r for r in csv.DictReader(stream) if r['eligible_date']=='True']
    groups=sorted({(r['camera_id'],r['capture_date']) for r in rows});assert len(groups)==6
    final={max((g for g in groups if g[0]==camera),key=lambda g:g[1]) for camera in sorted({g[0] for g in groups})}
    chosen=[]
    for camera,day in sorted(final):
        frames=sorted([r for r in rows if (r['camera_id'],r['capture_date'])==(camera,day)],key=lambda r:r['image_member'])
        assert len(frames)>=2
        for row in [frames[0],frames[-1]]:
            chosen.append(dict(camera_id=camera,date=day,image='data/raw/pklot_fresh_v1/'+row['image_member'],annotation='data/raw/pklot_fresh_v1/'+row['annotation_member'],
                image_archive_member=row['image_member'],annotation_archive_member=row['annotation_member'],source_id='SRC-DS-001',role='reserved_final_pixels_unopened'))
    plan=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-001',collection='PKLot-official',
        inventory_run=run['run_id'],inventory_manifest=summary['manifest'],inventory_manifest_sha256=summary['manifest_sha256'],archive='data/raw/pklot_subset/PKLot.tar.gz',archive_sha256=run['archive_sha256'],
        selection='Latest provisional unseen date per canonical camera reserved in full;first/last lexical frame per date preselected for a later6-frame final;remaining dates development-only. Selection uses member metadata,not pixels/labels/outcomes.',
        reserved_groups=[dict(camera_id=c,date=d) for c,d in sorted(final)],development_groups=[dict(camera_id=c,date=d) for c,d in groups if (c,d) not in final],
        whole_reserved_group_frames=sum((r['camera_id'],r['capture_date']) in final for r in rows),frames=chosen,
        images_materialized=False,pixels_decoded=False,xml_labels_parsed=False,final_evaluation_started=False,
        readiness='Metadata plan only. Audit selected member byte hashes/exact duplicates and explicit annotation support before a frozen model/protocol. Materialize without pixel decoding;use existing holdouts.evaluate_final_once before final pixels/labels.',
        limitations=['Known cameras,new dates only;not new-carpark generalization','Only6preselected final frames;cannot establish broad reliability','Conservative regex exclusion does not replace selected-group provenance/duplicate audit'])
    assert all(row['date'] not in run['excluded_dates'] for row in chosen)
    path.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:plan[k] for k in ['reserved_groups','development_groups','whole_reserved_group_frames','images_materialized']},indent=2))
if __name__=='__main__':main()
