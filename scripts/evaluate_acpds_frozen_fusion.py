"""Single prespecified development fusion study; frozen classifier scores, no fitting.

Each five-photo child checkpoints immutable per-frame evidence and exits. A
cancel marker, invocation deadline, RSS cap and low-system-RAM guard are enforced.
"""
import argparse,csv,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.fusion_diagnostics import state_from_probability,paired_fusion_metrics,fusion_gates

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def dump(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)

def verify(p):
    for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f

def prepare():
    state=read(ROOT/'data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    now=datetime.now(timezone.utc);rid='ACPDS-FROZEN-FUSION-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    card=read(ROOT/'models/acpds_image_qualification.json');manifest=ROOT/card['development_images'];assert digest(manifest)==card['development_images_sha256']
    frames=[f for f in read(manifest)['frames'] if f['role']=='valid'];assert len(frames)==35 and sum(f['slots'] for f in frames)==1904
    baseline=read(ROOT/'models/acpds_occupancy_baseline.json');candidate=read(ROOT/'models/acpds_last_block.json')
    bp='experiments/results/'+baseline['run_id']+'/development_predictions.json';cp='experiments/results/'+candidate['run_id']+'/candidate_predictions.json'
    complete=ROOT/'data/processed/acpds_development_v1/development_images.json';index={f['name']:f for f in read(complete)['frames']}
    for f in frames:assert read(ROOT/f['layout'])['slots']==read(ROOT/index[f['name']]['layout'])['slots']
    code=['scripts/evaluate_acpds_frozen_fusion.py','src/smart_parking/fusion_diagnostics.py','tests/test_fusion_diagnostics.py','src/smart_parking/vision.py','src/smart_parking/occupancy_patches.py','src/smart_parking/layout.py','src/smart_parking/analysis_identity.py']
    inputs=[manifest,complete,ROOT/'models/acpds_occupancy_baseline.json',ROOT/'models/acpds_last_block.json',ROOT/bp,ROOT/cp,ROOT/'data/manifests/acpds_source_roles_v1.json',ROOT/'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth',ROOT/'models/checkpoints/occupancy_resnet18.pt',ROOT/candidate['candidate_checkpoint']]+[ROOT/f[k] for f in frames for k in ['image','layout']]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=163,source_ids=['SRC-DS-021','SRC-MOD-001','SRC-MOD-003'],frames=frames,
        hypothesis='Existing fixed FasterRCNN evidence may flag source-shift confident false vacancies, but can also suppress correct vacancy answers because ground polygons and projected vehicle boxes differ.',
        prior_exposure='All35VALID/1904labels and classifier results already exposed. Original baseline62confidentfalsevacants;last-block14 and failed safety gates. No prior detector results on these35photos. Both fixed methods reported independently;no winner or threshold chosen.',
        baseline_predictions=bp,candidate_predictions=cp,candidate_method='Research last-block checkpoint;frozen previously saved probabilities,not installed or rerun',
        input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},source_hashes={f:digest(ROOT/f) for f in code},
        protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T010907Z/checks.json')['frozen_hashes_unchanged'],
        thresholds=dict(detector_confidence=.5,detector_resolution=640,overlap=.12,low=.25,high=.75),
        gates=dict(occupied_false_vacancy_max=.01,uncertainty_max=.10,correct_vacancy_retention_min=.95,image_correct_vacancy_retention_min=.90),
        gate_purpose='Same absolute1%occupiedfalsevacancy/10%uncertainty limits as prior source work;95%global/90%each-image retention of classifier-correct confident vacancies. Both methods scored,no tuning/promotion.',
        batch_frames=5,maximum_child_seconds=180,maximum_invocation_seconds=900,maximum_worker_rss_bytes=1792*1024**2,minimum_available_ram_bytes=300000000,
        expected_detector_calls=35,expected_classifier_calls=0,scope='Supplied-geometry development fusion only. Frozen score replay plus actual detector inference,not full end-to-end classifier/API/GUI evaluation. No exhaustive detector GT/mAP,trafficvideo,learned region,final or Singaporecamera claim;wholeTESTclosed.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json')

def worker(path,start,end):
    import threading,psutil,torch
    from PIL import Image
    from smart_parking.vision import VisionEngine,assign_occupancy
    from smart_parking.layout import load_layout
    p=read(path);verify(p);out=Path(path).parent;torch.manual_seed(p['seed']);torch.use_deterministic_algorithms(True)
    proc=psutil.Process();peak=[proc.memory_info().rss];stop=threading.Event()
    def monitor():
        while not stop.wait(.002):
            rss=proc.memory_info().rss;peak[0]=max(peak[0],rss)
            if rss>p['maximum_worker_rss_bytes'] or psutil.virtual_memory().available<p['minimum_available_ram_bytes']:os._exit(87)
    monitor_thread=threading.Thread(target=monitor,daemon=True);monitor_thread.start();clock=time.perf_counter();engine=VisionEngine('fasterrcnn',640);calls=dict(detector=0,classifier=0)
    def counter(key):
        def hook(*args):calls[key]+=1
        return hook
    engine.model.register_forward_hook(counter('detector'));engine.classifier.register_forward_hook(counter('classifier'))
    original={(r['image'],r['slot_id']):r for r in read(ROOT/p['baseline_predictions'])};research={(r['image'],r['slot_id']):r for r in read(ROOT/p['candidate_predictions'])['acpds']}
    assert len(original)==len(research)==1904
    for i in range(start,end):
        if (out/'CANCEL').exists():raise InterruptedError('Cancelled at frame boundary')
        target=out/f'frame_{i:03}.json';assert not target.exists();frame=p['frames'][i];assert frame['role']=='valid'
        assert digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['layout'])==frame['layout_sha256']
        layout=load_layout(ROOT/frame['layout'])
        with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
        started=datetime.now(timezone.utc);timer=time.perf_counter();result,unused_overlay=engine.analyze(image,None,.5,.25,.75);del unused_overlay
        assert result['classifier_checkpoint_sha256']==p['input_hashes']['models/checkpoints/occupancy_resnet18.pt'] and result['weight_sha256']==p['input_hashes']['models/pretrained/fasterrcnn_resnet50_fpn_v2.pth']
        methods={};ds=result['detections'];masks=[None]*len(ds)
        for name,index in [('original',original),('last_block',research)]:
            ordered=[index[(frame['name'],s['id'])] for s in layout['slots']]
            for slot,r in zip(layout['slots'],ordered):assert r['image_sha256']==frame['image_sha256'] and int(r['label'])==int(slot['ground_truth_occupied'])
            probabilities=[r['probability_occupied'] for r in ordered];assigned=assign_occupancy(image.size,layout,ds,masks,probabilities,.25,.75)
            methods[name]=[dict(image=frame['name'],image_sha256=frame['image_sha256'],slot_id=s['id'],label=int(s['ground_truth_occupied']),probability_occupied=prob,
                classifier_state=state_from_probability(prob),fusion_state=a['state'],vehicle_id=a['vehicle_id'],slot_overlap=a['slot_overlap']) for s,prob,a in zip(layout['slots'],probabilities,assigned)]
            paired_fusion_metrics(methods[name])
        dump(target,dict(index=i,image=frame['name'],started_at=started.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-timer,
            detector_result=result,methods=methods,worker_protocol_sha256=digest(path)));print('Completed frame',i,frame['name'],flush=True);del image,result,methods
    stop.set();monitor_thread.join(.1);assert calls==dict(detector=end-start,classifier=0)
    dump(out/f'batch_{start:03}_{end:03}.json',dict(start=start,end=end,peak_rss_bytes=peak[0],duration_seconds=time.perf_counter()-clock,model_calls=calls,protocol_sha256=digest(path)))

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256'] and not(out/'run.json').exists();verify(p)
    statepath=ROOT/'data/automation_state.json';s=read(statepath);assert not s['active_training_jobs'] and not s['active_validation_jobs'];assert p['run_id'] not in s['completed_run_ids']
    s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/evaluate_acpds_frozen_fusion.py --run '+path.relative_to(ROOT).as_posix(),maximum_seconds=p['maximum_invocation_seconds'])];dump(statepath,s)
    clock=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    try:
        for start in range(0,35,p['batch_frames']):
            end=min(start+p['batch_frames'],35);batch=out/f'batch_{start:03}_{end:03}.json'
            if batch.exists():assert read(batch)['protocol_sha256']==digest(path);continue
            if (out/'CANCEL').exists() or time.perf_counter()-clock>p['maximum_invocation_seconds']-p['maximum_child_seconds']:raise InterruptedError('Invocation boundary;resume completed frames')
            # A crash may leave a partial batch. Resume only uncompleted trailing
            # frames;previous evidence is never overwritten or re-inferred.
            pending=[i for i in range(start,end) if not(out/f'frame_{i:03}.json').exists()]
            assert pending,'Complete frame evidence without batch receipt;inspect before resuming'
            assert pending==list(range(pending[0],end))
            actual_start=pending[0];child=subprocess.run([sys.executable,__file__,'--worker',str(path),'--start',str(actual_start),'--end',str(end)],cwd=ROOT,capture_output=True,text=True,timeout=p['maximum_child_seconds'],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            tag=datetime.now(timezone.utc).strftime('%H%M%S%f');(out/f'batch_{start:03}_{tag}.stdout.txt').write_text(child.stdout,encoding='utf-8');(out/f'batch_{start:03}_{tag}.stderr.txt').write_text(child.stderr,encoding='utf-8');assert child.returncode==0,('Worker failed',child.returncode)
            if actual_start!=start:dump(batch,dict(start=start,end=end,partial_batch_recovery=True,protocol_sha256=digest(path),partial_resource_receipt=f'batch_{actual_start:03}_{end:03}.json'))
            print('Batch completed',start,end,flush=True)
        verify(p);records=[read(out/f'frame_{i:03}.json') for i in range(35)];assert all(r['worker_protocol_sha256']==digest(path) for r in records)
        methods={}
        for name in ['original','last_block']:
            rows=[r for record in records for r in record['methods'][name]];assert len(rows)==1904 and sum(r['label'] for r in rows)==831
            metrics=paired_fusion_metrics(rows);checks=fusion_gates(metrics,p['gates']);methods[name]=dict(metrics=metrics,checks=checks,development_gate_passed=all(checks.values()))
        batches=[read(out/f'batch_{i:03}_{min(i+5,35):03}.json') for i in range(0,35,5)];assert not any(b.get('partial_batch_recovery') for b in batches),'Recovered batch requires resource-receipt reconciliation before counting'
        calls={k:sum(b['model_calls'][k] for b in batches) for k in ['detector','classifier']};assert calls==dict(detector=35,classifier=0)
        r=dict(run_id=p['run_id'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=p['seed'],protocol_sha256=digest(path),methods=methods,model_calls=calls,images=35,labelled_spaces=1904,
            maximum_batch_rss_bytes=max(b['peak_rss_bytes'] for b in batches),batches=batches,production_promoted=False,thresholds_changed=False,training_performed=False,final_pixels_or_labels_opened=False,scope=p['scope'])
        dump(out/'run.json',r);dump(ROOT/'models/acpds_frozen_fusion.json',r);dump(ROOT/'reports/acpds_frozen_fusion_latest.json',r)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Fixed-method real DEVELOPMENT detector/frozen-score fusion diagnostic',started_at=started,finished_at=r['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='35reusedVALID/1904spaces;TESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture='FasterRCNN640 with original and research frozen classifier scores',random_seed=p['seed'],hardware='CPU4threads/sequential capped5frame workers',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps({k:dict(checks=v['checks'],development_gate_passed=v['development_gate_passed'],metrics={n:x for n,x in v['metrics'].items() if n!='per_image'}) for k,v in methods.items()}),logs=out.relative_to(ROOT).as_posix(),checkpoints='Frozen original and last-block scores;no weights changed',code_revision_basis='c004db7 plus sealed fixed-method diagnostics',implementation_sha256=digest(__file__),conclusions='Both prespecified methods reported;no threshold/model selection or promotion')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(statepath);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['acpds_frozen_fusion']=r;dump(statepath,s);print(json.dumps({k:dict(checks=v['checks'],metrics={n:x for n,x in v['metrics'].items() if n!='per_image'}) for k,v in methods.items()},indent=2))
    except BaseException as error:dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:s=read(statepath);s['active_validation_jobs']=[];dump(statepath,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');parser.add_argument('--worker');parser.add_argument('--start',type=int);parser.add_argument('--end',type=int);a=parser.parse_args()
    worker(a.worker,a.start,a.end) if a.worker else run(a.run) if a.run else prepare()
