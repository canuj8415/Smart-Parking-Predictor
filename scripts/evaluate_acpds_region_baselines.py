"""Prespecified frozen region models on all admitted ACPDS DEV masks;no fitting."""
import argparse,csv,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.partial');tmp.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');os.replace(tmp,p)


def prepare():
    state=read(ROOT/'data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    card=read(ROOT/'models/acpds_region_dataset.json');assert card['data_gate_passed']
    data=read(ROOT/card['manifest']);assert digest(ROOT/card['manifest'])==card['manifest_sha256']
    records=[r for r in data['records'] if r['role']=='development'];assert len(records)==35
    now=datetime.now(timezone.utc);rid='ACPDS-REGION-BASELINES-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    methods=[dict(name='original_unet',kind='unet',checkpoint='models/checkpoints/parking_unet.pt')]
    inputs=['models/acpds_region_dataset.json',card['manifest'],'data/manifests/acpds_source_roles_v1.json','models/pretrained/resnet18_imagenet.pth']
    for name,file in [('coarse_duration','models/region_fpn_duration.json'),('rgb_detail','models/region_fpn_detail.json'),('bounded_detail','models/region_fpn_bounded.json')]:
        r=read(ROOT/file);assert digest(ROOT/r['candidate_checkpoint'])==r['candidate_sha256'];inputs.append(file)
        methods.append(dict(name=name,kind=name,checkpoint=r['candidate_checkpoint']))
    for model in methods:model['checkpoint_sha256']=digest(ROOT/model['checkpoint']);inputs.append(model['checkpoint'])
    code=['scripts/evaluate_acpds_region_baselines.py','src/smart_parking/region_validity.py','tests/test_region_validity.py',
        'src/smart_parking/region_fpn.py','src/smart_parking/region_detail.py','src/smart_parking/region_bounded_detail.py','src/smart_parking/training.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=175,source_ids=['SRC-DS-021','SRC-DS-001','SRC-MOD-003'],
        hypothesis='Quantify source-shift behavior of four already-frozen PKLot region models on all35admitted ACPDS DEV images using nonpadding mask metrics before new training.',
        records=records,methods=methods,source_hashes={f:digest(ROOT/f) for f in code},input_hashes={f:digest(ROOT/f) for f in inputs},
        protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T093915Z/checks.json')['frozen_hashes_unchanged'],
        threshold=.5,batch_size=8,threads=4,maximum_seconds=300,absolute_reference_gates=dict(mean_image_iou=.8,minimum_image_iou=.65),
        original_input='Commonletterboxed256x144RGB ->PILbilinear192x112,raw0-1RGB,probabilitybilinearback to commongrid;not nativeappbenchmark replay',
        other_input='FixedImageNet normalization;frozen encoder features;preserved checkpoint constructors',
        template='Inapplicable:no matching supplied camera geometry for arbitrary new ACPDS views',
        scope='Previously exposed DEVELOPMENT source,derived supplied-bayunion masks,not fresh final/exhaustive facility/occupancy truth;no promotion',
        prior_exposure='ACPDS35 already used for occupancy adaptation/diagnostics;this is first region baseline on the derived target',
        neural_training=False,TEST_pixels_or_semantics_opened=False)
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')))
    dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json',flush=True)


def run(path):
    import numpy as np
    import torch
    from PIL import Image
    from torch.nn import functional as F
    from smart_parking.training import ParkingUNet
    from smart_parking.region_fpn import FrozenRegionEncoder,RegionPyramidDecoder
    from smart_parking.region_detail import RegionDetailDecoder
    from smart_parking.region_bounded_detail import BoundedRegionDetailDecoder
    from smart_parking.region_validity import valid_mask_metrics
    path=Path(path).resolve();out=path.parent;p=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not(out/'run.json').exists()
    assert digest(path)==read(out/'protocol_binding.json')['sha256'] and p['source_hashes'].get(Path(__file__).resolve().relative_to(ROOT).as_posix())==digest(__file__)
    bound={**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}
    for f,h in bound.items():assert digest(ROOT/f)==h,f
    sp=ROOT/'data/automation_state.json';state=read(sp);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    state['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),maximum_seconds=300,cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),
        resume_policy='No training;interruption is not a completed trial,retain outputs;rerun only this uncompleted sealed protocol')];dump(sp,state)
    allowed={(ROOT/r['cache']).resolve() for r in p['records']};forbidden=[]
    def audit(event,args):
        if event.startswith('socket.'):forbidden.append(event);raise PermissionError('Offline frozen baseline')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            q=Path(os.fsdecode(args[0])).resolve()
            if q.is_relative_to(ROOT/'data/raw') or (q.suffix.casefold() in {'.jpg','.jpeg','.xml','.npz'} and q not in allowed and not q.is_relative_to(out)):
                forbidden.append(str(q));raise PermissionError('Raw/final/unadmitted source access blocked')
    sys.addaudithook(audit);clock=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    def boundary():
        if (out/'CANCEL').exists() or time.perf_counter()-clock>300:raise InterruptedError('Cancelled/deadline;partial diagnostics retained')
    try:
        torch.set_num_threads(p['threads']);torch.manual_seed(p['seed']);rgb=[];truth=[];valid=[]
        for r in p['records']:
            boundary();assert r['source_id']=='SRC-DS-021' and r['role']=='development' and digest(ROOT/r['cache'])==r['cache_sha256']
            with np.load(ROOT/r['cache'],allow_pickle=False) as d:rgb.append(d['rgb'].copy());truth.append(d['mask'].copy());valid.append(d['valid'].copy())
        rgb=np.stack(rgb);truth=np.stack(truth);valid=np.stack(valid)
        x=torch.from_numpy(rgb).permute(0,3,1,2).float()/255;mean=torch.tensor([.485,.456,.406])[None,:,None,None];std=torch.tensor([.229,.224,.225])[None,:,None,None]
        encoder=FrozenRegionEncoder(torch.load(ROOT/'models/pretrained/resnet18_imagenet.pth',map_location='cpu',weights_only=True))
        chunks=[[] for _ in range(4)]
        with torch.inference_mode():
            for indices in torch.arange(35).split(p['batch_size']):
                boundary()
                for target,value in zip(chunks,encoder((x[indices]-mean)/std)):target.append(value)
            features=tuple(torch.cat(v) for v in chunks)
        results={};probabilities={}
        for item in p['methods']:
            boundary();checkpoint=torch.load(ROOT/item['checkpoint'],map_location='cpu',weights_only=True)
            if item['kind']=='unet':model=ParkingUNet()
            elif item['kind']=='coarse_duration':model=RegionPyramidDecoder(checkpoint['width'])
            elif item['kind']=='rgb_detail':model=RegionDetailDecoder(checkpoint['width'],checkpoint['detail_width'],checkpoint['detail_seed'])
            elif item['kind']=='bounded_detail':model=BoundedRegionDetailDecoder(checkpoint['width'],checkpoint['detail_width'],checkpoint['detail_seed'],checkpoint['max_detail_logit'])
            else:raise ValueError('Unregistered frozen method')
            model.load_state_dict(checkpoint['state_dict']);model.eval();outputs=[]
            with torch.inference_mode():
                for indices in torch.arange(35).split(p['batch_size']):
                    boundary()
                    if item['kind']=='unet':
                        a=np.stack([np.asarray(Image.fromarray(rgb[i]).resize((192,112),Image.Resampling.BILINEAR)) for i in indices.tolist()]);tensor=torch.from_numpy(a).permute(0,3,1,2).float()/255
                        probability=F.interpolate(model(tensor).sigmoid(),size=(144,256),mode='bilinear',align_corners=False)[:,0]
                    elif item['kind']=='coarse_duration':probability=model(tuple(v[indices] for v in features)).sigmoid()[:,0]
                    else:probability=model(tuple(v[indices] for v in features),(x[indices]-mean)/std).sigmoid()[:,0]
                    assert torch.isfinite(probability).all();outputs.append(probability.numpy())
            probability=np.concatenate(outputs);metric=valid_mask_metrics(probability>=.5,truth,valid)
            metric['absolute_reference_gates']=dict(mean_iou=metric['mean_image_iou']>=p['absolute_reference_gates']['mean_image_iou'],minimum_image_iou=metric['minimum_image_iou']>=p['absolute_reference_gates']['minimum_image_iou'])
            results[item['name']]=metric;probabilities[item['name']]=probability
            dump(out/(item['name']+'_metrics.json'),metric);print(item['name'],metric['mean_image_iou'],metric['minimum_image_iou'],flush=True)
        np.savez_compressed(out/'development_predictions.npz',RGB=rgb,actual=truth,valid=valid,**probabilities)
        assert not forbidden;normal=list(forbidden)
        try:(ROOT/'data/raw/ACPDS_TEST_DO_NOT_OPEN.JPG').read_bytes()
        except PermissionError:probe=True
        else:raise AssertionError('Unadmitted raw probe failed')
        for f,h in bound.items():assert digest(ROOT/f)==h,f
        for r in p['records']:assert digest(ROOT/r['cache'])==r['cache_sha256']
        report=dict(run_id=p['run_id'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=p['seed'],
            protocol_sha256=digest(path),images=35,methods=results,encoder_images=35,model_image_forwards=140,models_trained=0,
            source_ids=p['source_ids'],source_raw_images_opened=0,TEST_pixels_or_semantics_opened=False,production_promoted=False,
            normal_forbidden_accesses=normal,unadmitted_raw_probe_blocked=probe,validity_mask_applied=True,template=p['template'],scope=p['scope'])
        dump(out/'run.json',report);dump(ROOT/'models/acpds_region_baselines.json',report);dump(ROOT/'reports/acpds_region_baselines_latest.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='First frozen region source-shift baseline on35ACPDSDEV,no training',started_at=started,finished_at=report['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='All35admittedACPDSDEV only;wholeTESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture='Four preserved models,commonletterbox/nonpaddingmetrics',random_seed=175,hardware='CPU4threads',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps({k:{n:v[n] for n in ['mean_image_iou','minimum_image_iou','absolute_reference_gates']} for k,v in results.items()}),logs=out.relative_to(ROOT).as_posix(),code_revision_basis='5ba48b8 plus qualifieddata/maskedmetrics sources',implementation_sha256=digest(__file__),conclusions='Source-shift DEVELOPMENT baseline only,no final orpromotion')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(sp);assert p['run_id'] not in state['completed_run_ids'];state['completed_run_ids'].append(p['run_id']);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=p['run_id'];state['acpds_region_baselines']=report;dump(sp,state)
        print(json.dumps(dict(run_id=p['run_id'],images=35,methods=4,models_trained=0,duration_seconds=report['duration_seconds'])),flush=True)
    except BaseException as error:dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error_type=type(error).__name__,error=str(error),completed_run_counted=False));raise
    finally:state=read(sp);state['active_validation_jobs']=[];dump(sp,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args();run(args.run) if args.run else prepare()
