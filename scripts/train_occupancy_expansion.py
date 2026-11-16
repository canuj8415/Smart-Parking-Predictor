"""One resumable, bounded frozen-ResNet head candidate; no final-data access."""
import argparse
import copy
import csv
import gc
import json
import sys
import time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.occupancy_expansion import member_name


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def metrics(rows):
    n=len(rows);empty=[r for r in rows if r['probability_occupied']<=.25]
    correct_empty=sum(r['label']==0 for r in empty)
    uncertain=sum(.25<r['probability_occupied']<.75 for r in rows)
    errors=sum(int(r['probability_occupied']>=.5)!=r['label'] for r in rows)
    return dict(samples=n,hard_errors=errors,hard_accuracy=1-errors/n,
        false_vacant=sum(r['label']==1 for r in empty),vacant_predictions=len(empty),
        correct_vacant_predictions=correct_empty,vacancy_precision=correct_empty/len(empty) if empty else None,
        uncertain=uncertain,uncertain_fraction=uncertain/n,
        false_occupied=sum(r['label']==0 and r['probability_occupied']>=.75 for r in rows))


def summary(rows):
    groups=defaultdict(list);cameras=defaultdict(list)
    for row in rows:
        groups[(row['camera_id'],row['date'])].append(row)
        cameras[row['camera_id']].append(row)
    return dict(overall=metrics(rows),per_date=[dict(camera_id=c,date=d,**metrics(g)) for (c,d),g in sorted(groups.items())],
        per_camera=[dict(camera_id=c,**metrics(g)) for c,g in sorted(cameras.items())])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume');args=parser.parse_args()
    state_path=ROOT/'data/automation_state.json';state=read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs'],'Another job is recorded active'
    manifest_path=ROOT/'data/manifests/occupancy_expansion_v1.json';manifest=read(manifest_path)
    final_path=ROOT/'data/manifests/pklot_fresh_final_v2.json';assert_holdout_closed(final_path,root=ROOT)
    original_path=ROOT/'models/checkpoints/occupancy_resnet18.pt'
    started=datetime.now(timezone.utc)
    paths=['scripts/train_occupancy_expansion.py','src/smart_parking/layout.py',
        'src/smart_parking/vision.py','src/smart_parking/occupancy_expansion.py']
    hashes={p:digest(ROOT/p) for p in paths}
    if args.resume:
        if Path(args.resume).name!=args.resume or not args.resume.startswith('OCCUPANCY-HEAD-'):
            raise ValueError('Resume requires an existing run ID')
        rid=args.resume;folder=ROOT/'experiments/results'/rid;protocol=read(folder/'protocol.json')
        assert not (folder/'run.json').exists(),'Completed experiment cannot be replayed under the same ID'
        assert protocol['source_hashes']==hashes
    else:
        rid='OCCUPANCY-HEAD-'+started.strftime('%Y%m%dT%H%M%S%fZ')
        folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
        protocol=dict(run_id=rid,started_at=started.isoformat(),seed=130,
            source_ids=['SRC-DS-001','SRC-MOD-003'],source_hashes=hashes,
            manifest_sha256=digest(manifest_path),closed_final_manifest_sha256=digest(final_path),
            original_checkpoint_sha256=digest(original_path),
            hypothesis='Adding explicitly labelled third-camera training crops and balancing camera/class strata improves development occupancy reliability without material regressions on other cameras/dates.',
            model='Original frozen ResNet18 backbone; warm-start original512to2linear occupancy head; no backbone updates',
            preprocessing='Existing polygon crop_slot96x96 and normalize_crop; no augmentation or fitted preprocessing',
            optimizer=dict(name='AdamW',learning_rate=.001,weight_decay=.001,batch_size=128),
            training_weight='Inverse training-only(camera,class)stratum frequency, normalized to mean1',
            epoch_selection='Lowest macro-camera unweighted validation cross-entropy; minimum decrease1e-4; patience6',
            max_epochs=50,patience=6,min_delta=.0001,wall_seconds_per_invocation=900,
            validation_gates=dict(overall_hard_accuracy_drop_max=.005,per_camera_drop_max=.01,
                per_date_drop_max=.025,no_overall_false_vacant_regression=True,
                retain_all_baseline_correct_confident_vacancies=True,
                fresh12_hard_errors_max_exclusive=17,fresh12_false_vacant_max=2,fresh12_uncertainty_fraction_max=.10),
            limitations=['Development selection/gates only, including reused validation dates; not final accuracy',
                'Missing occupancy labels excluded, not inferred from masks/absence',
                'Known cameras; no auto geometry/detector/segmentation accuracy claim',
                'Separate candidate only; no automatic app/default checkpoint promotion',
                'Final6photos/labels and all earlier consumed final groups are excluded'])
        dump(folder/'protocol.json',protocol)
        dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    assert digest(manifest_path)==protocol['manifest_sha256']
    assert digest(final_path)==protocol['closed_final_manifest_sha256']
    assert digest(original_path)==protocol['original_checkpoint_sha256']
    state['active_training_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'),
        resume_command='scripts/train_occupancy_expansion.py --resume '+rid,deadline_seconds=900)]
    dump(state_path,state);timer=time.perf_counter()
    def boundary():
        if (folder/'CANCEL').exists() or time.perf_counter()-timer>900:
            raise InterruptedError('Training candidate cancellation/deadline; cached features and last head retained')
    try:
        import torch
        from PIL import Image
        from torchvision.models import resnet18
        from smart_parking.layout import read_pklot_xml,crop_slot
        from smart_parking.vision import normalize_crop
        torch.manual_seed(130);torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
        bundle=torch.load(original_path,map_location='cpu',weights_only=True)
        backbone=resnet18(weights=None);backbone.fc=torch.nn.Linear(512,2)
        backbone.load_state_dict(bundle['state_dict']);backbone.eval()
        original_head=copy.deepcopy(backbone.fc).eval()
        backbone.fc=torch.nn.Identity()
        for parameter in backbone.parameters():parameter.requires_grad_(False)
        all_features=[];rows=[];feature_files=[]
        for frame_no,frame in enumerate(manifest['frames'],1):
            boundary()
            assert digest(ROOT/frame['image'])==frame['image_sha256']
            assert digest(ROOT/frame['annotation'])==frame['annotation_sha256']
            chunk_path=folder/'feature_chunks'/f'frame_{frame_no:03d}.pt'
            if chunk_path.exists():
                chunk=torch.load(chunk_path,map_location='cpu',weights_only=True)
                assert chunk['frame']==frame and chunk['manifest_sha256']==protocol['manifest_sha256']
                assert chunk['original_checkpoint_sha256']==protocol['original_checkpoint_sha256']
                assert chunk['source_hashes']==hashes
            else:
                with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
                layout=read_pklot_xml(ROOT/frame['annotation'],image.size)
                slots=[s for s in layout['slots'] if s['ground_truth_occupied'] is not None]
                assert len(slots)==frame['explicit_labels']
                values=[];frame_rows=[]
                for offset in range(0,len(slots),64):
                    boundary();batch=slots[offset:offset+64]
                    tensor=torch.stack([normalize_crop(crop_slot(image,s)) for s in batch])
                    with torch.inference_mode():values.append(backbone(tensor).clone())
                    frame_rows.extend(dict(role=frame['role'],camera_id=frame['camera_id'],date=frame['date'],
                        frame=frame['image'],source_member=frame['image_archive_member'],image_sha256=frame['image_sha256'],
                        annotation_sha256=frame['annotation_sha256'],slot_id=s['id'],label=s['ground_truth_occupied']) for s in batch)
                chunk=dict(frame=frame,rows=frame_rows,features=torch.cat(values) if values else torch.empty(0,512),
                    manifest_sha256=protocol['manifest_sha256'],original_checkpoint_sha256=protocol['original_checkpoint_sha256'],source_hashes=hashes)
                chunk_path.parent.mkdir(parents=True,exist_ok=True);torch.save(chunk,chunk_path)
            all_features.append(chunk['features']);rows.extend(chunk['rows'])
            feature_files.append(dict(path=chunk_path.relative_to(ROOT).as_posix(),sha256=digest(chunk_path)))
            if frame_no%10==0 or frame_no==len(manifest['frames']):
                dump(folder/'progress.json',dict(phase='frozen_feature_extraction',frames_completed=frame_no,
                    frames_total=len(manifest['frames']),labelled_crops=len(rows),elapsed_seconds=time.perf_counter()-timer))
                print(f'Frozen features {frame_no}/{len(manifest["frames"])}frames, {len(rows)}labelled crops',flush=True)
        features=torch.cat(all_features);del all_features;gc.collect()
        assert features.shape==(12132,512) and torch.isfinite(features).all()
        labels=torch.tensor([r['label'] for r in rows],dtype=torch.long)
        indices={role:torch.tensor([i for i,r in enumerate(rows) if r['role']==role]) for role in ['train','validation']}
        assert len(indices['train'])==10104 and len(indices['validation'])==2028
        assert not {r['date'] for r in rows if r['role']=='train'}&{r['date'] for r in rows if r['role']=='validation'}
        strata=Counter((rows[int(i)]['camera_id'],rows[int(i)]['label']) for i in indices['train'])
        assert len(strata)==6 and min(strata.values())>=10
        weights=torch.ones(len(rows))
        for i in indices['train']:
            row=rows[int(i)];weights[i]=len(indices['train'])/(len(strata)*strata[(row['camera_id'],row['label'])])
        assert abs(float(weights[indices['train']].mean())-1)<1e-5
        camera_indices={camera:torch.tensor([i for i,r in enumerate(rows) if r['role']=='validation' and r['camera_id']==camera])
            for camera in sorted({r['camera_id'] for r in rows if r['role']=='validation'})}
        assert len(camera_indices)==3 and all(len(v)>=20 for v in camera_indices.values())
        def predict(head):
            with torch.inference_mode():p=torch.softmax(head(features[indices['validation']]),dim=1)[:,1].tolist()
            return [dict(rows[int(i)],probability_occupied=value) for i,value in zip(indices['validation'],p)]
        baseline_rows=predict(original_head);baseline=summary(baseline_rows)
        dump(folder/'baseline_validation_predictions.json',baseline_rows)
        head=copy.deepcopy(original_head);head.train()
        optimizer=torch.optim.AdamW(head.parameters(),lr=.001,weight_decay=.001)
        start_epoch=0;best_loss=float('inf');best_epoch=0;stale=0;curves=[];best_head=None
        last_path=folder/'last_head.pt'
        if last_path.exists():
            last=torch.load(last_path,map_location='cpu',weights_only=True)
            assert last['manifest_sha256']==protocol['manifest_sha256'] and last['source_hashes']==hashes
            head.load_state_dict(last['head']);optimizer.load_state_dict(last['optimizer'])
            start_epoch=last['epoch'];best_loss=last['best_loss'];best_epoch=last['best_epoch'];stale=last['stale']
            best_head=last['best_head'];curves=last['curves'];torch.set_rng_state(last['torch_rng_state'])
        for epoch in range(start_epoch,protocol['max_epochs']):
            boundary();head.train();order=indices['train'][torch.randperm(len(indices['train']))];total=0.
            for batch in order.split(128):
                boundary();optimizer.zero_grad()
                loss=(torch.nn.functional.cross_entropy(head(features[batch]),labels[batch],reduction='none')*weights[batch]).mean()
                loss.backward();optimizer.step();total+=float(loss.detach())*len(batch)
            head.eval()
            with torch.inference_mode():
                validation=float(torch.stack([torch.nn.functional.cross_entropy(head(features[idx]),labels[idx]) for idx in camera_indices.values()]).mean())
            curves.append(dict(epoch=epoch+1,train_weighted_cross_entropy=total/len(order),validation_macro_camera_cross_entropy=validation))
            if validation<best_loss-protocol['min_delta']:
                best_loss=validation;best_epoch=epoch+1;stale=0;best_head=copy.deepcopy(head.state_dict())
                torch.save(best_head,folder/'best_head.pt')
            else:stale+=1
            torch.save(dict(epoch=epoch+1,head=head.state_dict(),optimizer=optimizer.state_dict(),best_head=best_head,
                best_loss=best_loss,best_epoch=best_epoch,stale=stale,curves=curves,torch_rng_state=torch.get_rng_state(),
                manifest_sha256=protocol['manifest_sha256'],source_hashes=hashes),last_path)
            dump(folder/'curves.json',curves)
            dump(folder/'progress.json',dict(phase='training_head',epoch=epoch+1,best_epoch=best_epoch,
                validation_macro_camera_cross_entropy=validation,elapsed_seconds=time.perf_counter()-timer))
            print(f'Head epoch{epoch+1}:validation macro loss{validation:.6f};best epoch{best_epoch}',flush=True)
            if stale>=protocol['patience']:break
        assert best_head is not None
        head.load_state_dict(best_head);head.eval()
        candidate_rows=predict(head);candidate=summary(candidate_rows)
        fresh_members={member_name(f['image']) for f in read('data/manifests/pklot_fresh_development_v1.json')['frames']}
        fresh_baseline=metrics([r for r in baseline_rows if r['source_member'] in fresh_members])
        fresh_candidate=metrics([r for r in candidate_rows if r['source_member'] in fresh_members])
        assert fresh_baseline['samples']==fresh_candidate['samples']==720 and fresh_baseline['hard_errors']==17
        base_dates={(r['camera_id'],r['date']):r for r in baseline['per_date']}
        base_cameras={r['camera_id']:r for r in baseline['per_camera']}
        checks=dict(overall_accuracy_noninferior=candidate['overall']['hard_accuracy']>=baseline['overall']['hard_accuracy']-.005,
            no_camera_material_regression=all(r['hard_accuracy']>=base_cameras[r['camera_id']]['hard_accuracy']-.01 for r in candidate['per_camera']),
            no_date_material_regression=all(r['hard_accuracy']>=base_dates[(r['camera_id'],r['date'])]['hard_accuracy']-.025 for r in candidate['per_date']),
            no_false_vacant_regression=candidate['overall']['false_vacant']<=baseline['overall']['false_vacant'],
            retains_correct_vacancies=candidate['overall']['correct_vacant_predictions']>=baseline['overall']['correct_vacant_predictions'],
            fresh_errors_improved=fresh_candidate['hard_errors']<17,
            fresh_false_vacant_noninferior=fresh_candidate['false_vacant']<=2,
            fresh_uncertainty_within_limit=fresh_candidate['uncertain_fraction']<=.10)
        checkpoint=ROOT/'models/checkpoints/occupancy_expansion'/rid/'candidate.pt';checkpoint.parent.mkdir(parents=True,exist_ok=True)
        backbone.fc=head
        torch.save(dict(state_dict=backbone.state_dict(),run_id=rid,classes=['vacant','occupied'],crop_size=96,seed=130,
            training='Frozen original ResNet18 features; expanded source/date-qualified camera-class-balanced linear head',
            original_checkpoint_sha256=protocol['original_checkpoint_sha256'],manifest_sha256=protocol['manifest_sha256']),checkpoint)
        reloaded=resnet18(weights=None);reloaded.fc=torch.nn.Linear(512,2)
        reloaded.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['state_dict']);reloaded.eval()
        # Actual serialized full-model route versus the cached-feature/head route.
        first=next(f for f in manifest['frames'] if f['role']=='validation' and f['explicit_labels']>=1)
        with Image.open(ROOT/first['image']) as source:image=source.convert('RGB')
        layout=read_pklot_xml(ROOT/first['annotation'],image.size)
        slot=next(s for s in layout['slots'] if s['ground_truth_occupied'] is not None)
        with torch.inference_mode():actual=float(torch.softmax(reloaded(normalize_crop(crop_slot(image,slot)).unsqueeze(0)),dim=1)[0,1])
        expected=next(r['probability_occupied'] for r in candidate_rows if r['source_member']==first['image_archive_member'] and r['slot_id']==slot['id'])
        assert abs(actual-expected)<1e-5
        assert digest(original_path)==protocol['original_checkpoint_sha256'] and digest(final_path)==protocol['closed_final_manifest_sha256']
        assert digest(manifest_path)==protocol['manifest_sha256'] and all(digest(ROOT/p)==h for p,h in hashes.items())
        assert_holdout_closed(final_path,root=ROOT)
        outcome=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.perf_counter()-timer,
            epochs_completed=len(curves),selected_epoch=best_epoch,early_stopped=len(curves)<50,
            training_crops=10104,validation_crops=2028,training_strata=[dict(camera_id=c,label=y,count=n) for (c,y),n in sorted(strata.items())],
            baseline=baseline,candidate=candidate,fresh12_baseline=fresh_baseline,fresh12_candidate=fresh_candidate,
            checks=checks,validation_gate_passed=all(checks.values()),candidate_checkpoint=checkpoint.relative_to(ROOT).as_posix(),
            candidate_checkpoint_sha256=digest(checkpoint),checkpoint_roundtrip_probability_delta=abs(actual-expected),
            feature_cache_files=feature_files,original_checkpoint_unchanged=True,production_promoted=False,final_images_or_labels_read=0,
            resumptions_this_invocation=bool(args.resume))
        dump(folder/'candidate_validation_predictions.json',candidate_rows)
        dump(folder/'run.json',outcome);dump(ROOT/'models/occupancy_expansion_candidate.json',outcome)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Expanded camera-balanced occupancy head training/development validation',
            started_at=protocol['started_at'],finished_at=outcome['finished_at'],source_ids='SRC-DS-001;SRC-MOD-003',
            split_ids='occupancy_expansion_v1:32train dates/12validation dates; all final dates excluded',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture=protocol['model'],
            model_version=outcome['candidate_checkpoint_sha256'],optimizer='AdamW',learning_rate=.001,epochs=len(curves),batch_size=128,
            random_seed=130,hardware='CPU/Torch4threads',execution_environment=sys.version.split()[0],
            training_duration=outcome['duration_seconds_this_invocation'],loss_curves=(folder/'curves.json').relative_to(ROOT).as_posix(),
            evaluation_metrics=json.dumps(dict(baseline=baseline['overall'],candidate=candidate['overall'],fresh=fresh_candidate,checks=checks)),
            logs=folder.relative_to(ROOT).as_posix(),checkpoints=outcome['candidate_checkpoint'],code_revision_basis='e1c6461 plus frozen expansion sources',
            implementation_sha256=hashes[paths[0]],conclusions='Development gate='+str(outcome['validation_gate_passed'])+'; final unused, original/app unchanged')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);assert rid not in state['completed_run_ids'];state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps({k:v for k,v in outcome.items() if k in {'run_id','baseline','candidate','fresh12_candidate','selected_epoch','epochs_completed','checks','validation_gate_passed'}},indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False,
            resume_command='scripts/train_occupancy_expansion.py --resume '+rid,features_and_last_head_preserved=True))
        state=read(state_path);raise
    finally:
        state['active_training_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
