"""Resolve app-only CPU wheels from official indexes without installing packages."""
import hashlib,json,os,subprocess,sys,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from packaging.version import Version

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,digest


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    target=ROOT/'data/manifests/runtime_wheelhouse_plan_v1.json'
    if target.exists():raise FileExistsError('Preserve resolved version1 plan')
    started=datetime.now(timezone.utc);folder=ROOT/'data/raw/runtime_metadata'/('resolution_'+started.strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True,exist_ok=False)
    prior=json.loads((ROOT/'models/installation_readiness.json').read_text(encoding='utf-8'))
    python=ROOT/prior['fresh_environment']/'Scripts/python.exe'
    roots=['torch==2.14.0+cpu','torchvision==0.29.0+cpu','numpy==2.5.3','Pillow==12.3.0','matplotlib==3.11.2','opencv-python-headless==4.13.0.92']
    requirements=folder/'requested_roots.txt';requirements.write_text('\n'.join(roots)+'\n',encoding='utf-8')
    env=os.environ.copy();env.update(PIP_CONFIG_FILE=os.devnull,PIP_NO_INDEX='0',PIP_DISABLE_PIP_VERSION_CHECK='1',
        PIP_CACHE_DIR=str(ROOT/'.cache/runtime_resolver'),PIP_EXTRA_INDEX_URL='',PIP_FIND_LINKS='',PIP_TRUSTED_HOST='')
    command=[str(python),'-m','pip','install','--dry-run','--ignore-installed','--only-binary=:all:','--no-input',
        '--disable-pip-version-check','--timeout','25','--retries','1','--report',str(folder/'pip_report.json'),
        '--index-url','https://pypi.org/simple','--find-links','https://download.pytorch.org/whl/cpu/torch/',
        '--find-links','https://download.pytorch.org/whl/cpu/torchvision/','-r',str(requirements)]
    dump(folder/'operation.json',dict(started_at=started.isoformat(),command=command,source_id='SRC-PKG-002',packages_installed=False))
    with (folder/'resolver_stdout.txt').open('w',encoding='utf-8') as out,(folder/'resolver_stderr.txt').open('w',encoding='utf-8') as err:
        process=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=180)
    if process.returncode:raise RuntimeError('Official metadata resolution failed; preserved logs at '+str(folder))
    report=json.loads((folder/'pip_report.json').read_text(encoding='utf-8'));entries=[]
    for item in report['install']:
        meta=item['metadata'];name=meta['name'];version=meta['version'];url=item['download_info']['url'];parts=urllib.parse.urlsplit(url)
        if parts.hostname not in {'files.pythonhosted.org','download.pytorch.org','download-r2.pytorch.org'}:raise ValueError('Unexpected artifact provider')
        if not parts.path.endswith('.whl'):raise ValueError('Only wheels are allowed')
        expected=item['download_info']['archive_info']['hashes']['sha256']
        api=f'https://pypi.org/pypi/{name}/{version.split("+",1)[0]}/json'
        with urllib.request.urlopen(api,timeout=20) as response:raw=response.read(4000001)
        if len(raw)>4000000:raise ValueError('Metadata response exceeds bound')
        original=folder/(name+'.json')
        with original.open('xb') as stream:stream.write(raw)
        receipt('SRC-PKG-002',original,api,'Official resolved app dependency release/rights metadata; no manual package installation',metadata_only=True)
        info=json.loads(raw)['info'];declaration=info.get('license_expression') or info.get('license') or ''
        classifiers=info.get('classifiers',[])
        if not declaration and not any('License :: OSI Approved' in c for c in classifiers):raise ValueError('Missing publisher licence declaration: '+name)
        if 'LicenseRef-Proprietary' in declaration:raise ValueError('Unresolved licence: '+name)
        if parts.hostname=='files.pythonhosted.org':
            asset=next(a for a in json.loads(raw)['urls'] if a['url']==url)
            assert asset['digests']['sha256']==expected and not asset.get('yanked');size=asset['size']
        else:
            with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=20) as response:
                size=int(response.headers['Content-Length']);head=dict(url=url,status=response.status,headers=dict(response.headers),observed_at=datetime.now(timezone.utc).isoformat())
            dump(folder/(name+'_head.json'),head)
        if size>256*1024*1024:raise ValueError('Per-artifact256MiBbudget exceeded: '+name)
        entries.append(dict(name=name,version=version,filename=urllib.parse.unquote(parts.path.rsplit('/',1)[-1]),url=url,sha256=expected,bytes=size,
            license_declaration=declaration,license_classifiers=[c for c in classifiers if c.startswith('License')],
            author=info.get('author') or info.get('author_email'),metadata_path=original.relative_to(ROOT).as_posix(),metadata_sha256=digest(original),
            requirements_from_selected_variant=meta.get('requires_dist',[])))
    total=sum(e['bytes'] for e in entries)
    if total>512*1024*1024:raise ValueError('Total512MiBdownload budget exceeded')
    if any(e['name'].lower().startswith(('nvidia','cuda','triton')) for e in entries):raise ValueError('GPU packages unexpectedly selected')
    assert {e['name'].lower():e['version'] for e in entries}['torch']=='2.14.0+cpu'
    plan=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-PKG-002',
        requested_roots=roots,profile='App-only Windows64/Python3.12 CPU; Jupyter environment separate',
        resolver='pip dry-run/ignore-installed/only-binary using separate empty venv; no package installation',
        resolver_report_path=(folder/'pip_report.json').relative_to(ROOT).as_posix(),resolver_report_sha256=digest(folder/'pip_report.json'),
        metadata_folder=folder.relative_to(ROOT).as_posix(),entries=entries,total_bytes=total,
        dependency_closure_resolved=True,installer_files_acquired='pip dry-run may cache complete wheel bodies; inspect and hash-verify cache before use',offline_installation_tested=False,
        notice_policy='Retain original wheels and complete embedded licence/notices; local academic use only, no publication/redistribution clearance claimed',
        budget=dict(per_file_bytes=256*1024*1024,total_bytes=512*1024*1024))
    dump(target,plan)
    print(json.dumps(dict(plan=target.relative_to(ROOT).as_posix(),distributions=len(entries),total_bytes=total,names=[e['name'] for e in entries],packages_installed=False),indent=2))
