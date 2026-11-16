"""Sealed TRAIN-only frozen-checkpoint source-gradient diagnostic; no optimizer."""
import argparse,csv,hashlib,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def dump(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.partial');tmp.write_bytes((json.dumps(value,indent=2)+'\n').encode());os.replace(tmp,path)

def prepare():
    import numpy as np
    state=read(ROOT/'data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    parent=read(ROOT/'models/region_mixed.json');old_protocol='experiments/results/'+parent['run_id']+'/protocol.json';prior=read(ROOT/old_protocol)
    assert digest(ROOT/old_protocol)==parent['protocol_sha256']
    pools={name:[r for r in prior['records'] if r['study_source']==name and r['role']=='train'] for name in ['pklot','acpds']}
    rng=np.random.default_rng(178);records=[]
    for name in pools:
        assert len(pools[name])==dict(pklot=200,acpds=231)[name]
        for i in rng.permutation(len(pools[name]))[:32]:records.append(dict(pools[name][int(i)],diagnostic_index=len(records)))
    assert len(records)==64 and len({r['image_sha256'] for r in records})==64
    now=datetime.now(timezone.utc);rid='REGION-GRADIENTS-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    code=['scripts/diagnose_region_source_gradients.py','src/smart_parking/region_gradients.py','tests/test_region_gradients.py',
        'src/smart_parking/region_fpn.py','src/smart_parking/region_validity.py']
    inputs=['models/region_mixed.json',old_protocol,'models/region_dataset_v2.json','models/acpds_region_dataset.json',
        'models/pklot_current_role_ledger.json','data/manifests/acpds_source_roles_v1.json',prior['pretrained'],'data/source_manifest.csv']
    for f in ['models/region_dataset_v2.json','models/acpds_region_dataset.json']:inputs.append(read(ROOT/f)['manifest'])
    inputs.extend(v['path'] for v in parent['checkpoints'].values())
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=178,source_ids=prior['source_ids'],records=records,
        batches=[dict(batch=i,pklot=list(range(i*4,i*4+4)),acpds=list(range(32+i*4,36+i*4))) for i in range(8)],
        checkpoints=parent['checkpoints'],positive_weight=parent['positive_weight'],pretrained=prior['pretrained'],normalization=prior['normalization'],
        source_hashes={f:digest(ROOT/f) for f in code},input_hashes={f:digest(ROOT/f) for f in inputs},protected_hashes=prior['protected_hashes'],
        cache_hashes={r['cache']:r['cache_sha256'] for r in records},threads=4,maximum_seconds=300,maximum_RSS_bytes=1200000000,
        hypothesis='At the selected mixed decoder,at least4of8 fixed TRAIN batch pairs have negative PKLot/ACPDS gradient dot product,and at least1 equal-source raw-gradient descent direction locally increases PKLot loss at first order.',
        hypothesis_thresholds=dict(conflicting_pairs_minimum=4,pklot_first_order_worsening_pairs_minimum=1),
        measurements='Each fixed control/mixed checkpoint,8paired batches of4PKLot+4ACPDS TRAIN images;masked BCE+Dice,fixed previous PKLotTRAIN class weight;decoder-only autograd gradients;norms/dot/cosine and raw equal-gradient directional derivatives',
        sampling='One RNG178:permutation200PKLotTRAIN choose32,then permutation231ACPDSTRAIN choose32;no replacement or DEV;group consecutively in batches4',
        negative_dev_probe=next(r['cache'] for r in prior['records'] if r['role']=='development'),
        scope='Post-fit TRAIN-only local raw-gradient diagnostic on previously trained weights;not accuracy,not causal proof for AdamW trajectories,not a final or representative population study.',
        no_optimizer_or_weight_updates=True,DEV_or_final_image_access=False,run_definition='One completed two-checkpoint,eight-pair diagnostic;not a run per gradient,image,batch or model')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')))
    dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json',flush=True)

def run(path):
    import numpy as np
    import psutil
    import torch
    from smart_parking.region_fpn import FrozenRegionEncoder,RegionPyramidDecoder
    from smart_parking.region_validity import masked_bay_loss
    from smart_parking.region_gradients import gradient_geometry
    path=Path(path).resolve();out=path.parent;p=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not(out/'run.json').exists()
    assert digest(path)==read(out/'protocol_binding.json')['sha256'] and p['source_hashes'].get(Path(__file__).resolve().relative_to(ROOT).as_posix())==digest(__file__)
    bound={**p['source_hashes'],**p['input_hashes'],**p['protected_hashes'],**p['cache_hashes']}
    for name,expected in bound.items():assert digest(ROOT/name)==expected,name
    sp=ROOT/'data/automation_state.json';state=read(sp);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    state['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),phase='TRAIN-only frozen gradients;no optimizer',maximum_seconds=300,
        cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/diagnose_region_source_gradients.py --run '+path.relative_to(ROOT).as_posix())];dump(sp,state)
    allowed={(ROOT/r['cache']).resolve() for r in p['records']};forbidden=[]
    def audit(event,args):
        if event.startswith('socket.'):forbidden.append(event);raise PermissionError('Offline diagnostic')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            q=Path(os.fsdecode(args[0])).resolve()
            if q.is_relative_to(ROOT/'data/raw') or (q.suffix.casefold() in {'.jpg','.jpeg','.png','.xml','.npz','.npy'} and q not in allowed and not q.is_relative_to(out)):
                forbidden.append(str(q));raise PermissionError('Only prespecified TRAIN caches allowed')
    sys.addaudithook(audit);started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter();process=psutil.Process();peak=0
    def boundary():
        nonlocal peak
        peak=max(peak,process.memory_info().rss)
        if (out/'CANCEL').exists() or time.perf_counter()-clock>300 or peak>p['maximum_RSS_bytes']:raise InterruptedError('Cancel/deadline/RSS bound;completed batch journals retained')
    def state_hash(model):
        h=hashlib.sha256()
        for name,value in model.state_dict().items():h.update(name.encode());h.update(value.detach().contiguous().numpy().tobytes())
        return h.hexdigest()
    try:
        torch.set_num_threads(p['threads']);torch.use_deterministic_algorithms(True);torch.manual_seed(p['seed'])
        assert len(allowed)==64 and all(r['role']=='train' for r in p['records']);rgb=[];masks=[];valid=[]
        roles={r['camera_id']+'|'+r['capture_date']:r['status'] for r in read(ROOT/'models/pklot_current_role_ledger.json')['current_ledger']['groups']}
        for r in p['records']:
            boundary()
            if r['study_source']=='pklot':assert roles[r['group_id']]=='training_exposed'
            else:assert r['source_id']=='SRC-DS-021' and r['publisher_role']=='train'
            with np.load(ROOT/r['cache'],allow_pickle=False) as data:
                a=data['rgb'].copy();b=data['mask'].copy();v=data['valid'].copy() if r['study_source']=='acpds' else np.ones_like(b,dtype=np.bool_)
            assert a.shape==(144,256,3) and a.dtype==np.uint8 and b.shape==(144,256) and b.dtype==np.bool_ and v.dtype==np.bool_
            assert v.shape==b.shape and v.sum()==(36864 if r['study_source']=='pklot' else 27648) and not np.any(b&~v)
            rgb.append(a);masks.append(b);valid.append(v)
        rgb=np.stack(rgb);target=torch.from_numpy(np.stack(masks)[:,None].astype('float32'));support=torch.from_numpy(np.stack(valid)[:,None])
        encoder=FrozenRegionEncoder(torch.load(ROOT/p['pretrained'],map_location='cpu',weights_only=True));encoder_hash=state_hash(encoder)
        marker=out/'features_complete.json';encoder_images=0
        if marker.exists():
            fm=read(marker);assert fm['protocol_sha256']==digest(path) and digest(out/fm['file'])==fm['sha256']
            features=torch.load(out/fm['file'],map_location='cpu',weights_only=True)
        else:
            chunks=[[] for _ in range(4)];mean=torch.tensor(p['normalization']['mean'])[None,:,None,None];std=torch.tensor(p['normalization']['std'])[None,:,None,None]
            for batch in np.arange(64).reshape(8,8):
                boundary();x=torch.from_numpy(rgb[batch]).permute(0,3,1,2).float()/255
                for items,value in zip(chunks,encoder((x-mean)/std)):items.append(value.detach())
                encoder_images+=8
            features=tuple(torch.cat(v) for v in chunks)
            file='train_features_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.pt';torch.save(features,out/file)
            dump(marker,dict(file=file,sha256=digest(out/file),protocol_sha256=digest(path),TRAIN_images=64))
        assert state_hash(encoder)==encoder_hash and all(f.shape[0]==64 and torch.isfinite(f).all() for f in features)
        journals=out/'measurements';journals.mkdir(exist_ok=True);measurements=[];computed=0;states={}
        for arm,item in p['checkpoints'].items():
            boundary();saved=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True);model=RegionPyramidDecoder(saved['width']);model.load_state_dict(saved['state_dict']);model.eval()
            before=state_hash(model);parameters=tuple(model.parameters())
            for batch in p['batches']:
                boundary();journal=journals/(arm+'_'+str(batch['batch'])+'.json')
                if journal.exists():
                    row=read(journal);assert row['protocol_sha256']==digest(path) and row['checkpoint_sha256']==item['sha256'] and row['weight_state_hash']==before
                else:
                    gradients={};losses={}
                    for source in ['pklot','acpds']:
                        indices=batch[source];logits=model(tuple(f[indices] for f in features))
                        loss=masked_bay_loss(logits,target[indices],support[indices],p['positive_weight'])
                        parts=torch.autograd.grad(loss,parameters);gradient=torch.cat([g.detach().reshape(-1) for g in parts]).double().numpy()
                        assert np.isfinite(gradient).all();gradients[source]=gradient;losses[source]=float(loss.detach())
                    row=dict(arm=arm,batch=batch['batch'],protocol_sha256=digest(path),checkpoint_sha256=item['sha256'],weight_state_hash=before,
                        pklot_loss=losses['pklot'],acpds_loss=losses['acpds'],**gradient_geometry(gradients['pklot'],gradients['acpds']))
                    dump(journal,row);computed+=2
                assert all(v.grad is None for v in parameters);measurements.append(row)
            after=state_hash(model);assert before==after;states[arm]=dict(before=before,after=after,unchanged=True)
        assert len(measurements)==16 and {(r['arm'],r['batch']) for r in measurements}=={(a,i) for a in p['checkpoints'] for i in range(8)}
        summaries={}
        for arm in p['checkpoints']:
            rows=[r for r in measurements if r['arm']==arm];cosines=[r['cosine'] for r in rows if r['cosine_defined']]
            ratios=[r['acpds_to_pklot_norm_ratio'] for r in rows if r['acpds_to_pklot_norm_ratio'] is not None]
            summaries[arm]=dict(pairs=8,defined_cosines=len(cosines),conflicting_pairs=sum(r['conflicting'] for r in rows),
                mean_cosine=float(np.mean(cosines)) if cosines else None,minimum_cosine=min(cosines) if cosines else None,
                median_acpds_to_pklot_norm_ratio=float(np.median(ratios)) if ratios else None,
                pklot_first_order_worsening_pairs=sum(r['pklot_first_order_worsens'] for r in rows),
                acpds_first_order_worsening_pairs=sum(r['acpds_first_order_worsens'] for r in rows),
                mean_pklot_loss=float(np.mean([r['pklot_loss'] for r in rows])),mean_acpds_loss=float(np.mean([r['acpds_loss'] for r in rows])))
        hypothesis=(summaries['mixed']['conflicting_pairs']>=p['hypothesis_thresholds']['conflicting_pairs_minimum'] and
            summaries['mixed']['pklot_first_order_worsening_pairs']>=p['hypothesis_thresholds']['pklot_first_order_worsening_pairs_minimum'])
        assert not forbidden;normal=list(forbidden);negative={}
        for label,name in [('DEV_cache',p['negative_dev_probe']),('raw_source','data/raw/UNADMITTED_GRADIENT_PROBE.jpg')]:
            try:(ROOT/name).read_bytes()
            except PermissionError:negative[label]=True
            else:raise AssertionError('Unadmitted input was not blocked')
        for name,expected in bound.items():assert digest(ROOT/name)==expected,name
        assert state_hash(encoder)==encoder_hash
        finished=datetime.now(timezone.utc).isoformat();report=dict(run_id=p['run_id'],started_at=started,finished_at=finished,
            duration_seconds_this_invocation=time.perf_counter()-clock,peak_sampled_process_RSS_bytes=peak,seed=178,protocol_sha256=digest(path),
            source_ids=p['source_ids'],summaries=summaries,hypothesis_supported=hypothesis,weight_state_hashes=states,
            measurements=measurements,encoder_unchanged=True,encoder_images_this_invocation=encoder_images,
            decoder_gradient_evaluations_this_invocation=computed,models_trained=0,optimizer_steps=0,
            TRAIN_images=dict(pklot=32,acpds=32),DEV_or_final_pixels_opened=False,normal_forbidden_accesses=normal,
            negative_controls=negative,production_promoted=False,scope=p['scope'],run_definition=p['run_definition'])
        dump(out/'run.json',report);dump(ROOT/'models/region_source_gradients.json',report)
        dump(ROOT/'reports/region_source_gradients_latest.json',dict(run_id=p['run_id'],result_path=(out/'run.json').relative_to(ROOT).as_posix(),result_sha256=digest(out/'run.json')))
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;existing=list(reader)
        assert not any(r['experiment_id']==p['run_id'] for r in existing)
        entry=dict(experiment_id=p['run_id'],run_type='TRAIN-only frozen source-gradient diagnostic',started_at=started,finished_at=finished,
            source_ids=';'.join(p['source_ids']),split_ids='32PKLotTRAIN+32ACPDSTRAIN;8fixedbatchpairs;noDEV/final',configuration=path.relative_to(ROOT).as_posix(),
            architecture='Frozen selected control/mixed FPN;decoder autograd only',random_seed=178,hardware='CPU',execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(summaries),logs=out.relative_to(ROOT).as_posix(),
            code_revision_basis='Sealed source/split/cache/checkpoint protocol',implementation_sha256=digest(__file__),
            conclusions='Local gradient hypothesis='+str(hypothesis)+';no optimizer/weights/accuracy/promotion;one diagnostic not16runs')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields,lineterminator='\n').writerow({k:entry.get(k,'') for k in fields})
        state=read(sp);assert p['run_id'] not in state['completed_run_ids'];state['completed_run_ids'].append(p['run_id'])
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=p['run_id'];state['region_source_gradients']=report;dump(sp,state)
        print(json.dumps({k:report[k] for k in ['run_id','summaries','hypothesis_supported','duration_seconds_this_invocation','models_trained','optimizer_steps']}),flush=True)
    except BaseException as error:
        dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));raise
    finally:
        state=read(sp);state['active_validation_jobs']=[];dump(sp,state)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args();run(args.run) if args.run else prepare()
