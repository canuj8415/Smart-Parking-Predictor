"""Build and execute a separate local lesson copy with a known offline venv."""
import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def child(package, folder):
    sys.dont_write_bytecode = True
    sys.path = [p for p in sys.path if Path(p or '.').resolve() not in [ROOT, ROOT/'src', ROOT/'scripts']]
    sys.path[:0] = [str(package/'src'), str(package/'scripts')]
    from offline_jupyter_guard import install
    save_network = install(folder/'parent_network.json', loopback=True)
    from verify_lesson_package import verify
    assert verify(package)['all_payload_hashes_match']
    import nbclient
    original_client = nbclient.NotebookClient
    class ProvenanceClient(original_client):
        def __init__(self, book, *args, **kwargs):
            extra = '''
import smart_parking.singapore_lesson as _lesson_module
import numpy, matplotlib, nbformat, nbclient, IPython
_modules=[numpy,matplotlib,nbformat,nbclient,IPython]
_origins={module.__name__:str(Path(module.__file__).resolve()) for module in _modules}
assert all(Path(value).is_relative_to(Path(sys.prefix).resolve()) for value in _origins.values())
assert Path(_lesson_module.__file__).resolve().is_relative_to(ROOT.resolve())
_proof=dict(python=sys.executable,prefix=sys.prefix,dependency_origins=_origins,lesson_module=str(Path(_lesson_module.__file__).resolve()),root=str(ROOT.resolve()))
Path(PROOF_PATH).write_text(json.dumps(_proof,indent=2)+'\\n',encoding='utf-8')
_FILE_SAVE();_NETWORK_SAVE()
'''.replace('PROOF_PATH', repr(str(folder/'kernel/kernel_origins.json')))
            book.cells[-1].source += '\n'+extra
            super().__init__(book, *args, **kwargs)
    nbclient.NotebookClient = ProvenanceClient
    spec = importlib.util.spec_from_file_location('relocated_readonly_runner', package/'run_lesson.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.child(folder)
    assert verify(package)['all_payload_hashes_match']
    save_network()


def main():
    sys.path.insert(0, str(ROOT/'src'))
    from smart_parking.lesson_package import build_package, verify_payload
    state_path = ROOT/'data/automation_state.json'; state = read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    started = datetime.now(timezone.utc); timer = time.monotonic()
    run_id = 'SG-LESSON-PACK-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT/'experiments/results'/run_id; folder.mkdir(parents=True, exist_ok=False)
    package = ROOT/'outputs/singapore_lesson_packages'/run_id
    profile = read(ROOT/'reports/offline_jupyter_latest.json')
    assert profile['gate_passed']
    python = (ROOT/profile['python']).resolve(); assert python.is_file()
    assert digest(ROOT/profile['manifest']) == profile['manifest_sha256'] and digest(ROOT/profile['lock']) == profile['lock_sha256']
    paths = ['scripts/validate_singapore_lesson_package.py', 'src/smart_parking/lesson_package.py',
             'scripts/verify_lesson_package.py', 'tests/test_lesson_package.py']
    hashes = {name: digest(ROOT/name) for name in paths}
    lesson = read(ROOT/'experiments/results/SG-LESSON-20261026T092240303436Z/run.json')
    protected = {**lesson['protected_hashes'], **lesson['source_hashes'], **lesson['notebook_checks']['input_hashes']}
    protected[lesson['notebook']] = lesson['executed_notebook_sha256']
    for name in ['reports/demo_package_latest.json', 'reports/offline_demo_latest.json', 'reports/offline_jupyter_latest.json']:
        protected[name] = digest(ROOT/name)
    protocol = dict(run_id=run_id, started_at=started.isoformat(), seed=135, source_ids=['SRC-LIVE-001'],
        hypothesis='A minimal relocated lesson copy reproduces seven Jupyter cells using its own archived inputs/helpers and an existing hash-verified offline Jupyter venv, without modifying any payload or original study input.',
        source_hashes=hashes, protected_hashes=protected, package=package.relative_to(ROOT).as_posix(),
        python=python.relative_to(ROOT).as_posix(), prior_offline_installation_run=profile['run_id'],
        environment_scope='Reuse previously verified offline-installed local venv; no new install or new-machine/physical-disconnection claim',
        gates=['Ten archived inputs copied byte-identically; no raw/growing/final data or operational trainer/collector/scorer',
               'Actual seven-cell Jupyter execution, one PNG, same9202development rows/9globaltimes',
               'Imported lesson helper originates in relocated folder; dependencies originate in requested offline venv',
               'Python nonloopback networking blocked; expected read/write/network probes denied',
               'Every original payload byte and all main study/production/old-demo hashes unchanged'],
        real_final_evaluation=False, model_training=False)
    dump(folder/'protocol.json', protocol)
    dump(folder/'implementation_sources.json', {p: dict(sha256=h, source=(ROOT/p).read_text(encoding='utf-8')) for p, h in hashes.items()})
    state['active_validation_jobs'] = [dict(run_id=run_id, phase='Relocated lesson actual offline-profile kernel', cancel_file=(folder/'CANCEL').relative_to(ROOT).as_posix())]
    dump(state_path, state)
    try:
        manifest = build_package(ROOT, package, started.isoformat())
        dump(folder/'PACKAGE_MANIFEST.json', manifest)
        assert not (folder/'CANCEL').exists()
        env = dict(os.environ, PYTHONPATH='', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
        try:
            result = subprocess.run([str(python), str(Path(__file__).resolve()), '--child', str(package), str(folder)],
                                    cwd=package, env=env, capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired as error:
            dump(folder/'child_output.json', dict(timeout_seconds=240,
                stdout=(error.stdout or b'').decode(errors='replace') if isinstance(error.stdout, bytes) else error.stdout,
                stderr=(error.stderr or b'').decode(errors='replace') if isinstance(error.stderr, bytes) else error.stderr))
            raise
        dump(folder/'child_output.json', dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
        if result.returncode:
            raise RuntimeError('Relocated kernel failed; diagnostics and package retained')
        checks = read(folder/'notebook_checks.json'); origins = read(folder/'kernel/kernel_origins.json')
        files = read(folder/'kernel/file_audit.json'); network = read(folder/'kernel/network_audit.json'); parent_network = read(folder/'parent_network.json')
        assert checks['code_cells'] == 7 and checks['inline_png_outputs'] == 1 and checks['paired_development_windows'] == 9202
        assert Path(origins['root']).resolve() == package.resolve()
        assert Path(origins['lesson_module']).resolve().is_relative_to(package.resolve())
        assert Path(origins['prefix']).resolve() == python.parents[1]
        assert all(Path(p).resolve().is_relative_to(python.parents[1]) for p in origins['dependency_origins'].values())
        assert len(files['denied']) == 3 and len(network['denied']) == 1 and not parent_network['denied']
        payload = verify_payload(package, manifest)
        assert all(digest(ROOT/name) == expected for name, expected in {**hashes, **protected}.items())
        assert not (package/'data/raw').exists() and not (package/'data/processed').exists()
        assert not any('collect_singapore' in e['path'] or 'score_singapore' in e['path'] or 'fit_singapore' in e['path'] for e in manifest['entries'])
        archive = ROOT/'reports/singapore_lesson_package'/run_id; archive.mkdir(parents=True, exist_ok=False)
        for target, source in [('PACKAGE_MANIFEST.json', folder/'PACKAGE_MANIFEST.json'), ('README.md', package/'README.md'),
                               ('executed_notebook.ipynb', folder/'executed_notebook.ipynb'), ('development.png', folder/'development_1.png')]:
            (archive/target).write_bytes(source.read_bytes())
        finished = datetime.now(timezone.utc).isoformat()
        report = dict(protocol, finished_at=finished, duration_seconds=time.monotonic()-timer,
            package_manifest_sha256=digest(package/'PACKAGE_MANIFEST.json'), payload=payload, archive=archive.relative_to(ROOT).as_posix(),
            notebook_checks=checks, kernel_origins=origins, file_audit=files, network_audit=network, parent_network_audit=parent_network,
            all_payload_and_original_hashes_unchanged=True, copied_input_files=10, copied_original_acquisition_receipts=46,
            actual_kernel_executed=True, portable_lesson_gate_passed=True,
            existing_full_app_demo_unchanged=True, install_performed=False, physical_offline_new_machine_or_manual_browser_verified=False,
            scope='Relocated read-only historical lesson using an existing offline-installed venv; no new ML/final/live accuracy')
        dump(folder/'run.json', report); dump(ROOT/'reports/singapore_lesson_package_latest.json', report)
        registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig', newline='') as stream:
            fields = csv.DictReader(stream).fieldnames
        entry = dict(experiment_id=run_id, run_type='Relocated read-only lesson actual offline-profile Jupyter validation',
            started_at=started.isoformat(), finished_at=finished, source_ids='SRC-LIVE-001', split_ids='Ten archived historical lesson inputs; no real final read',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(), architecture='Minimal copied lesson and original offline Jupyter venv',
            random_seed=135, hardware='CPU', execution_environment=sys.version.split()[0], training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(dict(payload=payload, code_cells=7, png_outputs=1, dependency_origins_verified=True,
                original_inputs_unchanged=True, real_final_evaluated=False)), logs=folder.relative_to(ROOT).as_posix(),
            code_revision_basis='69592a7 plus sealed source snapshots', implementation_sha256=hashes[paths[0]],
            conclusions='Relocated lesson pass with existing offline-installed venv; no new-machine/physical/manual/ML-performance claim')
        with registry.open('a', encoding='utf-8', newline='') as stream:
            csv.DictWriter(stream, fieldnames=fields).writerow({k: entry.get(k, '') for k in fields})
        state = read(state_path); state['completed_run_ids'].append(run_id)
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids'])); state['last_completed_run'] = run_id
        print(json.dumps(dict(run_id=run_id, package=report['package'], payload=payload, code_cells=7, real_final_evaluated=False), indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json', dict(error=type(error).__name__, detail=str(error), completed_run_counted=False))
        state = read(state_path)
        raise
    finally:
        state['active_validation_jobs'] = []; dump(state_path, state)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--child':
        child(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve())
    else:
        main()
