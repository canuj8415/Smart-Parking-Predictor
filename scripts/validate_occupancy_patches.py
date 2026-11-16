"""One prespecified software equivalence/resource trial;no camera accuracy."""
import argparse,copy,csv,json,os,random,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    now=datetime.now(timezone.utc);rid='OCCUPANCY-PATCHES-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False);card=read(ROOT/'models/acpds_image_qualification.json');manifest=ROOT/card['development_images'];assert digest(manifest)==card['development_images_sha256'];frames=[f for f in read(manifest)['frames'] if f['role']=='train'];assert len(frames)==3
    code=['scripts/validate_occupancy_patches.py','scripts/occupancy_memory_worker.py','src/smart_parking/occupancy_patches.py','src/smart_parking/occupancy_fixtures.py','src/smart_parking/vision.py','src/smart_parking/layout.py','tests/test_occupancy_patches.py'];inputs=[manifest,*[ROOT/f['layout'] for f in frames],ROOT/'data/manifests/acpds_source_roles_v1.json']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=161,source_ids=['SRC-DS-021'],hypothesis='Reference-raster bounded slot patches preserve legacy occupancy assignments while reducing incremental memory on a fixed96slot software fixture.',
        prior_exposure='Six targeted fixtures passed before this protocol;real TRAIN geometry and prior classifier results already known. This is software validation,not unseen camera evaluation.',synthetic_cases=2000,geometry_frames=frames,geometry_slots_per_frame=8,maximum_seconds=180,
        gates=dict(all_outputs_exact=True,all_inputs_unmodified=True,isolated_large_fixture_hashes_equal=True,candidate_incremental_rss_fraction_max=.5,candidate_peak_rss_bytes_max=900*1024**2),
        resource_fixture='1920x1080/96spaces/24generatedboxes;both workers import same stack;sequential child processes;RSS sampled every2ms;60second child timeout/900MiB self cap;hidden windows',
        assumptions='Valid engine-shaped inputs;provided masks are original-sized boolean arrays. Missing lengths/duplicate IDs/invalid scores reject explicitly. Full-canvas rasterization retained. .12overlap and .25/.75uncertainty unchanged.',
        source_hashes={f:digest(ROOT/f) for f in code},input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in inputs},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        limits='Generated detections/probabilities and TRAIN geometry fixtures are not camera ground truth. No detector/classifier inference. Does not bound model inference,MaskRCNN postprocessing or already-produced dense instance masks. Original application unchanged.')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(str(out/'protocol.json'))

def run(path):
    from smart_parking.vision import assign_occupancy
    from smart_parking.occupancy_patches import assign_occupancy_patches
    from smart_parking.occupancy_fixtures import small_case
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not(out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    sp=ROOT/'data/automation_state.json';s=read(sp);assert not s['active_training_jobs'] and not s['active_validation_jobs'];s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix())];dump(sp,s);clock=time.perf_counter();start=datetime.now(timezone.utc).isoformat();done=0;geometry=[];workers=[]
    def boundary():
        if (out/'CANCEL').exists() or time.perf_counter()-clock>180:raise InterruptedError('Bounded software validation stopped')
    try:
        for i in range(p['synthetic_cases']):
            boundary();case=small_case(p['seed'],i);layout=copy.deepcopy(case[1]);ds=copy.deepcopy(case[2]);probs=copy.deepcopy(case[4]);expected=assign_occupancy(*case);actual=assign_occupancy_patches(*case)
            assert expected==actual,('Generated software output mismatch',i);assert layout==case[1] and ds==case[2] and probs==case[4];done+=1
        for frame in p['geometry_frames']:
            boundary();source=read(ROOT/frame['layout']);slots=[dict(id=r['id'],polygon=r['polygon']) for r in source['slots'][:8]];layout=dict(camera_id='providedTRAINgeometry-with-generated-detections',image_size=source['image_size'],slots=slots);ds=[]
            for i,slot in enumerate(slots):
                points=slot['polygon'];ds.append(dict(id=i,score=.85,box=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]))
            case=(tuple(source['image_size']),layout,ds,[None]*len(ds),[[.1,.25,.5,.75,.9][i%5] for i in range(len(slots))]);assert assign_occupancy(*case)==assign_occupancy_patches(*case);geometry.append(dict(image=frame['name'],slots=len(slots),outputs_exact=True,detections='Generated from ground polygon bounding boxes,not detector outputs',labels_used=False))
        for algorithm in ['reference','patches']:
            boundary();args=[sys.executable,str(ROOT/'scripts/occupancy_memory_worker.py'),'--algorithm',algorithm];process=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);(out/(algorithm+'_stdout.txt')).write_text(process.stdout,encoding='utf-8');(out/(algorithm+'_stderr.txt')).write_text(process.stderr,encoding='utf-8');assert process.returncode==0,('Isolated worker failed',algorithm,process.returncode);workers.append(json.loads(process.stdout))
        reference,candidate=workers;assert reference['observations_sha256']==candidate['observations_sha256'];checks=dict(generated_outputs_exact=done==2000,train_geometry_outputs_exact=len(geometry)==3,isolated_fixture_outputs_exact=True,incremental_peak_rss_reduced=candidate['incremental_peak_rss_bytes']<=.5*reference['incremental_peak_rss_bytes'],candidate_under900MiB=candidate['peak_rss_bytes']<=p['gates']['candidate_peak_rss_bytes_max'])
        for f,h in {**p['source_hashes'],**p['input_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        r=dict(run_id=p['run_id'],started_at=start,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=p['seed'],protocol_sha256=digest(path),synthetic_cases=done,train_geometry_cases=geometry,resource_workers=workers,checks=checks,implementation_gate_passed=all(checks.values()),incremental_rss_fraction=candidate['incremental_peak_rss_bytes']/max(1,reference['incremental_peak_rss_bytes']),slot_storage_fraction=candidate['slot_boolean_bytes']/reference['slot_boolean_bytes'],model_calls=0,real_camera_accuracy_evaluated=False,final_pixels_or_labels_opened=False,production_behavior_changed=False,limits=p['limits']);dump(out/'run.json',r);dump(ROOT/'models/occupancy_patch_validation.json',r);dump(ROOT/'reports/occupancy_patch_latest.json',r)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Software occupancy assignment equivalence and isolated resource validation',started_at=start,finished_at=r['finished_at'],source_ids='SRC-DS-021 geometry only;generated software fixtures',split_ids='2000synthetic+3TRAINgeometry+isolatedfixedfixture;no final',configuration=path.relative_to(ROOT).as_posix(),architecture='Original-raster bounded slot bitmaps',random_seed=161,hardware='CPU/sequential isolated workers',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(r),logs=out.relative_to(ROOT).as_posix(),checkpoints='No model',code_revision_basis='28b1f95 plus sealed patch-assignment candidate',implementation_sha256=digest(__file__),conclusions='Implementation gate='+str(r['implementation_gate_passed'])+';no neural/camera accuracy;original app unchanged')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(sp);s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['occupancy_patch_validation']=r;dump(sp,s);print(json.dumps(r,indent=2))
    except BaseException as e:dump(out/'interrupted.json',dict(error=type(e).__name__,detail=str(e),generated_cases_completed=done,completed_run_counted=False));raise
    finally:s=read(sp);s['active_validation_jobs']=[];dump(sp,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
