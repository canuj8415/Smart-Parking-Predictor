"""ENV-03 dependency/weight audit: installed versions vs lock vs wheel hashes vs licences vs weights.

Read-only reconciliation; no installs, downloads or model calls. Not an experiment trial.
"""
import csv, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm = lambda n: re.sub(r'[-_.]+', '-', n).lower()

def main(freeze_path, out_path):
    freeze = {}
    for line in Path(freeze_path).read_text(encoding='utf-8', errors='replace').splitlines():
        if '==' in line: n, v = line.strip().split('==', 1); freeze[norm(n)] = v
    lock_path = ROOT / 'dependencies/offline_app/v1/requirements-app-cpu-lock.txt'
    lock = {}
    for line in lock_path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'([A-Za-z0-9_.-]+)==(\S+)\s+--hash=sha256:([0-9a-f]{64})', line.strip())
        if m: lock[norm(m[1])] = dict(version=m[2], sha256=m[3])
    wheel_manifest = json.loads((ROOT / 'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json').read_text(encoding='utf-8'))
    wheels = []
    for e in wheel_manifest['entries']:
        f = ROOT / 'dependencies/offline_app/v1/wheels' / e['filename']
        actual = sha(f) if f.exists() else None
        wheels.append(dict(name=e['name'], version=e['version'], file_present=f.exists(), sha256_matches_manifest=actual == e['sha256'],
                           sha256_matches_lock=lock.get(norm(e['name']), {}).get('sha256') == e['sha256'],
                           license=e.get('license_declaration') or ', '.join(e.get('license_classifiers', [])) or 'UNDECLARED in metadata'))
    inventory = json.loads((ROOT / 'docs/DEPENDENCY_INVENTORY.json').read_text(encoding='utf-8'))
    direct = []
    for n, meta in inventory['direct_packages'].items():
        installed = freeze.get(norm(n)); locked = lock.get(norm(n), {}).get('version')
        direct.append(dict(name=n, inventory_version=meta['version'], installed_version=installed,
                           inventory_matches_installed=installed == meta['version'],
                           lock_version=locked, lock_matches_installed=(locked is None) or locked.split('+')[0] == installed,
                           license=(meta.get('license') or '')[:200]))
    weights = []
    with open(ROOT / 'data/source_manifest.csv', encoding='utf-8', newline='') as fh:
        for r in csv.DictReader(fh):
            if r['source_id'].startswith('SRC-MOD-'):
                path = next((v for v in r.values() if isinstance(v, str) and v.startswith('models/pretrained/')), None)
                expected = next((v for v in r.values() if isinstance(v, str) and re.fullmatch(r'[0-9a-f]{64}', v)), None)
                p = ROOT / path if path else None
                weights.append(dict(source_id=r['source_id'], path=path, present=bool(p and p.exists()),
                                    sha256_matches_manifest=bool(p and p.exists() and sha(p) == expected), expected_sha256=expected))
    drift = [d for d in direct if not d['inventory_matches_installed'] or not d['lock_matches_installed']]
    report = dict(created_at=datetime.now(timezone.utc).isoformat(), requirement='ENV-03', python_freeze=str(Path(freeze_path).relative_to(ROOT)),
                  freeze_sha256=sha(freeze_path), installed_packages=len(freeze), lock_sha256=sha(lock_path),
                  lock_matches_wheel_manifest_record=sha(lock_path) == wheel_manifest['lock_sha256'],
                  direct_packages=direct, version_drift=drift, offline_wheels=wheels,
                  wheels_all_present_and_hash_exact=all(w['file_present'] and w['sha256_matches_manifest'] and w['sha256_matches_lock'] for w in wheels),
                  wheels_with_undeclared_license=[w['name'] for w in wheels if w['license'].startswith('UNDECLARED')],
                  weights=weights, weights_all_hash_exact=all(w['sha256_matches_manifest'] for w in weights),
                  limitations='Licences are package-declared metadata, not legal review;transitive notices inside wheels not read;weights carry upstream dataset terms(see LICENSING_RECORD/THIRD_PARTY_SOURCES).',
                  new_downloads=0, installs=0, model_calls=0)
    Path(out_path).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['installed_packages', 'lock_matches_wheel_manifest_record', 'wheels_all_present_and_hash_exact', 'wheels_with_undeclared_license', 'weights_all_hash_exact']}, indent=1))
    print('drift', [(d['name'], d['inventory_version'], d['installed_version'], d['lock_version']) for d in drift])
    print('weights', [(w['source_id'], w['present'], w['sha256_matches_manifest']) for w in weights])

if __name__ == '__main__':
    main(ROOT / sys.argv[1], ROOT / sys.argv[2])
