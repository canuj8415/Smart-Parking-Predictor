"""Bounded resumable DEVELOPMENT-ONLY head study;no final reader or promotion."""
import argparse,copy,csv,json,sys,time,os
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.source_crops import balanced_source_weights
from train_occupancy_expansion import summary
def read(p):return json.loads((ROOT/p).read_text())
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume');parser.add_argument('--seconds',type=int,default=900);args=parser.parse_args()
    assert 0<args.seconds<=900
    state=read('data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    start=datetime.now(timezone.utc);rid=args.resume or 'SOURCE-BALANCED-HEAD-'+start.strftime('%Y%m%dT%H%M%S%fZ')
    if Path(rid).name!=rid:raise ValueError('Unsafe run identity')
    folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=bool(args.resume))
    assert not (folder/'run.json').exists(),'Completed studies are immutable'
    prep=read('models/source_occupancy_crop_preparation.json');old=read('models/occupancy_expansion_candidate.json')
    paths=['scripts/train_source_balanced_head.py','scripts/train_occupancy_expansion.py','src/smart_parking/source_crops.py','src/smart_parking/vision.py']
    hashes={p:digest(ROOT/p) for p in paths};protected=read('models/open_space_asset_qualification.json')['protected_hashes']
    warm=ROOT/old['candidate_checkpoint'];original=ROOT/'models/checkpoints/occupancy_resnet18.pt'
    assert digest(warm)==old['candidate_checkpoint_sha256'] and prep['crop_gate_passed']
    manifest=ROOT/prep['manifest'];assert digest(manifest)==prep['manifest_sha256']
    data=read(manifest)
    if not args.resume:
        protocol=dict(run_id=rid,started_at=start.isoformat(),seed=128,source_ids=['SRC-DS-001','SRC-DS-018','SRC-MOD-003'],source_hashes=hashes,protected_hashes=protected,
            hypothesis='Adding qualified new-source occupancy crops with25percent training weight to a frozen-ResNet head improves PKLot development errors while retaining confident correct vacancies.',
            study_scope='DEVELOPMENT ONLY:existing2028PKLot validation labels;no publisher018valid/test,no consumed final reads,no final callback,no production promotion',
            crop_preparation_run=prep['run_id'],crop_manifest=prep['manifest'],crop_manifest_sha256=prep['manifest_sha256'],
            pklot_feature_card_sha256=digest(ROOT/'models/occupancy_expansion_candidate.json'),pklot_manifest_sha256=old['manifest_sha256'],
            warm_checkpoint=old['candidate_checkpoint'],warm_checkpoint_sha256=digest(warm),original_checkpoint_sha256=digest(original),
            source_training_weights={'SRC-DS-001':.75,'SRC-DS-018':.25},max_epochs=6,patience=2,min_delta=.0001,learning_rate=.001,weight_decay=.001,batch_size=128,
            epoch_selection='Minimum macro-camera development cross-entropy;epoch0warm head retained if no improvement',
            gates=['Strictly fewer development hard errors than warm head','No increase in confidently false vacant predictions',
                'Per-camera hard accuracy drop<=0.01','Each development date retains>=95percent baseline correct confident vacancies','Uncertainty fraction increase<=0.02'],
            limitations=['Reused PKLot development is not final evidence','New source is training only;no source018/night/unseen-lot accuracy assessed',
                'Pretrained backbone frozen;class/sample-source weighting is not new ground truth','Even a passing development gate cannot replace original app model'])
        dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text()) for p,h in hashes.items()})
    else:protocol=read(folder/'protocol.json');assert protocol['source_hashes']==hashes
    assert digest(manifest)==protocol['crop_manifest_sha256'] and digest(warm)==protocol['warm_checkpoint_sha256'] and digest(original)==protocol['original_checkpoint_sha256']
    assert digest(ROOT/'models/occupancy_expansion_candidate.json')==protocol['pklot_feature_card_sha256']
    lock=ROOT/'outputs/training_locks/source_balanced_head.lock';lock.parent.mkdir(parents=True,exist_ok=True)
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(descriptor,str(os.getpid()).encode());os.close(descriptor)
    state['active_training_jobs']=[dict(run_id=rid,pid=os.getpid(),resume_command='scripts/train_source_balanced_head.py --resume '+rid)];dump('data/automation_state.json',state)
    clock=time.monotonic();features=[];rows=[];chunks=[]
    def boundary():
        if (folder/'CANCEL').exists() or time.monotonic()-clock>=args.seconds:raise InterruptedError('Cancellable invocation budget reached;resume retained features/head')
    try:
        import numpy as np
        import torch
        from PIL import Image
        from torchvision.models import resnet18
        from smart_parking.vision import normalize_crop
        torch.manual_seed(128);torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
        base=torch.load(original,map_location='cpu',weights_only=True);warm_bundle=torch.load(warm,map_location='cpu',weights_only=True)
        assert all(torch.equal(v,warm_bundle['state_dict'][k]) for k,v in base['state_dict'].items() if not k.startswith('fc.'))
        backbone=resnet18(weights=None);backbone.fc=torch.nn.Linear(512,2);backbone.load_state_dict(base['state_dict']);backbone.eval();backbone.fc=torch.nn.Identity()
        for p in backbone.parameters():p.requires_grad_(False)
        for item in old['feature_cache_files']:
            boundary();path=ROOT/item['path'];assert digest(path)==item['sha256']
            chunk=torch.load(path,map_location='cpu',weights_only=True)
            assert chunk['manifest_sha256']==old['manifest_sha256'] and chunk['original_checkpoint_sha256']==protocol['original_checkpoint_sha256']
            features.append(chunk['features']);rows.extend(dict(r,source_id='SRC-DS-001') for r in chunk['rows'])
        for n,item in enumerate(data['chunks'],1):
            boundary();assert digest(ROOT/item['path'])==item['sha256']
            path=folder/'feature_chunks'/f'frame_{n:03d}.pt'
            source_rows=[r for r in data['records'] if r['crop_file']==item['path']]
            if path.exists():
                chunk=torch.load(path,map_location='cpu',weights_only=True)
                assert chunk['crop_sha256']==item['sha256'] and chunk['source_hashes']==hashes
            else:
                with np.load(ROOT/item['path'],allow_pickle=False) as cache:arrays=cache['crops']
                assert len(arrays)==len(source_rows)==item['rows']
                for a,r in zip(arrays,source_rows):
                    import hashlib
                    assert hashlib.sha256(a.tobytes()).hexdigest()==r['crop_rgb_sha256'] and r['label']==1-r['source_class_id']
                with torch.inference_mode():values=backbone(torch.stack([normalize_crop(Image.fromarray(a)) for a in arrays])).clone() if len(arrays) else torch.empty(0,512)
                chunk=dict(features=values,crop_sha256=item['sha256'],source_hashes=hashes);path.parent.mkdir(parents=True,exist_ok=True);torch.save(chunk,path)
            features.append(chunk['features']);rows.extend(source_rows);chunks.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path)))
            if n%20==0 or n==len(data['chunks']):
                dump(folder/'progress.json',dict(phase='new_source_frozen_features',frames=n,total=len(data['chunks']),elapsed_seconds=time.monotonic()-clock));print('Frozen source features',n,'/',len(data['chunks']),flush=True)
        x=torch.cat(features);del features
        assert torch.isfinite(x).all() and len(x)==len(rows)
        train=torch.tensor([i for i,r in enumerate(rows) if r['role']=='train']);val=torch.tensor([i for i,r in enumerate(rows) if r['role']=='validation'])
        assert len(val)==2028 and all(rows[int(i)]['source_id']=='SRC-DS-001' for i in val)
        assert sum(r['source_id']=='SRC-DS-001' and r['role']=='train' for r in rows)==10104
        y=torch.tensor([r['label'] for r in rows],dtype=torch.long)
        train_rows=[rows[int(i)] for i in train];weights=torch.tensor(balanced_source_weights(train_rows,protocol['source_training_weights']),dtype=torch.float32)
        camera_indices={c:torch.tensor([int(i) for i in val if rows[int(i)]['camera_id']==c]) for c in sorted({rows[int(i)]['camera_id'] for i in val})}
        head=torch.nn.Linear(512,2);head.load_state_dict({k[3:]:v for k,v in warm_bundle['state_dict'].items() if k.startswith('fc.')});head.eval()
        def predict():
            with torch.inference_mode():p=torch.softmax(head(x[val]),dim=1)[:,1].tolist()
            return [dict(rows[int(i)],probability_occupied=float(v)) for i,v in zip(val,p)]
        def validation_loss():
            with torch.inference_mode():return float(torch.stack([torch.nn.functional.cross_entropy(head(x[i]),y[i]) for i in camera_indices.values()]).mean())
        baseline_rows=predict();baseline=summary(baseline_rows)
        assert baseline['overall']['hard_errors']==12 and baseline['overall']['false_vacant']==4
        dump(folder/'baseline_development_predictions.json',baseline_rows)
        optimizer=torch.optim.AdamW(head.parameters(),lr=.001,weight_decay=.001)
        best_loss=validation_loss();best_head=copy.deepcopy(head.state_dict());best_epoch=0;stale=0;curves=[];start_epoch=0
        last=folder/'last_head.pt'
        if last.exists():
            saved=torch.load(last,map_location='cpu',weights_only=True);assert saved['source_hashes']==hashes
            head.load_state_dict(saved['head']);optimizer.load_state_dict(saved['optimizer']);best_loss=saved['best_loss'];best_head=saved['best_head'];best_epoch=saved['best_epoch'];stale=saved['stale'];curves=saved['curves'];start_epoch=saved['epoch'];torch.set_rng_state(saved['rng'])
        for epoch in range(start_epoch,6):
            boundary();head.train();order=torch.randperm(len(train));loss_sum=0.
            for positions in order.split(128):
                boundary();batch=train[positions];optimizer.zero_grad();loss=(torch.nn.functional.cross_entropy(head(x[batch]),y[batch],reduction='none')*weights[positions]).mean();loss.backward();optimizer.step();loss_sum+=float(loss.detach())*len(batch)
            head.eval();value=validation_loss();curves.append(dict(epoch=epoch+1,weighted_train_cross_entropy=loss_sum/len(train),macro_camera_development_cross_entropy=value))
            if value<best_loss-.0001:best_loss=value;best_head=copy.deepcopy(head.state_dict());best_epoch=epoch+1;stale=0;torch.save(best_head,folder/'best_head.pt')
            else:stale+=1
            torch.save(dict(epoch=epoch+1,head=head.state_dict(),optimizer=optimizer.state_dict(),best_head=best_head,best_loss=best_loss,best_epoch=best_epoch,stale=stale,curves=curves,rng=torch.get_rng_state(),source_hashes=hashes),last)
            dump(folder/'curves.json',curves);print('Epoch',epoch+1,'development loss',value,'selected',best_epoch,flush=True)
            if stale>=2:break
        head.load_state_dict(best_head);head.eval();candidate_rows=predict();candidate=summary(candidate_rows)
        b=baseline['overall'];c=candidate['overall'];base_camera={r['camera_id']:r for r in baseline['per_camera']}
        checks=dict(strict_error_improvement=c['hard_errors']<b['hard_errors'],no_false_vacant_regression=c['false_vacant']<=b['false_vacant'],
            no_camera_material_regression=all(r['hard_accuracy']>=base_camera[r['camera_id']]['hard_accuracy']-.01 for r in candidate['per_camera']),
            per_date_vacancy_retention=True,uncertainty_noninferior=c['uncertain_fraction']<=b['uncertain_fraction']+.02)
        baseline_dates={(r['camera_id'],r['date']):r for r in baseline['per_date']}
        for r in candidate['per_date']:
            prior=baseline_dates[(r['camera_id'],r['date'])]['correct_vacant_predictions']
            if prior and r['correct_vacant_predictions']<.95*prior:checks['per_date_vacancy_retention']=False
        selected=copy.deepcopy(warm_bundle)
        for k,v in head.state_dict().items():selected['state_dict']['fc.'+k]=v.clone()
        selected.update(run_id=rid,training='Development-only source-balanced frozen-ResNet head;no final evidence',selected_epoch=best_epoch)
        checkpoint=ROOT/'models/checkpoints/source_balanced'/rid/'candidate.pt';checkpoint.parent.mkdir(parents=True,exist_ok=True);torch.save(selected,checkpoint)
        reloaded=torch.load(checkpoint,map_location='cpu',weights_only=True)
        assert all(torch.equal(v,reloaded['state_dict']['fc.'+k]) for k,v in head.state_dict().items())
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**protected}.items()) and digest(warm)==protocol['warm_checkpoint_sha256']
        dump(folder/'candidate_development_predictions.json',candidate_rows)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.monotonic()-clock,epochs_completed=len(curves),selected_epoch=best_epoch,
            training_crops=len(train),new_source_training_crops=len(data['records']),validation_crops=2028,baseline=baseline,candidate=candidate,checks=checks,
            development_gate_passed=all(checks.values()),candidate_checkpoint=checkpoint.relative_to(ROOT).as_posix(),candidate_checkpoint_sha256=digest(checkpoint),
            feature_cache_files=chunks,model_state_roundtrip_exact=True,production_promoted=False,final_images_or_labels_read=0,new_source_validation_or_test_read=0)
        dump(folder/'run.json',report);dump('models/source_balanced_development_head.json',report)
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='DEVELOPMENT-ONLY genuine source-balanced ResNet18 head training',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids='SRC-DS-001;SRC-DS-018;SRC-MOD-003',
            split_ids='Existing2028PKLot DEVELOPMENT only;newsourceTRAIN only',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Frozen ResNet18 plus AdamW linear head',random_seed=128,hardware='CPU4threads',
            execution_environment=sys.version.split()[0],training_duration=report['duration_seconds_this_invocation'],epochs=len(curves),batch_size=128,optimizer='AdamW',learning_rate=.001,
            evaluation_metrics=json.dumps(dict(baseline=b,candidate=c,checks=checks)),logs=folder.relative_to(ROOT).as_posix(),checkpoints=report['candidate_checkpoint'],
            code_revision_basis='8ae82a3 plus sealed source snapshots',implementation_sha256=hashes[paths[0]],conclusions='Development gate='+str(report['development_gate_passed'])+';no final replay or app promotion;epoch0warm baseline may be retained')
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read('data/automation_state.json');state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,selected_epoch=best_epoch,baseline=b,candidate=c,checks=checks),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False,resume_command='scripts/train_source_balanced_head.py --resume '+rid,features_and_head_preserved=True));state=read('data/automation_state.json');raise
    finally:
        state['active_training_jobs']=[];dump('data/automation_state.json',state);lock.unlink(missing_ok=True)
if __name__=='__main__':main()
