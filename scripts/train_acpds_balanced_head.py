"""One resumable source-balanced linear-head experiment;whole TEST closed."""
import argparse,copy,csv,json,os,sys,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.occupancy_evaluation import occupancy_metrics
from smart_parking.source_crops import balanced_source_weights
from smart_parking.vacancy_retention import vacancy_retention
ORIGINAL=ROOT/'models/checkpoints/occupancy_resnet18.pt';MANIFEST=ROOT/'data/processed/acpds_development_v1/development_images.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];data=read(MANIFEST);assert data['training_spaces']==7842 and data['validation_spaces']==1904
    now=datetime.now(timezone.utc);rid='ACPDS-BALANCED-HEAD-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    oldcard=ROOT/'models/occupancy_expansion_candidate.json';old=read(oldcard);base=ROOT/'models/acpds_occupancy_baseline.json'
    code=['scripts/train_acpds_balanced_head.py','src/smart_parking/source_crops.py','src/smart_parking/layout.py','src/smart_parking/vision.py','src/smart_parking/occupancy_evaluation.py','src/smart_parking/vacancy_retention.py','tests/test_vacancy_retention.py']
    claims=sorted((ROOT/'data/holdout_claims').glob('*.claim.json'));consumed=sorted({(str(camera).casefold(),day) for claim in claims for camera,day in read(claim).get('source_groups',[])})
    inputs=[MANIFEST,oldcard,base,ROOT/'data/manifests/acpds_source_roles_v1.json',ORIGINAL,*claims]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=154,source_ids=['SRC-DS-001','SRC-DS-021','SRC-MOD-003'],
        hypothesis='One frozen-backbone occupancy head trained with equal ACPDS/PKLot source mass and training-only class/camera balancing improves action-camera validation reliability while retaining original PKLot development decisions.',
        prior_exposure='Original ACPDS VALID baseline89.4958%/62confidentfalsevacants and PKLot reused development studies already known. This is DEVELOPMENT selection,not blind/final evidence. No ACPDS TEST values/pixels opened.',
        architecture='Original ResNet18 backbone frozen/eval;512to2linear head warm-starts original production head;no augmentation/crop/perspective/threshold grid',
        source_masses={'SRC-DS-001':.5,'SRC-DS-021':.5},balancing='Training-only inverse(camera,class) stratum frequency within each source. ACPDS uses collection camera stratum,not invented capture IDs.',
        optimizer='AdamW',learning_rate=.001,weight_decay=.001,batch_size=128,max_epochs=12,patience=3,min_delta=.0001,maximum_invocation_seconds=900,torch_threads=4,
        epoch_selection='Lowest .5*mean-per-ACPDS-image VALID cross-entropy + .5*macro-PKLot-camera development cross-entropy;include original epoch0;no gate-based epoch selection',
        thresholds=dict(hard=.5,vacant_at_or_below=.25,occupied_at_or_above=.75),baseline_probability_tolerance=1e-5,
        acpds_gates=dict(overall_hard_accuracy_min=.95,every_image_hard_accuracy_min=.90,confident_false_vacant_fraction_of_occupied_max=.01,uncertain_fraction_max=.10),
        retention_gates=dict(overall_hard_accuracy_drop_max=.005,per_camera_hard_accuracy_drop_max=.01,confident_false_vacant_increase_max=0,per_date_correct_confident_vacancy_retention_min=.95,uncertainty_fraction_increase_max=.02),
        input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},source_hashes={f:digest(ROOT/f) for f in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        original_checkpoint_sha256=digest(ORIGINAL),old_feature_files=old['feature_cache_files'],old_feature_manifest_sha256=old['manifest_sha256'],consumed_camera_date_groups=consumed,source_manifest=MANIFEST.relative_to(ROOT).as_posix(),frames=data['frames'],
        scope='DEVELOPMENT ONLY;old PKLot validation is reused retention evidence,not independent final data. All ACPDS TEST and all earlier consumed final groups excluded. No app promotion even if development gates pass.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(str(out/'protocol.json'))

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256'] and not (out/'run.json').exists()
    for f,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs']
    lock=ROOT/'outputs/training_locks/acpds_balanced_head.lock';lock.parent.mkdir(parents=True,exist_ok=True);fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    s['active_training_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/train_acpds_balanced_head.py --run '+path.relative_to(ROOT).as_posix(),maximum_invocation_seconds=900)];dump(ROOT/'data/automation_state.json',s)
    start=datetime.now(timezone.utc);clock=time.perf_counter();feature_files=[];epoch_done=0
    def boundary():
        if (out/'CANCEL').exists() or time.perf_counter()-clock>p['maximum_invocation_seconds']:raise InterruptedError('Bounded checkpointed invocation stopped;resume same protocol')
    def atomic_torch(value,path):
        import torch
        path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.partial');torch.save(value,tmp);os.replace(tmp,path)
    try:
        import torch
        from PIL import Image
        from torchvision.models import resnet18
        from smart_parking.layout import crop_slot,load_layout
        from smart_parking.vision import normalize_crop
        torch.manual_seed(p['seed']);torch.set_num_threads(p['torch_threads']);torch.use_deterministic_algorithms(True)
        original=torch.load(ORIGINAL,map_location='cpu',weights_only=True);backbone=resnet18(weights=None);backbone.fc=torch.nn.Linear(512,2);backbone.load_state_dict(original['state_dict']);backbone.fc=torch.nn.Identity();backbone.eval()
        for parameter in backbone.parameters():parameter.requires_grad_(False)
        features=[];rows=[]
        for item in p['old_feature_files']:
            boundary();assert digest(ROOT/item['path'])==item['sha256'];chunk=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True)
            assert chunk['manifest_sha256']==p['old_feature_manifest_sha256'] and chunk['original_checkpoint_sha256']==p['original_checkpoint_sha256']
            assert all(r['role'] in ('train','validation') and [r['camera_id'].casefold(),r['date']] not in p['consumed_camera_date_groups'] for r in chunk['rows']);features.append(chunk['features']);rows.extend(dict(r,source_id='SRC-DS-001') for r in chunk['rows'])
        assert len(rows)==12132 and sum(r['role']=='train' for r in rows)==10104
        for index,frame in enumerate(p['frames']):
            boundary();assert frame['role'] in ('train','validation');assert digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['layout'])==frame['layout_sha256'];cache=out/'feature_chunks'/f'frame_{index:03d}.pt';layout=load_layout(ROOT/frame['layout'])
            if cache.exists():
                chunk=torch.load(cache,map_location='cpu',weights_only=True)
                assert chunk['protocol_sha256']==digest(path) and chunk['frame']==frame and chunk['source_hashes']==p['source_hashes']
            else:
                with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
                values=[]
                for offset in range(0,len(layout['slots']),32):
                    boundary();slots=layout['slots'][offset:offset+32];x=torch.stack([normalize_crop(crop_slot(image,slot)) for slot in slots])
                    with torch.inference_mode():values.append(backbone(x).clone())
                chunk=dict(features=torch.cat(values),protocol_sha256=digest(path),frame=frame,source_hashes=p['source_hashes']);atomic_torch(chunk,cache)
            assert chunk['features'].shape==(len(layout['slots']),512) and torch.isfinite(chunk['features']).all();features.append(chunk['features']);rows.extend(dict(role=frame['role'],source_id='SRC-DS-021',camera_id='acpds_collection',frame=frame['name'],slot_id=slot['id'],label=slot['ground_truth_occupied']) for slot in layout['slots']);feature_files.append(dict(path=cache.relative_to(ROOT).as_posix(),sha256=digest(cache)))
            dump(out/'progress.json',dict(phase='source_features',source_images=index+1,total_source_images=len(p['frames']),source_slots=sum(f['slots'] for f in p['frames'][:index+1]),elapsed_seconds=time.perf_counter()-clock,resume_available=True))
            if (index+1)%25==0:print('Frozen source features',index+1,'/',len(p['frames']),flush=True)
        x=torch.cat(features);del features;assert len(rows)==21878 and torch.isfinite(x).all();y=torch.tensor([r['label'] for r in rows],dtype=torch.long)
        train=torch.tensor([i for i,r in enumerate(rows) if r['role']=='train']);newval=torch.tensor([i for i,r in enumerate(rows) if r['role']=='validation' and r['source_id']=='SRC-DS-021']);oldval=torch.tensor([i for i,r in enumerate(rows) if r['role']=='validation' and r['source_id']=='SRC-DS-001'])
        assert (len(train),len(newval),len(oldval))==(17946,1904,2028);weight=torch.tensor(balanced_source_weights([rows[int(i)] for i in train],p['source_masses']),dtype=torch.float32)
        newgroups={name:torch.tensor([int(i) for i in newval if rows[int(i)]['frame']==name]) for name in sorted({rows[int(i)]['frame'] for i in newval})};oldgroups={name:torch.tensor([int(i) for i in oldval if rows[int(i)]['camera_id']==name]) for name in sorted({rows[int(i)]['camera_id'] for i in oldval})}
        head=torch.nn.Linear(512,2);head.load_state_dict({k[3:]:v for k,v in original['state_dict'].items() if k.startswith('fc.')});head.eval()
        def predictions(indices):
            with torch.inference_mode():probs=torch.softmax(head(x[indices]),dim=1)[:,1].tolist()
            return [dict(rows[int(i)],probability_occupied=float(prob)) for i,prob in zip(indices,probs)]
        def report(values):return occupancy_metrics([r['label'] for r in values],[r['probability_occupied'] for r in values])
        def grouped(values,key):
            groups=defaultdict(list)
            for r in values:groups[key(r)].append(r)
            return {name:report(group) for name,group in groups.items()}
        def validation_loss():
            with torch.inference_mode():return float(.5*torch.stack([torch.nn.functional.cross_entropy(head(x[i]),y[i]) for i in newgroups.values()]).mean()+.5*torch.stack([torch.nn.functional.cross_entropy(head(x[i]),y[i]) for i in oldgroups.values()]).mean())
        baseline_new=predictions(newval);baseline_old=predictions(oldval);saved=read(ROOT/'experiments/results/ACPDS-BASELINE-20261026T231422794077Z/development_predictions.json');saved={(r['image'],r['slot_id']):r for r in saved};delta=max(abs(r['probability_occupied']-saved[(r['frame'],r['slot_id'])]['probability_occupied']) for r in baseline_new);assert delta<=p['baseline_probability_tolerance'],delta
        dump(out/'baseline_predictions.json',dict(acpds=baseline_new,pklot=baseline_old));optimizer=torch.optim.AdamW(head.parameters(),lr=p['learning_rate'],weight_decay=p['weight_decay']);best_loss=validation_loss();best=copy.deepcopy(head.state_dict());best_epoch=0;stale=0;curves=[];initial_epoch=0;last=out/'last_head.pt'
        if last.exists():
            checkpoint=torch.load(last,map_location='cpu',weights_only=True);assert checkpoint['protocol_sha256']==digest(path);head.load_state_dict(checkpoint['head']);optimizer.load_state_dict(checkpoint['optimizer']);best=checkpoint['best'];best_epoch=checkpoint['best_epoch'];best_loss=checkpoint['best_loss'];stale=checkpoint['stale'];curves=checkpoint['curves'];initial_epoch=checkpoint['epoch'];torch.set_rng_state(checkpoint['rng'])
        for epoch in range(initial_epoch,p['max_epochs']):
            if stale>=p['patience']:break
            boundary();head.train();order=torch.randperm(len(train))
            for offset in range(0,len(train),p['batch_size']):
                boundary();positions=order[offset:offset+p['batch_size']];i=train[positions];optimizer.zero_grad();loss=(torch.nn.functional.cross_entropy(head(x[i]),y[i],reduction='none')*weight[positions]).mean();loss.backward();optimizer.step()
            head.eval();value=validation_loss();curves.append(dict(epoch=epoch+1,validation_selection_loss=value));epoch_done=epoch+1
            if value<best_loss-p['min_delta']:best_loss=value;best=copy.deepcopy(head.state_dict());best_epoch=epoch+1;stale=0;atomic_torch(dict(head=best,protocol_sha256=digest(path)),out/'best_head.pt')
            else:stale+=1
            atomic_torch(dict(epoch=epoch+1,head=head.state_dict(),optimizer=optimizer.state_dict(),best=best,best_epoch=best_epoch,best_loss=best_loss,stale=stale,curves=curves,rng=torch.get_rng_state(),protocol_sha256=digest(path)),last);dump(out/'curves.json',curves);print('Epoch',epoch+1,'selection loss',value,'selected',best_epoch,flush=True)
        head.load_state_dict(best);head.eval();candidate_new=predictions(newval);candidate_old=predictions(oldval);bnew,cnew,bold,cold=(report(values) for values in [baseline_new,candidate_new,baseline_old,candidate_old]);by_image=grouped(candidate_new,lambda r:r['frame']);b_camera=grouped(baseline_old,lambda r:r['camera_id']);c_camera=grouped(candidate_old,lambda r:r['camera_id']);b_date=grouped(baseline_old,lambda r:r['camera_id']+'/'+r['date']);c_date=grouped(candidate_old,lambda r:r['camera_id']+'/'+r['date']);g=p['acpds_gates'];ret=p['retention_gates']
        retention=vacancy_retention(baseline_old,candidate_old,ret['per_date_correct_confident_vacancy_retention_min'])
        checks=dict(new_overall_accuracy=cnew['hard']['accuracy_on_covered']>=g['overall_hard_accuracy_min'],new_every_image_accuracy=all(m['hard']['accuracy_on_covered']>=g['every_image_hard_accuracy_min'] for m in by_image.values()),new_false_vacancy=cnew['selective']['fraction_of_occupied_called_vacant']<=g['confident_false_vacant_fraction_of_occupied_max'],new_uncertainty=cnew['selective']['uncertain']/1904<=g['uncertain_fraction_max'],old_overall_accuracy=cold['hard']['accuracy_on_covered']>=bold['hard']['accuracy_on_covered']-ret['overall_hard_accuracy_drop_max'],old_per_camera_accuracy=all(c_camera[k]['hard']['accuracy_on_covered']>=b_camera[k]['hard']['accuracy_on_covered']-ret['per_camera_hard_accuracy_drop_max'] for k in b_camera),old_false_vacancy=cold['selective']['false_vacant']<=bold['selective']['false_vacant'],old_uncertainty=cold['selective']['uncertain']/2028<=bold['selective']['uncertain']/2028+ret['uncertainty_fraction_increase_max'],old_per_date_vacancy_retention=retention['gate_passed'])
        selected=copy.deepcopy(original)
        for k,v in best.items():selected['state_dict']['fc.'+k]=v.clone()
        selected.update(run_id=p['run_id'],selected_epoch=best_epoch,training='Development-only equal-source frozen-backbone head;wholeTESTclosed');cp=ROOT/'models/checkpoints/acpds_balanced'/p['run_id']/'candidate.pt';atomic_torch(selected,cp);roundtrip=torch.load(cp,map_location='cpu',weights_only=True);assert all(torch.equal(v,roundtrip['state_dict'][k]) for k,v in original['state_dict'].items() if not k.startswith('fc.'));assert all(torch.equal(v,roundtrip['state_dict']['fc.'+k]) for k,v in best.items())
        for f,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        dump(out/'candidate_predictions.json',dict(acpds=candidate_new,pklot=candidate_old));r=dict(run_id=p['run_id'],started_at=p['prepared_at'],finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.perf_counter()-clock,seed=p['seed'],protocol_sha256=digest(path),selected_epoch=best_epoch,epochs_completed=len(curves),early_stopped=stale>=p['patience'],selection_loss=best_loss,baseline_probability_max_delta=delta,baseline_acpds=bnew,candidate_acpds=cnew,baseline_pklot=bold,candidate_pklot=cold,per_image=by_image,per_camera=c_camera,per_date_identity_retention=retention,checks=checks,development_gate_passed=all(checks.values()),candidate_checkpoint=cp.relative_to(ROOT).as_posix(),candidate_checkpoint_sha256=digest(cp),feature_cache_files=feature_files,train_samples=17946,new_training_samples=7842,new_validation_samples=1904,old_validation_samples=2028,backbone_unchanged=True,model_state_roundtrip_exact=True,production_promoted=False,final_pixels_or_semantics_opened=False,scope=p['scope'])
        dump(out/'run.json',r);dump(ROOT/'models/acpds_balanced_head.json',r);dump(ROOT/'reports/acpds_balanced_head_latest.json',r);registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='DEVELOPMENT source-balanced occupancy head adaptation',started_at=r['started_at'],finished_at=r['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='ACPDS7842TRAIN/1904VALID;PKLot10104TRAIN/2028reusedDEV;wholeTESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture='Frozen original ResNet18 plus warm linear head',optimizer='AdamW',learning_rate=.001,epochs=len(curves),batch_size=128,random_seed=154,hardware='CPU4threads',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(dict(baseline_acpds=bnew,candidate_acpds=cnew,baseline_pklot=bold,candidate_pklot=cold,checks=checks,selected_epoch=best_epoch)),logs=out.relative_to(ROOT).as_posix(),checkpoints=r['candidate_checkpoint'],code_revision_basis='b89f874 plus sealed adaptation protocol',implementation_sha256=digest(__file__),conclusions='Development gate='+str(r['development_gate_passed'])+';wholeTESTclosed;no app promotion')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(ROOT/'data/automation_state.json');s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['acpds_balanced_head']=r;dump(ROOT/'data/automation_state.json',s);print(json.dumps(dict(run_id=p['run_id'],selected_epoch=best_epoch,acpds_accuracy=cnew['hard']['accuracy_on_covered'],acpds_confident_false_vacant=cnew['selective']['false_vacant'],checks=checks),indent=2))
    except BaseException as e:dump(out/'interrupted.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),error=type(e).__name__,detail=str(e),feature_files_completed=len(feature_files),epoch_done=epoch_done,completed_run_counted=False,resume_command='scripts/train_acpds_balanced_head.py --run '+path.relative_to(ROOT).as_posix()));raise
    finally:
        s=read(ROOT/'data/automation_state.json');s['active_training_jobs']=[];dump(ROOT/'data/automation_state.json',s);lock.unlink(missing_ok=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
