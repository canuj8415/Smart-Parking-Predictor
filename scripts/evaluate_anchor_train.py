"""One TRAIN-only fixed geometric-support hypothesis; no classifier or final score."""
import argparse,csv,json,os,random,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.anchor_support import assign_bottom_center,support_diagnostics,support_gates

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);temporary=p.with_suffix(p.suffix+'.partial');temporary.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');os.replace(temporary,p)
def verify(p):
    for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f

def prepare():
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs']
    now=datetime.now(timezone.utc);rid='ANCHOR-TRAIN-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    manifest=ROOT/'data/processed/acpds_development_v1/development_images.json';data=read(manifest)
    excluded=['GOPR6654.JPG','GOPR6797.JPG','GOPR6801.JPG'];pool=sorted([f for f in data['frames'] if f['role']=='train' and f['name'] not in excluded],key=lambda f:f['name']);assert len(pool)==228
    frames=random.Random(164).sample(pool,24);assert all(f['role']=='train' for f in frames)
    code=['scripts/evaluate_anchor_train.py','src/smart_parking/anchor_support.py','tests/test_anchor_support.py','src/smart_parking/occupancy_patches.py','src/smart_parking/vision.py','src/smart_parking/layout.py']
    inputs=[manifest,ROOT/'data/manifests/acpds_source_roles_v1.json',ROOT/'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth',ROOT/'models/checkpoints/occupancy_resnet18.pt']+[ROOT/f[k] for f in frames for k in ['image','layout']]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=164,source_ids=['SRC-DS-021','SRC-MOD-001'],frames=frames,pool_images=228,excluded_prior_train_previews=excluded,
        hypothesis='A fixed bottom-center detector-box point may suppress false support of vacant ground polygons while preserving occupied-bay support compared with full-box overlap.',
        selection='PythonRandom164 sample24 of sorted228admittedTRAIN excluding3previousTRAIN API previews;no selection by labels/detector results.',
        prior_exposure='All TRAIN images/labels used by earlier representation training;not unseen model evaluation. No classifier scores/forward/fitting here. Prior35VALID detector study exposed projection ambiguity;do not read or tune against those VALID results in this experiment.',
        recipe=dict(detector='fasterrcnn',resolution=640,confidence=.5,reference_overlap=.12,anchor='((x0+x1)/2,y1);floor to original image raster;out-of-image unknown,not clipped;inside supplied bay mask',matching='Greedy descending detector score,slot index,ID;one vehicle/one bay. No threshold/crop/model alternatives.'),
        gates=dict(minimum_each_truth_count=100,false_support_fraction_of_reference_max=.5,occupied_support_retention_min=.95,image_occupied_support_retention_min=.90),
        gate_scope='Component TRAIN geometry gates only. False support counts assigned-to-vacant labels;retention counts originally supported occupied bay labels,not correct vehicle association. No support is unknown,never proof of vacancy. Passing would not authorize app/final promotion.',
        source_hashes={f:digest(ROOT/f) for f in code},input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T013907Z/checks.json')['frozen_hashes_unchanged'],
        batch_frames=4,maximum_child_seconds=180,maximum_invocation_seconds=900,maximum_rss_bytes=1792*1024**2,minimum_available_ram_bytes=300000000,
        expected_model_calls=dict(detector=24,classifier=0),scope='Supplied-geometry TRAIN-only support diagnostic,not occupancy accuracy,detector precision/mAP,calibrated contact,learned segmentation,video/final/GUI acceptance;no model fitting or production changes.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json')

def worker(path,start,end):
    import psutil,threading,torch
    from PIL import Image
    from smart_parking.vision import VisionEngine,assign_occupancy
    from smart_parking.layout import load_layout
    path=Path(path);out=path.parent;p=read(path);verify(p);torch.manual_seed(164);torch.use_deterministic_algorithms(True)
    proc=psutil.Process();peak=[proc.memory_info().rss];stop=threading.Event()
    def monitor():
        while not stop.wait(.002):
            rss=proc.memory_info().rss;peak[0]=max(peak[0],rss)
            if rss>p['maximum_rss_bytes'] or psutil.virtual_memory().available<p['minimum_available_ram_bytes']:os._exit(87)
    thread=threading.Thread(target=monitor,daemon=True);thread.start();clock=time.perf_counter();engine=VisionEngine('fasterrcnn',640);calls=dict(detector=0,classifier=0)
    def hook(key):
        def count(*args):calls[key]+=1
        return count
    engine.model.register_forward_hook(hook('detector'));engine.classifier.register_forward_hook(hook('classifier'))
    for i in range(start,end):
        assert not(out/'CANCEL').exists(),'Cancellation requested';target=out/f'frame_{i:03}.json';assert not target.exists();f=p['frames'][i];assert f['role']=='train'
        assert digest(ROOT/f['image'])==f['image_sha256'] and digest(ROOT/f['layout'])==f['layout_sha256'];layout=load_layout(ROOT/f['layout'])
        with Image.open(ROOT/f['image']) as source:image=source.convert('RGB')
        started=datetime.now(timezone.utc).isoformat();timer=time.perf_counter();result,unused=engine.analyze(image,None,.5,.25,.75);del unused;ds=result['detections']
        reference=assign_occupancy(image.size,layout,ds,[None]*len(ds),None);anchor=assign_bottom_center(image.size,layout,ds)
        rows=[dict(image=f['name'],slot_id=slot['id'],label=int(slot['ground_truth_occupied']),reference_id=r['vehicle_id'],reference_overlap=r['slot_overlap'],anchor_id=a['vehicle_id'],anchor_xy=a['anchor_xy']) for slot,r,a in zip(layout['slots'],reference,anchor)]
        assert len(rows)==f['slots'];support_diagnostics(rows)
        dump(target,dict(index=i,image=f['name'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-timer,rows=rows,detector_result=result,protocol_sha256=digest(path)));print('Completed TRAIN',i,f['name'],flush=True);del image,result,rows
    stop.set();thread.join(.1);assert calls==dict(detector=end-start,classifier=0)
    dump(out/f'batch_{start:03}_{end:03}.json',dict(start=start,end=end,duration_seconds=time.perf_counter()-clock,peak_rss_bytes=peak[0],model_calls=calls,protocol_sha256=digest(path)))

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256'] and not(out/'run.json').exists();verify(p)
    sp=ROOT/'data/automation_state.json';s=read(sp);assert not s['active_validation_jobs'] and not s['active_training_jobs'];assert p['run_id'] not in s['completed_run_ids'];s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/evaluate_anchor_train.py --run '+path.relative_to(ROOT).as_posix(),maximum_seconds=900)];dump(sp,s);clock=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    try:
        for start in range(0,24,4):
            end=start+4;receipt=out/f'batch_{start:03}_{end:03}.json'
            if receipt.exists():assert read(receipt)['protocol_sha256']==digest(path);continue
            assert not any((out/f'frame_{i:03}.json').exists() for i in range(start,end)),'Partial child evidence preserved;inspect before resuming,never repeat frames'
            if (out/'CANCEL').exists() or time.perf_counter()-clock>720:raise InterruptedError('Bounded invocation;resume complete batches later')
            child=subprocess.run([sys.executable,__file__,'--worker',str(path),'--start',str(start),'--end',str(end)],cwd=ROOT,capture_output=True,text=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            (out/f'batch_{start:03}.stdout.txt').write_text(child.stdout,encoding='utf-8');(out/f'batch_{start:03}.stderr.txt').write_text(child.stderr,encoding='utf-8');assert child.returncode==0,('Owned worker failed',child.returncode);print('TRAIN batch completed',start,end,flush=True)
        verify(p);records=[read(out/f'frame_{i:03}.json') for i in range(24)];assert all(r['protocol_sha256']==digest(path) for r in records);rows=[r for record in records for r in record['rows']];metrics=support_diagnostics(rows);checks=support_gates(metrics,p['gates']);batches=[read(out/f'batch_{i:03}_{i+4:03}.json') for i in range(0,24,4)];calls={k:sum(b['model_calls'][k] for b in batches) for k in ['detector','classifier']};assert calls==p['expected_model_calls']
        r=dict(run_id=p['run_id'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=164,protocol_sha256=digest(path),metrics=metrics,checks=checks,train_geometry_gate_passed=all(checks.values()),model_calls=calls,images=24,slots=len(rows),batches=batches,maximum_batch_rss_bytes=max(b['peak_rss_bytes'] for b in batches),production_promoted=False,training_performed=False,validation_or_final_pixels_or_labels_opened=False,scope=p['scope'])
        dump(out/'run.json',r);dump(ROOT/'models/anchor_support_train.json',r);dump(ROOT/'reports/anchor_support_train_latest.json',r)
        reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Fixed geometric support TRAIN-only paired diagnostic',started_at=started,finished_at=r['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='24seededTRAINphotos;noVALID/TEST',configuration=path.relative_to(ROOT).as_posix(),architecture='Faster640 full-box vs fixed bottom-center raster support',random_seed=164,hardware='CPU4threads/sequential4photo cappedworkers',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(dict(metrics={k:v for k,v in metrics.items() if k!='per_image'},checks=checks,train_geometry_gate_passed=r['train_geometry_gate_passed'])),logs=out.relative_to(ROOT).as_posix(),checkpoints='Unchanged detector;no classifier forwards or model training',code_revision_basis='2a14398 plus sealed TRAIN-only geometric hypothesis',implementation_sha256=digest(__file__),conclusions='TRAIN component evidence only;no production/final promotion')
        with reg.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(sp);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['anchor_support_train']=r;dump(sp,s);print(json.dumps(dict(metrics={k:v for k,v in metrics.items() if k!='per_image'},checks=checks,train_geometry_gate_passed=r['train_geometry_gate_passed']),indent=2))
    except BaseException as error:dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:s=read(sp);s['active_validation_jobs']=[];dump(sp,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');parser.add_argument('--worker');parser.add_argument('--start',type=int);parser.add_argument('--end',type=int);a=parser.parse_args();worker(a.worker,a.start,a.end) if a.worker else run(a.run) if a.run else prepare()
