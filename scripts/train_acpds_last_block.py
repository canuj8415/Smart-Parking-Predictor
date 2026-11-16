"""One bounded warm last-block adaptation;all final cohorts remain closed."""
import argparse,copy,csv,json,os,sys,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.last_block import configure_last_block,normalize_rgb_batch
from smart_parking.occupancy_evaluation import occupancy_metrics
from smart_parking.source_crops import balanced_source_weights
from smart_parking.vacancy_retention import vacancy_retention
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];old=read(ROOT/'reports/pklot_rgb_retention_latest.json');new=read(ROOT/'reports/acpds_exact_crop_cache_latest.json');warmcard=ROOT/'models/acpds_balanced_head.json';warm=read(warmcard)
    assert new['implementation_gate_passed'] and old['pixel_mismatches']==0 and not warm['development_gate_passed']
    oldpath=ROOT/old['manifest'];newpath=ROOT/new['cache_manifest'];assert digest(oldpath)==old['manifest_sha256'] and digest(newpath)==new['cache_manifest_sha256'];checkpoint=ROOT/warm['candidate_checkpoint'];assert digest(checkpoint)==warm['candidate_checkpoint_sha256']
    now=datetime.now(timezone.utc);rid='ACPDS-LAST-BLOCK-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False);claims=sorted((ROOT/'data/holdout_claims').glob('*.claim.json'))
    code=['scripts/train_acpds_last_block.py','src/smart_parking/last_block.py','tests/test_last_block.py','src/smart_parking/occupancy_evaluation.py','src/smart_parking/source_crops.py','src/smart_parking/vacancy_retention.py'];inputs=[oldpath,newpath,warmcard,checkpoint,ROOT/'data/manifests/acpds_source_roles_v1.json',ROOT/'experiments/results'/warm['run_id']/'candidate_predictions.json',*claims]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=160,source_ids=['SRC-DS-001','SRC-DS-021','SRC-MOD-003'],hypothesis='Adapting layer4 convolutional representation plus the occupancy head improves the source-limited frozen-head candidate while retaining existing development behavior.',prior_exposure='Two ACPDS development model studies already known;warm head93.0672%/31confidentfalsevacants. This is another distinct bounded DEVELOPMENT hypothesis,not final evidence or parameter grid. WholeTESTclosed.',
        warm_checkpoint=checkpoint.relative_to(ROOT).as_posix(),warm_checkpoint_sha256=digest(checkpoint),warm_prediction_file='experiments/results/'+warm['run_id']+'/candidate_predictions.json',datasets=[oldpath.relative_to(ROOT).as_posix(),newpath.relative_to(ROOT).as_posix()],source_masses={'SRC-DS-001':.5,'SRC-DS-021':.5},architecture='Only layer4 convolution weights and fc trainable;all lower parameters and all batch-normalization affine/buffers frozen;model.eval retained',optimizer='AdamW',learning_rate=.0001,weight_decay=.0001,batch_size=64,max_epochs=4,patience=2,min_delta=.0001,gradient_clip_norm=1.,maximum_invocation_seconds=900,torch_threads=4,minimum_available_ram_bytes=1600000000,epoch_selection='Minimum .5*ACPDS mean-per-image VALID CE+.5*PKLot macro-camera DEV CE,including warm epoch0;no gate-based epoch cherry-picking',normalization='Exact cached96RGB uint8 -> existing ImageNet normalization;no augmentation/ROI/crop/threshold changes',baseline_probability_tolerance=1e-5,
        thresholds=dict(hard=.5,vacant_at_or_below=.25,occupied_at_or_above=.75),acpds_gates=read(ROOT/'experiments/results'/warm['run_id']/'protocol.json')['acpds_gates'],retention_gates=read(ROOT/'experiments/results'/warm['run_id']/'protocol.json')['retention_gates'],retention_baseline='Warm selected head,including its improved reused PKLot development decisions',
        input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},source_hashes={f:digest(ROOT/f) for f in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],consumed_groups=sorted({tuple(g) for c in claims for g in read(c).get('source_groups',[])}),scope='Development only;3932validation samples/17946training samples. Reused PKLot validation is retention evidence,not independent final. No TEST/consumedfinal semantic or pixel access,no production promotion.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(str(out/'protocol.json'))

def run(path):
    import numpy as np,torch,psutil
    from torchvision.models import resnet18
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not (out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    for f,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    assert psutil.virtual_memory().available>=p['minimum_available_ram_bytes'],'Insufficient available RAM;resume later without changing recipe'
    sp=ROOT/'data/automation_state.json';s=read(sp);assert not s['active_training_jobs'] and not s['active_validation_jobs'];lock=ROOT/'outputs/training_locks/acpds_last_block.lock';lock.parent.mkdir(parents=True,exist_ok=True);fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd);s['active_training_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/train_acpds_last_block.py --run '+path.relative_to(ROOT).as_posix(),maximum_invocation_seconds=900)];dump(sp,s);clock=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    def boundary():
        if (out/'CANCEL').exists() or time.perf_counter()-clock>900:raise InterruptedError('Bounded invocation stopped;resume saved checkpoint')
        if psutil.virtual_memory().available<300000000:raise InterruptedError('Low available RAM;checkpoint before stopping')
    def save(value,file):
        tmp=file.with_suffix('.partial');torch.save(value,tmp);os.replace(tmp,file)
    try:
        torch.manual_seed(p['seed']);torch.set_num_threads(4);torch.use_deterministic_algorithms(True);data=np.empty((21878,96,96,3),dtype=np.uint8);rows=[];offset=0
        for filename in p['datasets']:
            dataset=read(ROOT/filename);groups=defaultdict(list)
            for r in dataset['records']:groups[r['crop_file']].append(r)
            for chunk in dataset['chunks']:
                boundary();assert digest(ROOT/chunk['path'])==chunk['sha256'];rs=sorted(groups[chunk['path']],key=lambda r:r['crop_index'])
                with np.load(ROOT/chunk['path'],allow_pickle=False) as a:
                    n=len(rs);assert a['crops'].dtype==np.uint8 and a['crops'].shape==(n,96,96,3) and a['labels'].tolist()==[r['label'] for r in rs];data[offset:offset+n]=a['crops']
                for r in rs:
                    if r['source_id']=='SRC-DS-001':assert [r['camera_id'],r['date']] not in p['consumed_groups']
                    assert r['role'] in ('train','validation');rows.append(dict(r,frame=r.get('frame',r.get('image')),camera_id=r.get('camera_id','acpds_collection')))
                offset+=n
        assert offset==len(rows)==21878;y=torch.tensor([r['label'] for r in rows],dtype=torch.long);train=torch.tensor([i for i,r in enumerate(rows) if r['role']=='train']);newval=[i for i,r in enumerate(rows) if r['role']=='validation' and r['source_id']=='SRC-DS-021'];oldval=[i for i,r in enumerate(rows) if r['role']=='validation' and r['source_id']=='SRC-DS-001'];assert (len(train),len(newval),len(oldval))==(17946,1904,2028)
        weights=torch.tensor(balanced_source_weights([rows[int(i)] for i in train],p['source_masses']),dtype=torch.float32);warm=torch.load(ROOT/p['warm_checkpoint'],map_location='cpu',weights_only=True);model=resnet18(weights=None);model.fc=torch.nn.Linear(512,2);model.load_state_dict(warm['state_dict']);names=configure_last_block(model);frozen={k:v.clone() for k,v in model.state_dict().items() if k not in names};parameters=[q for q in model.parameters() if q.requires_grad];optimizer=torch.optim.AdamW(parameters,lr=p['learning_rate'],weight_decay=p['weight_decay'])
        def batch(indices):return normalize_rgb_batch(torch.from_numpy(data[np.asarray(indices,dtype=np.int64)]))
        def evaluate(indices):
            result=[]
            with torch.inference_mode():
                for k in range(0,len(indices),128):
                    boundary();ids=indices[k:k+128];logits=model(batch(ids));probs=torch.softmax(logits,dim=1)[:,1].tolist();costs=torch.nn.functional.cross_entropy(logits,y[ids],reduction='none').tolist();result.extend(dict(rows[i],probability_occupied=float(v),negative_log_probability=float(cost)) for i,v,cost in zip(ids,probs,costs))
            return result
        def metrics(values):return occupancy_metrics([r['label'] for r in values],[r['probability_occupied'] for r in values])
        def group(values,key):
            d=defaultdict(list)
            for r in values:d[key(r)].append(r)
            return d
        def selection(new,old):
            # Stable,unweighted two-class CE computed from logits before softmax.
            def loss(v):return sum(r['negative_log_probability'] for r in v)/len(v)
            n=group(new,lambda r:r['frame']);o=group(old,lambda r:r['camera_id']);return .5*sum(loss(v) for v in n.values())/len(n)+.5*sum(loss(v) for v in o.values())/len(o)
        baseline_new=evaluate(newval);baseline_old=evaluate(oldval);saved=read(ROOT/p['warm_prediction_file']);saved={(r['source_id'],r['frame'],r['slot_id']):r for v in saved.values() for r in v};delta=max(abs(r['probability_occupied']-saved[(r['source_id'],r['frame'],r['slot_id'])]['probability_occupied']) for r in baseline_new+baseline_old);assert delta<=p['baseline_probability_tolerance'],delta;dump(out/'baseline_predictions.json',dict(acpds=baseline_new,pklot=baseline_old));best_loss=selection(baseline_new,baseline_old);best=copy.deepcopy(model.state_dict());best_epoch=0;stale=0;curves=[];initial_epoch=0;resume_order=None;resume_offset=0;checkpoint=out/'last.pt'
        if checkpoint.exists():
            last=torch.load(checkpoint,map_location='cpu',weights_only=True);assert last['protocol_sha256']==digest(path);model.load_state_dict(last['model']);optimizer.load_state_dict(last['optimizer']);best=last['best'];best_loss=last['best_loss'];best_epoch=last['best_epoch'];stale=last['stale'];curves=last['curves'];initial_epoch=last['epoch'];resume_order=last['order'];resume_offset=last['offset'];torch.set_rng_state(last['rng'])
        def checkpoint_at(epoch,order,offset):save(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),best=best,best_loss=best_loss,best_epoch=best_epoch,stale=stale,curves=curves,epoch=epoch,order=order,offset=offset,rng=torch.get_rng_state(),protocol_sha256=digest(path)),checkpoint)
        checkpoint_at(initial_epoch,resume_order,resume_offset)
        for epoch in range(initial_epoch,p['max_epochs']):
            if stale>=p['patience']:break
            order=resume_order if resume_order is not None else torch.randperm(len(train));begin=resume_offset if resume_order is not None else 0;resume_order=None;resume_offset=0
            for at in range(begin,len(train),64):
                try:boundary()
                except InterruptedError:checkpoint_at(epoch,order,at);raise
                positions=order[at:at+64];ids=train[positions];optimizer.zero_grad();loss=(torch.nn.functional.cross_entropy(model(batch(ids.tolist())),y[ids],reduction='none')*weights[positions]).mean();assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(parameters,1.);optimizer.step()
                if (at//64)%35==0:dump(out/'progress.json',dict(phase='training',epoch=epoch+1,max_epochs=4,training_rows_completed=min(at+64,len(train)),training_rows=len(train),elapsed_seconds=time.perf_counter()-clock))
            try:new=evaluate(newval);old=evaluate(oldval)
            except InterruptedError:checkpoint_at(epoch,order,len(train));raise
            value=selection(new,old);curves.append(dict(epoch=epoch+1,selection_loss=value));
            if value<best_loss-p['min_delta']:best_loss=value;best=copy.deepcopy(model.state_dict());best_epoch=epoch+1;stale=0;save(dict(state_dict=best,protocol_sha256=digest(path)),out/'best.pt')
            else:stale+=1
            checkpoint_at(epoch+1,None,0);dump(out/'curves.json',curves);print('Epoch',epoch+1,'loss',value,'selected',best_epoch,flush=True)
        model.load_state_dict(best);new=evaluate(newval);old=evaluate(oldval);bn,cn,bo,co=(metrics(v) for v in [baseline_new,new,baseline_old,old]);byimage={k:metrics(v) for k,v in group(new,lambda r:r['frame']).items()};bc={k:metrics(v) for k,v in group(baseline_old,lambda r:r['camera_id']).items()};cc={k:metrics(v) for k,v in group(old,lambda r:r['camera_id']).items()};ret=vacancy_retention(baseline_old,old);g=p['acpds_gates'];rg=p['retention_gates'];checks=dict(new_accuracy=cn['hard']['accuracy_on_covered']>=g['overall_hard_accuracy_min'],new_every_image=all(m['hard']['accuracy_on_covered']>=g['every_image_hard_accuracy_min'] for m in byimage.values()),new_false_vacancy=cn['selective']['fraction_of_occupied_called_vacant']<=g['confident_false_vacant_fraction_of_occupied_max'],new_uncertainty=cn['selective']['uncertain']/1904<=g['uncertain_fraction_max'],old_accuracy=co['hard']['accuracy_on_covered']>=bo['hard']['accuracy_on_covered']-rg['overall_hard_accuracy_drop_max'],old_camera=all(cc[k]['hard']['accuracy_on_covered']>=bc[k]['hard']['accuracy_on_covered']-rg['per_camera_hard_accuracy_drop_max'] for k in bc),old_false_vacancy=co['selective']['false_vacant']<=bo['selective']['false_vacant'],old_uncertainty=co['selective']['uncertain']/2028<=bo['selective']['uncertain']/2028+rg['uncertainty_fraction_increase_max'],old_vacancy_identity_retention=ret['gate_passed'])
        assert all(torch.equal(v,model.state_dict()[k]) for k,v in frozen.items());candidate=copy.deepcopy(warm);candidate.update(state_dict=best,run_id=p['run_id'],selected_epoch=best_epoch,training='DEVELOPMENT last-block adaptation;no app/final promotion');dest=ROOT/'models/checkpoints/acpds_last_block'/p['run_id']/'candidate.pt';dest.parent.mkdir(parents=True,exist_ok=True);save(candidate,dest);reloaded=torch.load(dest,map_location='cpu',weights_only=True);assert all(torch.equal(v,reloaded['state_dict'][k]) for k,v in best.items())
        for f,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        r=dict(run_id=p['run_id'],started_at=p['prepared_at'],finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.perf_counter()-clock,seed=160,protocol_sha256=digest(path),epochs_completed=len(curves),selected_epoch=best_epoch,early_stopped=stale>=p['patience'],baseline_probability_delta=delta,baseline_acpds=bn,candidate_acpds=cn,baseline_pklot=bo,candidate_pklot=co,per_image=byimage,per_camera=cc,per_date_retention=ret,checks=checks,development_gate_passed=all(checks.values()),candidate_checkpoint=dest.relative_to(ROOT).as_posix(),candidate_checkpoint_sha256=digest(dest),lower_parameters_and_all_bn_unchanged=True,checkpoint_roundtrip_exact=True,trainable_parameter_names=names,training_samples=17946,validation_samples=3932,production_promoted=False,final_pixels_or_labels_opened=False,scope=p['scope']);dump(out/'candidate_predictions.json',dict(acpds=new,pklot=old));dump(out/'run.json',r);dump(ROOT/'models/acpds_last_block.json',r);dump(ROOT/'reports/acpds_last_block_latest.json',r)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Bounded last-block representation DEVELOPMENT adaptation',started_at=r['started_at'],finished_at=r['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='ACPDS+PKLotTRAIN;3932DEV;wholeTESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture=p['architecture'],optimizer='AdamW',learning_rate=.0001,epochs=len(curves),batch_size=64,random_seed=160,hardware='CPU4threads',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(dict(acpds=cn,pklot=co,checks=checks)),logs=out.relative_to(ROOT).as_posix(),checkpoints=r['candidate_checkpoint'],code_revision_basis='5bcd136 plus sealed last-block protocol',implementation_sha256=digest(__file__),conclusions='Development gate='+str(r['development_gate_passed'])+';no final/app promotion')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(sp);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['acpds_last_block']=r;dump(sp,s);print(json.dumps(dict(run_id=p['run_id'],epochs=len(curves),selected_epoch=best_epoch,acpds_accuracy=cn['hard']['accuracy_on_covered'],false_vacant=cn['selective']['false_vacant'],checks=checks),indent=2))
    except BaseException as e:dump(out/'interrupted.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),error=type(e).__name__,detail=str(e),completed_run_counted=False,resume_command='scripts/train_acpds_last_block.py --run '+path.relative_to(ROOT).as_posix()));raise
    finally:s=read(sp);s['active_training_jobs']=[];dump(sp,s);lock.unlink(missing_ok=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
