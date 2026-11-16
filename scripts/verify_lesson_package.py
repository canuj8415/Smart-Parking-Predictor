"""Verify the lesson's declared payload; generated outputs are kept separately."""
import hashlib
import json
from pathlib import Path


def verify(root):
    root = Path(root).resolve()
    manifest = json.loads((root/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    seen = set()
    for item in manifest['entries']:
        name = item['path']; path = (root/name).resolve()
        if Path(name).is_absolute() or '..' in Path(name).parts or not path.is_relative_to(root) or name in seen:
            raise ValueError('Invalid or duplicate declared package path')
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != item['sha256'] or path.stat().st_size != item['bytes']:
            raise ValueError('Missing or changed payload: '+name)
        seen.add(name)
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
                    and p.name != 'PACKAGE_MANIFEST.json' and not p.relative_to(root).as_posix().startswith('outputs/')}
    if actual_files != seen:
        raise ValueError('Unexpected non-output files in package')
    return dict(files=len(seen), all_payload_hashes_match=True)


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), indent=2))
