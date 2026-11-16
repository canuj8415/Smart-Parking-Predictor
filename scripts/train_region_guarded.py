"""Sealed matched warm-start raw versus guarded plain-SGD DEVELOPMENT study."""
import argparse
import copy
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def dump(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_bytes((json.dumps(value,indent=2)+'\n').encode());os.replace(tmp,path)

def prepare():
    state=read(ROOT/'data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    now=datetime.now(timezone.utc);rid='REGION-GUARDED-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    cards=['models/region_dataset_v2.json','models/acpds_region_dataset.json'];records=[];inputs=cards.copy()
    for source,cardfile in zip(['pklot','acpds'],cards):
        card=read(ROOT/cardfile);assert card['data_gate_passed'] and digest(ROOT/card['manifest'])==card['manifest_sha256']
        inputs.append(card['manifest'])
        for row in read(ROOT/card['manifest'])['records']:
            assert row['role'] in ['train','development'];records.append(dict(row,study_source=source,study_index=len(records)))
    inputs+=['models/pklot_current_role_ledger.json','data/manifests/acpds_source_roles_v1.json',
        'models/region_fpn_duration.json','models/acpds_region_baselines.json','models/pretrained/resnet18_imagenet.pth','data/source_manifest.csv']
    code=['scripts/train_region_guarded.py','src/smart_parking/region_mixed.py','tests/test_region_mixed.py',
        'src/smart_parking/region_validity.py','tests/test_region_validity.py','src/smart_parking/region_fpn.py']
    protected=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T104816Z/protected_before.json')['hashes']
    protected.update(read(ROOT/'data/manifests/singapore_trend_scoring_v1.json')['implementation_hashes'])
    for file in ['models/region_fpn_duration.json','models/region_fpn_detail.json','models/region_fpn_bounded.json']:
        card=read(ROOT/file);protected[card['candidate_checkpoint']]=card['candidate_sha256']
    parent=read(ROOT/'models/region_mixed.json');old_protocol='experiments/results/'+parent['run_id']+'/protocol.json';prior=read(ROOT/old_protocol)
    assert digest(ROOT/old_protocol)==parent['protocol_sha256'] and records==prior['records']
    warm=parent['checkpoints']['control'];assert digest(ROOT/warm['path'])==warm['sha256']
    feature_cache='experiments/results/'+parent['run_id']+'/frozen_features.pt';feature_marker='experiments/results/'+parent['run_id']+'/features_complete.json'
    fm=read(ROOT/feature_marker);assert fm['images']==496 and digest(ROOT/feature_cache)==fm['sha256']
    inputs+=['models/region_mixed.json',old_protocol,warm['path'],feature_cache,feature_marker,'models/region_source_gradients.json','scripts/train_region_mixed.py']
    code+=['src/smart_parking/region_guarded_training.py','tests/test_region_guarded_training.py','src/smart_parking/region_gradient_guard.py','tests/test_region_gradient_guard.py','src/smart_parking/region_gradients.py']
    restart_path='experiments/evidence/HEARTBEAT-20261027T121817Z/restart_validation.json';restart=read(ROOT/restart_path)
    assert restart['passed'] and digest(ROOT/restart['log'])==restart['log_sha256']
    for name,expected in restart['source_hashes'].items():assert digest(ROOT/name)==expected,name
    inputs.extend([restart_path,restart['log']])
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=180,sampler_seed=180,acpds_sampler_seed=181,
        hypothesis='From a common PKLot warm start,projecting/norm-capping ACPDS gradients improves PKLot DEVmacroIoU at least.02 over matched raw-SGD balance while ACPDS loses at most.02;fixed-teacher relative and all source/template/previous-coarse gates also required.',
        source_ids=['SRC-DS-001','SRC-DS-021','SRC-MOD-003'],records=records,
        source_hashes={f:digest(ROOT/f) for f in code},input_hashes={f:digest(ROOT/f) for f in inputs},protected_hashes=protected,
        cache_hashes={r['cache']:r['cache_sha256'] for r in records},
        architecture='Frozen ImageNet ResNet18 scales1-4 plus32channel additive FPN decoder;no RGB detail branch',
        normalization=dict(mean=[.485,.456,.406],std=[.229,.224,.225]),pretrained='models/pretrained/resnet18_imagenet.pth',
        optimizer='SGD',learning_rate=.01,weight_decay=0.,momentum=0.,batch_size=8,maximum_rounds=32,steps_per_round=25,
        maximum_updates_per_arm=800,patience_rounds=6,selection_minimum_improvement=.001,
        selection='Both arms maximize equal-source(.5PKLotmacro-cameraIoU+.5ACPDSmean-imageIoU),earliest on ties;paired shared early stop only if BOTH arms stale6rounds,so actual updates stay equal',
        sampling='BOTH arms use the identical mixed schedule from paired_schedule seeds180/181:4PKLot+4ACPDS,25updates per validation round,32rounds maximum;no DEV sampling.',
        controlled_change='Only auxiliary gradient transform(raw versus opposition projection plus norm cap);same warm checkpoint,batches,class weight,plainSGD,stepbudget,selection,threshold andloss. Common warmstart/SGD differ from previousAdamW study;not a one-factor comparison against that old run.',
        loss='masked_bay_loss:valid-pixel-normalized per-image weighted BCE+softDice eps1;class weight from PKLotTRAIN valid pixels ONLY,fixed for BOTH arms',
        threshold=.5,augmentation='None;frozen feature cache',threads=4,maximum_seconds=900,maximum_RSS_bytes=1700000000,
        relative_gates=dict(pklot_macro_gain=.02,acpds_mean_regression=.02,pklot_camera_regression=.05,pklot_image_regression=.05),
        teacher_retention_gates=dict(acpds_gain=.05,pklot_macro_regression=.02,pklot_camera_regression=.05,pklot_image_regression=.05),
        absolute_gates=dict(pklot_macro=.8,pklot_camera=.75,pklot_image=.65,acpds_mean=.8,acpds_image=.65,
            gain_over_original=.02,original_camera_regression=.05,template_camera_regression=.05,
            previous_coarse_macro_regression=.02,previous_coarse_camera_regression=.05,previous_coarse_image_regression=.05),
        source_scope='PKLot200TRAIN/30DEV across familiar cameras;ACPDS231TRAIN/35previously exposed DEV. Supplied bay unions,not exhaustive facility/occupancy truth. Near duplicates/lot/date/pretraining independence unknown.',
        final_access=False,production_promotion=False,template='PKLotTRAIN camera-conditioned comparator only;ACPDS matching geometry is inapplicable',
        run_definition='One completed recorded two-arm matched experiment,not two runs,updates,frames or validation rounds')
    p.update(warm_start=warm['path'],warm_start_sha256=warm['sha256'],fixed_positive_weight=parent['positive_weight'],
        warm_tensor_hash=read(ROOT/'models/region_source_gradients.json')['weight_state_hashes']['control']['before'],
        feature_cache=feature_cache,feature_cache_sha256=fm['sha256'],feature_source_protocol=old_protocol,
        numeric_guard_tolerance=1e-5,synthetic_restart_test='tests/test_region_guarded_training.py:test_mid_pair_interruption_restores_models_optimizer_groups_cursor_and_logs_exactly',
        synthetic_restart_validation=restart_path,synthetic_restart_evidence=restart['log'],synthetic_restart_verified=restart['passed'],
        comparison_scope='New matched SGD arms;priorAdamW andfixedPKLot teacher retained as separate references')
    assert prior['normalization']==p['normalization']
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')))
    dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json',flush=True)

def run(path):
    import numpy as np
    import psutil
    import torch
    from smart_parking.region_fpn import FrozenRegionEncoder,RegionPyramidDecoder,mask_metrics
    from smart_parking.region_validity import masked_bay_loss,valid_mask_metrics
    from smart_parking.region_mixed import paired_schedule,source_balanced_score,retention_checks
    from smart_parking.region_guarded_training import source_step,save_pair_state,load_pair_state
    path=Path(path).resolve();out=path.parent;p=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not(out/'run.json').exists()
    assert digest(path)==read(out/'protocol_binding.json')['sha256']
    assert p['source_hashes'].get(Path(__file__).resolve().relative_to(ROOT).as_posix())==digest(__file__)
    bound={**p['source_hashes'],**p['input_hashes'],**p['protected_hashes'],**p['cache_hashes']}
    for file,expected in bound.items():assert digest(ROOT/file)==expected,file
    sp=ROOT/'data/automation_state.json';state=read(sp);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    checkpoint_dir=ROOT/'models/checkpoints/region_guarded'/p['run_id'];checkpoint_dir.mkdir(parents=True,exist_ok=True)
    state['active_training_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),phase='Paired warm-start raw/guarded SGD',maximum_seconds=p['maximum_seconds'],
        cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/train_region_guarded.py --run '+path.relative_to(ROOT).as_posix())];dump(sp,state)
    records=p['records'];allowed={(ROOT/r['cache']).resolve() for r in records};forbidden=[]
    def audit(event,args):
        if event.startswith('socket.'):forbidden.append(event);raise PermissionError('Offline paired trainer')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            q=Path(os.fsdecode(args[0])).resolve()
            if q.is_relative_to(ROOT/'data/raw') or (q.suffix.casefold() in {'.jpg','.jpeg','.png','.xml','.npz','.npy'} and q not in allowed and not q.is_relative_to(out)):
                forbidden.append(str(q));raise PermissionError('Raw/final/unadmitted source access blocked')
    sys.addaudithook(audit);started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter();process=psutil.Process();peak=0
    def boundary():
        nonlocal peak
        peak=max(peak,process.memory_info().rss)
        if (out/'CANCEL').exists() or time.perf_counter()-clock>p['maximum_seconds'] or peak>p['maximum_RSS_bytes']:
            raise InterruptedError('Cancel/deadline/RSS bound reached;paired checkpoint retained')
    def save(destination,value):
        temporary=destination.with_suffix(destination.suffix+'.partial');torch.save(value,temporary);os.replace(temporary,destination)
    def tensor_hash(model):
        h=hashlib.sha256()
        for name,value in model.state_dict().items():h.update(name.encode());h.update(value.detach().contiguous().numpy().tobytes())
        return h.hexdigest()
    try:
        torch.set_num_threads(p['threads']);torch.use_deterministic_algorithms(True);torch.manual_seed(p['seed'])
        assert len(records)==496 and len(allowed)==496
        roles={r['camera_id']+'|'+r['capture_date']:r['status'] for r in read(ROOT/'models/pklot_current_role_ledger.json')['current_ledger']['groups']}
        rgb=[];masks=[];valid=[]
        for row in records:
            boundary()
            if row['study_source']=='pklot':assert roles[row['group_id']]==('training_exposed' if row['role']=='train' else 'development_exposed')
            else:assert row['source_id']=='SRC-DS-021' and row['publisher_role']==('train' if row['role']=='train' else 'valid')
            with np.load(ROOT/row['cache'],allow_pickle=False) as data:
                a=data['rgb'].copy();b=data['mask'].copy();v=data['valid'].copy() if row['study_source']=='acpds' else np.ones_like(b,dtype=np.bool_)
            assert a.shape==(144,256,3) and a.dtype==np.uint8 and b.shape==(144,256) and b.dtype==np.bool_ and v.dtype==np.bool_
            assert v.shape==b.shape and not np.any(b&~v) and v.sum()==(27648 if row['study_source']=='acpds' else 36864)
            rgb.append(a);masks.append(b);valid.append(v)
        rgb=np.stack(rgb);masks=np.stack(masks);valid=np.stack(valid)
        def indices(source,role):return np.array([i for i,r in enumerate(records) if r['study_source']==source and r['role']==role],dtype=np.int64)
        pk=indices('pklot','train');ac=indices('acpds','train');pd=indices('pklot','development');ad=indices('acpds','development')
        assert [len(v) for v in [pk,ac,pd,ad]]==[200,231,30,35]
        schedule=paired_schedule(pk,ac,p['maximum_rounds'],p['sampler_seed'])[1]
        schedules={'control':schedule,'guarded':schedule.copy()}
        assert np.isin(schedule[:,:,:4],pk).all() and np.isin(schedule[:,:,4:],ac).all()
        schedule_hashes={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in schedules.items()}
        dump(out/'sampling.json',dict(hashes=schedule_hashes,shape=list(schedules['control'].shape),
            covered_train_indices={k:len(np.unique(v)) for k,v in schedules.items()},seed=p['sampler_seed']))
        np.savez_compressed(out/'schedules.npz',**schedules)
        y=torch.from_numpy(masks[:,None].astype('float32'));support=torch.from_numpy(valid[:,None])
        positive=y[pk].sum()/support[pk].sum();weight=((1-positive)/positive).detach()
        assert float(weight)==p['fixed_positive_weight']
        encoder=FrozenRegionEncoder(torch.load(ROOT/p['pretrained'],map_location='cpu',weights_only=True));encoder_before=tensor_hash(encoder)
        first=RegionPyramidDecoder();warm=torch.load(ROOT/p['warm_start'],map_location='cpu',weights_only=True)
        assert warm['normalization']==p['normalization'] and warm['width']==32 and warm['arm']=='control'
        first.load_state_dict(warm['state_dict']);models={'control':first,'guarded':copy.deepcopy(first)}
        initial_hashes={name:tensor_hash(model) for name,model in models.items()};assert set(initial_hashes.values())=={p['warm_tensor_hash']}
        optimizers={name:torch.optim.SGD(model.parameters(),lr=p['learning_rate'],momentum=0.,weight_decay=0.,foreach=False) for name,model in models.items()}
        feature_path=ROOT/p['feature_cache'];assert digest(feature_path)==p['feature_cache_sha256']
        features=torch.load(feature_path,map_location='cpu',weights_only=True);encoder_images=0
        dump(out/'features_reused.json',dict(path=p['feature_cache'],sha256=p['feature_cache_sha256'],images=496,
            source_protocol=p['feature_source_protocol'],normalization=p['normalization'],pretrained_sha256=p['input_hashes'][p['pretrained']],encoder_images=0))
        assert tensor_hash(encoder)==encoder_before and all(x.shape[0]==496 and torch.isfinite(x).all() for x in features)
        training=dict(round=0,cursor=0,loss_sum={k:0. for k in models},curves=[],best={k:dict(score=-1.,path=None,stale=0) for k in models},
            step_statistics={k:dict(steps=0,pklot_positive_directional_derivative=0,max_projection_violation=0.,max_descent_violation=0.,max_auxiliary_norm_ratio=0.) for k in models})
        last=checkpoint_dir/'last.pt'
        if last.exists():training=load_pair_state(last,models,optimizers,digest(path),schedule_hashes)
        def checkpoint():save_pair_state(last,models,optimizers,training,digest(path),schedule_hashes)
        checkpoint()
        dev=np.concatenate([pd,ad]);cameras=[records[i]['camera_id'] for i in pd]
        def evaluate(model):
            model.eval();probability=[]
            with torch.no_grad():
                for batch in np.array_split(dev,(len(dev)+7)//8):
                    boundary();probability.append(model(tuple(f[batch] for f in features)).sigmoid()[:,0].numpy())
            probability=np.concatenate(probability)
            return dict(pklot=mask_metrics(probability[:30]>=.5,masks[pd],cameras),acpds=valid_mask_metrics(probability[30:]>=.5,masks[ad],valid[ad])),probability
        while training['round']<p['maximum_rounds'] and not all(v['stale']>=p['patience_rounds'] for v in training['best'].values()):
            while training['cursor']<p['steps_per_round']:
                boundary()
                for name,model in models.items():
                    model.train();batch=schedules[name][training['round'],training['cursor']]
                    step=source_step(model,optimizers[name],features,y,support,batch[:4],batch[4:],weight,name=='guarded')
                    training['loss_sum'][name]+=step['combined_loss'];stats=training['step_statistics'][name];stats['steps']+=1
                    stats['pklot_positive_directional_derivative']+=int(step['typed_pklot_directional_derivative']>0)
                    stats['max_projection_violation']=max(stats['max_projection_violation'],step['typed_relative_projection_violation'])
                    stats['max_descent_violation']=max(stats['max_descent_violation'],step['typed_relative_descent_violation'])
                    stats['max_auxiliary_norm_ratio']=max(stats['max_auxiliary_norm_ratio'],step['typed_auxiliary_norm_ratio'] or 0.)
                training['cursor']+=1;checkpoint()
            curve=dict(round=training['round']+1,updates_per_arm=(training['round']+1)*25,update_geometry=copy.deepcopy(training['step_statistics']))
            for name,model in models.items():
                metrics,_=evaluate(model);score=source_balanced_score(metrics['pklot'],metrics['acpds']);best=training['best'][name]
                improved=score>best['score']+p['selection_minimum_improvement']
                curve[name]=dict(training_loss=training['loss_sum'][name]/25,selection_score=score,pklot_macro_iou=metrics['pklot']['macro_camera_iou'],
                    acpds_mean_iou=metrics['acpds']['mean_image_iou'],selected=improved)
                if improved:
                    destination=checkpoint_dir/(name+'_round_'+str(curve['round'])+'_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.pt')
                    assert not destination.exists()
                    save(destination,dict(run_id=p['run_id'],protocol_sha256=digest(path),state_dict=model.state_dict(),arm=name,round=curve['round'],
                        updates=curve['updates_per_arm'],width=32,input_size=[256,144],normalization=p['normalization'],threshold=.5,
                        pretrained=p['pretrained'],pretrained_sha256=p['input_hashes'][p['pretrained']],metrics=metrics))
                    best.update(score=score,path=destination.relative_to(ROOT).as_posix(),stale=0)
                else:best['stale']+=1
            training['curves'].append(curve);training['round']+=1;training['cursor']=0;training['loss_sum']={k:0. for k in models}
            checkpoint();dump(out/'curves.json',training['curves']);print(json.dumps(curve),flush=True)
        results={};probabilities={};checkpoints={}
        for name,model in models.items():
            best=read_best=torch.load(ROOT/training['best'][name]['path'],map_location='cpu',weights_only=True);model.load_state_dict(best['state_dict'])
            metrics,probability=evaluate(model);assert abs(source_balanced_score(metrics['pklot'],metrics['acpds'])-training['best'][name]['score'])<1e-12
            results[name]=metrics;probabilities[name]=probability;checkpoints[name]=dict(path=training['best'][name]['path'],sha256=digest(ROOT/training['best'][name]['path']),selected_round=best['round'],selected_updates=best['updates'])
        a=results['guarded'];b=results['control'];g=p['relative_gates']
        relative=dict(pklot_macro_gain=a['pklot']['macro_camera_iou']-b['pklot']['macro_camera_iou']>=g['pklot_macro_gain'],
            acpds_mean_noninferior=a['acpds']['mean_image_iou']>=b['acpds']['mean_image_iou']-g['acpds_mean_regression'],
            every_pklot_camera_retained=all(a['pklot']['by_camera'][k]['mean_iou']>=v['mean_iou']-g['pklot_camera_regression'] for k,v in b['pklot']['by_camera'].items()),
            every_pklot_image_retained=all(x['iou']>=y['iou']-g['pklot_image_regression'] for x,y in zip(a['pklot']['per_image'],b['pklot']['per_image'])))
        teacher=read(ROOT/'models/region_mixed.json')['results']['control']
        teacher_checks=retention_checks(results['guarded'],teacher,p['teacher_retention_gates'])
        reference=read(ROOT/'models/region_fpn_duration.json')
        g=p['absolute_gates'];absolute={}
        for name,m in results.items():
            pk_m=m['pklot'];ac_m=m['acpds'];previous=reference['candidate'];original=reference['original'];template=reference['conditional_train_template']
            absolute[name]=dict(pklot_macro=pk_m['macro_camera_iou']>=g['pklot_macro'],pklot_every_camera=min(v['mean_iou'] for v in pk_m['by_camera'].values())>=g['pklot_camera'],
                pklot_every_image=pk_m['minimum_image_iou']>=g['pklot_image'],acpds_mean=ac_m['mean_image_iou']>=g['acpds_mean'],acpds_every_image=ac_m['minimum_image_iou']>=g['acpds_image'],
                gain_over_original=pk_m['macro_camera_iou']>=original['macro_camera_iou']+g['gain_over_original'],
                no_original_camera_regression=all(pk_m['by_camera'][k]['mean_iou']>=v['mean_iou']-g['original_camera_regression'] for k,v in original['by_camera'].items()),
                no_template_camera_regression=all(pk_m['by_camera'][k]['mean_iou']>=v['mean_iou']-g['template_camera_regression'] for k,v in template['by_camera'].items()),
                previous_coarse_macro_retained=pk_m['macro_camera_iou']>=previous['macro_camera_iou']-g['previous_coarse_macro_regression'],
                previous_coarse_cameras_retained=all(pk_m['by_camera'][k]['mean_iou']>=v['mean_iou']-g['previous_coarse_camera_regression'] for k,v in previous['by_camera'].items()),
                previous_coarse_images_retained=all(a['iou']>=b['iou']-g['previous_coarse_image_regression'] for a,b in zip(pk_m['per_image'],previous['per_image'])))
        np.savez_compressed(out/'development_predictions.npz',RGB=rgb[dev],actual=masks[dev],valid=valid[dev],**{k+'_probability':v for k,v in probabilities.items()})
        dump(out/'development_records.json',[records[i] for i in dev]);dump(out/'comparisons.json',results)
        assert not forbidden;normal_forbidden=list(forbidden)
        try:(ROOT/'data/raw/UNADMITTED_RAW_PROBE.jpg').read_bytes()
        except PermissionError:negative=True
        else:raise AssertionError('Unadmitted raw guard failed')
        for file,expected in bound.items():assert digest(ROOT/file)==expected,file
        assert tensor_hash(encoder)==encoder_before
        finished=datetime.now(timezone.utc).isoformat()
        report=dict(run_id=p['run_id'],started_at=started,finished_at=finished,duration_seconds_this_invocation=time.perf_counter()-clock,
            peak_sampled_process_RSS_bytes=peak,seed=p['seed'],sampler_seed=p['sampler_seed'],protocol_sha256=digest(path),
            models_trained=2,completed_rounds=training['round'],updates_per_arm=training['round']*25,shared_early_stop=training['round']<p['maximum_rounds'],
            checkpoints=checkpoints,results=results,relative_checks=relative,teacher_retention_checks=teacher_checks,absolute_checks=absolute,
            step_statistics=training['step_statistics'],warm_start=p['warm_start'],warm_start_sha256=p['warm_start_sha256'],
            optimizer='SGD',learning_rate=p['learning_rate'],momentum=0.,weight_decay=0.,features_reused=p['feature_cache'],synthetic_mid_pair_restart_test_passed=p['synthetic_restart_verified'],
            development_gate_passed=all(relative.values()) and all(teacher_checks.values()) and all(absolute['guarded'].values()),production_promoted=False,
            initial_decoder_hashes=initial_hashes,positive_weight=float(weight),class_weight_source='PKLot TRAIN only for BOTH arms',
            sampling_hashes=schedule_hashes,encoder_images_this_invocation=encoder_images,encoder_unchanged=True,normal_forbidden_accesses=normal_forbidden,
            unadmitted_raw_probe_blocked=negative,source_ids=p['source_ids'],TRAIN_counts=dict(pklot=200,acpds=231),DEV_counts=dict(pklot=30,acpds=35),
            final_pixels_or_semantics_opened=False,source_scope=p['source_scope'],run_definition=p['run_definition'])
        dump(out/'run.json',report);dump(ROOT/'models/region_guarded.json',report)
        dump(ROOT/'reports/region_guarded_latest.json',dict(run_id=p['run_id'],result_path=(out/'run.json').relative_to(ROOT).as_posix(),result_sha256=digest(out/'run.json'),production_promoted=False))
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;existing=list(reader)
        assert not any(r['experiment_id']==p['run_id'] for r in existing)
        entry=dict(experiment_id=p['run_id'],run_type='Matched warm-start raw/guarded SGD region DEVELOPMENT training',started_at=started,finished_at=finished,
            source_ids=';'.join(p['source_ids']),split_ids='PKLot200TRAIN/30DEV +ACPDS231TRAIN/35DEV;all final closed',configuration=path.relative_to(ROOT).as_posix(),
            architecture=p['architecture'],optimizer='SGD',learning_rate=.01,batch_size=8,random_seed=180,hardware='CPU',execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(dict(results=results,relative_checks=relative,teacher_retention_checks=teacher_checks,absolute_checks=absolute)),
            logs=out.relative_to(ROOT).as_posix(),checkpoints=json.dumps(checkpoints),code_revision_basis='Sealed implementation/input/sampler hashes',
            implementation_sha256=digest(__file__),conclusions='Gate='+str(report['development_gate_passed'])+';one paired trial,two conditions;no app promotion')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields,lineterminator='\n').writerow({k:entry.get(k,'') for k in fields})
        state=read(sp);assert p['run_id'] not in state['completed_run_ids'];state['completed_run_ids'].append(p['run_id'])
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=p['run_id'];state['region_guarded']=report;dump(sp,state)
        print(json.dumps({k:report[k] for k in ['run_id','completed_rounds','updates_per_arm','relative_checks','development_gate_passed','duration_seconds_this_invocation','peak_sampled_process_RSS_bytes']}),flush=True)
    except BaseException as error:
        dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:
        state=read(sp);state['active_training_jobs']=[];dump(sp,state)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args();run(args.run) if args.run else prepare()
