"""Bounded real TRAIN-photo API integration;no ground-truth accuracy scoring."""
import argparse,ast,copy,json,os,subprocess,sys,threading,time,csv
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261027T010907Z'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    gate=read(ROOT/'models/occupancy_patch_validation.json');assert gate['implementation_gate_passed'];card=read(ROOT/'models/acpds_image_qualification.json');manifest=ROOT/card['development_images'];frames=[f for f in read(manifest)['frames'] if f['role']=='train'];assert len(frames)==3
    old=ast.parse((E/'vision_before_patch_integration.py').read_text());new=ast.parse((ROOT/'src/smart_parking/vision.py').read_text());a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='assign_occupancy');b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='_assign_occupancy_dense_reference');b.name=a.name;assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
    now=datetime.now(timezone.utc);rid='ASSIGNMENT-API-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False);code=['scripts/validate_assignment_api.py','src/smart_parking/vision.py','src/smart_parking/occupancy_patches.py','src/smart_parking/layout.py','src/smart_parking/analysis_identity.py'];inputs=[ROOT/'models/occupancy_patch_validation.json',manifest,E/'vision_before_patch_integration.py',ROOT/'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth',ROOT/'models/checkpoints/occupancy_resnet18.pt',*[ROOT/f[k] for f in frames for k in ['image','layout']]]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=162,source_ids=['SRC-DS-021','SRC-MOD-001','SRC-MOD-003'],hypothesis='The integrated assignment preserves API identities/counts/uncertainty contracts on already exposed native4KTRAIN photos under a bounded FasterRCNN process.',frames=frames,detector='fasterrcnn',resolution=640,maximum_worker_seconds=180,maximum_worker_rss_bytes=1536*1024**2,maximum_model_calls=dict(detector=3,classifier=3),prior_exposure='ThreeTRAINphotos/overlays already inspected;not blind/camera accuracy evaluation. Original application weights,thresholds andgeometry unchanged;only allocation implementation integrated.',gates=['All3realphoto analyses complete','Image/layout identities and original inputs preserved','Counts/slot IDs/state rules/unique vehicle support valid','Original model hashes retained','Worker stays within time/RSS cap'],input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},source_hashes={f:digest(ROOT/f) for f in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],legacy_reference_ast_unchanged=True,scope='API/schema/resource integration only. TRAIN labels ignored for scoring. No real-world accuracy,visibleGUI,physicaloffline,newmachine or MaskRCNN postprocessing memory claim;wholeTESTclosed.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(str(out/'protocol.json'))

def worker(path):
    import psutil
    from PIL import Image
    from smart_parking.vision import VisionEngine
    from smart_parking.layout import load_layout
    from smart_parking.analysis_identity import image_identity,layout_identity
    path=Path(path);out=path.parent;p=read(path);proc=psutil.Process();peak=[proc.memory_info().rss];stop=threading.Event()
    def monitor():
        while not stop.wait(.002):
            rss=proc.memory_info().rss;peak[0]=max(peak[0],rss)
            if rss>p['maximum_worker_rss_bytes'] or psutil.virtual_memory().available<250000000:os._exit(87)
    t=threading.Thread(target=monitor,daemon=True);t.start();clock=time.perf_counter();engine=VisionEngine('fasterrcnn',640);calls=dict(detector=0,classifier=0)
    def count(key):
        def hook(module,args,result):calls[key]+=1
        return hook
    engine.model.register_forward_hook(count('detector'));engine.classifier.register_forward_hook(count('classifier'));cases=[]
    for index,frame in enumerate(p['frames']):
        assert digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['layout'])==frame['layout_sha256']
        with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
        layout=load_layout(ROOT/frame['layout'],image.size);before=copy.deepcopy(layout);identity=image_identity(image);result,overlay=engine.analyze(image,layout);assert result['input_image']==identity==image_identity(image) and result['layout_identity']==layout_identity(layout) and before==layout
        assert len(result['slots'])==len(layout['slots']) and [r['slot_id'] for r in result['slots']]==[r['id'] for r in layout['slots']];assert sum(result['counts'][k] for k in ['occupied','vacant','uncertain'])==result['counts']['total']==len(layout['slots']);used=[r['vehicle_id'] for r in result['slots'] if r['vehicle_id'] is not None];assert len(used)==len(set(used))
        for row in result['slots']:
            score=row['occupancy_score'];expected='occupied' if score>=.75 else 'vacant' if score<=.25 and row['vehicle_id'] is None else 'uncertain';assert row['state']==expected
        assert overlay.size==image.size and overlay.mode=='RGB' and result['classifier_checkpoint_sha256']==p['input_hashes']['models/checkpoints/occupancy_resnet18.pt'];assert result['weight_sha256']==p['input_hashes']['models/pretrained/fasterrcnn_resnet50_fpn_v2.pth'];dump(out/f'analysis_{index}.json',result);overlay.thumbnail((1000,750));overlay.save(out/f'preview_{index}.png');cases.append(dict(image=frame['name'],width=image.width,height=image.height,spaces=len(result['slots']),detections=len(result['detections']),api_contract_passed=True,label_accuracy_scored=False,latency_seconds=result['latency_seconds']));print('Completed real TRAIN API case',index+1,flush=True)
    stop.set();t.join(.1);assert calls==p['maximum_model_calls'];dump(out/'worker.json',dict(cases=cases,peak_rss_bytes=peak[0],duration_seconds=time.perf_counter()-clock,model_calls=calls,gt_accuracy_evaluated=False))

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not(out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    sp=ROOT/'data/automation_state.json';s=read(sp);assert not s['active_training_jobs'] and not s['active_validation_jobs'];s['active_validation_jobs']=[dict(run_id=p['run_id'],cancel_scope='Owned isolated180second worker')];dump(sp,s);clock=time.perf_counter();start=datetime.now(timezone.utc).isoformat()
    try:
        child=subprocess.run([sys.executable,__file__,'--worker',str(path)],cwd=ROOT,capture_output=True,text=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);(out/'stdout.txt').write_text(child.stdout,encoding='utf-8');(out/'stderr.txt').write_text(child.stderr,encoding='utf-8');assert child.returncode==0,('API worker failed',child.returncode);w=read(out/'worker.json');assert len(w['cases'])==3 and w['peak_rss_bytes']<=p['maximum_worker_rss_bytes']
        for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        r=dict(run_id=p['run_id'],started_at=start,finished_at=datetime.now(timezone.utc).isoformat(),parent_duration_seconds=time.perf_counter()-clock,seed=162,protocol_sha256=digest(path),**w,integration_gate_passed=True,model_parameters_unchanged=True,classification_thresholds_unchanged=True,assignment_semantics_preserved=True,final_pixels_or_labels_opened=False,scope=p['scope']);dump(out/'run.json',r);dump(ROOT/'models/assignment_api_validation.json',r);dump(ROOT/'reports/assignment_api_latest.json',r);reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Actual4KTRAIN FasterRCNN API/schema/resource integration',started_at=start,finished_at=r['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='3previouslyexposedTRAINphotos;labels ignored,TESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture='ExistingFasterRCNN+originalclassifier with bounded assignment',random_seed=162,hardware='CPU4threads/isolated capped worker',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(r),logs=out.relative_to(ROOT).as_posix(),checkpoints='Original weights unchanged',code_revision_basis='145bdc7 plus allocation-only integration',implementation_sha256=digest(__file__),conclusions='API integration pass;not camera/GUI/offline accuracy acceptance')
        with reg.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(sp);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['assignment_api_validation']=r;dump(sp,s);print(json.dumps(r,indent=2))
    except BaseException as e:dump(out/'interrupted.json',dict(error=type(e).__name__,detail=str(e),completed_run_counted=False));raise
    finally:s=read(sp);s['active_validation_jobs']=[];dump(sp,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');parser.add_argument('--worker');a=parser.parse_args();worker(a.worker) if a.worker else run(a.run) if a.run else prepare()
