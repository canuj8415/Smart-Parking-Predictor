"""Capture bounded official metadata and core wheel candidates; no installers run."""
import html,json,re,sys,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename,canonicalize_name
from packaging.version import Version

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,digest

PINS={'torch':'2.14.0','torchvision':'0.29.0','numpy':'2.5.3','Pillow':'12.3.0','matplotlib':'3.11.2'}


def fetch(url,path,purpose):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SmartParkingPBL/0.2'}),timeout=20) as response:raw=response.read(4000001)
    if len(raw)>4000000:raise ValueError('Metadata response exceeds4MBbound')
    with path.open('xb') as stream:stream.write(raw)
    receipt('SRC-PKG-002',path,url,purpose,metadata_only=True)
    return raw


if __name__=='__main__':
    at=datetime.now(timezone.utc);folder=ROOT/'data/raw/runtime_metadata'/at.strftime('%Y%m%dT%H%M%S%fZ');folder.mkdir(parents=True,exist_ok=False)
    candidates=[];failures=[];tags=set(sys_tags())
    for name,version in PINS.items():
        url=f'https://pypi.org/pypi/{name}/{version}/json'
        try:
            path=folder/(name+'.json');metadata=json.loads(fetch(url,path,'Official existing-app pin release/rights/file metadata; no wheel downloaded'))
            assert metadata['info']['version']==version
            record=dict(distribution=name,public_version=version,metadata_url=url,metadata_path=path.relative_to(ROOT).as_posix(),metadata_sha256=digest(path),
                author=metadata['info'].get('author') or metadata['info'].get('author_email'),
                license_expression=metadata['info'].get('license_expression'),license_text=metadata['info'].get('license'),
                requires_dist=metadata['info'].get('requires_dist'),requires_python=metadata['info'].get('requires_python'))
            selected=[]
            if name in {'torch','torchvision'}:
                index=f'https://download.pytorch.org/whl/cpu/{name}/';index_path=folder/(name+'_cpu_index.html')
                text=fetch(index,index_path,'Official CPU wheel index inspection; no GPU/CUDA package or installer acquired').decode('utf-8')
                for href in re.findall(r'href=["\']([^"\']+)',text):
                    wheel_url=urllib.parse.urljoin(index,html.unescape(href));parts=urllib.parse.urlsplit(wheel_url)
                    filename=urllib.parse.unquote(parts.path.rsplit('/',1)[-1])
                    if not filename.endswith('.whl'):continue
                    try:wheel_name,wheel_version,_,wheel_tags=parse_wheel_filename(filename)
                    except ValueError:continue
                    if canonicalize_name(name)!=wheel_name or Version(wheel_version.base_version)!=Version(version) or not wheel_tags&tags:continue
                    if 'cpu' not in str(wheel_version.local or ''):continue
                    expected=urllib.parse.parse_qs(parts.fragment).get('sha256',[None])[0]
                    selected.append(dict(filename=filename,url=urllib.parse.urlunsplit(parts._replace(fragment='')),sha256=expected,bytes=None,variant='official CPU wheel',index_url=index))
                record['cpu_index_path']=index_path.relative_to(ROOT).as_posix();record['cpu_index_sha256']=digest(index_path)
            else:
                for asset in metadata['urls']:
                    if asset.get('yanked') or not asset['filename'].endswith('.whl'):continue
                    try:_,_,_,wheel_tags=parse_wheel_filename(asset['filename'])
                    except ValueError:continue
                    if wheel_tags&tags:selected.append(dict(filename=asset['filename'],url=asset['url'],sha256=asset['digests']['sha256'],bytes=asset['size'],variant='official PyPI compatible wheel'))
            record['compatible_core_candidates']=selected;candidates.append(record)
        except Exception as error:failures.append(dict(distribution=name,version=version,url=url,error=repr(error)))
    plan=dict(captured_at=at.isoformat(),source_id='SRC-PKG-002',platform='Current Windows64/Python3.12 interpreter tags',
        metadata_folder=folder.relative_to(ROOT).as_posix(),core_candidates=candidates,failures=failures,
        wheel_files_downloaded=0,packages_installed=0,transitive_dependency_closure_resolved=False,
        all_licences_and_wheel_sizes_verified=False,offline_installation_accepted=False,
        next_step='Resolve complete dependency closure,verify CPU wheel size/sha/licence and bounded total budget,then acquire immutable wheels without changing shared Python; perform a new offline fresh-venv install and compatibility trial.')
    destination=ROOT/'data/manifests/runtime_core_candidates_v1.json'
    if destination.exists():raise FileExistsError('Preserve existing metadata selection plan')
    destination.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plan=destination.relative_to(ROOT).as_posix(),candidates={r['distribution']:len(r['compatible_core_candidates']) for r in candidates},failures=failures,wheels_downloaded=0),indent=2))
