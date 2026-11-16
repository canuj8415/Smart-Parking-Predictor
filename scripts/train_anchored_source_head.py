"""One bounded teacher-anchored DEVELOPMENT-ONLY cached-feature head trial."""
import argparse,copy,csv,json,os,sys,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.source_crops import balanced_source_weights
from smart_parking.teacher_anchor import teacher_anchor_loss
from train_occupancy_expansion import summary
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume');args=parser.parse_args()
    state=read('data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    start=datetime.now(timezone.utc);rid=args.resume or 'ANCHORED-HEAD-'+start.strftime('%Y%m%dT%H%M%S%fZ');assert Path(rid).name==rid
    folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=bool(args.resume));assert not (folder/'run.json').exists()
    previous=read('models/source_balanced_development_head.json');old=read('models/occupancy_expansion_candidate.json');prep=read('models/source_occupancy_crop_preparation.json');diagnosis=read('models/source_transfer_diagnostics.json')
    assert diagnosis['findings']['new_source_in_sample_fit_improved'] and diagnosis['findings']['reused_development_errors_worsened']
    assert digest(ROOT/prep['manifest'])==prep['manifest_sha256'];data=read(prep['manifest']);warm=ROOT/previous['warm_checkpoint'];assert digest(warm)==previous['warm_checkpoint_sha256']
    paths=['scripts/train_anchored_source_head.py','src/smart_parking/teacher_anchor.py','src/smart_parking/source_crops.py','scripts/train_occupancy_expansion.py'];hashes={p:digest(ROOT/p) for p in paths};protected=previous['protected_hashes']
    if not args.resume:
        protocol=dict(run_id=rid,started_at=start.isoformat(),seed=128,source_ids=previous['source_ids'],source_hashes=hashes,protected_hashes=protected,
            hypothesis='A KL penalty toward warm-head predictions on original TRAIN samples reduces old-task drift while fitting new-source training crops.',
            scope='DEVELOPMENT ONLY;no final/new-source validation/night/live evaluation or app promotion',diagnosis_run=diagnosis['run_id'],
            parent_study=previous['run_id'],parent_study_card_sha256=digest(ROOT/'models/source_balanced_development_head.json'),
            crop_manifest_sha256=prep['manifest_sha256'],warm_checkpoint_sha256=digest(warm),source_masses={'SRC-DS-001':.75,'SRC-DS-018':.25},
            teacher_temperature=2.,anchor_strength=1.,teacher_cohort='Original PKLot TRAIN only;no validation soft targets',
            optimizer='AdamW',learning_rate=.001,weight_decay=.001,batch_size=128,max_epochs=6,patience=2,maximum_invocation_seconds=180,
            epoch_selection='Minimum macro-camera reused-development CE,including warm epoch0;no gate-based epoch cherry-picking',
            gates={'strict_hard_error_improvement':True,'false_vacant_increase_max':0,'per_camera_accuracy_drop_max':.01,'per_date_correct_vacancy_retention_min':.95,'uncertainty_fraction_increase_max':.02},
            limits=['Reused development after earlier studies is not final evidence','Different runtime RNG consumption may differ from prior study;not isolated causal proof of anchoring','New source is training only,no independent source generalization assessed'])
        dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    else:protocol=read(folder/'protocol.json');assert protocol['source_hashes']==hashes
    assert digest(ROOT/'models/source_balanced_development_head.json')==protocol['parent_study_card_sha256']
    lock=ROOT/'outputs/training_locks/source_balanced_head.lock';lock.parent.mkdir(parents=True,exist_ok=True);fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    state['active_training_jobs']=[dict(run_id=rid,pid=os.getpid())];dump('data/automation_state.json',state);timer=time.monotonic()
    def boundary():
        if (folder/'CANCEL').exists() or time.monotonic()-timer>180:raise InterruptedError('Bounded checkpointed training stopped;resume is available')
    try:
        import torch
        torch.set_num_threads(4);torch.manual_seed(128);torch.use_deterministic_algorithms(True)
        features=[];rows=[]
        for item in old['feature_cache_files']:
            boundary();assert digest(ROOT/item['path'])==item['sha256'];chunk=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True)
            assert chunk['manifest_sha256']==old['manifest_sha256'];features.append(chunk['features']);rows.extend(dict(r,source_id='SRC-DS-001') for r in chunk['rows'])
        by_file=defaultdict(list)
        for row in data['records']:by_file[row['crop_file']].append(row)
        for item,crop in zip(previous['feature_cache_files'],data['chunks']):
            boundary();assert digest(ROOT/item['path'])==item['sha256'];chunk=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True);assert chunk['crop_sha256']==crop['sha256'];features.append(chunk['features']);rows.extend(by_file[crop['path']])
        x=torch.cat(features);assert x.shape==(28580,512) and torch.isfinite(x).all();y=torch.tensor([r['label'] for r in rows])
        train=torch.tensor([i for i,r in enumerate(rows) if r['role']=='train']);val=torch.tensor([i for i,r in enumerate(rows) if r['role']=='validation']);assert len(train)==26552 and len(val)==2028
        assert all(rows[int(i)]['source_id']=='SRC-DS-001' for i in val)
        old_train=torch.tensor([rows[int(i)]['source_id']=='SRC-DS-001' for i in train]);assert int(old_train.sum())==10104
        weights=torch.tensor(balanced_source_weights([rows[int(i)] for i in train]),dtype=torch.float32)
        bundle=torch.load(warm,map_location='cpu',weights_only=True);head=torch.nn.Linear(512,2);head.load_state_dict({k[3:]:v for k,v in bundle['state_dict'].items() if k.startswith('fc.')});head.eval()
        with torch.inference_mode():teacher_logits=head(x[train]).detach().clone()
        cameras={c:torch.tensor([int(i) for i in val if rows[int(i)]['camera_id']==c]) for c in sorted({rows[int(i)]['camera_id'] for i in val})}
        def loss_value():
            with torch.inference_mode():return float(torch.stack([torch.nn.functional.cross_entropy(head(x[i]),y[i]) for i in cameras.values()]).mean())
        def predict():
            with torch.inference_mode():prob=torch.softmax(head(x[val]),dim=1)[:,1].tolist()
            return [dict(rows[int(i)],probability_occupied=p) for i,p in zip(val,prob)]
        baseline_rows=predict();baseline=summary(baseline_rows);assert baseline['overall']['hard_errors']==12 and baseline['overall']['false_vacant']==4
        best_loss=loss_value();best_epoch=0;best_head=copy.deepcopy(head.state_dict());stale=0;curves=[];first_epoch=0
        optimizer=torch.optim.AdamW(head.parameters(),lr=.001,weight_decay=.001);last=folder/'last_head.pt'
        if last.exists():
            saved=torch.load(last,map_location='cpu',weights_only=True);assert saved['source_hashes']==hashes;head.load_state_dict(saved['head']);optimizer.load_state_dict(saved['optimizer']);best_loss=saved['best_loss'];best_head=saved['best_head'];best_epoch=saved['best_epoch'];stale=saved['stale'];curves=saved['curves'];first_epoch=saved['epoch'];torch.set_rng_state(saved['rng'])
        for epoch in range(first_epoch,6):
            boundary();head.train();order=torch.randperm(len(train));total=0.;total_anchor=0.
            for positions in order.split(128):
                boundary();batch=train[positions];optimizer.zero_grad();logits=head(x[batch]);ce=(torch.nn.functional.cross_entropy(logits,y[batch],reduction='none')*weights[positions]).mean();mask=old_train[positions]
                anchor=teacher_anchor_loss(logits[mask],teacher_logits[positions][mask],2.) if mask.any() else logits.sum()*0
                loss=ce+anchor;loss.backward();optimizer.step();total+=float(ce.detach())*len(batch);total_anchor+=float(anchor.detach())*len(batch)
            head.eval();v=loss_value();curves.append(dict(epoch=epoch+1,weighted_train_ce=total/len(train),old_train_teacher_kl=total_anchor/len(train),macro_camera_development_ce=v))
            if v<best_loss-.0001:best_loss=v;best_epoch=epoch+1;best_head=copy.deepcopy(head.state_dict());stale=0;torch.save(best_head,folder/'best_head.pt')
            else:stale+=1
            torch.save(dict(epoch=epoch+1,head=head.state_dict(),optimizer=optimizer.state_dict(),best_loss=best_loss,best_head=best_head,best_epoch=best_epoch,stale=stale,curves=curves,rng=torch.get_rng_state(),source_hashes=hashes),last)
            dump(folder/'curves.json',curves);print('Anchored epoch',epoch+1,'development CE',v,'selected',best_epoch,flush=True)
            if stale>=2:break
        last_rows=predict();last_metrics=summary(last_rows);head.load_state_dict(best_head);head.eval();candidate_rows=predict();candidate=summary(candidate_rows);b=baseline['overall'];c=candidate['overall']
        by_camera={r['camera_id']:r for r in baseline['per_camera']};by_date={(r['camera_id'],r['date']):r for r in baseline['per_date']}
        checks=dict(strict_error_improvement=c['hard_errors']<b['hard_errors'],no_false_vacant_regression=c['false_vacant']<=b['false_vacant'],
            no_camera_material_regression=all(r['hard_accuracy']>=by_camera[r['camera_id']]['hard_accuracy']-.01 for r in candidate['per_camera']),
            per_date_vacancy_retention=all(not by_date[(r['camera_id'],r['date'])]['correct_vacant_predictions'] or r['correct_vacant_predictions']>=.95*by_date[(r['camera_id'],r['date'])]['correct_vacant_predictions'] for r in candidate['per_date']),
            uncertainty_noninferior=c['uncertain_fraction']<=b['uncertain_fraction']+.02)
        selected=copy.deepcopy(bundle)
        for k,v in best_head.items():selected['state_dict']['fc.'+k]=v.clone()
        selected.update(run_id=rid,selected_epoch=best_epoch,training='Teacher-anchored DEVELOPMENT-ONLY source-balanced head')
        checkpoint=ROOT/'models/checkpoints/anchored_source'/rid/'candidate.pt';checkpoint.parent.mkdir(parents=True,exist_ok=True);torch.save(selected,checkpoint)
        serialized=torch.load(checkpoint,map_location='cpu',weights_only=True);assert all(torch.equal(v,serialized['state_dict']['fc.'+k]) for k,v in best_head.items())
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**protected}.items()) and digest(warm)==protocol['warm_checkpoint_sha256']
        dump(folder/'baseline_development_predictions.json',baseline_rows);dump(folder/'last_epoch_development_predictions.json',last_rows);dump(folder/'selected_development_predictions.json',candidate_rows)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.monotonic()-timer,epochs_completed=len(curves),selected_epoch=best_epoch,
            training_crops=26552,validation_crops=2028,baseline=baseline,last_epoch=last_metrics,candidate=candidate,checks=checks,development_gate_passed=all(checks.values()),
            candidate_checkpoint=checkpoint.relative_to(ROOT).as_posix(),candidate_checkpoint_sha256=digest(checkpoint),model_state_roundtrip_exact=True,production_promoted=False,
            final_images_or_labels_read=0,new_source_validation_or_test_read=0,feature_cache_reused_from=previous['run_id'])
        dump(folder/'run.json',report);dump('models/anchored_source_development_head.json',report)
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Genuine teacher-anchored DEVELOPMENT-ONLY head training',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids=';'.join(protocol['source_ids']),split_ids='PKLot reused DEVELOPMENT only;source018TRAIN only',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Frozen ResNet18,linear head,source CE plus TRAIN-only KL teacher',optimizer='AdamW',learning_rate=.001,epochs=len(curves),batch_size=128,random_seed=128,hardware='CPU4threads',execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(dict(baseline=b,selected=c,last_epoch=last_metrics['overall'],checks=checks)),logs=folder.relative_to(ROOT).as_posix(),checkpoints=report['candidate_checkpoint'],
            code_revision_basis='55ce4bd plus sealed source snapshots',implementation_sha256=hashes[paths[0]],conclusions='Development gate='+str(report['development_gate_passed'])+';no final evidence or app promotion')
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read('data/automation_state.json');state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,selected_epoch=best_epoch,last_epoch=last_metrics['overall'],candidate=c,checks=checks),indent=2))
    except BaseException as error:dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False,resume_command='scripts/train_anchored_source_head.py --resume '+rid));state=read('data/automation_state.json');raise
    finally:state['active_training_jobs']=[];dump('data/automation_state.json',state);lock.unlink(missing_ok=True)
if __name__=='__main__':main()
