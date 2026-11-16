"""Minimal local lesson copy; no live inputs, trainers or production weights."""
import ast
import csv
import hashlib
import json
import shutil
from pathlib import Path

LESSON_RUN = 'SG-LESSON-20261026T092240303436Z'


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root, name):
    if not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('Package entries must be relative paths without traversal')
    result = (Path(root)/name).resolve()
    if not result.is_relative_to(Path(root).resolve()):
        raise ValueError('Package entry escapes its root')
    return result


def verify_payload(root, manifest):
    seen = set()
    for entry in manifest['entries']:
        name = entry['path']; path = safe_path(root, name)
        if name in seen or path.stat().st_size != entry['bytes'] or file_hash(path) != entry['sha256']:
            raise ValueError('Missing, duplicate or changed payload: '+name)
        seen.add(name)
    actual = {p.relative_to(root).as_posix() for p in Path(root).rglob('*') if p.is_file()
              and p.name != 'PACKAGE_MANIFEST.json' and not p.relative_to(root).as_posix().startswith('outputs/')}
    if actual != seen:
        raise ValueError('Unexpected non-output file in lesson package')
    return dict(files=len(seen), bytes=sum(e['bytes'] for e in manifest['entries']), all_hashes_match=True)


def build_package(root, destination, created_at):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    allowed = root/'outputs/singapore_lesson_packages'
    if not destination.is_relative_to(allowed) or destination == allowed:
        raise ValueError('A new dedicated local lesson-package folder is required')
    destination.mkdir(parents=True, exist_ok=False)
    def load(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    report = load(f'experiments/results/{LESSON_RUN}/run.json')
    assert report['lesson_gate_passed'] and not report['real_final_evaluated']
    copied = {}
    def copy(name, expected=None):
        source = safe_path(root, name); target = safe_path(destination, name)
        if expected is not None and file_hash(source) != expected:
            raise ValueError('Original lesson input changed: '+name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert file_hash(target) == file_hash(source)
        copied[name] = file_hash(source)
    for name, expected in report['notebook_checks']['input_hashes'].items():
        if not (name.startswith('data/manifests/') or name.startswith('experiments/results/')):
            raise ValueError('Lesson input is outside the archived whitelist')
        copy(name, expected)
    assert len(report['notebook_checks']['input_hashes']) == 10
    copy(report['notebook'], report['executed_notebook_sha256'])
    for name in ['src/smart_parking/__init__.py', 'src/smart_parking/provenance.py', 'src/smart_parking/singapore_lesson.py',
                 'scripts/execute_notebook.py', 'scripts/offline_jupyter_guard.py', 'scripts/singapore_lesson_guard.py',
                 'scripts/verify_lesson_package.py']:
        copy(name, report['source_hashes'].get(name))
    runner_source = (root/'scripts/validate_singapore_lesson.py').read_text(encoding='utf-8')
    assert file_hash(root/'scripts/validate_singapore_lesson.py') == report['source_hashes']['scripts/validate_singapore_lesson.py']
    tree = ast.parse(runner_source)
    functions = {node.name: ast.get_source_segment(runner_source, node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    child = functions['child']
    assert child.count('    nbformat.write(book, source)') == 1
    # Save only an executed copy. Never rewrite the original packaged notebook.
    child = child.replace('    nbformat.write(book, source)\n', '')
    runner = ('"""Execute the read-only lesson, keeping all original payload bytes intact."""\n'
              'import argparse,base64,hashlib,json,os,sys\nfrom datetime import datetime,timezone\nfrom pathlib import Path\n'
              'sys.dont_write_bytecode=True\nROOT=Path(__file__).resolve().parent\nsys.path.insert(0,str(ROOT/"scripts"))\n\n'
              +functions['dump']+'\n\n'+functions['cell_hash']+'\n\n'+child+'\n\n'
              'if __name__=="__main__":\n'
              '    from verify_lesson_package import verify\n    verify(ROOT)\n'
              '    parser=argparse.ArgumentParser(description=__doc__)\n'
              '    parser.add_argument("--output",type=Path)\n    args=parser.parse_args()\n'
              '    output=args.output or ROOT/"outputs/executions"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")\n'
              '    output.mkdir(parents=True,exist_ok=False)\n    child(output)\n'
              '    print("Executed lesson saved:",output/"executed_notebook.ipynb")\n')
    (destination/'run_lesson.py').write_text(runner, encoding='utf-8')
    with (root/'data/source_manifest.csv').open(encoding='utf-8-sig', newline='') as stream:
        sources = {row['source_id']: row for row in csv.DictReader(stream)}
    admission = load('experiments/results/SG-HISTORY-20261026T074623970649Z/run.json')
    selected = {r['path']: r for r in admission['selected_snapshots']}
    receipts = [json.loads(line) for line in (root/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    historical_receipts = []
    for item in receipts:
        if item['source_id'] == 'SRC-LIVE-001' and item['local_path'] in selected:
            original = selected[item['local_path']]
            if item['sha256'] != original['sha256'] or item['accessed_at'] != original['available_at']:
                raise ValueError('Historical source receipt differs from sealed admission')
            historical_receipts.append(item)
    assert len(historical_receipts) == 46
    source_folder = destination/'sources'; source_folder.mkdir()
    (source_folder/'ATTRIBUTION.json').write_text(json.dumps(dict(
        source_record=sources['SRC-LIVE-001'], licence_record=sources['SRC-DOC-014'],
        original_receipts=historical_receipts, raw_bytes_included=False,
        scope='Derived archived historical DEVELOPMENT rows only; no later live/final observations'), indent=2)+'\n', encoding='utf-8')
    guide = ('# Read-only Singapore forecasting lesson\n\n'
        'Open notebooks/10_singapore_forecast_study.ipynb to read the saved explanation and chart. '
        'To execute with an existing Python/Jupyter environment, run `python run_lesson.py`. '
        'It saves a new executed copy under outputs/executions and preserves all original payload files.\n\n'
        'This folder contains ten hash-bound historical study inputs, the small archived statistical checkpoint, '
        'helper code, and source/licence/acquisition records. It contains no raw snapshots, growing histories, '
        'future forecast batches, production neural weights, live collector, trainer or final scorer.\n\n'
        'Requires a Python3.12 environment with Jupyter/ipykernel/nbclient/nbformat/matplotlib and their dependencies already installed. '
        'No installer or wheel set is included. Pandas is not required. `python scripts/verify_lesson_package.py` checks the local payload.\n\n'
        'The candidate had development MAE6.31spaces versus6.96for persistence on the same9,202windows at nine collection times. '
        'That is not learned live/final performance. The synthetic examples are teaching arithmetic. '
        'The sealed future result is deliberately not loaded by this lesson, even when opened later. '
        'The runtime uses bounded Python file/socket audits; this is not proof of physical disconnection, a new-machine installation, '
        'manual browser layout, student mastery or official university compliance.\n\n'
        'Data attribution: HDB/data.gov.sg; official source https://api.data.gov.sg/v1/transport/carpark-availability ; '
        'Singapore Open Data Licence1.0 https://data.gov.sg/open-data-licence . '
        'See sources/ATTRIBUTION.json for the original46 acquisition times, URLs and checksums.\n')
    (destination/'README.md').write_text(guide, encoding='utf-8')
    docs = destination/'docs'; docs.mkdir()
    (docs/'SINGAPORE_FORECAST_STUDY.md').write_text(guide, encoding='utf-8')
    entries = [dict(path=p.relative_to(destination).as_posix(), bytes=p.stat().st_size, sha256=file_hash(p))
               for p in sorted(destination.rglob('*')) if p.is_file()]
    manifest = dict(schema_version=1, created_at=created_at, lesson_run=LESSON_RUN,
        data_inputs=10, input_hashes=report['notebook_checks']['input_hashes'], copied_sources=copied,
        generated_runner=dict(original='scripts/validate_singapore_lesson.py',
            original_sha256=report['source_hashes']['scripts/validate_singapore_lesson.py'],
            functions=['dump', 'cell_hash', 'child'], modification='Remove original-notebook writeback only; keep executed copy'),
        entries=entries, total_payload_bytes=sum(e['bytes'] for e in entries),
        generated_output_prefixes=['outputs/'], manifest_not_self_hashed=True,
        scope='Local read-only lesson copy; existing Python/Jupyter environment required; no real future evaluation')
    (destination/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    verify_payload(destination, manifest)
    return manifest
