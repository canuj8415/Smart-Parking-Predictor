"""Sealed, cancellable image-only bay-footprint TRAIN/DEV experiment; no final access."""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.provenance import digest


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    os.replace(temporary, path)


def prepare():
    state = read(ROOT/'data/automation_state.json')
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    card = read(ROOT/'models/region_dataset_v2.json')
    assert card['data_gate_passed']
    now = datetime.now(timezone.utc)
    rid = 'REGION-FPN-BOUNDED-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT/'experiments/results'/rid
    out.mkdir(exist_ok=False)
    paths = ['scripts/train_region_fpn_bounded.py', 'src/smart_parking/region_fpn.py',
             'src/smart_parking/region_detail.py','tests/test_region_detail.py',
             'src/smart_parking/region_bounded_detail.py','tests/test_region_bounded_detail.py',
             'tests/test_region_fpn.py', 'src/smart_parking/training.py']
    inputs = [card['manifest'], 'models/region_dataset_v2.json', 'models/pklot_current_role_ledger.json',
              'models/pretrained/resnet18_imagenet.pth', 'data/source_manifest.csv']
    protocol = dict(run_id=rid, prepared_at=now.isoformat(), seed=169,
        hypothesis='A bounded score-gated RGB residual can improve DEVmacroIoU by at least0.02 over the unbounded detail model while retaining initial parameters,sampler,loss,budget and six admission gates.',
        source_ids=['SRC-DS-001', 'SRC-MOD-003'], dataset_manifest=card['manifest'],
        dataset_manifest_sha256=card['manifest_sha256'], train_images=200, development_images=30,
        source_hashes={p: digest(ROOT/p) for p in paths},
        input_hashes={p: digest(ROOT/p) for p in inputs},
        protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T090914Z/checks.json')['frozen_hashes_unchanged'],
        architecture='Frozen ResNet18/FPN/RGBdetail;delta=0.5*tanh(raw)*4*p*(1-p),detached coarse sigmoid score p;unchanged zero-start parameters',
        detail_seed=170, detail_width=8,max_detail_logit=.5,
        decoder_class='smart_parking.region_bounded_detail.BoundedRegionDetailDecoder',
        pretrained='models/pretrained/resnet18_imagenet.pth', backbone_parameters_and_BN_frozen=True,
        input_size=[256,144], normalization=dict(mean=[.485,.456,.406],std=[.229,.224,.225]),
        learning_rate=.001, weight_decay=.0001, optimizer='AdamW', batch_size=8, maximum_epochs=32,
        patience=6, selection_minimum_improvement=.001, selection='Maximum equal-camera mean per-image DEV IoU;earliest checkpoint on ties',
        threshold=.5, augmentation='None;cached frozen image features',
        loss='TRAIN-only positive-weight BCE plus soft Dice(epsilon1)', threads=4, maximum_seconds=900,
        comparisons=dict(original='Preserved U-Net;common256x144RGB cache resized PIL-bilinear192x112;raw0-1RGB;probability bilinear back to commongrid;threshold0.5',
            template='Per-camera pixel majority of TRAIN masks only,threshold0.5;camera-conditioned comparator,not image-only inference'),
        gates=dict(macro_camera_iou_minimum=.80, minimum_camera_iou=.75, minimum_image_iou=.65,
                   macro_gain_over_original_minimum=.02, maximum_camera_regression_from_original=.05,
                   maximum_camera_regression_from_train_template=.05),
        scope='DEVELOPMENT selection only;familiar camera views,not unseen/final/new-slot or exhaustive facility/occupancy truth;no app promotion',
        final_access=False, source_groups='Existing50TRAIN/15DEV groups only;all17consumed and16quarantine excluded')
    reference = read(ROOT/'models/region_fpn_detail.json')
    reference_folder = 'experiments/results/'+reference['run_id']
    protocol.update(reference_card='models/region_fpn_detail.json', reference_run_id=reference['run_id'],
        reference_protocol=reference_folder+'/protocol.json', reference_curves=reference_folder+'/curves.json',
        reference_last='models/checkpoints/region_fpn/'+reference['run_id']+'/last.pt',
        minimum_bounded_gain_over_reference=.02,
        maximum_paired_regression=.05,
        controlled_change='Only the residual score gate/bound changes;initial parameters,sampler,loss,budget andall admission gates fixed')
    for name in ['reference_card','reference_protocol','reference_curves','reference_last']:
        protocol['input_hashes'][protocol[name]]=digest(ROOT/protocol[name])
    short=read(ROOT/protocol['reference_protocol'])
    same_fields=['seed','dataset_manifest','dataset_manifest_sha256','train_images','development_images',
        'pretrained','input_size','normalization','learning_rate','weight_decay','optimizer',
        'batch_size','selection_minimum_improvement','selection','threshold','augmentation','loss','threads','gates',
        'detail_seed','detail_width','maximum_epochs','patience']
    assert all(protocol[k]==short[k] for k in same_fields)
    protocol['unchanged_recipe_fields']=same_fields
    dump(out/'protocol.json', protocol)
    dump(out/'protocol_binding.json', dict(sha256=digest(out/'protocol.json')))
    dump(out/'implementation_sources.json', {p:(ROOT/p).read_text(encoding='utf-8') for p in paths})
    print(out/'protocol.json', flush=True)


def run(path):
    import random
    import numpy as np
    import psutil
    import torch
    from PIL import Image
    from torch.nn import functional as F
    from smart_parking.region_fpn import (FrozenRegionEncoder, RegionPyramidDecoder,
        segmentation_loss, train_camera_templates, mask_metrics)
    from smart_parking.training import ParkingUNet
    from smart_parking.region_detail import RegionDetailDecoder,reference_sampler_orders,sampler_order_digest
    from smart_parking.region_bounded_detail import BoundedRegionDetailDecoder
    path = Path(path).resolve(); out = path.parent; p = read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve())
    assert digest(path) == read(out/'protocol_binding.json')['sha256'] and not (out/'run.json').exists()
    assert p['source_hashes'].get(Path(__file__).relative_to(ROOT).as_posix())==digest(__file__),'Wrong executor for sealed protocol'
    bound = {**p['source_hashes'], **p['input_hashes'], **p['protected_hashes']}
    for f,h in bound.items():
        assert digest(ROOT/f) == h, f
    state_path = ROOT/'data/automation_state.json'; state = read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    checkpoints = ROOT/'models/checkpoints/region_fpn'/p['run_id']
    checkpoints.mkdir(parents=True,exist_ok=True)
    state['active_training_jobs'] = [dict(run_id=p['run_id'],pid=os.getpid(),phase='Frozen features then decoder TRAIN/DEV',
        cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),maximum_seconds=900,
        resume_command='scripts/train_region_fpn_bounded.py --run '+path.relative_to(ROOT).as_posix())]
    dump(state_path,state)
    started=datetime.now(timezone.utc).isoformat(); clock=time.perf_counter(); process=psutil.Process(); peak=process.memory_info().rss
    forbidden=[]; manifest=read(ROOT/p['dataset_manifest']); records=manifest['records']
    allowed={(ROOT/r['cache']).resolve() for r in records}
    def audit(event,args):
        if event.startswith('socket.'):
            forbidden.append(event); raise PermissionError('Offline research trainer')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            q=Path(os.fsdecode(args[0])).resolve()
            if q.suffix.casefold() in {'.jpg','.jpeg','.xml','.npz'} and q not in allowed and not q.is_relative_to(out):
                forbidden.append(str(q)); raise PermissionError('Only admitted RGB/mask caches may be opened')
    sys.addaudithook(audit)
    def boundary():
        nonlocal peak
        peak=max(peak,process.memory_info().rss)
        if (out/'CANCEL').exists() or time.perf_counter()-clock>p['maximum_seconds']:
            raise InterruptedError('Cancelled/deadline;last batch checkpoint retained')
    def save_torch(destination,value):
        temporary=destination.with_suffix(destination.suffix+'.partial')
        torch.save(value,temporary); os.replace(temporary,destination)
    try:
        torch.set_num_threads(p['threads']); torch.manual_seed(p['seed']); np.random.seed(p['seed']); random.seed(p['seed'])
        assert digest(ROOT/p['dataset_manifest']) == p['dataset_manifest_sha256']
        assert manifest['data_gate_passed'] and len(records)==230
        train=torch.tensor([i for i,r in enumerate(records) if r['role']=='train'])
        dev=torch.tensor([i for i,r in enumerate(records) if r['role']=='development'])
        assert len(train)==200 and len(dev)==30
        roles=read(ROOT/'models/pklot_current_role_ledger.json')['current_ledger']['groups']
        roles={r['camera_id']+'|'+r['capture_date']:r['status'] for r in roles}
        rgb=[]; masks=[]
        for r in records:
            boundary(); assert roles[r['group_id']]==('training_exposed' if r['role']=='train' else 'development_exposed')
            assert digest(ROOT/r['cache'])==r['cache_sha256']
            with np.load(ROOT/r['cache'],allow_pickle=False) as cache:
                a=cache['rgb']; b=cache['mask']
                assert a.shape==(144,256,3) and a.dtype==np.uint8 and b.shape==(144,256) and b.dtype==np.bool_
                rgb.append(a.copy()); masks.append(b.copy())
        rgb=np.stack(rgb); masks=np.stack(masks); y=torch.from_numpy(masks[:,None].astype('float32'))
        x=torch.from_numpy(rgb).permute(0,3,1,2).float()/255
        mean=torch.tensor(p['normalization']['mean'])[None,:,None,None]; std=torch.tensor(p['normalization']['std'])[None,:,None,None]
        encoder=FrozenRegionEncoder(torch.load(ROOT/p['pretrained'],map_location='cpu',weights_only=True))
        encoder_before={k:v.clone() for k,v in encoder.state_dict().items()}
        decoder=BoundedRegionDetailDecoder(detail_width=p['detail_width'],detail_seed=p['detail_seed'],max_detail_logit=p['max_detail_logit'])
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(p['seed'])
            reference_encoder=FrozenRegionEncoder(torch.load(ROOT/p['pretrained'],map_location='cpu',weights_only=True))
            reference_decoder=RegionDetailDecoder(detail_width=p['detail_width'],detail_seed=p['detail_seed'])
            reference_rng=torch.random.get_rng_state().clone()
            assert all(torch.equal(v,reference_decoder.state_dict()[k]) for k,v in decoder.state_dict().items())
        assert torch.equal(torch.random.get_rng_state(),reference_rng)
        assert not torch.count_nonzero(decoder.residual[-1].weight) and not torch.count_nonzero(decoder.residual[-1].bias)
        del reference_encoder,reference_decoder
        expected_orders,_=reference_sampler_orders(train,reference_rng,p['maximum_epochs'])
        reference_epochs=len(read(ROOT/p['reference_curves']))
        _,reference_end=reference_sampler_orders(train,reference_rng,reference_epochs)
        reference_last=torch.load(ROOT/p['reference_last'],map_location='cpu',weights_only=True)
        assert torch.equal(reference_last['rng_state'],reference_end),'Sampler reference differs from actual duration checkpoint'
        del reference_last
        expected_digests=[sampler_order_digest(order) for order in expected_orders]
        dump(out/'sampler_control.json',dict(reference_run=p['reference_run_id'],reference_completed_epochs=reference_epochs,
            reference_last_sha256=p['input_hashes'][p['reference_last']],reference_final_RNG_matches=True,
            initial_coarse_parameters_match=True,all_initial_parameters_match=True,initial_residual_zero=True,expected_epoch_order_sha256=expected_digests))
        optimizer=torch.optim.AdamW(decoder.parameters(),lr=p['learning_rate'],weight_decay=p['weight_decay'])
        features_path=out/'frozen_features.pt'; marker=out/'features_complete.json'; encoder_images=0
        if marker.exists():
            fm=read(marker); assert fm['protocol_sha256']==digest(path) and digest(features_path)==fm['sha256']
            features=torch.load(features_path,map_location='cpu',weights_only=True)
        else:
            chunks=[[] for _ in range(4)]
            for indices in torch.arange(len(records)).split(p['batch_size']):
                boundary(); output=encoder((x[indices]-mean)/std); encoder_images+=len(indices)
                for target,value in zip(chunks,output):target.append(value.detach().clone())
            features=tuple(torch.cat(parts) for parts in chunks)
            save_torch(features_path,features)
            dump(marker,dict(protocol_sha256=digest(path),sha256=digest(features_path),images=230,
                shapes=[list(f.shape) for f in features],feature_bytes=sum(f.numel()*f.element_size() for f in features)))
        assert all(f.shape[0]==230 and torch.isfinite(f).all() for f in features)
        for k,v in encoder.state_dict().items():assert torch.equal(v,encoder_before[k]),k
        positive=y[train].mean(); weight=((1-positive)/positive).detach()
        training=dict(epoch=0,cursor=0,order=None,loss_sum=0.,curves=[],best_score=-1.,best_path=None,stale=0,
                      training_batches=0,development_batches=0,epoch_order_digests=[])
        last=checkpoints/'last.pt'
        if last.exists():
            saved=torch.load(last,map_location='cpu',weights_only=True)
            assert saved['protocol_sha256']==digest(path)
            decoder.load_state_dict(saved['decoder']); optimizer.load_state_dict(saved['optimizer'])
            training=saved['training']; torch.random.set_rng_state(saved['rng_state'])
        def checkpoint():
            save_torch(last,dict(protocol_sha256=digest(path),decoder=decoder.state_dict(),optimizer=optimizer.state_dict(),
                                training=training,rng_state=torch.random.get_rng_state()))
        cameras=[records[i]['camera_id'] for i in dev.tolist()]
        def predictions():
            decoder.eval(); outputs=[]
            with torch.no_grad():
                for indices in dev.split(p['batch_size']):
                    boundary(); outputs.append(decoder(tuple(f[indices] for f in features),(x[indices]-mean)/std).sigmoid()[:,0].numpy())
                    training['development_batches']+=1
            return np.concatenate(outputs)
        while training['epoch']<p['maximum_epochs'] and training['stale']<p['patience']:
            if training['order'] is None:
                training['order']=train[torch.randperm(len(train))]; training['cursor']=0; training['loss_sum']=0.
                order_hash=sampler_order_digest(training['order'])
                assert order_hash==expected_digests[training['epoch']],'Changed TRAIN sample order'
                training['epoch_order_digests'].append(order_hash)
            decoder.train()
            while training['cursor']<len(train):
                boundary(); indices=training['order'][training['cursor']:training['cursor']+p['batch_size']]
                optimizer.zero_grad(set_to_none=True)
                logits=decoder(tuple(f[indices] for f in features),(x[indices]-mean)/std); loss=segmentation_loss(logits,y[indices],weight)
                assert torch.isfinite(loss); loss.backward(); optimizer.step()
                training['loss_sum']+=float(loss.detach())*len(indices)
                training['cursor']+=len(indices); training['training_batches']+=1; checkpoint()
            probability=predictions(); metrics=mask_metrics(probability>=p['threshold'],masks[dev.numpy()],cameras)
            score=metrics['macro_camera_iou']; epoch=training['epoch']+1
            improved=score>training['best_score']+p['selection_minimum_improvement']
            training['curves'].append(dict(epoch=epoch,training_loss=training['loss_sum']/len(train),
                macro_camera_iou=score,minimum_image_iou=metrics['minimum_image_iou'],by_camera=metrics['by_camera'],selected=improved))
            if improved:
                candidate=checkpoints/('epoch_'+str(epoch)+'_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.pt')
                assert not candidate.exists()
                save_torch(candidate,dict(run_id=p['run_id'],protocol_sha256=digest(path),state_dict=decoder.state_dict(),
                    epoch=epoch,architecture=p['architecture'],pretrained=p['pretrained'],pretrained_sha256=p['input_hashes'][p['pretrained']],
                    input_size=p['input_size'],normalization=p['normalization'],width=32,threshold=.5,
                    decoder_class=p['decoder_class'],detail_width=p['detail_width'],detail_seed=p['detail_seed'],
                    max_detail_logit=p['max_detail_logit'],
                    target=manifest['target'],development_metrics=metrics,dataset_manifest_sha256=p['dataset_manifest_sha256']))
                training['best_score']=score; training['best_path']=candidate.relative_to(ROOT).as_posix(); training['stale']=0
            else:training['stale']+=1
            training['epoch']=epoch; training['order']=None; checkpoint()
            dump(out/'curves.json',training['curves']); print(json.dumps(training['curves'][-1]),flush=True)
        assert training['epoch_order_digests']==expected_digests[:training['epoch']]
        best=torch.load(ROOT/training['best_path'],map_location='cpu',weights_only=True); decoder.load_state_dict(best['state_dict'])
        probability=predictions(); candidate_metrics=mask_metrics(probability>=.5,masks[dev.numpy()],cameras)
        assert abs(candidate_metrics['macro_camera_iou']-training['best_score'])<1e-12
        maximum_forward_delta=0.;strong_pixels=0;bound_batches=0
        with torch.no_grad():
            for indices in dev.split(p['batch_size']):
                boundary();f=tuple(v[indices] for v in features)
                coarse=decoder.coarse(f);logits=decoder(f,(x[indices]-mean)/std)
                assert torch.isfinite(coarse).all() and torch.isfinite(logits).all(),'Nonfinite forward-bound inputs'
                maximum_forward_delta=max(maximum_forward_delta,float((logits-coarse).abs().max()))
                strong=coarse.abs()>p['max_detail_logit'];strong_pixels+=int(strong.sum())
                assert torch.equal((logits>=0)[strong],(coarse>=0)[strong])
                bound_batches+=1
        assert maximum_forward_delta<=p['max_detail_logit']+1e-6
        original=ParkingUNet(); original.load_state_dict(torch.load(ROOT/'models/checkpoints/parking_unet.pt',map_location='cpu',weights_only=True)['state_dict']); original.eval()
        old=[]
        with torch.no_grad():
            for indices in dev.split(p['batch_size']):
                boundary(); a=np.stack([np.asarray(Image.fromarray(rgb[i]).resize((192,112),Image.Resampling.BILINEAR)) for i in indices.tolist()])
                tensor=torch.from_numpy(a).permute(0,3,1,2).float()/255
                old.append(F.interpolate(original(tensor).sigmoid(),size=(144,256),mode='bilinear',align_corners=False)[:,0].numpy())
        old=np.concatenate(old); original_metrics=mask_metrics(old>=.5,masks[dev.numpy()],cameras)
        templates=train_camera_templates(masks,records); templated=np.stack([templates[c] for c in cameras])
        template_metrics=mask_metrics(templated,masks[dev.numpy()],cameras)
        g=p['gates']; c=candidate_metrics
        checks=dict(macro_camera_iou=c['macro_camera_iou']>=g['macro_camera_iou_minimum'],
            every_camera_iou=min(v['mean_iou'] for v in c['by_camera'].values())>=g['minimum_camera_iou'],
            every_image_iou=c['minimum_image_iou']>=g['minimum_image_iou'],
            gain_over_original=c['macro_camera_iou']-original_metrics['macro_camera_iou']>=g['macro_gain_over_original_minimum'],
            no_camera_regression_from_original=all(c['by_camera'][k]['mean_iou']>=v['mean_iou']-g['maximum_camera_regression_from_original'] for k,v in original_metrics['by_camera'].items()),
            no_camera_regression_from_train_template=all(c['by_camera'][k]['mean_iou']>=v['mean_iou']-g['maximum_camera_regression_from_train_template'] for k,v in template_metrics['by_camera'].items()))
        np.savez_compressed(out/'development_predictions.npz',candidate_probability=probability,original_probability=old,conditional_template=templated,actual=masks[dev.numpy()],RGB=rgb[dev.numpy()])
        dump(out/'development_records.json',[records[i] for i in dev.tolist()])
        dump(out/'comparisons.json',dict(candidate=candidate_metrics,original=original_metrics,conditional_train_template=template_metrics))
        assert not forbidden; normal_forbidden=list(forbidden)
        try:(ROOT/'data/processed/NEVER_OPEN_UNQUALIFIED.npz').read_bytes()
        except PermissionError:negative_control=True
        else:raise AssertionError('Unqualified cache guard failed')
        for f,h in bound.items():assert digest(ROOT/f)==h,f
        for k,v in encoder.state_dict().items():assert torch.equal(v,encoder_before[k]),k
        report=dict(run_id=p['run_id'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),
            duration_seconds_this_invocation=time.perf_counter()-clock,peak_sampled_process_RSS_bytes=peak,
            seed=p['seed'],protocol_sha256=digest(path),candidate_checkpoint=training['best_path'],candidate_sha256=digest(ROOT/training['best_path']),
            selected_epoch=best['epoch'],completed_epochs=training['epoch'],early_stopped=training['stale']>=p['patience'],
            positive_weight=float(weight),train_images=200,development_images=30,
            candidate=candidate_metrics,original=original_metrics,conditional_train_template=template_metrics,
            gates=checks,development_gate_passed=all(checks.values()),production_promoted=False,
            source_ids=p['source_ids'],scope=p['scope'],final_pixels_or_XML_decoded=0,
            backbone_and_BN_unchanged=True,normal_forbidden_accesses=normal_forbidden,unqualified_cache_probe_blocked=negative_control,
            encoder_images_this_invocation=encoder_images,decoder_training_batches=training['training_batches'],
            decoder_development_batches=training['development_batches'],original_development_images=30,
            actual_completed_experiments_added=1,continuation='Fresh rights-qualified final reservation still required;DEVELOPMENT pass alone not promotion')
        reference=read(ROOT/p['reference_card'])
        gain=candidate_metrics['macro_camera_iou']-reference['candidate']['macro_camera_iou']
        worst_pair=min(a['iou']-b['iou'] for a,b in zip(candidate_metrics['per_image'],reference['candidate']['per_image']))
        report['bounded_comparison']=dict(reference_run_id=p['reference_run_id'],
            reference_candidate_macro_camera_iou=reference['candidate']['macro_camera_iou'],
            gain_over_reference= gain, minimum_gain_prespecified=p['minimum_bounded_gain_over_reference'],
            mean_gain_objective_passed=gain>=p['minimum_bounded_gain_over_reference'],
            worst_paired_iou_change=worst_pair,maximum_paired_regression=p['maximum_paired_regression'],
            paired_nonregression_objective_passed=worst_pair>=-p['maximum_paired_regression'],
            bounded_hypothesis_passed=gain>=p['minimum_bounded_gain_over_reference'] and worst_pair>=-p['maximum_paired_regression'],
            sampler_epoch_order_sha256=training['epoch_order_digests'],
            coarse_initial_parameters_identical=True,initial_residual_zero=True,reference_sampler_final_RNG_matches=True,
            all_other_recipe_fields_unchanged=True)
        report['forward_bound_check']=dict(maximum_observed_logit_delta=maximum_forward_delta,
            bound=p['max_detail_logit'],strong_coarse_pixels=strong_pixels,strong_coarse_signs_preserved=True,
            batches=bound_batches,scope='Relative to this trained model current coarse logits,not GT or earlier checkpoint accuracy')
        dump(out/'run.json',report); dump(ROOT/'models/region_fpn_bounded.json',report); dump(ROOT/'reports/region_fpn_bounded_latest.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Image-only frozen encoder/decoder TRAIN/DEV candidate',started_at=started,finished_at=report['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='Existing50TRAIN/15DEV date groups;230qualifiedpairs;no final',configuration=path.relative_to(ROOT).as_posix(),architecture=p['architecture'],random_seed=p['seed'],hardware='CPU4threads',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(dict(candidate=candidate_metrics,original=original_metrics,template=template_metrics,gates=checks)),logs=out.relative_to(ROOT).as_posix(),checkpoints=training['best_path'],code_revision_basis='fc648a3 plus sealed bounded-residual source snapshots',implementation_sha256=digest(__file__),conclusions='DEVgate='+str(all(checks.values()))+';no final/app promotion')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path); assert p['run_id'] not in state['completed_run_ids']; state['completed_run_ids'].append(p['run_id']);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=p['run_id'];state['region_fpn_bounded']=report;dump(state_path,state)
        print(json.dumps({k:report[k] for k in ['run_id','selected_epoch','completed_epochs','development_gate_passed','gates','duration_seconds_this_invocation','candidate_checkpoint']}),flush=True)
    except BaseException as error:
        dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error=type(error).__name__,detail=str(error),completed_run_counted=False))
        raise
    finally:
        state=read(state_path);state['active_training_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args()
    run(args.run) if args.run else prepare()
