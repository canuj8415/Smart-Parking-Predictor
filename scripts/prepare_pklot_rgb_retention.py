"""Routine RGB preparation with paired pixel and development-role checks."""
import json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.layout import read_pklot_xml,crop_slot
from smart_parking.exact_crops import crop_slot_exact
OUT=ROOT/'data/processed/pklot_rgb_retention_v1';PLAN=ROOT/'data/manifests/pklot_rgb_retention_plan_v1.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    import numpy as np,torch
    from PIL import Image
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];assert not (OUT/'manifest.json').exists()
    manifest=ROOT/'data/manifests/occupancy_expansion_v1.json';card=ROOT/'models/occupancy_expansion_candidate.json';claims=sorted((ROOT/'data/holdout_claims').glob('*.claim.json'));source=read(manifest);old=read(card);consumed={tuple(g) for c in claims for g in read(c).get('source_groups',[])};OUT.mkdir(parents=True,exist_ok=True)
    if not PLAN.exists():dump(PLAN,dict(prepared_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-001',purpose='Routine old-source RGB preparation for one representation trial;no added experiment per image/crop',input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in [manifest,card,*claims]},source_hashes={p:digest(ROOT/p) for p in ['scripts/prepare_pklot_rgb_retention.py','src/smart_parking/exact_crops.py','src/smart_parking/layout.py']},maximum_seconds=300,consumed_groups=sorted(consumed)))
    p=read(PLAN)
    for f,h in {**p['input_hashes'],**p['source_hashes']}.items():assert digest(ROOT/f)==h,f
    s['active_validation_jobs']=[dict(kind='Routine PKLot RGB retention preparation',pid=os.getpid(),cancel_file=(OUT/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/prepare_pklot_rgb_retention.py')];dump(ROOT/'data/automation_state.json',s);clock=time.perf_counter();records=[];chunks=[]
    try:
        assert len(source['frames'])==len(old['feature_cache_files'])==215
        for index,(frame,feature) in enumerate(zip(source['frames'],old['feature_cache_files'])):
            if (OUT/'CANCEL').exists() or time.perf_counter()-clock>300:raise InterruptedError('Bounded preparation stopped;completed chunks preserved')
            assert frame['role'] in ('train','validation') and (frame['camera_id'],frame['date']) not in consumed;assert digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['annotation'])==frame['annotation_sha256'] and digest(ROOT/feature['path'])==feature['sha256']
            rows=torch.load(ROOT/feature['path'],map_location='cpu',weights_only=True)['rows'];assert all(r['frame']==frame['image'] and r['role']==frame['role'] and r['camera_id']==frame['camera_id'] and r['date']==frame['date'] for r in rows)
            cache=OUT/f'frame_{index:03d}.npz';proof=OUT/f'frame_{index:03d}.json'
            if proof.exists():
                saved=read(proof);assert saved['plan_sha256']==digest(PLAN) and saved['feature_sha256']==feature['sha256'] and digest(cache)==saved['chunk']['sha256'];records.extend(saved['records']);chunks.append(saved['chunk']);continue
            with Image.open(ROOT/frame['image']) as image:image=image.convert('RGB')
            layout=read_pklot_xml(ROOT/frame['annotation'],image.size);slots={slot['id']:slot for slot in layout['slots']};crops=[];kept=[]
            for n,row in enumerate(rows):
                slot=slots[row['slot_id']];assert slot['ground_truth_occupied']==row['label'] and row['label'] in (0,1);a=np.asarray(crop_slot_exact(image,slot));b=np.asarray(crop_slot(image,slot));assert np.array_equal(a,b),'Exact crop mismatch'
                crops.append(a.copy());kept.append(dict(row,source_id='SRC-DS-001',crop_file=cache.relative_to(ROOT).as_posix(),crop_index=n))
            with cache.with_suffix('.partial').open('wb') as f:np.savez_compressed(f,crops=np.stack(crops),labels=np.array([r['label'] for r in kept],dtype=np.int8))
            os.replace(cache.with_suffix('.partial'),cache)
            with np.load(cache,allow_pickle=False) as arrays:assert np.array_equal(arrays['crops'],np.stack(crops)) and arrays['labels'].tolist()==[r['label'] for r in kept]
            chunk=dict(path=cache.relative_to(ROOT).as_posix(),sha256=digest(cache),rows=len(kept),bytes=cache.stat().st_size);dump(proof,dict(plan_sha256=digest(PLAN),feature_sha256=feature['sha256'],records=kept,chunk=chunk,pixel_mismatches=0));chunks.append(chunk);records.extend(kept)
            if (index+1)%40==0:print('PKLot RGB frames',index+1,'/215',flush=True)
            dump(OUT/'progress.json',dict(images_completed=index+1,total_images=215,rows=len(records),elapsed_seconds=time.perf_counter()-clock))
        assert len(records)==12132 and sum(r['role']=='train' for r in records)==10104 and sum(r['role']=='validation' for r in records)==2028
        for f,h in {**p['input_hashes'],**p['source_hashes']}.items():assert digest(ROOT/f)==h,f
        result=dict(completed_at=datetime.now(timezone.utc).isoformat(),plan_sha256=digest(PLAN),source_manifest_sha256=digest(manifest),chunks=chunks,records=records,training_rows=10104,validation_rows=2028,consumed_groups_excluded=True,pixel_mismatches=0,model_calls=0,completed_experiment_count_added=0,duration_seconds=time.perf_counter()-clock);dump(OUT/'manifest.json',result);dump(ROOT/'reports/pklot_rgb_retention_latest.json',dict(manifest=(OUT/'manifest.json').relative_to(ROOT).as_posix(),manifest_sha256=digest(OUT/'manifest.json'),**{k:v for k,v in result.items() if k not in ('records','chunks')}));print(json.dumps({k:v for k,v in result.items() if k not in ('records','chunks')}))
    except BaseException as e:dump(OUT/'interrupted.json',dict(error=type(e).__name__,detail=str(e),completed_experiment_count_added=0));raise
    finally:s=read(ROOT/'data/automation_state.json');s['active_validation_jobs']=[];dump(ROOT/'data/automation_state.json',s)

if __name__=='__main__':main()
