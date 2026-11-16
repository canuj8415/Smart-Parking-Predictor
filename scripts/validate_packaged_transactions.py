"""Complete deferred transaction checks without declaring the whole copy ready."""
import csv,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T180901Z'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def main():
    pointer=read(E/'component_run_pointer.json');path=ROOT/pointer['protocol'];out=path.parent;p=read(path)
    assert not (out/'run.json').exists() and digest(path)==pointer['protocol_sha256']
    code='scripts/validate_packaged_transactions.py';p['source_hashes'][code]=digest(ROOT/code);dump(path,p)
    pointer['protocol_sha256']=digest(path);dump(E/'component_run_pointer.json',pointer)
    dump(out/'runner_source.json',dict(path=code,sha256=digest(ROOT/code),source=(ROOT/code).read_text(encoding='utf-8')))
    for f,h in {**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    package=ROOT/p['package'];assert digest(package/'BUNDLE_MANIFEST.json')==p['manifest_sha256']
    assert all(digest(package/v['path'])==v['sha256'] for v in read(package/'BUNDLE_MANIFEST.json')['files'])
    s=read(ROOT/'data/automation_state.json');assert s['completed_recorded_runs_since_schedule']==83 and not s['active_validation_jobs']
    s['active_validation_jobs']=[dict(run_id=p['run_id'],phase='Deferred copied transaction/version checks,no Jupyter/model')];dump(ROOT/'data/automation_state.json',s)
    start=datetime.now(timezone.utc);clock=time.monotonic();failure=None;checks={}
    try:
        python=package/'.venv/Scripts/python.exe'
        child=subprocess.run([str(python),'-I',str(package/'scripts/verify_offline_bundle.py'),'transactions'],cwd=package,capture_output=True,text=True,timeout=90)
        (out/'transactions_stdout.txt').write_text(child.stdout,encoding='utf-8');(out/'transactions_stderr.txt').write_text(child.stderr,encoding='utf-8')
        assert child.returncode==0,child.stderr
        transaction=read(package/'EXPORT_TRANSACTION_VALIDATION.json');assert transaction['synthetic_transaction_tests']==13 and transaction['normal_forbidden_attempts']==0
        checks['copied_transaction_tests']=transaction
        probe='''import importlib.metadata as md,json,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'scripts'))
from package_offline_guard import install
save=install(root,root/'outputs/setup/version_probe_audit.json');expected={}
for p in ['dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json','dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json']:
 for e in json.loads((root/p).read_text())['entries']:expected[e['name'].lower().replace('_','-')]=e['version']
actual={}
for n,v in expected.items():
 d=md.distribution(n);assert d.version==v and Path(d.locate_file('')).resolve().is_relative_to(Path(sys.prefix).resolve()),n
 actual[n]=d.version
save();audit=json.loads((root/'outputs/setup/version_probe_audit.json').read_text());assert not audit['denied'] and len(actual)==107
print(json.dumps(dict(versions=actual,all107versions_match=True,all_distributions_inside_copy=True,normal_forbidden_attempts=0)))
'''
        version=subprocess.run([str(python),'-I','-c',probe],cwd=package,capture_output=True,text=True,timeout=45)
        (out/'versions_stdout.txt').write_text(version.stdout,encoding='utf-8');(out/'versions_stderr.txt').write_text(version.stderr,encoding='utf-8');assert version.returncode==0,version.stderr
        checks['versions']=json.loads(version.stdout)
        config=package/'.venv/pyvenv.cfg';before=digest(config)
        refusal=subprocess.run([str(python),'-I',str(package/'scripts/setup_offline_bundle.py')],cwd=package,capture_output=True,text=True,timeout=20)
        (out/'overwrite_refusal_stderr.txt').write_text(refusal.stderr,encoding='utf-8')
        assert refusal.returncode!=0 and 'Preserve existing environment' in refusal.stderr and digest(config)==before
        checks['existing_environment_overwrite_refused']=True
        assert all(digest(package/v['path'])==v['sha256'] for v in read(package/'BUNDLE_MANIFEST.json')['files'])
        assert all(digest(ROOT/f)==h for f,h in p['protected_hashes'].items())
    except Exception as error:failure=repr(error)
    finally:
        result=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-clock,
            seed=147,protocol_sha256=digest(path),checks=checks,failure=failure,component_gate_passed=failure is None and len(checks)==3,
            whole_package_ready=False,jupyter_acceptance=False,model_calls=0,learned_target_decoding=False,source_ids=p['source_ids'])
        dump(out/'run.json',result)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Deferred fresh-copy transaction/version component;whole package still NOT READY',started_at=result['started_at'],finished_at=result['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='Synthetic export fixtures/distribution metadata only',configuration=path.relative_to(ROOT).as_posix(),architecture='Fresh copied107-package environment;no Jupyter/model replay',random_seed=147,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(dict(component_gate_passed=result['component_gate_passed'],failure=failure,whole_package_ready=False,checks=checks)),logs=out.relative_to(ROOT).as_posix(),checkpoints='Original weights/claims unchanged',code_revision_basis='9ebc059 plus sealed component source snapshots',implementation_sha256=digest(ROOT/code),conclusions='Component checks only;whole copied Jupyter gate remainsfailed;no newaccuracy/READYpromotion')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(ROOT/'data/automation_state.json');s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['active_validation_jobs']=[];dump(ROOT/'data/automation_state.json',s)
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()
