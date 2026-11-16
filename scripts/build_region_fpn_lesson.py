"""Build and optionally execute a bounded archived-development teaching notebook."""
import argparse
import base64
import hashlib
import json
import os
import sys
import faulthandler
from datetime import datetime,timezone
from pathlib import Path
import nbformat as n

ROOT=Path(__file__).resolve().parents[1]
RID='REGION-FPN-V1-20261027T061402381508Z'
REPORT='reports/region_fpn_'+RID


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def cell_hash(book):return hashlib.sha256(json.dumps([(c.cell_type,c.source) for c in book.cells]).encode()).hexdigest()


def build():
    inputs=[f'experiments/results/{RID}/run.json',f'experiments/results/{RID}/protocol.json',
        REPORT+'/EXPLANATION.md',*[REPORT+'/'+c+'_worst_development.png' for c in ['pucpr','ufpr04','ufpr05']]]
    binding=ROOT/'data/manifests/region_fpn_lesson_v1.json'
    assert not binding.exists()
    dump(binding,dict(schema_version=1,run_id=RID,inputs={p:sha(ROOT/p) for p in inputs},
        scope='Six fixed archived-development inputs only;no model/raw/cache/operationalforecast/final reads'))
    cells=[n.v4.new_markdown_cell('''# Why a better development score can still fail

This lesson reads completed DEVELOPMENT evidence from familiar parking cameras.
It does not train, run a neural model, acquire data or open a final holdout. The
app retains its original model. Sources: PKLot, Almeida et al./UFPR, CC BY4.0;
TorchVision ImageNet ResNet18 under existing local academic weight terms.
Student understanding remains unassessed.'''),n.v4.new_code_cell(f'''from pathlib import Path
import json,hashlib
ROOT=next((p for p in (Path.cwd().resolve(),*Path.cwd().resolve().parents)
           if (p/'data/manifests/region_fpn_lesson_v1.json').is_file()),None)
if ROOT is None:raise FileNotFoundError('Open inside the Smart Parking project')
binding=ROOT/'data/manifests/region_fpn_lesson_v1.json'
assert hashlib.sha256(binding.read_bytes()).hexdigest()=={sha(binding)!r}
manifest=json.loads(binding.read_text(encoding='utf-8'))
for path,expected in manifest['inputs'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
result=json.loads((ROOT/'experiments/results/{RID}/run.json').read_text(encoding='utf-8'))
print('Verified six archived inputs. No model calls or fresh evaluation.')'''),
    n.v4.new_code_cell('''from IPython.display import display,HTML,Image
methods=['candidate','original','conditional_train_template']
names=['New image-only model','Original U-Net, common cache','Conditional TRAIN camera template']
rows=[]
for key,name in zip(methods,names):
    m=result[key]
    rows.append('<tr><td>'+name+'</td><td>'+f"{m['macro_camera_iou']:.6f}"+'</td><td>'+f"{m['minimum_image_iou']:.6f}"+'</td></tr>')
display(HTML('<table><tr><th>Method</th><th>Equal-camera mean IoU</th><th>Worst image IoU</th></tr>'+''.join(rows)+'</table>'))
print('Acceptance gates:',result['gates'])
assert not result['development_gate_passed'] and not result['production_promoted']'''),
    n.v4.new_markdown_cell('''IoU is the area of overlap divided by the area of the
union of predicted and supplied bay masks. These values do not measure vehicle
occupancy accuracy. The original comparator shares the same256x144 cached RGB,
uses its192x112 input and returns probabilities to the common mask grid. This is
a paired development comparison, not its earlier final benchmark.

The new decoder uses frozen image features; camera IDs are not model inputs.
The comparator template uses the majority TRAIN mask for an explicitly supplied
camera. Two views have identical TRAIN/DEV target geometry and yield1.0 template
IoU. UFPR04 contains different layouts, so its camera template scores0.284.
Perfect repeated geometry does not establish perfect scene understanding.'''),
    n.v4.new_code_cell('''by_camera=result['candidate']['by_camera']
equal=sum(v['mean_iou'] for v in by_camera.values())/len(by_camera)
image_weighted=sum(v['mean_iou']*v['images'] for v in by_camera.values())/sum(v['images'] for v in by_camera.values())
assert abs(equal-result['candidate']['macro_camera_iou'])<1e-12
print('Camera image counts:',{c:v['images'] for c,v in by_camera.items()})
print('Equal-camera mean:',equal,'Image-weighted mean:',image_weighted)
print('Unequal camera sizes make these summaries different.')'''),
    n.v4.new_code_cell(f'''for camera in ['pucpr','ufpr04','ufpr05']:
    display(Image(filename=str(ROOT/'{REPORT}'/(camera+'_worst_development.png'))))
print('Worst candidate example per camera, selected after scoring; not representative or final.')'''),
    n.v4.new_markdown_cell('''Green marks agreement, red extra predicted area,
and blue missed supplied bay area. Unannotated parking regions are not exhaustive
negative ground truth. Four gates failed: meanIoU0.80, each-camera0.75,
each-image0.65, and no camera regression beyond0.05 from the TRAIN template.
Improvement over the original alone is insufficient. No gate was relaxed.
All consumed/quarantined/fresh-final boundaries remain protected.'''),
    n.v4.new_code_cell('''# SYNTHETIC teaching fixture; not a real image or an extra experiment.
truth={(0,0),(0,1)}
prediction={(0,0),(1,1)}
intersection=len(truth & prediction);union=len(truth | prediction)
iou=intersection/union;dice=2*intersection/(len(truth)+len(prediction))
assert iou==1/3 and dice==.5
print('Synthetic IoU:',iou,'Synthetic Dice:',dice)'''),
    n.v4.new_code_cell('''checks=dict(archived_inputs=len(manifest['inputs']),images=30,cameras=3,
    failed_gates=sum(not value for value in result['gates'].values()),
    new_model_calls=0,raw_or_final_reads=0,training=False,app_promoted=False,student_mastery_assessed=False)
assert checks['archived_inputs']==6 and checks['failed_gates']==4
print('REGION_LESSON_CHECKS='+json.dumps(checks))'''),
    n.v4.new_markdown_cell('''## Explain this yourself

1. Compute the difference between the new and original mean IoU. Why does it not
   authorize app promotion?
2. Why do equal-camera and image-weighted averages differ?
3. How can a TRAIN-only template score1.0 without understanding an image?
4. Why can the same camera require different layout geometry?
5. Why are the worst examples useful but not a representative sample?
6. What fresh source/split evidence is required before a final reliability claim?

Independent answers and manual presentation remain necessary. Successful code
execution alone does not assess student mastery. Longer, view-balanced training
is a future hypothesis; its recipe and gates must be sealed before fitting.''')]
    book=n.v4.new_notebook(cells=cells,metadata=dict(kernelspec=dict(name='smart-parking-python',display_name='Python (Smart Parking)',language='python'),language_info=dict(name='python')))
    destination=ROOT/'notebooks/12_region_segmentation_development.ipynb'
    assert not destination.exists();n.write(book,destination)
    return destination


def execute(source):
    from nbclient import NotebookClient
    from execute_notebook import setup_kernel
    folder=ROOT/'experiments/results'/RID/('lesson_validation_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));folder.mkdir(exist_ok=False)
    work=folder/'kernel';work.mkdir();setup_kernel(work/'jupyter')
    startup=work/'jupyter/ipython/profile_default/startup';startup.mkdir(parents=True,exist_ok=True)
    code='import sys\nsys.dont_write_bytecode=True\nfrom pathlib import Path\n'
    code+='sys.path.insert(0,'+repr(str(ROOT/'scripts'))+')\n'
    code+='from offline_jupyter_guard import install as _net\n_NET_SAVE=_net('+repr(str(work/'network_audit.json'))+',loopback=True)\n'
    code+='from singapore_lesson_guard import install as _files\n_FILE_SAVE=_files('+repr(str(ROOT))+','+repr(str(work))+','+repr(str(work/'file_audit.json'))+')\n'
    (startup/'00-read-only-region.py').write_text(code,encoding='utf-8')
    book=n.read(source,as_version=4);original_hash=cell_hash(book)
    book.cells.append(n.v4.new_code_cell('''import socket
denied=[]
for name,action in [
 ('raw_read',lambda:(ROOT/'data/raw/DO_NOT_OPEN.json').read_bytes()),
 ('prospective_read',lambda:(ROOT/'data/processed/singapore_learned_v1/DO_NOT_OPEN.jsonl').read_bytes()),
 ('project_write',lambda:(ROOT/'data/manifests/REGION_LESSON_DO_NOT_CREATE.json').write_text('probe')),
 ('external_dns',lambda:socket.getaddrinfo('example.invalid',443))]:
    try:action()
    except PermissionError:denied.append(name)
    else:raise AssertionError('Probe should be denied:'+name)
assert len(denied)==4
_NET_SAVE();_FILE_SAVE()
'''))
    try:NotebookClient(book,timeout=120,startup_timeout=60,kernel_name='smart-parking-python',resources={'metadata':{'path':str(ROOT/'notebooks')}}).execute()
    except BaseException:n.write(book,folder/'failed_notebook.ipynb');raise
    book.cells.pop();assert cell_hash(book)==original_hash
    checks=None;pngs=[]
    for cell in book.cells:
        for output in cell.get('outputs',[]):
            assert output.output_type!='error'
            for line in output.get('text','').splitlines():
                if line.startswith('REGION_LESSON_CHECKS='):checks=json.loads(line.split('=',1)[1])
            if 'image/png' in output.get('data',{}):
                png=folder/f'inline_{len(pngs)+1}.png';png.write_bytes(base64.b64decode(output['data']['image/png']));pngs.append(png)
    assert checks and len(pngs)==3 and sum(c.cell_type=='code' for c in book.cells)==6
    file_audit=json.loads((work/'file_audit.json').read_text(encoding='utf-8'))
    network=json.loads((work/'network_audit.json').read_text(encoding='utf-8'))
    assert len(file_audit['denied'])==3 and len(network['denied'])==1
    n.write(book,source);n.write(book,folder/'executed_notebook.ipynb')
    dump(folder/'checks.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),passed=True,lesson_checks=checks,
        code_cells=6,inline_pngs=3,cell_sources_sha256=original_hash,kernel_python=sys.executable,
        file_audit=file_audit,network_audit=network,validation_probe_removed=True,
        new_model_calls=0,extra_experiments_counted=0,
        source_hashes={p:sha(ROOT/p) for p in ['scripts/build_region_fpn_lesson.py','scripts/execute_notebook.py','scripts/offline_jupyter_guard.py','scripts/singapore_lesson_guard.py']},
        scope='Actual local Jupyter with Python file/socket audits;not OS isolation,physicaloffline,newmachine,browser orstudentmastery'))
    dump(ROOT/'reports/region_fpn_lesson_latest.json',dict(run_id=RID,checks=(folder/'checks.json').relative_to(ROOT).as_posix(),
        notebook=source.relative_to(ROOT).as_posix(),passed=True,new_model_calls=0,extra_experiments_counted=0))
    print(json.dumps(dict(notebook=source.relative_to(ROOT).as_posix(),code_cells=6,inline_pngs=3,passed=True)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');parser.add_argument('--execute-existing',action='store_true');args=parser.parse_args()
    source=ROOT/'notebooks/12_region_segmentation_development.ipynb' if args.execute_existing else build()
    if args.execute or args.execute_existing:
        faulthandler.dump_traceback_later(45,repeat=True)
        try:execute(source)
        finally:faulthandler.cancel_dump_traceback_later()
