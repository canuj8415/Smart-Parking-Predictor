"""Read archive headers only; identify dates absent from prior experiment evidence.

Gzip/tar bytes are streamed to reach headers; JPEG pixels and XML labels are
neither decoded nor parsed. Candidate dates remain provisional, not final data.
"""
import csv,json,re,sys,tarfile,time
from collections import Counter
from datetime import date,datetime,timezone
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T001740Z'
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def camera_path(name):
    parts=PurePosixPath(name).parts
    if PurePosixPath(name).is_absolute() or '..' in parts or any(':' in p for p in parts):raise ValueError('Unsafe archive member')
    indices=[i for i,p in enumerate(parts) if p.casefold()=='pklot']
    if not indices or indices[-1]+1>=len(parts):raise ValueError('Unrecognized source folder')
    return parts[indices[-1]+1].casefold()
def main():
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    assert not state['active_validation_jobs'] and not state['active_training_jobs']
    started=datetime.now(timezone.utc);rid='PKLOT-INVENTORY-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    archive=ROOT/'data/raw/pklot_subset/PKLot.tar.gz';clock=time.perf_counter()
    with (ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8-sig',newline='') as stream:old=list(csv.DictReader(stream))
    cameras={camera_path(r['image']):r['camera_id'] for r in old};assert len(cameras)==3
    # Conservative exclusion: any historical2012/2013date mentioned in model,
    # manifest,layout or experiment JSON is ineligible,even if only metadata was
    # inspected. Raw acquisition inventories are not model-use evidence.
    records=[];used=set();pattern=re.compile(r'201[23]-\d{2}-\d{2}')
    candidates=set((ROOT/'models').glob('*.json'))|set((ROOT/'data/manifests').glob('*.json'))|set((ROOT/'configs/layouts').glob('*.json'))|set((ROOT/'experiments/results').rglob('*.json'))|set((ROOT/'data/holdout_claims').glob('*.json'))
    for p in sorted(candidates):
        text=p.read_text(encoding='utf-8');days=set(pattern.findall(p.name+'\n'+text))
        if days:used.update(days);records.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p),excluded_dates=sorted(days)))
    paths=['scripts/inventory_unused_pklot_dates.py'];hashes={p:digest(ROOT/p) for p in paths}
    weights=json.loads((ROOT/'experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json').read_text(encoding='utf-8'))
    protocol=dict(run_id=rid,started_at=started.isoformat(),seed=125,source_ids=['SRC-DS-001'],source_hashes=hashes,
        hypothesis='The existing licensed full archive may contain valid paired camera/date groups never mentioned in earlier model/experiment inputs,which can support a later fresh reservation without replaying consumed groups.',
        archive_sha256=digest(archive),exclusion_records=records,excluded_dates=sorted(used),canonical_camera_mapping=cameras,
        gates=['Safe paired member metadata and valid matching folder/filename dates','No candidate date overlaps conservative prior evidence date set','No JPEG decoding,XML label parsing or model use','Original model hashes unchanged'],
        limitations=['Regex exclusion is conservative and may exclude dates never actually used','Candidate freshness still needs selected-group provenance/duplicate audit before any final reservation',
            'Gzip decompression needed to reach headers;no image-format decoding or annotation parsing','Original known cameras;not a new-carpark benchmark'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    members={};duplicates=[];rejected=[];seen=0;deadline=time.monotonic()+240
    try:
        with tarfile.open(archive,mode='r|gz') as source:
            for member in source:
                if (folder/'CANCEL').exists() or time.monotonic()>deadline:raise InterruptedError('Metadata scan cancellation/deadline')
                if not member.isfile():continue
                suffix=PurePosixPath(member.name).suffix.lower()
                if suffix not in ('.jpg','.xml'):continue
                seen+=1
                try:
                    camera=camera_path(member.name)
                    if camera not in cameras:raise ValueError('Unknown camera folder')
                    day=PurePosixPath(member.name).parent.name
                    if date.fromisoformat(day).isoformat()!=day or PurePosixPath(member.name).stem[:10]!=day:raise ValueError('Folder/filename date mismatch')
                    if not 0<member.size<=10*1024**2:raise ValueError('Unexpected member size')
                    key=str(PurePosixPath(member.name).with_suffix('')).casefold();pair=members.setdefault(key,{})
                    if suffix in pair:duplicates.append(member.name);continue
                    pair[suffix]=dict(path=member.name,bytes=member.size,camera_id=cameras[camera],capture_date=day)
                except ValueError as error:rejected.append(dict(path=member.name,error=str(error)))
                if seen%2000==0:dump(folder/'progress.json',dict(phase='streaming_headers',members_seen=seen))
        pairs=[]
        for pair in members.values():
            if '.jpg' not in pair or '.xml' not in pair:continue
            image=pair['.jpg'];annotation=pair['.xml'];assert image['capture_date']==annotation['capture_date']
            pairs.append(dict(image_member=image['path'],annotation_member=annotation['path'],camera_id=image['camera_id'],capture_date=image['capture_date'],
                image_bytes=image['bytes'],annotation_bytes=annotation['bytes'],eligible_date=image['capture_date'] not in used))
        assert pairs and not duplicates
        target=ROOT/'data/splits/pklot-archive-inventory-v1';target.mkdir(parents=True,exist_ok=False)
        with (target/'pairs.csv').open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(pairs[0]));w.writeheader();w.writerows(sorted(pairs,key=lambda r:r['image_member']))
        groups=Counter((r['camera_id'],r['capture_date']) for r in pairs);eligible=Counter((r['camera_id'],r['capture_date']) for r in pairs if r['eligible_date'])
        summary=dict(valid_paired_frames=len(pairs),valid_camera_date_groups=len(groups),valid_dates=len({r['capture_date'] for r in pairs}),
            provisional_unused_frames=sum(eligible.values()),provisional_unused_date_groups=len(eligible),provisional_unused_global_dates=len({d for _,d in eligible}),
            eligible_groups=[dict(camera_id=c,capture_date=d,paired_frames=n) for (c,d),n in sorted(eligible.items())],
            rejected_member_metadata=len(rejected),duplicate_members=len(duplicates),jpeg_pixels_decoded=0,xml_labels_parsed=0,models_trained_or_scored=False,
            manifest='data/splits/pklot-archive-inventory-v1/pairs.csv',manifest_sha256=digest(target/'pairs.csv'),fresh_final_reserved=False)
        assert all(r['capture_date'] not in used for r in pairs if r['eligible_date'])
        assert digest(archive)==protocol['archive_sha256'] and all(digest(ROOT/p)==h for p,h in weights.items())
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,metadata_inventory_gate_passed=True,summary=summary)
        dump(folder/'run.json',report);dump(folder/'rejected_member_metadata.json',rejected);dump(ROOT/'models/pklot_unused_date_inventory.json',report);dump(target/'summary.json',summary)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Licensed archive metadata/provisional fresh-date inventory',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids='SRC-DS-001',split_ids='No new split/reservation;all prior evidence dates excluded',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Archive headers;no image/model use',epochs=0,batch_size=0,random_seed=125,hardware='CPU;gzip/tar metadata scan',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(summary),logs=folder.relative_to(ROOT).as_posix(),checkpoints='Original weights unchanged',code_revision_basis='fde889c plus source snapshot/CNRrecovery',implementation_sha256=hashes[paths[0]],conclusions='Metadata inventory only;provisional candidates require further audit/reservation;no accuracy or new-carpark claim')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,summary=summary),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)
if __name__=='__main__':main()
