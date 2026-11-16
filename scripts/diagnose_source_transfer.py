"""Cached paired development and in-sample fit diagnosis;never final testing."""
import csv,json,sys,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.prediction_changes import paired_changes
from train_occupancy_expansion import metrics
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    start=datetime.now(timezone.utc);rid='TRANSFER-DIAG-'+start.strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    state=read('data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    study=read('models/source_balanced_development_head.json');old=read('models/occupancy_expansion_candidate.json');prep=read('models/source_occupancy_crop_preparation.json')
    assert digest(ROOT/prep['manifest'])==prep['manifest_sha256'];data=read(prep['manifest'])
    warm=ROOT/study['warm_checkpoint'];last=ROOT/'experiments/results'/study['run_id']/'last_head.pt'
    assert digest(warm)==study['warm_checkpoint_sha256']
    paths=['scripts/diagnose_source_transfer.py','src/smart_parking/prediction_changes.py','scripts/train_occupancy_expansion.py']
    hashes={p:digest(ROOT/p) for p in paths};protected=study['protected_hashes']
    protocol=dict(run_id=rid,started_at=start.isoformat(),seed=129,source_ids=study['source_ids'],source_hashes=hashes,protected_hashes=protected,
        parent_study=study['run_id'],warm_checkpoint_sha256=digest(warm),last_head_sha256=digest(last),crop_manifest_sha256=prep['manifest_sha256'],
        hypothesis='Rejected transfer improved new-source TRAIN fit while worsening reused PKLot development,and paired identities expose which camera/date mistakes changed.',
        source_training_quality_bins=[12,24,48],maximum_seconds=180,scope='Cached development diagnosis plus explicitly IN-SAMPLE training fit;not final/new-source validation/night/live accuracy',
        gates=['All feature caches/checkpoints match frozen identities','PKLot development cohort exactly2028;training counts10104+16448',
            'Warm predictions match saved baseline','Paired corrected/regressed counts reconcile','No source images/labels/finals read or model parameters changed'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=rid,phase='cached paired/in-sample diagnosis')];dump('data/automation_state.json',state);timer=time.monotonic()
    try:
        import torch,numpy as np
        torch.set_num_threads(4);all_x=[];rows=[]
        for item in old['feature_cache_files']:
            assert digest(ROOT/item['path'])==item['sha256'];chunk=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True)
            all_x.append(chunk['features']);rows.extend(dict(r,source_id='SRC-DS-001') for r in chunk['rows'])
        by_file=defaultdict(list)
        for row in data['records']:by_file[row['crop_file']].append(row)
        assert len(study['feature_cache_files'])==len(data['chunks'])==517
        for feature,crops in zip(study['feature_cache_files'],data['chunks']):
            if (folder/'CANCEL').exists() or time.monotonic()-timer>180:raise InterruptedError('Bounded diagnosis cancelled')
            assert digest(ROOT/feature['path'])==feature['sha256'];chunk=torch.load(ROOT/feature['path'],map_location='cpu',weights_only=True)
            assert chunk['crop_sha256']==crops['sha256'];all_x.append(chunk['features']);rows.extend(by_file[crops['path']])
        x=torch.cat(all_x);labels=torch.tensor([r['label'] for r in rows]);assert len(x)==len(rows)==28580
        warm_bundle=torch.load(warm,map_location='cpu',weights_only=True);trained=torch.load(last,map_location='cpu',weights_only=True)
        heads=[{k[3:]:v for k,v in warm_bundle['state_dict'].items() if k.startswith('fc.')},trained['head']]
        predictions=[];losses=[];head=torch.nn.Linear(512,2)
        for weights in heads:
            head.load_state_dict(weights);head.eval()
            with torch.inference_mode():logits=head(x);predictions.append(torch.softmax(logits,dim=1)[:,1]);losses.append(torch.nn.functional.cross_entropy(logits,labels,reduction='none'))
        groups={name:[i for i,r in enumerate(rows) if predicate(r)] for name,predicate in {
            'pklot_training_in_sample':lambda r:r['source_id']=='SRC-DS-001' and r['role']=='train',
            'new_source_training_in_sample':lambda r:r['source_id']=='SRC-DS-018',
            'pklot_reused_development':lambda r:r['role']=='validation'}.items()}
        assert [len(groups[k]) for k in groups]==[10104,16448,2028]
        fits={}
        for name,indices in groups.items():
            fits[name]={}
            for h,title in enumerate(['warm','trained_epoch2']):
                fit=metrics([dict(label=rows[i]['label'],probability_occupied=float(predictions[h][i])) for i in indices])
                fits[name][title]=dict(fit,mean_cross_entropy=float(losses[h][indices].mean()))
        indices=groups['pklot_reused_development'];before=[dict(rows[i],probability_occupied=float(predictions[0][i])) for i in indices];after=[dict(rows[i],probability_occupied=float(predictions[1][i])) for i in indices]
        archived=read('experiments/results/'+study['run_id']+'/baseline_development_predictions.json')
        assert all(a['image_sha256']==b['image_sha256'] and a['slot_id']==b['slot_id'] and abs(a['probability_occupied']-b['probability_occupied'])<1e-7 for a,b in zip(archived,before))
        changes,overall=paired_changes(before,after);grouped={}
        for key in ['camera_id','date']:
            values=defaultdict(list)
            for row in changes:values[str(row[key])].append(row)
            grouped[key]=[dict(group=name,observations=len(v),regressed=sum(r['regressed'] for r in v),corrected=sum(r['corrected'] for r in v),
                new_false_vacant=sum(r['false_vacant_after'] and not r['false_vacant_before'] for r in v),removed_false_vacant=sum(r['false_vacant_before'] and not r['false_vacant_after'] for r in v)) for name,v in sorted(values.items())]
        quality={}
        for title,low,high in [('side12_to23',12,24),('side24_to47',24,48),('side48_or_more',48,float('inf'))]:
            ids=[i for i in groups['new_source_training_in_sample'] if low<=min(rows[i]['quality']['width'],rows[i]['quality']['height'])<high]
            quality[title]=dict(samples=len(ids),warm_training_errors=int(((predictions[0][ids]>=.5)!=labels[ids]).sum()),trained_training_errors=int(((predictions[1][ids]>=.5)!=labels[ids]).sum()))
        np.savez_compressed(folder/'in_sample_predictions.npz',warm=predictions[0].numpy(),trained=predictions[1].numpy(),labels=labels.numpy())
        with (folder/'observations.csv').open('x',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=list(changes[0]));writer.writeheader();writer.writerows(changes)
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**protected}.items()) and digest(warm)==protocol['warm_checkpoint_sha256'] and digest(last)==protocol['last_head_sha256']
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,paired_development=overall,grouped_changes=grouped,
            fit_metrics=fits,new_source_training_quality=quality,observations_sha256=digest(folder/'observations.csv'),
            findings=dict(new_source_in_sample_fit_improved=fits['new_source_training_in_sample']['trained_epoch2']['mean_cross_entropy']<fits['new_source_training_in_sample']['warm']['mean_cross_entropy'],
                reused_development_errors_worsened=overall['errors_after']>overall['errors_before']),
            limits='In-sample fit is not generalization accuracy;observed tradeoff does not isolate a causal mechanism;no new selection or promotion',
            diagnosis_gate_passed=True,parameters_modified=False,source_image_or_raw_label_files_read=0,final_images_or_labels_read=0)
        dump(folder/'run.json',report);dump('models/source_transfer_diagnostics.json',report)
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Cached paired development / IN-SAMPLE fit diagnosis;no new training/final score',started_at=protocol['started_at'],finished_at=report['finished_at'],source_ids='SRC-DS-001;SRC-DS-018',split_ids='Reused development2028;training10104+16448',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Frozen cached features;warm/trained linear heads',random_seed=129,hardware='CPU4threads',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(dict(paired_development=overall,findings=report['findings'])),logs=folder.relative_to(ROOT).as_posix(),code_revision_basis='55ce4bd plus sealed source snapshots',implementation_sha256=hashes[paths[0]],conclusions='Paired regression and in-sample fit evidence preserved;not independent accuracy or causal proof')
        with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read('data/automation_state.json');state['completed_run_ids'].append(rid);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,paired=overall,fit=fits,by_camera=grouped['camera_id']),indent=2))
    except BaseException as error:dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False));state=read('data/automation_state.json');raise
    finally:state['active_validation_jobs']=[];dump('data/automation_state.json',state)
if __name__=='__main__':main()
