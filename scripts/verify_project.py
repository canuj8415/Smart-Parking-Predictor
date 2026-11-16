"""Save actual integrity/test evidence and a measured dataset inventory."""
import csv
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.data import acquire, prepare, sha256

if __name__ == '__main__':
    started = datetime.now(timezone.utc).isoformat()
    run_id = 'RUN-DATA-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    timer = time.perf_counter()
    acquire(ROOT, allow_download=False)
    report = prepare(ROOT)
    split = ROOT/'data/splits'/report['split_id']
    before = {p.name: sha256(p) for p in sorted(split.iterdir()) if p.is_file()}
    prepare(ROOT)
    after = {p.name: sha256(p) for p in sorted(split.iterdir()) if p.is_file()}
    if before != after:
        raise RuntimeError('Repeated preparation produced different bytes.')
    test = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],
                          cwd=ROOT, capture_output=True, text=True)
    if test.returncode:
        raise RuntimeError(test.stdout+test.stderr)
    notebook = json.loads((ROOT/'notebooks/01_real_data_audit.ipynb').read_text(encoding='utf-8'))
    code = [c for c in notebook['cells'] if c['cell_type']=='code']
    if not all(c['execution_count'] is not None for c in code):
        raise RuntimeError('Notebook has unexecuted code cells.')
    errors = [o for c in code for o in c.get('outputs',[]) if o['output_type']=='error']
    if errors:
        raise RuntimeError('Notebook contains execution errors.')
    files = [ROOT/'data/raw/uci_parking_birmingham/parking-birmingham.zip',
             ROOT/'data/raw/uci_parking_birmingham/dataset.csv', *sorted(split.iterdir())]
    inventory = dict(schema_version=1, inventoried_at=datetime.now(timezone.utc).isoformat(),
        datasets=[dict(source_id='SRC-DS-003', status='downloaded_and_prepared',
          version='UCI 482 snapshot pinned by SHA-256', raw_rows=report['raw_rows'],
          accepted_rows=report['accepted_rows'], quarantine_rows=report['quarantine_rows'],
          car_parks=report['car_parks'], split_id=report['split_id'],
          used_for_model_training=False, used_for_model_evaluation=False,
          files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha256(p)) for p in files])],
        not_acquired=['PKLot','CNRPark+EXT','COCO','Cityscapes','MOT17','CARPK/PUCPR+','VIRAT','KITTI'])
    (ROOT/'data/dataset_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    evidence_dir=ROOT/'experiments/evidence'/run_id
    evidence_dir.mkdir(parents=True,exist_ok=False)
    (evidence_dir/'unit_tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
    evidence=dict(run_id=run_id,type='data_validation_not_model_experiment',
        started_at=started, finished_at=datetime.now(timezone.utc).isoformat(),
        measured_validation_seconds=time.perf_counter()-timer, python=sys.version,
        interpreter=sys.executable, source_id='SRC-DS-003', split_id=report['split_id'],
        implementation_sha256=sha256(ROOT/'src/smart_parking/data.py'),
        config_sha256=sha256(ROOT/'configs/birmingham_split.json'),
        code_revision_basis=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        code_revision_note='Parent commit plus working changes; implementation/config hashes pin executed code; final commit contains these exact files',
        unit_test_exit_code=test.returncode,unit_tests_passed=int(re.search(r'Ran (\d+) tests?',test.stderr).group(1)),
        deterministic_preparation='pass; repeated outputs byte-identical',
        executed_notebook_code_cells=len(code),notebook_errors=0,
        notebook_sha256=sha256(ROOT/'notebooks/01_real_data_audit.ipynb'),
        split_file_hashes=after, model_metrics=None, models_trained=0)
    (evidence_dir/'verification.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    fields=['experiment_id','run_type','started_at','finished_at','source_ids','split_ids',
            'configuration','architecture','model_version','optimizer','learning_rate','epochs',
            'batch_size','random_seed','hardware','execution_environment','training_duration',
            'loss_curves','evaluation_metrics','logs','checkpoints','code_revision_basis',
            'implementation_sha256','conclusions']
    row={key:'not applicable: no model training/evaluation' for key in fields}
    row.update(experiment_id=evidence['run_id'],run_type=evidence['type'],started_at=started,
        finished_at=evidence['finished_at'],source_ids='SRC-DS-003',split_ids=report['split_id'],
        configuration='configs/birmingham_split.json',hardware='i9-14900HX; CPU data audit',
        execution_environment=sys.version.split()[0],logs=evidence_dir.relative_to(ROOT).as_posix()+'/',
        code_revision_basis=evidence['code_revision_basis'],implementation_sha256=evidence['implementation_sha256'],
        conclusions='Unit tests passed; deterministic preparation; executed notebook has no errors; this data-validation run has no model metrics')
    registry = ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
    new_registry = not registry.exists()
    with registry.open('a',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        if new_registry: writer.writeheader()
        writer.writerow(row)
    print(json.dumps(evidence,indent=2))
