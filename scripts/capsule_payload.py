"""Exact manifest/ZIP verification for the small archived lesson payload."""
import hashlib,json,stat,zipfile
from pathlib import Path,PurePosixPath
MANIFEST='PAYLOAD_MANIFEST.json'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_names(names):
    seen=set()
    for name in names:
        p=PurePosixPath(name)
        if (not name or name=='.' or '\\' in name or ':' in name or p.is_absolute() or any(x in ['.','..'] for x in p.parts)
                or p.as_posix()!=name or name.casefold() in seen):raise ValueError('Unsafe/duplicate capsule member:'+name)
        if name.startswith(('data/raw/','data/processed/','models/checkpoints/','models/pretrained/')) or p.suffix.casefold() in ['.pt','.pth','.npz']:
            raise ValueError('Raw/cache/model artifact excluded:'+name)
        if any(part.casefold() in ['kernel','runtime','__pycache__','.ipynb_checkpoints'] for part in p.parts):raise ValueError('Private runtime excluded:'+name)
        seen.add(name.casefold())


def verify_payload(root,expected_manifest_sha256=None):
    root=Path(root).resolve();manifest=root/MANIFEST
    if expected_manifest_sha256 is not None and digest(manifest)!=expected_manifest_sha256:raise ValueError('Payload manifest changed')
    value=json.loads(manifest.read_text(encoding='utf-8'));files=value['files'];safe_names(list(files)+[MANIFEST])
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=set(files)|{MANIFEST}:raise ValueError('Payload file set differs:missing='+str(set(files)-actual)+' extra='+str(actual-set(files)-{MANIFEST}))
    total=0
    for name,entry in files.items():
        original=root/name;path=original.resolve()
        if not path.is_relative_to(root) or original.is_symlink():raise ValueError('Payload member escaped its root')
        if digest(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:raise ValueError('Payload bytes changed:'+name)
        total+=entry['bytes']
    return dict(files=len(files),payload_bytes=total,manifest_sha256=digest(manifest))


def create_zip(root,destination):
    root=Path(root).resolve();verify_payload(root)
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(p for p in root.rglob('*') if p.is_file()):archive.write(path,path.relative_to(root).as_posix())


def extract_checked(archive_path,target,expected_manifest_sha256):
    target=Path(target).resolve()
    if target.exists():raise ValueError('Extraction target must be new')
    with zipfile.ZipFile(archive_path) as archive:
        infos=archive.infolist();safe_names([i.filename for i in infos])
        if any(i.flag_bits&1 or stat.S_ISLNK(i.external_attr>>16) or i.is_dir() for i in infos):raise ValueError('Encrypted/symlink/directory members excluded')
        body=archive.read(MANIFEST)
        if hashlib.sha256(body).hexdigest()!=expected_manifest_sha256:raise ValueError('ZIP manifest binding changed')
        manifest=json.loads(body);files=manifest['files']
        if {i.filename for i in infos}!=set(files)|{MANIFEST}:raise ValueError('ZIP file set differs from manifest')
        if any(i.filename!=MANIFEST and i.file_size!=files[i.filename]['bytes'] for i in infos):raise ValueError('ZIP size differs from manifest')
        if archive.testzip() is not None:raise ValueError('ZIP CRC check failed')
        # Validate all bytes BEFORE creating any extracted payload.
        for name,entry in files.items():
            data=archive.read(name)
            if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('ZIP member hash changed:'+name)
        target.mkdir(parents=True,exist_ok=False)
        for info in infos:
            path=target/info.filename;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(info))
    return verify_payload(target,expected_manifest_sha256)
