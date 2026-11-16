"""One bounded real/synthetic equivalence trial;publish cache only on pass."""
import argparse,csv,hashlib,json,math,os,random,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
MANIFEST=ROOT/'data/processed/acpds_development_v1/development_images.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    now=datetime.now(timezone.utc);rid='EXACT-CROP-CACHE-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False);data=read(MANIFEST);assert len(data['frames'])==266
    inputs=[MANIFEST,ROOT/'data/manifests/acpds_source_roles_v1.json',ROOT/'models/acpds_balanced_head.json'];candidate=read(inputs[-1]);inputs.append(ROOT/candidate['candidate_checkpoint'])
    code=['scripts/validate_exact_crop_cache.py','src/smart_parking/local_crops.py','src/smart_parking/layout.py','tests/test_local_crops.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=157,source_ids=['SRC-DS-021'],hypothesis='Translating already validated polygons into a local bounding mask gives exactly the existing grey-masked96RGB crop with substantially less work than a full-frame allocation.',
        prior_exposure='Five unit tests/50small seeded fixture cases already passed before this protocol. All development geometry and earlier classifier outcomes known;this is implementation equivalence/performance validation,not a new model benchmark.',
        frames=data['frames'],synthetic_cases=2000,maximum_invocation_seconds=900,expected_real_images=266,expected_real_slots=9746,
        synthetic_distribution='Seed157;positive integer and fractional convex quadrilaterals/rectangles,near image edges,thin or full-frame rectangles;RGB teaching fixtures,not parking truth',
        timing='perf_counter_ns around crop functions only;alternate which method runs first by slot/image parity. Image decoding,hashing,NPZ encoding excluded;CPU local process timings,not deployment inference latency.',
        gates=dict(all_synthetic_byte_equal=True,all_real_byte_equal=True,real_reference_to_local_time_ratio_min=2.,all_cache_roundtrips_exact=True,all_source_and_protected_bindings_unchanged=True),
        input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},source_hashes={f:digest(ROOT/f) for f in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        cache_root='data/processed/acpds_exact_crop_cache_v1/'+rid,output_size=96,model_calls=0,final_access=False,production_behavior_changed=False,
        limitations='Exactness demonstrated only for tested validated RGB polygons and observed cohorts;no universal accuracy/perfection or arbitrary invalid/mode semantics. Supplied bay geometry,not learned segmentation. No TEST/consumed-final image or label access.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(str(out/'protocol.json'))

def run(path):
    import numpy as np
    from PIL import Image
    from smart_parking.layout import crop_slot,load_layout
    from smart_parking.local_crops import crop_slot_local
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not (out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    for name,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/name)==h,name
    statepath=ROOT/'data/automation_state.json';s=read(statepath);assert not s['active_training_jobs'] and not s['active_validation_jobs'];s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/validate_exact_crop_cache.py --run '+path.relative_to(ROOT).as_posix())];dump(statepath,s)
    start=datetime.now(timezone.utc);clock=time.perf_counter();root=ROOT/p['cache_root'];root.mkdir(parents=True,exist_ok=True);rng=random.Random(p['seed']);reference_ns=0;local_ns=0;box_fraction_sum=0.;records=[];chunks=[];real_count=0
    def boundary():
        if (out/'CANCEL').exists() or time.perf_counter()-clock>p['maximum_invocation_seconds']:raise InterruptedError('Bounded crop validation stopped;completed frame proofs retained')
    try:
        synthetic_done=0
        for i in range(p['synthetic_cases']):
            boundary();w=rng.randint(8,240);h=rng.randint(8,190);array=np.random.default_rng(p['seed']+i).integers(0,256,(h,w,3),dtype=np.uint8);image=Image.fromarray(array);left=rng.uniform(0,w-2);top=rng.uniform(0,h-2);right=rng.uniform(left+.01,w-1);bottom=rng.uniform(top+.01,h-1)
            if i%5==0:points=[[0,0],[w-1,0],[w-1,h-1],[0,h-1]]
            elif i%3==0:points=[[int(left),int(top)],[int(right),int(top)],[int(right),int(bottom)],[int(left),int(bottom)]]
            else:points=[[left,top],[right,top+(bottom-top)*.13],[right-(right-left)*.08,bottom],[left,top+(bottom-top)*.91]]
            slot=dict(polygon=points)
            if crop_slot(image,slot).tobytes()!=crop_slot_local(image,slot).tobytes():raise AssertionError('Synthetic byte mismatch case'+str(i))
            synthetic_done+=1
        for index,frame in enumerate(p['frames']):
            boundary();assert frame['role'] in ('train','validation') and digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['layout'])==frame['layout_sha256'];cache=root/f'frame_{index:03d}.npz';proof=root/f'frame_{index:03d}.json';layout=load_layout(ROOT/frame['layout'])
            if proof.exists():
                saved=read(proof);assert saved['protocol_sha256']==digest(path) and saved['frame']==frame and digest(cache)==saved['cache_sha256'] and saved['pixel_mismatches']==0
                with np.load(cache,allow_pickle=False) as arrays:
                    assert arrays['crops'].shape==(len(layout['slots']),96,96,3) and arrays['labels'].tolist()==[slot['ground_truth_occupied'] for slot in layout['slots']]
                    for a,row in zip(arrays['crops'],saved['records']):assert hashlib.sha256(a.tobytes()).hexdigest()==row['crop_rgb_sha256']
                records.extend(saved['records']);chunks.append(saved['chunk']);reference_ns+=saved['reference_ns'];local_ns+=saved['local_ns'];real_count+=len(layout['slots']);box_fraction_sum+=saved['box_fraction_sum'];continue
            assert not cache.exists(),'Incomplete unproved cache preserved;use a new explicit recovery path'
            with Image.open(ROOT/frame['image']) as source:image=source.convert('RGB')
            crops=[];rows=[];ref_frame=0;local_frame=0;box_frame=0.
            for j,slot in enumerate(layout['slots']):
                boundary()
                if (index+j)%2:
                    timer=time.perf_counter_ns();fast=crop_slot_local(image,slot);local_frame+=time.perf_counter_ns()-timer;timer=time.perf_counter_ns();reference=crop_slot(image,slot);ref_frame+=time.perf_counter_ns()-timer
                else:
                    timer=time.perf_counter_ns();reference=crop_slot(image,slot);ref_frame+=time.perf_counter_ns()-timer;timer=time.perf_counter_ns();fast=crop_slot_local(image,slot);local_frame+=time.perf_counter_ns()-timer
                expected=np.asarray(reference);actual=np.asarray(fast)
                if not np.array_equal(expected,actual):
                    dump(out/'pixel_mismatch.json',dict(image=frame['name'],slot_id=slot['id'],differing_channels=int((expected!=actual).sum()),label_used_for_comparison=False));raise AssertionError('Real source crop bytes differ')
                points=slot['polygon'];bw=min(image.width,math.ceil(max(x for x,y in points))+1)-max(0,math.floor(min(x for x,y in points)));bh=min(image.height,math.ceil(max(y for x,y in points))+1)-max(0,math.floor(min(y for x,y in points)));box_frame+=bw*bh/(image.width*image.height);crops.append(actual.copy());rows.append(dict(role=frame['role'],source_id='SRC-DS-021',image=frame['name'],image_sha256=frame['image_sha256'],layout_sha256=frame['layout_sha256'],slot_id=slot['id'],label=slot['ground_truth_occupied'],crop_rgb_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),crop_file=cache.relative_to(ROOT).as_posix(),crop_index=j))
            with cache.with_suffix('.partial').open('wb') as f:np.savez_compressed(f,crops=np.stack(crops),labels=np.array([r['label'] for r in rows],dtype=np.int8))
            os.replace(cache.with_suffix('.partial'),cache)
            with np.load(cache,allow_pickle=False) as arrays:assert np.array_equal(arrays['crops'],np.stack(crops)) and arrays['labels'].tolist()==[r['label'] for r in rows]
            chunk=dict(path=cache.relative_to(ROOT).as_posix(),sha256=digest(cache),rows=len(rows),bytes=cache.stat().st_size);dump(proof,dict(protocol_sha256=digest(path),frame=frame,cache_sha256=digest(cache),records=rows,chunk=chunk,pixel_mismatches=0,reference_ns=ref_frame,local_ns=local_frame,box_fraction_sum=box_frame));records.extend(rows);chunks.append(chunk);reference_ns+=ref_frame;local_ns+=local_frame;box_fraction_sum+=box_frame;real_count+=len(rows)
            dump(out/'progress.json',dict(phase='exact_real_crops',images_completed=index+1,total_images=266,real_crops=real_count,synthetic_fixtures=synthetic_done,elapsed_seconds=time.perf_counter()-clock,pixel_mismatches=0,resume_available=True))
            if (index+1)%25==0:print('Exact crop images',index+1,'/266;slots',real_count,flush=True)
        assert len(chunks)==266 and len(records)==real_count==9746 and synthetic_done==2000
        for name,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/name)==h,name
        ratio=reference_ns/local_ns;gate=ratio>=p['gates']['real_reference_to_local_time_ratio_min'];cachemanifest=dict(run_id=p['run_id'],protocol_sha256=digest(path),source_manifest_sha256=digest(MANIFEST),chunks=chunks,records=records,exact_reference_verified=True,final_pixels_or_labels_opened=False);dump(root/'cache_manifest.json',cachemanifest)
        r=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.perf_counter()-clock,seed=p['seed'],protocol_sha256=digest(path),real_images=266,real_crops=9746,synthetic_fixture_cases=2000,pixel_mismatches=0,all_cache_roundtrips_exact=True,reference_crop_seconds=reference_ns/1e9,local_crop_seconds=local_ns/1e9,reference_to_local_time_ratio=ratio,mean_local_box_fraction_of_full_image=box_fraction_sum/real_count,implementation_gate_passed=gate,cache_manifest=(root/'cache_manifest.json').relative_to(ROOT).as_posix(),cache_manifest_sha256=digest(root/'cache_manifest.json'),cached_rgb_bytes=sum(c['bytes'] for c in chunks),training_rows=sum(r['role']=='train' for r in records),validation_rows=sum(r['role']=='validation' for r in records),model_calls=0,final_pixels_or_labels_opened=False,original_layout_implementation_unchanged=True,production_behavior_changed=False,scientific_accuracy_evaluated=False,limitations=p['limitations'])
        dump(out/'run.json',r);dump(ROOT/'models/exact_crop_cache_validation.json',r)
        if gate:dump(ROOT/'reports/acpds_exact_crop_cache_latest.json',r)
        reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Real development and synthetic crop byte equivalence/performance validation',started_at=r['started_at'],finished_at=r['finished_at'],source_ids='SRC-DS-021',split_ids='All266admitteddevelopment images/9746spaces;TESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture='Equivalent local RGB polygon allocation',random_seed=157,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(r),logs=out.relative_to(ROOT).as_posix(),checkpoints='No model;validated crop cache',code_revision_basis='43f474b plus sealed equivalent crop helper',implementation_sha256=digest(__file__),conclusions='Pixel/cache/performance gate='+str(gate)+';not model accuracy;original application unchanged')
        with reg.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(statepath);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['exact_crop_cache_validation']=r;dump(statepath,s);print(json.dumps(r,indent=2))
    except BaseException as e:
        dump(out/'interrupted.json',dict(error=type(e).__name__,detail=str(e),real_crops_completed=real_count,completed_run_counted=False,resume_command='scripts/validate_exact_crop_cache.py --run '+path.relative_to(ROOT).as_posix()));raise
    finally:s=read(statepath);s['active_validation_jobs']=[];dump(statepath,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
