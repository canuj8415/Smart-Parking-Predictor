"""Execute this capsule's own notebook with local helpers and project-file guards."""
import sys
sys.dont_write_bytecode=True
import argparse,base64,hashlib,json,os,time
from datetime import datetime,timezone
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from capsule_payload import verify_payload,digest
ROOT=Path(__file__).resolve().parents[1]
def dump(p,v):p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def cells_hash(book):return hashlib.sha256(json.dumps([(c.cell_type,c.source) for c in book.cells]).encode()).hexdigest()


def execute(scratch,output,blocked_project=None,expected_manifest=None):
    before=verify_payload(ROOT,expected_manifest);scratch=Path(scratch).resolve();output=Path(output).resolve()
    if scratch.is_relative_to(ROOT) or output.is_relative_to(ROOT):raise ValueError('Private runtime/results must be outside payload')
    scratch.mkdir(parents=True,exist_ok=False);output.mkdir(parents=True,exist_ok=False)
    base=scratch/'jupyter';kernel=base/'kernels/smart-parking-capsule';kernel.mkdir(parents=True)
    dump(kernel/'kernel.json',dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Archived Parking Lesson Capsule',language='python'))
    os.environ['JUPYTER_PATH']=str(base);os.environ['JUPYTER_RUNTIME_DIR']=str(base/'runtime')
    os.environ['JUPYTER_CONFIG_DIR']=str(base/'config');os.environ['IPYTHONDIR']=str(base/'ipython');os.environ['MPLCONFIGDIR']=str(base/'matplotlib')
    (base/'runtime').mkdir();startup=base/'ipython/profile_default/startup';startup.mkdir(parents=True)
    startup_code='import sys\nsys.dont_write_bytecode=True\nfrom pathlib import Path\n'
    startup_code+='sys.path.insert(0,'+repr(str(ROOT/'scripts'))+')\n'
    startup_code+='import offline_jupyter_guard as _network_guard\nimport capsule_lesson_guard as _file_guard\n'
    startup_code+='_NET_SAVE=_network_guard.install('+repr(str(scratch/'network_audit.json'))+',loopback=True)\n'
    startup_code+='_FILE_SAVE=_file_guard.install('+repr(str(ROOT))+','+repr(str(scratch))+','+repr(str(scratch/'file_audit.json'))+','+repr(str(blocked_project) if blocked_project else None)+')\n'
    (startup/'00-capsule.py').write_bytes(startup_code.encode())
    notebook=ROOT/'notebooks/13_guarded_multisource_segmentation.ipynb';book=nbformat.read(notebook,as_version=4);original_cells=cells_hash(book)
    for cell in book.cells:
        if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
    probe="""import socket
from pathlib import Path
assert Path(_network_guard.__file__).resolve().is_relative_to(ROOT)
assert Path(_file_guard.__file__).resolve().is_relative_to(ROOT)
denied=[]
actions=[('raw_read',lambda:(ROOT/'data/raw/CAPSULE_DENIED.json').read_bytes()),
 ('prospective_read',lambda:(ROOT/'data/processed/singapore_learned_v1/CAPSULE_DENIED.jsonl').read_bytes()),
 ('payload_write',lambda:(ROOT/'data/manifests/CAPSULE_DO_NOT_CREATE.json').write_text('probe')),
 ('external_dns',lambda:socket.getaddrinfo('example.invalid',443))]
"""
    if blocked_project:
        probe+="actions.append(('original_project_read',lambda:Path("+repr(str(Path(blocked_project)/'docs/PROJECT_PROGRESS.md'))+").read_bytes()))\n"
    probe+="""for name,action in actions:
    try:action()
    except PermissionError:denied.append(name)
    else:raise AssertionError('Expected denial:'+name)
assert len(denied)==len(actions)
_NET_SAVE();_FILE_SAVE()
"""
    book.cells.append(nbformat.v4.new_code_cell(probe));clock=time.monotonic()
    def boundary(**kwargs):
        if time.monotonic()-clock>180 or (output/'CANCEL').exists():raise InterruptedError('Capsule execution cancelled/deadline')
    try:
        NotebookClient(book,timeout=60,startup_timeout=45,kernel_name='smart-parking-capsule',on_cell_start=boundary,
            resources={'metadata':{'path':str(ROOT/'notebooks')}}).execute()
    except BaseException:nbformat.write(book,output/'failed_notebook.ipynb');raise
    book.cells.pop();assert cells_hash(book)==original_cells;checks=None;pngs=[]
    for cell in book.cells:
        for result in cell.get('outputs',[]):
            assert result.output_type!='error'
            for line in result.get('text','').splitlines():
                if line.startswith('GUARDED_LESSON_CHECKS='):checks=json.loads(line.split('=',1)[1])
            if 'image/png' in result.get('data',{}):
                p=output/f'inline_{len(pngs)+1}.png';p.write_bytes(base64.b64decode(result['data']['image/png']));pngs.append(p)
    files=read(scratch/'file_audit.json');network=read(scratch/'network_audit.json')
    expected_file_denials=4 if blocked_project else 3
    assert len(files['denied'])==expected_file_denials and len(network['denied'])==1
    assert checks and checks['archived_inputs']==6 and checks['failed_candidate_admissions']==3
    assert len(pngs)==2 and sum(c.cell_type=='code' for c in book.cells)==5
    after=verify_payload(ROOT,expected_manifest);assert before==after
    nbformat.write(book,output/'executed_notebook.ipynb')
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,payload_before=before,payload_after=after,
        code_cells=5,inline_PNGs=2,lesson_checks=checks,cell_sources_sha256=original_cells,
        file_audit=files,network_audit=network,helpers_loaded_inside_capsule=True,
        original_project_fallback_denied=bool(blocked_project),private_runtime_outside_payload=True,
        notebook_sha256=digest(notebook),executed_notebook_sha256=digest(output/'executed_notebook.ipynb'),
        duration_seconds=time.monotonic()-clock,models_trained=0,new_model_calls=0,raw_or_final_reads=0,
        scope='Actual relocated local Jupyter/Python file/socket audits;existing external runtime,not OS isolation or physical/new-machine/student acceptance')
    dump(output/'checks.json',report);print(json.dumps(dict(passed=True,code_cells=5,inline_PNGs=2,original_project_fallback_denied=bool(blocked_project))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scratch');parser.add_argument('--output');parser.add_argument('--deny-project');parser.add_argument('--manifest-sha256');args=parser.parse_args()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    execute(args.scratch or ROOT.parent/('private_runtime_'+stamp),args.output or ROOT.parent/('execution_'+stamp),args.deny_project,args.manifest_sha256)
