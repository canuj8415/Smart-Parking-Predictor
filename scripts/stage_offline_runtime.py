"""Recover hash-verified original wheel archives from the resolver cache, no network."""
import csv,email,hashlib,json,shutil,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,digest


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    source=ROOT/'data/manifests/runtime_wheelhouse_plan_v1.json';plan=json.loads(source.read_text(encoding='utf-8'))
    folder=ROOT/'dependencies/offline_app/v1';wheels=folder/'wheels';wheels.mkdir(parents=True,exist_ok=True)
    if (folder/'WHEELHOUSE_MANIFEST.json').exists():raise FileExistsError('Preserve completed wheelhouse')
    if shutil.disk_usage(folder).free<3*1024**3:raise RuntimeError('Reserve at least3GiBfor staged wheels and fresh install')
    assert plan['total_bytes']<=512*1024**2 and len(plan['entries'])==24
    wanted={row['sha256']:row for row in plan['entries']};sizes={row['bytes'] for row in plan['entries']};cached={}
    for path in (ROOT/'.cache/runtime_resolver').rglob('*.body'):
        if path.stat().st_size in sizes:
            checksum=digest(path)
            if checksum in wanted:cached[checksum]=path
    if set(cached)!=set(wanted):raise RuntimeError('Incomplete cache; missing verified artifacts:'+str([wanted[h]['filename'] for h in set(wanted)-set(cached)]))
    source_path=ROOT/'data/source_manifest.csv'
    with source_path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    if not any(row['source_id']=='SRC-PKG-003' for row in sources):
        record=dict(source_id='SRC-PKG-003',resource_type='official pinned software installer archives',resource='Windows CPython3.12 CPU app wheelhouse',
            original_creator='Individual package creators in per-release JSON and embedded licence/notices; PyTorch/NumPy/Pillow/Matplotlib and dependencies',
            source_url='https://download.pytorch.org/whl/cpu/',download_url='Exact PyPI/PyTorch artifact URLs in wheelhouse manifest/resource receipts',
            access_date=datetime.now(timezone.utc).isoformat(),access_time_precision='Cache recovery timestamps exact; prior resolver network access bounded by preserved operation/logs,per-file network times not captured',
            version='24resolved Windows/Python3.12 CPU wheels; versions and publisher SHA256 in manifest',
            license='Publisher open-source declarations and full original embedded notices retained per wheel; local academic use; no external distribution/legal clearance claim',
            permission='Authorized legitimate public software acquisition/local isolated installation; no accounts,agreements,paid services or shared-runtime changes',
            original_size=str(plan['total_bytes'])+'bytes/24wheel archives',local_location='dependencies/offline_app/v1/wheels/',
            sha256='Per-wheel publisher SHA256,archive CRC and licence-member hashes in WHEELHOUSE_MANIFEST.json',
            purpose='Fresh app-only offline dependency installation and compatibility checks',used_by='Runtime preparation; fresh-install validation pending',
            modifications='Original wheel bytes recovered from pip HTTP cache,not edited; originals/cache retained',
            attribution='Per-wheel creator/licence metadata and complete original notices retained',status='staging verified cached originals',
            open_issues='Existing base Python/Tk reused; Jupyter profile,new-machine/physical-offline and deployment rights separate')
        sources.append({key:record.get(key,'') for key in fields})
        with source_path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    entries=[];lock=[]
    for item in plan['entries']:
        origin=cached[item['sha256']]
        with zipfile.ZipFile(origin) as archive:
            if archive.testzip() is not None:raise ValueError('Wheel CRC failure')
            names=archive.namelist()
            if any(PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts for name in names):raise ValueError('Unsafe archive path')
            metadata_name=next(name for name in names if name.endswith('.dist-info/METADATA'))
            metadata=email.message_from_bytes(archive.read(metadata_name));assert metadata['Version']==item['version']
            notices=[name for name in names if any(part.lower().startswith(('license','licence','copying','notice')) for part in PurePosixPath(name).parts) and not name.endswith('/')]
            if not notices:raise ValueError('No embedded licence/notices:'+item['name'])
            notice_hashes={name:hashlib.sha256(archive.read(name)).hexdigest() for name in notices}
        target=wheels/item['filename']
        if target.exists():assert digest(target)==item['sha256']
        else:
            shutil.copyfile(origin,target);assert digest(target)==item['sha256']
            receipt('SRC-PKG-003',target,item['url'],'Original installer archive recovered from prior official resolver cache; no additional network transfer',
                acquisition_kind='verified_pip_cache_copy',parent_cache=origin.relative_to(ROOT).as_posix(),publisher_sha256=item['sha256'],
                exact_per_file_network_timestamp_captured=False,license_declaration=item['license_declaration'])
        entries.append(dict(item,path=target.relative_to(ROOT).as_posix(),embedded_notice_hashes=notice_hashes,crc_verified=True,full_sha256_verified=True,
            cache_origin=origin.relative_to(ROOT).as_posix()))
        lock.append(item['name']+'=='+item['version']+' --hash=sha256:'+item['sha256'])
    requirements=folder/'requirements-app-cpu-lock.txt';requirements.write_text('\n'.join(lock)+'\n',encoding='utf-8')
    manifest=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-PKG-003',
        profile='App-only Windows64/Python3.12 CPU; Jupyter dependencies not included',entries=entries,total_bytes=sum(e['bytes'] for e in entries),
        lock_path=requirements.relative_to(ROOT).as_posix(),lock_sha256=digest(requirements),
        selected_plan_sha256=digest(source),all_original_archives_and_notices_retained=True,
        network_transfer_during_staging=0,packages_installed_during_staging=0,offline_installation_tested=False)
    dump(folder/'WHEELHOUSE_MANIFEST.json',manifest)
    # Preserve the initial resolver report; correct its misleading no-download flag
    # in a new version rather than erasing the prior statement.
    corrected=dict(plan,previous_plan_sha256=digest(source),installer_files_acquired=True,
        cache_recovery_manifest=(folder/'WHEELHOUSE_MANIFEST.json').relative_to(ROOT).as_posix(),
        correction='pip --dry-run cached complete wheel archives before the post-resolution size check. All24now publisher-hash/CRC verified;208542037bytes is within512MiBbudget. No packages installed.')
    dump(ROOT/'data/manifests/runtime_wheelhouse_plan_v2.json',corrected)
    correction=ROOT/'data/provenance_corrections/RUNTIME_DRYRUN_CACHE_20261025.json';correction.parent.mkdir(parents=True,exist_ok=True)
    dump(correction,dict(recorded_at=datetime.now(timezone.utc).isoformat(),initial_plan='data/manifests/runtime_wheelhouse_plan_v1.json',initial_sha256=digest(source),
        incorrect_field='installer_files_acquired=False',corrected_plan='data/manifests/runtime_wheelhouse_plan_v2.json',
        reason='Resolver dry-run does not install packages but can download/cache complete archives. Initial flag was inaccurate; prior file retained.',
        observed_archive_bytes=manifest['total_bytes'],source_id='SRC-PKG-003'))
    print(json.dumps(dict(files=len(entries),bytes=manifest['total_bytes'],manifest=str(folder/'WHEELHOUSE_MANIFEST.json'),network_transfer_during_staging=0,packages_installed=0),indent=2))
