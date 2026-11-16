"""One actual Jupyter-kernel lesson validation, with bounded file/network audits."""
import base64
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src')); sys.path.insert(0, str(ROOT/'scripts'))
from smart_parking.provenance import digest


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def cell_hash(book):
    return hashlib.sha256(json.dumps([(c.cell_type, c.source) for c in book.cells], ensure_ascii=False).encode()).hexdigest()


def child(folder):
    import nbformat
    from nbclient import NotebookClient
    from execute_notebook import setup_kernel
    work = folder/'kernel'; work.mkdir(parents=True, exist_ok=False)
    setup_kernel(work/'jupyter')
    startup = work/'jupyter/ipython/profile_default/startup'
    startup.mkdir(parents=True, exist_ok=True)
    text = ('import sys\nfrom pathlib import Path\nsys.dont_write_bytecode=True\n'
            'sys.path.insert(0, '+repr(str(ROOT/'scripts'))+')\n'
            'from offline_jupyter_guard import install as _install_network\n'
            '_NETWORK_SAVE=_install_network('+repr(str(work/'network_audit.json'))+',loopback=True)\n'
            'from singapore_lesson_guard import install as _install_files\n'
            '_FILE_SAVE=_install_files('+repr(str(ROOT))+','+repr(str(work))+','+repr(str(work/'file_audit.json'))+')\n'
            'assert Path(sys.prefix)==Path('+repr(str(Path(sys.prefix)))+')\n')
    (startup/'00-read-only-study.py').write_text(text, encoding='utf-8')
    source = ROOT/'notebooks/10_singapore_forecast_study.ipynb'
    book = nbformat.read(source, as_version=4); expected_cells = cell_hash(book)
    for cell in book.cells:
        if cell.cell_type == 'code':
            cell.outputs = []; cell.execution_count = None
    # A validation-only cell is removed from the student notebook afterwards.
    book.cells.append(nbformat.v4.new_code_cell('''import socket
probe_denials = []
for label, action in [
    ('future_batch_read', lambda: (ROOT/'data/processed/singapore_learned_v1/batches/LESSON_GUARD_PROBE_DO_NOT_READ.jsonl').read_text()),
    ('final_result_read', lambda: (ROOT/'reports/singapore_final_latest.json').read_text()),
    ('study_write', lambda: (ROOT/'data/manifests/LESSON_GUARD_PROBE_DO_NOT_CREATE.json').write_text('probe')),
    ('nonloopback_dns', lambda: socket.getaddrinfo('example.invalid', 443)),
]:
    try: action()
    except PermissionError: probe_denials.append(label)
    else: raise AssertionError('Expected guard denial: '+label)
assert len(probe_denials)==4
print('VALIDATION_ONLY_PROBES='+json.dumps(probe_denials))
_NETWORK_SAVE(); _FILE_SAVE()
'''))
    try:
        NotebookClient(book, timeout=180, startup_timeout=60, kernel_name='smart-parking-python',
                       resources={'metadata': {'path': str(ROOT)}}).execute()
    except BaseException:
        nbformat.write(book, folder/'failed_notebook.ipynb')
        raise
    probe = book.cells.pop()
    assert cell_hash(book) == expected_cells
    assert all(o.output_type != 'error' for c in [*book.cells, probe] if c.cell_type == 'code' for o in c.outputs)
    checks = None; pngs = []
    for cell in book.cells:
        for output in cell.get('outputs', []):
            for line in output.get('text', '').splitlines():
                if line.startswith('LESSON_CHECKS='):
                    checks = json.loads(line.split('=', 1)[1])
            if 'image/png' in output.get('data', {}):
                path = folder/('development_'+str(len(pngs)+1)+'.png')
                path.write_bytes(base64.b64decode(output['data']['image/png'])); pngs.append(path)
    assert checks and checks['paired_development_windows'] == 9202 and checks['global_development_times'] == 9
    assert checks['training_windows'] == 18393 and not checks['actual_final_result_loaded'] and not checks['model_trained']
    assert len(pngs) >= 1
    nbformat.write(book, source)
    nbformat.write(book, folder/'executed_notebook.ipynb')
    dump(folder/'notebook_checks.json', dict(checks, code_cells=sum(c.cell_type == 'code' for c in book.cells),
        inline_png_outputs=len(pngs), code_and_markdown_cells_unchanged=True, additional_validation_only_probe_cell_removed=True,
        actual_kernel_python=sys.executable, source_cells_sha256=expected_cells,
        scope='Shared local venv, actual Jupyter kernel. Python file/socket audits only; no physical-offline/new-machine/browser/student-mastery claim'))


def main():
    import nbformat
    start = datetime.now(timezone.utc); timer = time.monotonic()
    run_id = 'SG-LESSON-'+start.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT/'experiments/results'/run_id; folder.mkdir(parents=True, exist_ok=False)
    state_path = ROOT/'data/automation_state.json'; state = read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    source = ROOT/'notebooks/10_singapore_forecast_study.ipynb'; book = nbformat.read(source, as_version=4)
    paths = ['scripts/validate_singapore_lesson.py', 'scripts/build_singapore_lesson.py', 'scripts/singapore_lesson_guard.py',
             'src/smart_parking/singapore_lesson.py', 'scripts/offline_jupyter_guard.py', 'scripts/execute_notebook.py',
             'tests/test_singapore_lesson.py']
    hashes = {p: digest(ROOT/p) for p in paths}
    scoring = read('data/manifests/singapore_trend_scoring_v1.json')
    protected = {**read('models/singapore_trend_development.json')['protected_hashes'], **scoring['implementation_hashes']}
    for p in ['data/manifests/singapore_forecast_reservation_v1.json', 'data/manifests/singapore_trend_issuance_v1.json',
              'data/manifests/singapore_trend_scoring_v1.json', 'data/manifests/singapore_trend_frozen_selection_v1.json']:
        protected[p] = digest(ROOT/p)
    protocol = dict(run_id=run_id, started_at=start.isoformat(), seed=134, source_ids=['SRC-LIVE-001'],
        hypothesis='A read-only teaching notebook can reproduce archived paired DEVELOPMENT arithmetic in a real Jupyter kernel while avoiding growing/final evidence and study writes.',
        source_hashes=hashes, protected_hashes=protected, initial_notebook_sha256=digest(source),
        source_cells_sha256=cell_hash(book), notebook=source.relative_to(ROOT).as_posix(),
        data_scope='Completed development CSVs only; toy prediction/missing-target arithmetic explicitly synthetic',
        gates=['Seven original code cells execute without errors', 'Same9202historical rows/9global times,18393training windows',
               'Stored ridge/trend/paired-persistence arithmetic reproduces recorded reports', 'Inline development PNG produced',
               'No raw/growing/final semantic input read; guarded read/write/network probes denied',
               'Original data, frozen implementation and checkpoint/claim hashes unchanged'],
        new_model_training_or_final_evaluation=False)
    dump(folder/'protocol.json', protocol)
    dump(folder/'implementation_sources.json', {p: dict(sha256=h, source=(ROOT/p).read_text(encoding='utf-8')) for p, h in hashes.items()})
    (folder/'source_notebook.json').write_bytes(source.read_bytes())
    state['active_validation_jobs'] = [dict(run_id=run_id, phase='Actual Jupyter kernel; read-only historical lesson')]
    dump(state_path, state)
    try:
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--child', str(folder)],
                                capture_output=True, text=True, timeout=240)
        dump(folder/'child_output.json', dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
        if result.returncode:
            raise RuntimeError('Notebook child failed; actual diagnostics retained in '+str(folder/'child_output.json'))
        checks = read(folder/'notebook_checks.json'); files = read(folder/'kernel/file_audit.json'); network = read(folder/'kernel/network_audit.json')
        assert len(files['denied']) == 3 and len(network['denied']) == 1 and network['denied'][0]['host'] == 'example.invalid'
        assert checks['code_cells'] == 7 and checks['source_cells_sha256'] == protocol['source_cells_sha256']
        assert all(digest(ROOT/p) == h for p, h in {**hashes, **protected, **checks['input_hashes']}.items())
        assert not (ROOT/'data/manifests/LESSON_GUARD_PROBE_DO_NOT_CREATE.json').exists()
        forbidden_prefixes = ['data/raw/', 'data/processed/', 'data/receipts/', 'data/singapore_forecast_holdout_claims/']
        assert all(not any(p.startswith(prefix) for prefix in forbidden_prefixes) for p in files['project_reads'])
        archive = ROOT/'reports/singapore_lesson'/run_id; archive.mkdir(parents=True, exist_ok=False)
        for filename, src in [('10_singapore_forecast_study.ipynb', source), ('development.png', folder/'development_1.png')]:
            (archive/filename).write_bytes(src.read_bytes())
        finished = datetime.now(timezone.utc).isoformat()
        report = dict(protocol, finished_at=finished, duration_seconds=time.monotonic()-timer,
            notebook_checks=checks, file_audit=files, network_audit=network,
            executed_notebook_sha256=digest(source), development_png=(folder/'development_1.png').relative_to(ROOT).as_posix(),
            development_png_sha256=digest(folder/'development_1.png'), archive=archive.relative_to(ROOT).as_posix(),
            lesson_gate_passed=True, original_inputs_and_frozen_sources_unchanged=True,
            real_final_evaluated=False, physical_offline_new_machine_or_manual_ui_verified=False)
        dump(folder/'run.json', report); dump(ROOT/'reports/singapore_lesson_latest.json', report)
        registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig', newline='') as stream:
            fields = csv.DictReader(stream).fieldnames
        entry = dict(experiment_id=run_id, run_type='Read-only Singapore lesson: actual guarded Jupyter validation',
            started_at=start.isoformat(), finished_at=finished, source_ids='SRC-LIVE-001', split_ids='Archived DEVELOPMENT only; final inputs excluded',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(), architecture='Notebook/paired evidence loader, no training', random_seed=134,
            hardware='CPU', execution_environment=sys.version.split()[0], training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(dict(code_cells=7, paired_development_windows=9202, global_times=9, png_outputs=checks['inline_png_outputs'],
                final_evaluated=False, original_inputs_unchanged=True, guarded_probes_blocked=4)),
            logs=folder.relative_to(ROOT).as_posix(), code_revision_basis='160760f plus sealed source snapshots',
            implementation_sha256=hashes[paths[0]], conclusions='Actual kernel pass; read-only study evidence, not new ML/offline-machine/student acceptance')
        with registry.open('a', encoding='utf-8', newline='') as stream:
            csv.DictWriter(stream, fieldnames=fields).writerow({k: entry.get(k, '') for k in fields})
        state = read(state_path); state['completed_run_ids'].append(run_id)
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids'])); state['last_completed_run'] = run_id
        print(json.dumps(dict(run_id=run_id, code_cells=checks['code_cells'], png_outputs=checks['inline_png_outputs'],
            guarded_probes_blocked=4, paired_windows=9202, real_final_evaluated=False), indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json', dict(error=type(error).__name__, detail=str(error), completed_run_counted=False))
        state = read(state_path)
        raise
    finally:
        state['active_validation_jobs'] = []; dump(state_path, state)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--child':
        child(Path(sys.argv[2]))
    else:
        main()
