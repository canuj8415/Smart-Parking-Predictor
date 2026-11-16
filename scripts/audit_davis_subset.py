"""Validate original member identities/headers and reserve an entire new sequence."""
import csv,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    started=datetime.now(timezone.utc);run='DAVIS-DATA-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False);clock=time.perf_counter()
    source=ROOT/'data/raw/davis2017_metadata/subset_acquisition.json';acq=json.loads(source.read_text());assert len(acq['entries'])==310
    files=['scripts/audit_davis_subset.py','scripts/acquire_davis_subset.py','scripts/inspect_davis_archive.py']
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-DS-012',seed='Deterministic byte/header/membership audit',hypothesis='A bounded original-byte acquisition contains paired, consecutive car sequences with explicit rights/split/timebase metadata, without viewing the reserved sequence pixels or annotation values',
        scope='Data readiness only; no detector/segmentation/counting accuracy',role_plan={'car-turn':'development','car-roundabout':'reserved_final'},acquisition_sha256=digest(source),source_hashes={p:digest(ROOT/p) for p in files},
        gates=['310 original entries retain acquisition hashes','80/75 consecutive paired image/mask files','same dimensions within each sequence','reserved sequence only lazy image headers, no pixel/mask value decoding','licence/creator/source records present'],frame_rate='Not established; frame index only; no fabricated physical timestamps')
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=digest(ROOT/p),source=(ROOT/p).read_text(encoding='utf-8')) for p in files})
    frames=[]
    for sequence,expected in [('car-turn',80),('car-roundabout',75)]:
        entries=[r for r in acq['entries'] if r['sequence']==sequence]
        images={Path(r['member']).stem:r for r in entries if r['kind']=='JPEGImages'};masks={Path(r['member']).stem:r for r in entries if r['kind']=='Annotations'}
        assert set(images)==set(masks)=={f'{i:05d}' for i in range(expected)}
        dimensions=set()
        for ident in sorted(images):
            a,b=images[ident],masks[ident]
            assert digest(ROOT/a['path'])==a['sha256'] and digest(ROOT/b['path'])==b['sha256']
            # Pillow .size/.mode are lazy header metadata; never call load/array.
            with Image.open(ROOT/a['path']) as im:image_size=list(im.size);image_mode=im.mode
            with Image.open(ROOT/b['path']) as im:mask_size=list(im.size);mask_mode=im.mode
            assert image_size==mask_size and mask_mode in ['P','L'];dimensions.add(tuple(image_size))
            frames.append(dict(sequence=sequence,role=a['role'],frame_index=int(ident),image=a['path'],annotation=b['path'],image_sha256=a['sha256'],annotation_sha256=b['sha256'],image_size=image_size,image_mode=image_mode,mask_mode=mask_mode))
        assert len(dimensions)==1
    manifest=ROOT/'data/manifests/davis_car_sequences_v2.json';reservation=ROOT/'data/manifests/davis_car_roundabout_final_v2.json'
    if manifest.exists() or reservation.exists():raise FileExistsError('Preserve sealed original memberships')
    dump(manifest,dict(schema_version=1,run_id=run,source_id='SRC-DS-012',acquisition_sha256=digest(source),frames=frames,timebase='frame_index',physical_fps=None,annotation_scope='Selected foreground objects only; not exhaustive traffic occupancy/detection ground truth'))
    dump(reservation,dict(schema_version=1,source_id='SRC-DS-012',reserved_sequences=['car-roundabout'],frames=[r for r in frames if r['role']=='reserved_final'],parent_manifest_sha256=digest(manifest),reserved_at=datetime.now(timezone.utc).isoformat(),status='reserved, pixels and annotation values unopened',rules=['Reserve entire sequence, never frame subsets across training/final','Before final pixel decoding, freeze method/protocol/weights and acquire durable exclusive source/sequence claim; failure consumes sequence','No repeated changed-method evaluation; use genuinely new sequences for future changes','Publisher foreground annotations may be partial; do not claim exhaustive precision or camera occupancy accuracy','Original fps unknown: report frame-index tracking, not physical timestamps or real-time throughput']))
    report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,data_gate_passed=True,frames=len(frames),original_entries=310,
        member_bytes=sum(r['bytes'] for r in acq['entries']),original_archive_size=acq['archive_size'],archive_fully_downloaded=False,full_archive_sha256=None,
        manifest_sha256=digest(manifest),reservation_sha256=digest(reservation),reserved_pixels_decoded=False,reserved_annotation_values_decoded=False,source_docs={p.name:digest(p) for p in (ROOT/'data/raw/davis2017_metadata').glob('*') if p.is_file()},model_accuracy_evaluated=False)
    dump(folder/'run.json',report)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run;dump(state_path,state)
    print(json.dumps(dict(run_id=run,data_gate_passed=True,frames=155,original_entries=310,member_bytes=report['member_bytes'],reserved_final_frames=75,pixels_decoded=False),indent=2))
