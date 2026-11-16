"""Build/execute a read-only archived multicamera development lesson,no new accuracy."""
import argparse,base64,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
import nbformat as n
R=Path(__file__).resolve().parents[1]
SOURCE=R/'notebooks/13_guarded_multisource_segmentation.ipynb'
BINDING=R/'data/manifests/guarded_region_lesson_v1.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def cell_hash(book):return hashlib.sha256(json.dumps([(c.cell_type,c.source) for c in book.cells]).encode()).hexdigest()

def build():
    assert not SOURCE.exists() and not BINDING.exists()
    inputs={}
    for key,file in [('mixed','models/region_mixed.json'),('gradients','models/region_source_gradients.json'),('guarded','models/region_guarded.json'),('detail','models/region_detail_guarded.json')]:
        r=read(R/file);path='experiments/results/'+r['run_id']+'/run.json';assert read(R/path)==r;inputs[key]=path
    folder=Path(inputs['detail']).parent/'report_v1'
    inputs.update(capacity_plot=(folder/'capacity_comparison.png').as_posix(),quality_plot=(folder/'quality_gap.png').as_posix())
    dump(BINDING,dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),run_id=read(R/inputs['detail'])['run_id'],
        inputs={path:sha(R/path) for path in inputs.values()},roles=inputs,
        scope='Six fixed archived research outputs only;no raw/cache/model weights/operational forecasts/final reads;no training or new accuracy',
        source_ids=['SRC-DS-001','SRC-DS-021','SRC-MOD-003']))
    cells=[n.v4.new_markdown_cell('''# Why retained performance can still fail admission

Read-only archived research: all candidate admission gates still failed.
This notebook explains the PKLot/ACPDS studies and their limitations. It does not
train a model,open raw/final images,acquire data or change the app. The source
datasets provide bay polygons,not exhaustive facility or occupancy truth.

Credits: PKLot/Almeida etal./UFPR,CC BY4.0;ACPDS/Martin Marek,explicit MIT2021 grant;
existing ImageNet ResNet18 under recorded local academic terms. Development images
were repeatedly exposed. Student mastery and physical offline use are unassessed.'''),
    n.v4.new_code_cell(f'''from pathlib import Path
import json,hashlib
ROOT=next(p for p in (Path.cwd().resolve(),*Path.cwd().resolve().parents) if (p/'data/manifests/guarded_region_lesson_v1.json').exists())
binding=ROOT/'data/manifests/guarded_region_lesson_v1.json'
assert hashlib.sha256(binding.read_bytes()).hexdigest()=={sha(BINDING)!r}
manifest=json.loads(binding.read_text())
for name,expected in manifest['inputs'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
archive={{key:json.loads((ROOT/path).read_text()) for key,path in manifest['roles'].items() if key in ['mixed','gradients','guarded','detail']}}
print('Verified archived inputs:',len(manifest['inputs']))'''),
    n.v4.new_markdown_cell('''## Compare matched controls,not unrelated averages

Different studies used different starting weights,optimizers and source allocations.
Within each paired study,compare its own control and candidate. Equal training
budgets can still select checkpoints at different steps. IoU measures overlap with
the provided bay union;it is not occupancy accuracy.'''),
    n.v4.new_code_cell('''print('study / arm       PKLot macro IoU   ACPDS mean IoU   selected new updates')
for study,arms in [('mixed',['control','mixed']),('guarded',['control','guarded']),('detail',['control','detail'])]:
    report=archive[study]
    for arm in arms:
        result=report['results'][arm]
        print(f"{study}/{arm:8} {result['pklot']['macro_camera_iou']:.6f}          {result['acpds']['mean_image_iou']:.6f}          {report['checkpoints'][arm]['selected_updates']}")
    print('overall admission:',report['development_gate_passed'],'shared updates:',report['updates_per_arm'])
print('Gradient diagnostic supported?',archive['gradients']['hypothesis_supported'])
print('Two fixed checkpoints do not establish the cause/timing of an AdamW regression.')'''),
    n.v4.new_code_cell('''from IPython.display import display,Image
for key in ['capacity_plot','quality_plot']:
    display(Image(data=(ROOT/manifest['roles'][key]).read_bytes()))'''),
    n.v4.new_markdown_cell('''## A synthetic first-order example

The following two-dimensional gradients are a teaching fixture,not parking data
or another experiment. Removing opposition and capping the auxiliary norm can
change a local directional derivative. It does not guarantee finite-step loss,
AdamW behavior,held-out quality or universal retention.'''),
    n.v4.new_code_cell('''# SYNTHETIC fixture: a=(1,0),b=(-2,2),analytically guarded b=(0,1).
a=(1.,0.);b=(-2.,2.);guarded_b=(0.,1.)
raw_direction=tuple(-(x+y)/2 for x,y in zip(a,b))
safe_direction=tuple(-(x+y)/2 for x,y in zip(a,guarded_b))
raw_derivative=sum(x*y for x,y in zip(a,raw_direction))
safe_derivative=sum(x*y for x,y in zip(a,safe_direction))
assert raw_derivative==.5 and safe_derivative==-.5
print('Synthetic PKLot-like local derivatives:',raw_derivative,safe_derivative)
print('This is not measured image or deployment accuracy.')'''),
    n.v4.new_code_cell('''checks=dict(archived_inputs=len(manifest['inputs']),models_trained=0,new_model_calls=0,
    raw_or_final_reads=0,app_promoted=False,student_mastery_assessed=False,
    failed_candidate_admissions=sum(not archive[k]['development_gate_passed'] for k in ['mixed','guarded','detail']),
    latest_detail_gain=archive['detail']['results']['detail']['acpds']['mean_image_iou']-archive['detail']['results']['control']['acpds']['mean_image_iou'])
assert checks['archived_inputs']==6 and checks['failed_candidate_admissions']==3
assert checks['latest_detail_gain']<.02
print('GUARDED_LESSON_CHECKS='+json.dumps(checks))'''),
    n.v4.new_markdown_cell('''## Explain the evidence yourself

1. Why did the guarded model fail despite passing fixed-start retention checks?
2. Why is a gain around0.00019 insufficient when the frozen requirement is0.02?
3. Why do0positive TRAIN directional derivatives not establish perfect accuracy?
4. What do the worst-image diagnostic and partial polygons leave unknown?
5. Why can missing later live observations never be scored as zero error?
6. What fresh final evidence and manual/student checks remain necessary?

Running these cells does not establish independent understanding. Preserve failed
experiments andtheir gates;do not retune on consumed final groups.''')]
    book=n.v4.new_notebook(cells=cells,metadata=dict(kernelspec=dict(name='smart-parking-python',display_name='Python (Smart Parking)',language='python'),language_info=dict(name='python')))
    n.write(book,SOURCE);return SOURCE

def execute():
    from nbclient import NotebookClient
    from execute_notebook import setup_kernel
    manifest=read(BINDING);rid=manifest['run_id'];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=R/'experiments/results'/rid/('lesson_validation_'+stamp);folder.mkdir(exist_ok=False)
    work=R/'outputs/guarded_region_lesson_runtime'/stamp;work.mkdir(parents=True);setup_kernel(work/'jupyter')
    startup=work/'jupyter/ipython/profile_default/startup';startup.mkdir(parents=True,exist_ok=True)
    code='import sys\nsys.dont_write_bytecode=True\n'
    code+='sys.path.insert(0,'+repr(str(R/'scripts'))+')\n'
    code+='from offline_jupyter_guard import install as _net\n_NET_SAVE=_net('+repr(str(work/'network_audit.json'))+',loopback=True)\n'
    code+='from singapore_lesson_guard import install as _files\n_FILE_SAVE=_files('+repr(str(R))+','+repr(str(work))+','+repr(str(work/'file_audit.json'))+')\n'
    (startup/'00-guarded-region.py').write_bytes(code.encode())
    book=n.read(SOURCE,as_version=4);source_hash=cell_hash(book)
    book.cells.append(n.v4.new_code_cell('''import socket
denied=[]
for name,action in [('raw_read',lambda:(ROOT/'data/raw/GUARDED_LESSON_DENIED.json').read_bytes()),
 ('prospective_read',lambda:(ROOT/'data/processed/singapore_learned_v1/GUARDED_LESSON_DENIED.jsonl').read_bytes()),
 ('project_write',lambda:(ROOT/'data/manifests/GUARDED_LESSON_DO_NOT_CREATE.json').write_text('probe')),
 ('external_dns',lambda:socket.getaddrinfo('example.invalid',443))]:
    try:action()
    except PermissionError:denied.append(name)
    else:raise AssertionError('Expected denial:'+name)
assert len(denied)==4
_NET_SAVE();_FILE_SAVE()
'''))
    try:NotebookClient(book,timeout=120,startup_timeout=60,kernel_name='smart-parking-python',resources={'metadata':{'path':str(R/'notebooks')}}).execute()
    except BaseException:n.write(book,folder/'failed_notebook.ipynb');raise
    book.cells.pop();assert cell_hash(book)==source_hash;checks=None;pngs=[]
    for cell in book.cells:
        for output in cell.get('outputs',[]):
            assert output.output_type!='error'
            for line in output.get('text','').splitlines():
                if line.startswith('GUARDED_LESSON_CHECKS='):checks=json.loads(line.split('=',1)[1])
            if 'image/png' in output.get('data',{}):
                png=folder/f'inline_{len(pngs)+1}.png';png.write_bytes(base64.b64decode(output['data']['image/png']));pngs.append(png)
    files=read(work/'file_audit.json');network=read(work/'network_audit.json')
    assert checks and checks['archived_inputs']==6 and len(pngs)==2 and sum(c.cell_type=='code' for c in book.cells)==5
    assert len(files['denied'])==3 and len(network['denied'])==1
    for path,expected in manifest['inputs'].items():assert sha(R/path)==expected
    n.write(book,SOURCE);n.write(book,folder/'executed_notebook.ipynb')
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,lesson_checks=checks,code_cells=5,inline_pngs=2,
        cell_sources_sha256=source_hash,notebook_sha256=sha(SOURCE),binding_sha256=sha(BINDING),
        file_audit=files,network_audit=network,private_runtime=work.relative_to(R).as_posix(),probe_cell_removed=True,
        new_model_calls=0,extra_experiments_counted=0,source_hashes={p:sha(R/p) for p in ['scripts/build_guarded_region_lesson.py','scripts/execute_notebook.py','scripts/offline_jupyter_guard.py','scripts/singapore_lesson_guard.py']},
        scope='Actual local Jupyter with Python file/socket audits;not OS isolation,physicaloffline,newmachine,browser or student mastery')
    dump(folder/'checks.json',report);dump(R/'reports/guarded_region_lesson_latest.json',dict(notebook=SOURCE.relative_to(R).as_posix(),checks=(folder/'checks.json').relative_to(R).as_posix(),passed=True,extra_experiments_counted=0))
    print(json.dumps(dict(notebook=SOURCE.relative_to(R).as_posix(),code_cells=5,inline_pngs=2,passed=True)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');parser.add_argument('--execute-existing',action='store_true');args=parser.parse_args()
    if not args.execute_existing:build()
    if args.execute or args.execute_existing:execute()
