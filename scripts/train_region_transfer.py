"""Bounded known-camera transfer study with a sealed, conditional fresh final set."""
import argparse,csv,json,os,random,sys,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import torch
from PIL import Image
from torchvision.models import resnet18
from torchvision.transforms import functional as TF
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.region_transfer import FrozenRegionEncoder,RegionDecoder
from smart_parking.layout import read_pklot_xml,union_mask
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.checkpointing import save_checkpoint_atomic
from smart_parking.region_evaluation import project_logits

def metric(predicted,actual):
    p=np.asarray(predicted,dtype=bool);a=np.asarray(actual,dtype=bool)
    if p.shape!=a.shape:raise ValueError('Mask dimensions differ')
    i=int((p&a).sum());u=int((p|a).sum());n=int(p.sum()+a.sum())
    return dict(pixel_iou=i/u if u else 1.,dice=2*i/n if n else 1.,pixels=int(a.size))

def load(rows,size=(192,112)):
    images=[];masks=[]
    for row in rows:
        with Image.open(ROOT/row['image']) as source:
            image=source.convert('RGB');layout=read_pklot_xml(ROOT/row['annotation'],image.size)
            if layout['camera_id']!=row['camera_id']:raise ValueError('Source camera mismatch')
            images.append(TF.to_tensor(image.resize(size,Image.Resampling.BILINEAR)))
            masks.append(TF.to_tensor(union_mask(layout,size)))
    return torch.stack(images),torch.stack(masks)

def masks_at_grid(rows,size=(192,112)):
    masks=[]
    for row in rows:
        with Image.open(ROOT/row['image']) as source:layout=read_pklot_xml(ROOT/row['annotation'],source.size)
        masks.append(TF.to_tensor(union_mask(layout,size)))
    return torch.stack(masks)

def scores(predictions,actual,rows):
    return dict(overall=metric(predictions,actual),per_camera={c:metric(predictions[[i for i,r in enumerate(rows) if r['camera_id']==c]],actual[[i for i,r in enumerate(rows) if r['camera_id']==c]]) for c in sorted({r['camera_id'] for r in rows})})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--loss-mode',choices=['balanced','unweighted'],default='balanced')
    parser.add_argument('--holdout-manifest',required=True,help='Previously sealed, still-unconsumed final reservation; never decoded by training')
    parser.add_argument('--seed',type=int,default=71)
    parser.add_argument('--input-scale',type=int,choices=[1,2],default=1)
    parser.add_argument('--development-manifest',default='data/manifests/segmentation_known_camera_v1.json')
    parser.add_argument('--max-epochs',type=int,default=80)
    args=parser.parse_args()
    lock=ROOT/'.cache/region_transfer.lock';lock.parent.mkdir(exist_ok=True)
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(descriptor,str(os.getpid()).encode());os.close(descriptor)
    try:study(args.loss_mode,args.holdout_manifest,args.seed,args.input_scale,args.development_manifest,args.max_epochs)
    except BaseException as error:
        state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
        owned=[j for j in state.get('active_training_jobs',[]) if j.get('pid')==os.getpid()]
        for job in owned:
            (ROOT/'experiments/results'/job['run_id']/'execution_failure.json').write_text(json.dumps(dict(error=type(error).__name__,detail=str(error),checkpoint='latest.pt if written',completed_run_counted=False),indent=2),encoding='utf-8')
        state['active_training_jobs']=[j for j in state.get('active_training_jobs',[]) if j.get('pid')!=os.getpid()];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
        raise
    finally:lock.unlink(missing_ok=True)

def study(loss_mode='balanced',holdout_manifest=None,seed=71,input_scale=1,development_manifest='data/manifests/segmentation_known_camera_v1.json',max_epochs=80):
    if loss_mode not in {'balanced','unweighted'}:raise ValueError('Unknown loss weighting')
    if input_scale not in {1,2}:raise ValueError('Unsupported input scale')
    if input_scale==2 and loss_mode!='balanced':raise ValueError('The resolution contrast fixes the reference balanced loss coefficient')
    if not 1<=max_epochs<=80:raise ValueError('Choose a bounded1-80epoch budget')
    source_manifest=(ROOT/development_manifest).resolve()
    if not source_manifest.is_relative_to((ROOT/'data/manifests').resolve()):raise ValueError('Development manifest must stay in project manifests')
    broad=source_manifest.name=='region_broader_development_v1.json'
    if broad:
        reservation=json.loads(source_manifest.read_text());audit=json.loads((ROOT/'experiments/results'/reservation['run_id']/'run.json').read_text())
        if not audit['data_gate_passed'] or digest(source_manifest)!=audit['development_manifest_sha256']:raise ValueError('Broader development data audit missing or changed')
    input_size=(192*input_scale,112*input_scale);evaluation_grid=(192,112)
    torch.set_num_threads(4);torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
    started=datetime.now(timezone.utc);run='REGION-TRANSFER-'+started.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    old=json.loads(source_manifest.read_text());rows=old['frames']
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
    if holdout_manifest is None:raise ValueError('An explicit sealed final reservation is required')
    final_manifest=(ROOT/holdout_manifest).resolve()
    if not final_manifest.is_relative_to((ROOT/'data/manifests').resolve()):raise ValueError('Reservation must stay in project manifests')
    final=assert_holdout_closed(final_manifest)
    owner=json.loads(final_manifest.read_text()).get('run_id')
    legacy_report=ROOT/'experiments/results'/str(owner)/'run.json'
    if legacy_report.exists() and json.loads(legacy_report.read_text()).get('final_images_decoded',0):raise ValueError('Legacy final reservation was already decoded')
    if {r['date'] for r in final}&{r['date'] for r in rows}:raise ValueError('Final reservation overlaps development dates')
    weights=ROOT/'models/pretrained/resnet18_imagenet.pth'
    protocol=dict(run_id=run,started_at=started.isoformat(),seed=seed,source_id='SRC-DS-001',pretrained_source_id='SRC-MOD-003',scope=f'Represented cameras; train{len(train)}/validation{len(val)}; existing sealed final6 remains closed throughout training; not unseen-camera generalization',
        hypothesis='Training the unchanged high-resolution architecture from scratch on18previously unused training dates improves overlap on6newdevelopment dates relative to the frozen old candidate. Data, date membership and epoch budget differ; no single-factor causal claim.' if broad else 'Doubling spatial sampling resolution preserves slot boundaries; unchanged decoder capacity, data, seed, augmentation and loss coefficient, selected/scored on the original common192x112 grid.' if input_scale==2 else 'Removing the extra positive BCE weight reduces false-positive bridges between parking spaces; fixed architecture, seed, data, augmentation, optimization and Dice term isolate the loss-weight change.' if loss_mode=='unweighted' else 'Confirm the reference balanced configuration at the declared seed without changing model/data/loss settings.',
        loss_mode=loss_mode,reference_run='REGION-TRANSFER-20261024T204533261212Z',final_evaluation_policy='Development only; never decode final data in this trainer, even if validation gate passes. Reuse sealed unconsumed reservation; separate guarded final evaluation required.',
        architecture='Frozen ResNet18 stem/layers1-3; global256->16 context; XY channels; multiscale64/64/32 decoder; full-resolution RGB+XY refinement16; binary logits',
        max_epochs=max_epochs,patience=12,min_validation_improvement=.0005,optimizer='Adam',learning_rate=.002,batch_size=4,input_size=list(input_size),evaluation_grid=list(evaluation_grid),input_scale=input_scale,augmentation='Per-frame brightness chosen from0.85/1.0/1.15; cached frozen-encoder features; masks unchanged',
        loss='BCE positive weight1 plus soft Dice' if loss_mode=='unweighted' else 'BCE positive coefficient fixed from the reference train-only balanced model plus soft Dice',selection='Best common192x112 validation IoU; bilinear logits projection align_cornersFalse BEFORE sigmoid/threshold0.5. Native-grid results secondary. No final-data selection.',
        validation_gate='AggregateIoU>=0.80, each camera>=0.65 and no camera more than0.10 below train-only majority. Validation gate only; no final decoding or automatic promotion.',
        final_gate='AggregateIoU>=0.80, each camera>=0.65 and no camera more than0.10 below train-only majority; report all comparators on same fresh frames. No automatic promotion.',
        split_manifest=str(source_manifest.relative_to(ROOT)),split_manifest_sha256=digest(source_manifest),broader_data_study=broad,reference_result_sha256=digest(ROOT/'experiments/results/REGION-TRANSFER-20261024T204533261212Z/run.json'),fresh_final_manifest=str(final_manifest.relative_to(ROOT)),fresh_final_manifest_sha256=digest(final_manifest),
        code_sha256=digest(Path(__file__)),architecture_code_sha256=digest(ROOT/'src/smart_parking/region_transfer.py'),evaluation_code_sha256=digest(ROOT/'src/smart_parking/region_evaluation.py'),checkpointing_code_sha256=digest(ROOT/'src/smart_parking/checkpointing.py'),layout_code_sha256=digest(ROOT/'src/smart_parking/layout.py'),encoder_weights_sha256=digest(weights),production_checkpoint_sha256=digest(ROOT/'models/checkpoints/parking_unet.pt'),
        input_hashes={r['image']:digest(ROOT/r['image']) for r in train+val},annotation_hashes={r['annotation']:digest(ROOT/r['annotation']) for r in train+val},
        environment=dict(torch=str(torch.__version__),device='cpu',threads=4,thread_limits={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}))
    # Hash-only duplicate screening is allowed; final images/labels are not decoded.
    final_hashes=[digest(ROOT/r['image']) for r in final]
    original_hashes={r['image_sha256'] for r in csv.DictReader((ROOT/'data/manifests/pklot_frames.csv').open(encoding='utf-8'))}
    prior_hashes=original_hashes|{r.get('image_sha256') or digest(ROOT/r['image']) for r in rows}
    if len(set(final_hashes))!=6 or set(final_hashes)&(set(protocol['input_hashes'].values())|prior_hashes):raise ValueError('Duplicate final source image')
    protocol['fresh_final_image_sha256']=final_hashes
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state.get('active_training_jobs') or state.get('active_validation_jobs'):raise RuntimeError('Another recorded experiment is active')
    state['active_training_jobs']=[dict(run_id=run,pid=os.getpid(),checkpoint=str(folder/'latest.pt'))];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    clock=time.perf_counter();x,y=load(train,input_size);vx,vy=load(val,input_size)
    common_y=y if input_scale==1 else masks_at_grid(train,evaluation_grid)
    common_vy=vy if input_scale==1 else masks_at_grid(val,evaluation_grid)
    backbone=resnet18(weights=None);backbone.load_state_dict(torch.load(weights,map_location='cpu',weights_only=True));encoder=FrozenRegionEncoder(backbone)
    decoder=RegionDecoder();optimizer=torch.optim.Adam(decoder.parameters(),lr=.002)
    mean=torch.tensor([.485,.456,.406])[None,:,None,None];std=torch.tensor([.229,.224,.225])[None,:,None,None]
    def features(rgb):
        if not broad:return tuple(t.detach().clone() for t in encoder((rgb-mean)/std))
        parts=[encoder((batch-mean)/std) for batch in rgb.split(8)]
        return tuple(torch.cat([part[level] for part in parts]) for level in range(3))
    variants=[(x*brightness).clamp(0,1) for brightness in [.85,1.,1.15]]
    cached=[features(rgb) for rgb in variants];validation_features=features(vx)
    baseline={c:(common_y[[i for i,r in enumerate(train) if r['camera_id']==c]].mean(0)>=.5).numpy() for c in sorted({r['camera_id'] for r in train})}
    val_geometry=np.stack([baseline[r['camera_id']] for r in val]);val_truth=(common_vy>=.5).numpy();baseline_scores=scores(val_geometry,val_truth,val)
    reference=json.loads((ROOT/'experiments/results/REGION-TRANSFER-20261024T204533261212Z/run.json').read_text())
    foreground=y.mean().item();positive_weight=torch.tensor(1. if loss_mode=='unweighted' else reference['positive_weight'])
    def loss_fn(logits,target):
        p=logits.sigmoid();dice=1-((2*(p*target).sum((1,2,3))+1)/(p.sum((1,2,3))+target.sum((1,2,3))+1)).mean()
        return torch.nn.functional.binary_cross_entropy_with_logits(logits,target,pos_weight=positive_weight)+dice
    best=-1.;best_epoch=0;stale=0;curves=[];best_state=None
    try:
        for epoch in range(1,max_epochs+1):
            decoder.train();total=0.
            for indices in torch.randperm(len(train)).split(4):
                choices=torch.randint(0,3,(len(indices),))
                rgb=torch.stack([variants[int(choice)][int(i)] for i,choice in zip(indices,choices)])
                batch_features=tuple(torch.stack([cached[int(choice)][level][int(i)] for i,choice in zip(indices,choices)]) for level in range(3))
                optimizer.zero_grad();loss=loss_fn(decoder(rgb,batch_features),y[indices]);loss.backward();optimizer.step();total+=loss.item()*len(indices)
            decoder.eval()
            with torch.no_grad():
                validation_logits=decoder(vx,validation_features)
                prediction=(project_logits(validation_logits,evaluation_grid).sigmoid()>=.5).numpy()
            current=scores(prediction,val_truth,val);score=current['overall']['pixel_iou'];curves.append(dict(epoch=epoch,train_loss=total/len(train),validation=current))
            if score>best+.0005:best=score;best_epoch=epoch;stale=0;best_state={k:v.detach().clone() for k,v in decoder.state_dict().items()}
            else:stale+=1
            save_checkpoint_atomic(dict(decoder_state_dict=decoder.state_dict(),optimizer_state_dict=optimizer.state_dict(),best_decoder_state_dict=best_state,epoch=epoch,best_epoch=best_epoch,stale_epochs=stale,torch_rng_state=torch.get_rng_state(),run_id=run,input_size=list(input_size),evaluation_grid=list(evaluation_grid),encoder_weights_sha256=protocol['encoder_weights_sha256']),folder/'latest.pt')
            (folder/'curves.json').write_text(json.dumps(curves,indent=2),encoding='utf-8')
            if epoch%5==0:print(f'{run} epoch{epoch}: validationIoU{score:.4f}, best{best:.4f}',flush=True)
            if stale>=12:break
    except KeyboardInterrupt:
        (folder/'cancelled.json').write_text(json.dumps(dict(last_epoch=len(curves),checkpoint='latest.pt',completed_run_counted=False),indent=2),encoding='utf-8')
        state=json.loads(state_path.read_text());state['active_training_jobs']=[];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8');raise
    decoder.load_state_dict(best_state);decoder.eval()
    checkpoint=folder/'candidate.pt';save_checkpoint_atomic(dict(decoder_state_dict=best_state,input_size=list(input_size),evaluation_grid=list(evaluation_grid),encoder_weights_sha256=protocol['encoder_weights_sha256'],run_id=run),checkpoint)
    with torch.no_grad():
        validation_logits=decoder(vx,validation_features)
        candidate=(project_logits(validation_logits,evaluation_grid).sigmoid()>=.5).numpy()
        native_candidate=(validation_logits.sigmoid()>=.5).numpy()
    validation=scores(candidate,val_truth,val)
    def gate(value,comparator):return value['overall']['pixel_iou']>=.80 and all(m['pixel_iou']>=.65 and m['pixel_iou']>=comparator['per_camera'][c]['pixel_iou']-.10 for c,m in value['per_camera'].items())
    passed=gate(validation,baseline_scores)
    (folder/'selection_closed.json').write_text(json.dumps(dict(closed_at=datetime.now(timezone.utc).isoformat(),best_epoch=best_epoch,checkpoint_sha256=digest(checkpoint),validation_gate_passed=passed),indent=2),encoding='utf-8')
    final_result=None
    # Final decoding is deliberately absent from the training controller.
    for i in range(len(val)):
        for name,array in [('validation_candidate',candidate),('validation_truth',val_truth),('validation_geometry',val_geometry)]:Image.fromarray((array[i,0]*255).astype('uint8')).save(folder/f'{name}_{i}.png')
        if input_scale!=1:
            for name,array in [('validation_candidate_native',native_candidate),('validation_truth_native',(vy>=.5).numpy())]:Image.fromarray((array[i,0]*255).astype('uint8')).save(folder/f'{name}_{i}.png')
    report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,epochs_completed=len(curves),best_epoch=best_epoch,checkpoint_sha256=digest(checkpoint),positive_weight=float(positive_weight),validation=validation,validation_geometry=baseline_scores,validation_gate_passed=passed,
        native_validation=scores(native_candidate,(vy>=.5).numpy(),val),native_train_foreground_fraction=foreground,final_images_decoded=0,final_annotations_decoded=0,final_result=final_result,production_changed=False,
        limitations=[f'Known-camera development study with{len(val)}validation frames; small date groups','Spatial coordinates/global context may encode deployment geometry; no unseen-camera claim','Broader-data study changes date membership, sample count and budget; compare on the same24newdevelopment frames, not directly against old six-frame scores.' if broad else 'Single-seed resolution contrast; common192x112 logits projection defines selection/comparison, while native-grid metrics are secondary.' if input_scale==2 else 'Single seed; current loss contrast holds architecture/data/augmentation/optimizer fixed. Comparisons with tiny models still change multiple components.','Final image bytes hashed only for duplicate screening; final decoding is absent from this trainer','No automatic app promotion from a development gate'])
    (folder/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    card='region_broader_candidate.json' if broad else 'region_resolution_candidate.json' if input_scale!=1 else 'region_loss_unweighted_candidate.json' if loss_mode=='unweighted' else 'region_transfer_candidate.json'
    (ROOT/'models'/card).write_text(json.dumps(report,indent=2),encoding='utf-8')
    state=json.loads(state_path.read_text());state['active_training_jobs']=[];state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run;state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['run_id','duration_seconds','epochs_completed','best_epoch','validation','validation_gate_passed','final_images_decoded','final_result']},indent=2),flush=True)

if __name__=='__main__':main()
