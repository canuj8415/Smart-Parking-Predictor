"""Prepare a separate immutable Jupyter wheel extension; never install packages.

pip dry-run may download complete archives into its local cache. Actual selected
archive size is checked after resolution; this is not a pre-transfer byte cap.
"""
import concurrent.futures,csv,email,hashlib,json,os,shutil,subprocess,sys,urllib.parse,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt

SOURCE='SRC-PKG-004'
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def main():
    target=ROOT/'dependencies/offline_jupyter/v1';manifest=target/'WHEELHOUSE_MANIFEST.json'
    if manifest.exists():raise FileExistsError('Keep immutable completed Jupyter wheelhouse')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    raw=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'data/raw/jupyter_metadata'/stamp
    if len(sys.argv)>1:
        assert raw.is_relative_to(ROOT/'data/raw/jupyter_metadata') and (raw/'pip_report.json').exists()
        assert json.loads((raw/'completion.json').read_text(encoding='utf-8'))['returncode']==0
    else:raw.mkdir(parents=True,exist_ok=False)
    app=json.loads((ROOT/'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json').read_text(encoding='utf-8'))
    constraints=raw/'app_constraints.txt';constraints.write_text('\n'.join(e['name']+'=='+e['version'] for e in app['entries'])+'\n')
    roots=['jupyterlab==4.6.3','ipykernel==7.3.0','nbclient==0.11.0','nbformat==5.11.1','matplotlib-inline==0.2.2']
    python=ROOT/'outputs/installation_checks/OFFLINE-INSTALL-20261025T210141239920Z/venv/Scripts/python.exe'
    env=os.environ.copy();env.update(PIP_CONFIG_FILE=os.devnull,PIP_NO_INDEX='0',PIP_EXTRA_INDEX_URL='',PIP_FIND_LINKS='',
        PIP_TRUSTED_HOST='',PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_CACHE_DIR=str(ROOT/'.cache/jupyter_resolver'))
    command=[str(python),'-m','pip','install','--dry-run','--ignore-installed','--only-binary=:all:','--no-input',
        '--disable-pip-version-check','--timeout','20','--retries','1','--report',str(raw/'pip_report.json'),
        '--index-url','https://pypi.org/simple','-c',str(constraints),*roots]
    if len(sys.argv)==1:
        dump(raw/'operation.json',dict(started_at=datetime.now(timezone.utc).isoformat(),command=command,
            packages_installed=False,complete_archives_may_be_downloaded_to_cache=True,post_resolution_incremental_budget_bytes=128*1024**2))
        with (raw/'stdout.txt').open('w',encoding='utf-8') as out,(raw/'stderr.txt').open('w',encoding='utf-8') as err:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=300)
        dump(raw/'completion.json',dict(finished_at=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
        if result.returncode:raise RuntimeError('Resolver failed; preserve '+str(raw))
    report=json.loads((raw/'pip_report.json').read_text(encoding='utf-8'));app_names={e['name'].lower().replace('_','-'):e for e in app['entries']}
    selected=[]
    for item in report['install']:
        meta=item['metadata'];name=meta['name'];key=name.lower().replace('_','-')
        if key in app_names:
            assert meta['version']==app_names[key]['version'];continue
        selected.append(item)
    def metadata(item):
        name=item['metadata']['name'];version=item['metadata']['version'];url=item['download_info']['url']
        if urllib.parse.urlsplit(url).hostname!='files.pythonhosted.org' or not url.endswith('.whl'):raise ValueError('Unexpected wheel provider')
        api=f'https://pypi.org/pypi/{name}/{version}/json'
        with urllib.request.urlopen(api,timeout=25) as response:data=response.read(4000001)
        if len(data)>4000000:raise ValueError('Oversized metadata')
        path=raw/(name+'.json')
        with path.open('xb') as stream:stream.write(data)
        release=json.loads(data);asset=next(e for e in release['urls'] if e['url']==url)
        sha=item['download_info']['archive_info']['hashes']['sha256']
        assert sha==asset['digests']['sha256'] and not asset.get('yanked')
        info=release['info'];licence=info.get('license_expression') or info.get('license') or ''
        classifiers=[c for c in info.get('classifiers',[]) if c.startswith('License')]
        if not licence and not any('OSI Approved' in c for c in classifiers):raise ValueError('Missing licence: '+name)
        if 'LicenseRef-Proprietary' in licence:raise ValueError('Unresolved rights')
        return dict(name=name,version=version,url=url,filename=urllib.parse.unquote(url.rsplit('/',1)[-1]),sha256=sha,bytes=asset['size'],
            metadata_path=path.relative_to(ROOT).as_posix(),metadata_sha256=digest(path),metadata_url=api,
            license_declaration=licence,license_classifiers=classifiers,author=info.get('author') or info.get('author_email'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:entries=list(pool.map(metadata,selected))
    total=sum(e['bytes'] for e in entries)
    assert total<128*1024**2 and all(e['bytes']<64*1024**2 for e in entries)
    sizes={e['bytes'] for e in entries};wanted={e['sha256'] for e in entries};cached={}
    for path in (ROOT/'.cache/jupyter_resolver').rglob('*.body'):
        if path.stat().st_size in sizes:
            checksum=digest(path)
            if checksum in wanted:cached[checksum]=path
    if set(cached)!=wanted:raise RuntimeError('Missing original cache bodies; do not invent acquisition')
    for e in entries:
        with zipfile.ZipFile(cached[e['sha256']]) as archive:
            assert archive.testzip() is None
            if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n for n in archive.namelist()):raise ValueError('Unsafe ZIP path')
            names=[n for n in archive.namelist() if not n.endswith('/') and any(p.lower().startswith(('license','licence','copying','notice')) for p in PurePosixPath(n).parts)]
            if not names:raise ValueError('Missing embedded licence/notices: '+e['name'])
            meta=email.message_from_bytes(archive.read(next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))))
            assert meta['Version']==e['version']
            e['embedded_notice_hashes']={n:hashlib.sha256(archive.read(n)).hexdigest() for n in names}
    catalog=ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;rows=list(r)
    if any(r['source_id']==SOURCE for r in rows):raise ValueError('Source already registered; inspect retained partial work')
    record=dict(source_id=SOURCE,resource_type='official software metadata and pinned installer archives',resource='JupyterLab and notebook-kernel Windows CPython3.12 offline extension',
        original_creator='Individual package creators in original PyPI release JSON and embedded notices',source_url='https://pypi.org/',download_url='Per-file official JSON/artifact URLs in wheelhouse manifest and receipts',
        access_date=datetime.now(timezone.utc).isoformat(),access_time_precision='Resolver start/end bounds; exact local copy/verification receipts; per-file original network times not captured',
        version='Pinned JupyterLab4.6.3/ipykernel7.3.0/nbclient0.11.0/nbformat5.11.1 plus complete resolved extension',
        license='Per-wheel publisher open-source declarations and original notices retained; local academic use; external redistribution clearance not claimed',
        permission='Authorized public software acquisition and isolated local installation',original_size=str(total)+' bytes/'+str(len(entries))+' extension wheels',
        local_location=target.relative_to(ROOT).as_posix(),sha256='Full per-artifact publisher SHA256 and embedded notice hashes in manifest',
        purpose='Fresh offline Jupyter notebook execution; app-only profile preserved',used_by='Offline installation validation pending',
        modifications='Original archives copied from resolver HTTP cache; no package installation during acquisition',attribution='Complete original creator/licence/notices retained',
        status='Publisher hashes/ZIP CRC/notices verified',open_issues='Existing base Python/OS/assets reused; no physical/new-machine/manual acceptance')
    rows.append({f:record.get(f,'') for f in fields})
    with catalog.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(rows)
    wheels=target/'wheels';wheels.mkdir(parents=True,exist_ok=True)
    for e in entries:
        origin=cached[e['sha256']];path=wheels/e['filename'];shutil.copyfile(origin,path);assert digest(path)==e['sha256']
        e.update(path=path.relative_to(ROOT).as_posix(),crc_verified=True,full_sha256_verified=True,source_id=SOURCE)
        receipt(SOURCE,ROOT/e['metadata_path'],e['metadata_url'],'Official pinned Jupyter dependency release metadata',metadata_only=True)
        receipt(SOURCE,path,e['url'],'Original Jupyter dependency wheel recovered from resolver cache without further network transfer',
            acquisition_kind='verified_pip_cache_copy',publisher_sha256=e['sha256'],parent_cache=origin.relative_to(ROOT).as_posix(),exact_per_file_network_timestamp_captured=False)
    combined=[*app['entries'],*entries];lock=target/'requirements-app-jupyter-lock.txt'
    lock.write_text('\n'.join(e['name']+'=='+e['version']+' --hash=sha256:'+e['sha256'] for e in combined)+'\n',encoding='utf-8')
    value=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),source_id=SOURCE,entries=entries,
        app_manifest_path='dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json',app_manifest_sha256=digest(ROOT/'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json'),
        extension_bytes=total,extension_wheels=len(entries),combined_wheels=len(combined),combined_bytes=app['total_bytes']+total,
        lock_path=lock.relative_to(ROOT).as_posix(),lock_sha256=digest(lock),resolver_report_path=(raw/'pip_report.json').relative_to(ROOT).as_posix(),
        resolver_report_sha256=digest(raw/'pip_report.json'),packages_installed_during_acquisition=False,
        size_gate='Post-resolution cache size verification,not pre-transfer hard cap',offline_installation_tested=False)
    dump(manifest,value);dump(ROOT/'data/manifests/offline_jupyter_v1.json',value)
    print(json.dumps({k:value[k] for k in ['extension_bytes','extension_wheels','combined_wheels','combined_bytes']},indent=2))

if __name__=='__main__':main()
