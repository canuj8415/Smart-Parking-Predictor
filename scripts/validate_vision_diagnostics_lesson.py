"""One bounded actual Jupyter validation of the archived vision lesson."""
import base64
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from smart_parking.provenance import digest


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def cell_hash(book):return hashlib.sha256(json.dumps([(c.cell_type,c.source) for c in book.cells],ensure_ascii=False).encode()).hexdigest()


def child(folder):
    import nbformat
    from nbclient import NotebookClient
    from execute_notebook import setup_kernel
    folder=Path(folder).resolve();assert folder.is_relative_to((ROOT/'experiments/results').resolve())
    work=folder/'kernel';work.mkdir(parents=True,exist_ok=False);setup_kernel(work/'jupyter')
    startup=work/'jupyter/ipython/profile_default/startup';startup.mkdir(parents=True,exist_ok=True)
    code=('import sys\nfrom pathlib import Path\nsys.dont_write_bytecode=True\n'
          'sys.path.insert(0,'+repr(str(ROOT/'scripts'))+')\n'
          'from offline_jupyter_guard import install as _network_install\n'
          '_NETWORK_SAVE=_network_install('+repr(str(work/'network_audit.json'))+',loopback=True)\n'
          'from singapore_lesson_guard import install as _files_install\n'
          '_FILE_SAVE=_files_install('+repr(str(ROOT))+','+repr(str(work))+','+repr(str(work/'file_audit.json'))+')\n')
    (startup/'00-read-only-vision.py').write_text(code,encoding='utf-8')
    source=ROOT/'notebooks/11_visual_detection_diagnostics.ipynb';book=nbformat.read(source,as_version=4);expected=cell_hash(book)
    for cell in book.cells:
        if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
    book.cells.append(nbformat.v4.new_code_cell('''import socket
denied=[]
for label,action in [
 ('reserved_raw_read',lambda:(ROOT/'data/raw/uvg_vcm_official/HighwayDrive/DO_NOT_READ.json').read_text()),
 ('prospective_read',lambda:(ROOT/'data/processed/singapore_learned_v1/batches/DO_NOT_READ.jsonl').read_text()),
 ('project_write',lambda:(ROOT/'data/manifests/VISION_LESSON_DO_NOT_CREATE.json').write_text('probe')),
 ('external_dns',lambda:socket.getaddrinfo('example.invalid',443)),
]:
    try:action()
    except PermissionError:denied.append(label)
    else:raise AssertionError('Expected denial: '+label)
assert len(denied)==4
print('VALIDATION_ONLY_DENIALS='+json.dumps(denied))
_NETWORK_SAVE();_FILE_SAVE()
'''))
    config=read(folder/'protocol.json')
    working=ROOT/'notebooks' if config.get('kernel_working_directory')=='notebooks' else ROOT
    try:NotebookClient(book,timeout=120,startup_timeout=60,kernel_name='smart-parking-python',resources={'metadata':{'path':str(working)}}).execute()
    except BaseException:nbformat.write(book,folder/'failed_notebook.ipynb');raise
    probe=book.cells.pop();assert cell_hash(book)==expected
    checks=None;pngs=[]
    for cell in [*book.cells,probe]:
        for output in cell.get('outputs',[]):
            assert output.output_type!='error'
            for line in output.get('text','').splitlines():
                if line.startswith('VISION_LESSON_CHECKS='):checks=json.loads(line.split('=',1)[1])
            if 'image/png' in output.get('data',{}):
                path=folder/f'archived_{len(pngs)+1}.png';path.write_bytes(base64.b64decode(output['data']['image/png']));pngs.append(path.name)
    assert checks and checks['archived_inputs']==11 and len(pngs)==2
    nbformat.write(book,source);nbformat.write(book,folder/'executed_notebook.ipynb')
    dump(folder/'notebook_checks.json',dict(checks,code_cells=sum(c.cell_type=='code' for c in book.cells),inline_png_outputs=2,
        cell_sources_sha256=expected,validation_probe_removed=True,kernel_python=sys.executable,
        scope='Actual local Jupyter;Python file/socket audits,not OS isolation,physicaloffline,newmachine,browser orstudentmastery'))


def main(notebook_directory=False):
    import nbformat
    start=datetime.now(timezone.utc);timer=time.monotonic();run_id='VISION-LESSON-'+start.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run_id;folder.mkdir(parents=True,exist_ok=False)
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    source=ROOT/'notebooks/11_visual_detection_diagnostics.ipynb';manifest_path=ROOT/'data/manifests/vision_diagnostics_lesson_v1.json';manifest=read(manifest_path)
    protected=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'];protected.update(read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')['implementation_hashes'])
    paths=['scripts/validate_vision_diagnostics_lesson.py','scripts/build_vision_diagnostics_lesson.py','src/smart_parking/vision_lesson.py','src/smart_parking/detection_diagnosis.py','tests/test_vision_lesson.py','scripts/execute_notebook.py','scripts/offline_jupyter_guard.py','scripts/singapore_lesson_guard.py']
    protocol=dict(run_id=run_id,started_at=start.isoformat(),seed=140,source_ids=['SRC-DS-019','SRC-DOC-021'],
        hypothesis='Seven archived-evidence teaching cells can reproduce reported development counts and classify a synthetic miss in an actual read-only guarded Jupyter kernel without raw/growing/final reads,inference or study writes.',
        gates=['Seven source code cells execute without errors;cell sources unchanged','11bound archived inputs;41eligible signature observations/detector;allabsolute failures retained',
               'Two inline archived PNG outputs','Three protected file/write probes and one external-DNS probe denied;no successful raw/growing/final reads','Protected source/model/input bytes unchanged'],
        input_hashes={**manifest['inputs'],manifest_path.relative_to(ROOT).as_posix():digest(manifest_path)},
        source_hashes={p:digest(ROOT/p) for p in paths},protected_hashes=protected,cell_sources_sha256=cell_hash(nbformat.read(source,as_version=4)),maximum_child_seconds=180,
        new_model_inference=False,scientific_results_recomputed_from_fresh_data=False,student_mastery_assessed=False,
        kernel_working_directory='notebooks' if notebook_directory else 'project_root')
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in paths});(folder/'source_notebook.json').write_bytes(source.read_bytes())
    state['active_validation_jobs']=[dict(run_id=run_id,pid=os.getpid(),phase='Actual archived vision Jupyter lesson')];dump(state_path,state)
    try:
        completed=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',str(folder)],capture_output=True,text=True,timeout=180)
        dump(folder/'child_output.json',dict(returncode=completed.returncode,stdout=completed.stdout,stderr=completed.stderr));assert completed.returncode==0,'Actual Jupyter child failed;retain diagnostics'
        checks=read(folder/'notebook_checks.json');files=read(folder/'kernel/file_audit.json');network=read(folder/'kernel/network_audit.json')
        assert checks['code_cells']==7 and checks['inline_png_outputs']==2 and checks['cell_sources_sha256']==protocol['cell_sources_sha256']
        assert len(files['denied'])==3 and len(network['denied'])==1
        forbidden=['data/raw/','data/processed/','data/receipts/','data/singapore_forecast_holdout_claims/']
        assert all(not any(p.startswith(prefix) for prefix in forbidden) for p in files['project_reads'])
        assert not (ROOT/'data/manifests/VISION_LESSON_DO_NOT_CREATE.json').exists()
        assert all(digest(ROOT/p)==h for p,h in {**protocol['source_hashes'],**protocol['protected_hashes'],**protocol['input_hashes']}.items())
        dump(folder/'file_audit.json',files);dump(folder/'network_audit.json',network)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,checks=checks,
            actual_file_guard_denials=3,actual_network_guard_denials=1,successful_raw_or_growing_reads=0,all_gates_passed=True,
            executed_notebook_sha256=digest(source),new_model_inference=False,physical_offline_or_student_mastery=False)
        dump(folder/'run.json',report);dump(ROOT/'reports/vision_diagnostics_lesson_latest.json',dict(run_id=run_id,report=(folder/'run.json').relative_to(ROOT).as_posix(),checks=checks,all_gates_passed=True))
        print(json.dumps(dict(run_id=run_id,duration_seconds=report['duration_seconds'],checks=checks),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:
        state=read(state_path);state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--child':child(sys.argv[2])
    else:main('--notebook-directory' in sys.argv)
