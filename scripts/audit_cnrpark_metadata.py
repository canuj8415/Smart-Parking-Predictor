"""Validate official CNR-EXT metadata/archive membership,without image decompression."""
import csv,json,sys,time,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.cnrpark_metadata import COLLECTION,read_metadata,global_date_split
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'));assert not state['active_validation_jobs'] and not state['active_training_jobs']
    started=datetime.now(timezone.utc);rid='CNR-METADATA-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    metadata=ROOT/'data/raw/cnrpark_official/CNRPark+EXT.csv';archive=ROOT/'data/raw/cnrpark_official/CNR-EXT-Patches-150x150.zip'
    paths=['scripts/audit_cnrpark_metadata.py','src/smart_parking/cnrpark_metadata.py','src/smart_parking/cnrpark_holdouts.py'];hashes={p:digest(ROOT/p) for p in paths}
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=124,source_ids=['SRC-DS-002','SRC-DOC-012'],
        hypothesis='Official CNR-EXT factual metadata can be matched to safe archive members and partitioned by whole chronological dates across all9cameras,without decompressing image contents or using occupancy target values.',
        source_hashes=hashes,source_metadata_sha256=digest(metadata),source_archive_sha256=digest(archive),
        gates=['Exact CSV schema/calendar/path identities','Every accepted EXT row matches exactly one JPEG archive member','All9cameras retained','Whole global dates disjoint across train/development/reserved final',
            'No image bytes decompressed and no model scoring/training','Targets absent from derived manifest'],
        limitations=['Database ODbL declared;individual image-content permission remains unqualified,so images inspection-only','Local SHA256 only;publisher release digest is null',
            'Source metadata labels not evaluated;final images unopened','One carpark; chronological split is not unseen-camera validation'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid)];dump(state_path,state);clock=time.perf_counter();report=None
    try:
        rows,rejected,base=read_metadata(metadata);rows,mapping=global_date_split(rows)
        with zipfile.ZipFile(archive) as source:
            entries=source.infolist();names={i.filename for i in entries};assert len(names)==len(entries)
            assert not any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts for n in names)
            jpeg={i.filename for i in entries if i.filename.lower().endswith('.jpg')}
            selected={r['archive_member'] for r in rows};missing=sorted(selected-jpeg);unmapped=sorted(jpeg-selected)
            assert not missing and not unmapped and not rejected
            for row in rows:
                info=source.getinfo(row['archive_member']);row.update(archive_crc32=f'{info.CRC:08x}',compressed_bytes=info.compress_size,original_jpeg_bytes=info.file_size)
        assert len({r['camera_id'] for r in rows})==9
        assert not any('occupancy' in r for r in rows)
        target=ROOT/'data/splits/cnrpark-global-dates-v1';target.mkdir(parents=True,exist_ok=False)
        manifest=target/'manifest.csv'
        with manifest.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        reserved=dict(schema_version=1,collection=COLLECTION,source_id='SRC-DS-002',created_at=datetime.now(timezone.utc).isoformat(),
            reserved_dates=[d for d,role in mapping.items() if role=='reserved_final'],reserved_rows=sum(r['split']=='reserved_final' for r in rows),
            parent_manifest=manifest.relative_to(ROOT).as_posix(),parent_manifest_sha256=digest(manifest),source_metadata=metadata.relative_to(ROOT).as_posix(),source_metadata_sha256=digest(metadata),
            source_archive=archive.relative_to(ROOT).as_posix(),source_archive_sha256=digest(archive),image_analysis_authorized=False,
            selection='First60percent chronological dates train,next20percent development,remainder final;all camera views on a date share role;no target-based selection',
            image_members_decompressed=0,targets_parsed_or_scored=False,claim_registry='data/cnrpark_holdout_claims')
        reservation=ROOT/'data/manifests/cnrpark_final_dates_v1.json';assert not reservation.exists();dump(reservation,reserved)
        summary=dict(rows=len(rows),excluded_preliminary_cnrpark_rows=base,rejected_rows=len(rejected),jpeg_members=len(jpeg),safe_archive_entries=len(entries),
            dates=len(mapping),cameras=9,rows_by_role=dict(Counter(r['split'] for r in rows)),dates_by_role=dict(Counter(mapping.values())),date_roles=mapping,
            missing_members=0,unmapped_jpegs=0,image_members_decompressed=0,occupancy_targets_parsed=False,models_trained_or_scored=False,
            metadata_manifest=manifest.relative_to(ROOT).as_posix(),metadata_manifest_sha256=digest(manifest),reservation=reservation.relative_to(ROOT).as_posix(),reservation_sha256=digest(reservation),
            individual_image_content_rights_qualified=False,operational_image_use_allowed=False)
        dump(target/'summary.json',summary)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,metadata_gate_passed=True,summary=summary)
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        dump(folder/'run.json',report);dump(ROOT/'models/cnrpark_metadata_qualification.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='New-source factual metadata/archive/split qualification;no images or accuracy',started_at=protocol['started_at'],finished_at=report['finished_at'],
            source_ids=';'.join(protocol['source_ids']),split_ids='cnrpark-global-dates-v1;whole dates across9cameras',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Metadata parser and durable date reservation;no model use',epochs=0,batch_size=0,random_seed=124,hardware='CPU;file metadata only',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(summary),logs=folder.relative_to(ROOT).as_posix(),checkpoints='All original model weights unchanged',code_revision_basis='fde889c plus sealed source snapshots',implementation_sha256=hashes[paths[0]],
            conclusions='Metadata mapping/split pass;individual image-content permission unqualified,so no images scored/trained;final dates sealed')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,metadata_gate_passed=True,summary=summary),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)
if __name__=='__main__':main()
