"""Bounded,receipted ACPDS TRAIN/VALID bay-union qualification;whole TEST closed."""
import argparse,csv,json,os,sys,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.region_letterbox import check_admitted_frames


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.partial');tmp.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');os.replace(tmp,p)


def prepare():
    state=read(ROOT/'data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    source='data/processed/acpds_development_v1/development_images.json';annotations='experiments/results/ACPDS-DEVELOPMENT-20261026T224240258641Z/development_annotations.json';roles='data/manifests/acpds_source_roles_v1.json'
    assert digest(ROOT/source)=='2e0705c8b1fa1089fff36be7ca663ca0e81fc05a92825f80775082eb8d3a13ed'
    assert digest(ROOT/annotations)=='39534723e30bd162d26eece35da63ce58f336ee92575fcda9f78ce9b536885fc'
    assert digest(ROOT/roles)=='aab4890c3697fb3ce9117ee9220def3ecd131b372d0cfb96dd2b433c8b9ede1f'
    manifest=read(ROOT/source);dev=read(ROOT/annotations);assert set(dev)=={'train','valid'}
    names={k:v['file_names'] for k,v in dev.items()};frames=sorted(manifest['frames'],key=lambda f:(f['role'],f['name'].casefold()))
    check_admitted_frames(frames,names);assert len(frames)==266 and manifest['final_members_accessed']==0
    now=datetime.now(timezone.utc);rid='ACPDS-REGION-DATA-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    snapshots={}
    for frame in frames:
        row=next((r for r in reversed(receipts) if r['source_id']=='SRC-DS-021' and r['local_path']==frame['image'] and r['sha256']==frame['image_sha256']),None)
        assert row is not None,frame['name'];snapshots[frame['image']]=row
    dump(out/'qualified_input_receipts.json',snapshots)
    marker='experiments/results/REGION-DATA-V2-20261027T054847435415Z/hash_phase_complete.json';pk=read(ROOT/marker)
    table='experiments/results/REGION-DATA-V2-20261027T054847435415Z/'+pk['table'];assert digest(ROOT/table)==pk['table_sha256']
    code=['scripts/prepare_acpds_region_data.py','src/smart_parking/region_letterbox.py','tests/test_region_letterbox.py','src/smart_parking/layout.py']
    inputs=[source,annotations,roles,marker,table,(out/'qualified_input_receipts.json').relative_to(ROOT).as_posix()]
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=174,source_ids=['SRC-DS-021','SRC-DS-001'],training_data_sources=['SRC-DS-021'],
        hypothesis='All explicitly admitted ACPDS TRAIN231/VALID35 images can yield role-safe,source-bound letterboxed RGB/bay-union/nonpadding arrays without touching TEST or admitting byte aliases.',
        source_manifest=source,development_annotations=annotations,role_manifest=roles,pklot_hash_table=table,frames=frames,
        publisher_names=names,input_hashes={f:digest(ROOT/f) for f in inputs},source_hashes={f:digest(ROOT/f) for f in code},
        protected_hashes=read(ROOT/'experiments/evidence/HEARTBEAT-20261027T093915Z/checks.json')['frozen_hashes_unchanged'],
        output_size=[256,144],rgb_fill=[124,116,104],RGB_resize='PIL bilinear',mask_resize='Native polygon raster then nearest-neighbor',
        coordinate_mapping='Use admitted native layout coordinates unchanged;publisher W-1/H-1 already applied',
        target='Union of supplied bay polygons,not exhaustive facility/occupancy truth;outside union not verified nonparking',
        validity='Nonpadding pixels only;not certainty of all real-image annotations',maximum_native_pixels=25000000,maximum_seconds=900,
        gates=dict(train_images=231,development_images=35,minimum_target_pixels=16,minimum_valid_foreground_fraction=.001,maximum_valid_foreground_fraction=.95,maximum_errors=0,maximum_aliases=0),
        preview_names=[f['name'] for f in frames if f['role']=='train'][:2],
        limits='Known exact byte aliases only;unacquired TEST hashes/near duplicates/date/location/pretraining overlap unknown. All27TEST andaliases closed;no freshfinal admission.',
        occupancy_labels_used_as_targets=False,neural_training=False)
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')))
    dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json',flush=True)


def run(path):
    import numpy as np
    from PIL import Image,ImageDraw
    from smart_parking.layout import validate_layout,union_mask
    from smart_parking.region_letterbox import letterbox_arrays
    path=Path(path).resolve();out=path.parent;p=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256']
    assert not(out/'run.json').exists() and p['source_hashes'].get(Path(__file__).resolve().relative_to(ROOT).as_posix())==digest(__file__)
    bound={**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}
    for f,h in bound.items():assert digest(ROOT/f)==h,f
    check_admitted_frames(p['frames'],p['publisher_names'])
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    state['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),maximum_seconds=900,
        resume_command='scripts/prepare_acpds_region_data.py --run '+path.relative_to(ROOT).as_posix())];dump(state_path,state)
    cache=ROOT/'data/processed/acpds_region_v1'/p['run_id'];cache.mkdir(parents=True,exist_ok=True)
    allowed={(ROOT/f['image']).resolve() for f in p['frames']};forbidden=[]
    def audit(event,args):
        if event.startswith('socket.'):forbidden.append(event);raise PermissionError('Region dataset qualification is offline')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            q=Path(os.fsdecode(args[0])).resolve()
            if (q.is_relative_to(ROOT/'data/raw') or q.suffix.casefold() in {'.jpg','.jpeg','.xml','.png'}) and q not in allowed and not q.is_relative_to(out):
                forbidden.append(str(q));raise PermissionError('Unadmitted raw/image access blocked')
    sys.addaudithook(audit);clock=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    def boundary():
        if (out/'CANCEL').exists() or time.perf_counter()-clock>900:raise InterruptedError('Cancelled/deadline;per-frame caches retained')
    try:
        hashes={};aliases=[]
        with (ROOT/p['pklot_hash_table']).open(encoding='utf-8',newline='') as f:pk_hashes={r['sha256'] for r in csv.DictReader(f)}
        assert len(pk_hashes)==12417
        for frame in p['frames']:
            boundary();image=ROOT/frame['image'];layout=ROOT/frame['layout'];assert image.resolve().is_relative_to(ROOT/'data/raw/acpds_official')
            assert layout.resolve().is_relative_to(ROOT/'data/processed/acpds_development_v1/layouts')
            assert digest(image)==frame['image_sha256'] and digest(layout)==frame['layout_sha256']
            h=frame['image_sha256'];hashes.setdefault(h,[]).append(frame['name'])
            if h in pk_hashes:aliases.append(dict(name=frame['name'],reason='Exact alias to known PKLot member'))
        for h,names in hashes.items():
            if len(names)>1:aliases.extend(dict(name=n,reason='Duplicate ACPDS development JPEG',sha256=h) for n in names)
        dump(out/'byte_qualification.json',dict(images_hashed=266,unique_hashes=len(hashes),aliases=aliases,pklot_hashes_compared=12417,TEST_bytes_acquired=0,transformed_aliases_checked=False))
        excluded={r['name'] for r in aliases};records=[];errors=[];previews=[];g=p['gates']
        for index,frame in enumerate(p['frames']):
            boundary();journal=out/f'completed_frame_{index:03}.json'
            if frame['name'] in excluded:continue
            if journal.exists():
                rec=read(journal);assert digest(ROOT/rec['cache'])==rec['cache_sha256'];records.append(rec)
                if frame['name'] in p['preview_names']:previews.append(frame['name'])
                continue
            try:
                with Image.open(ROOT/frame['image']) as source:
                    assert source.width*source.height<=p['maximum_native_pixels'],'Native pixel budget exceeded'
                    native_size=source.size;orientation=source.getexif().get(274,1);rgb=source.convert('RGB')
                raw=read(ROOT/frame['layout']);geometry={k:raw[k] for k in ['schema_version','camera_id','image_size','origin']}
                geometry['slots']=[dict(id=s['id'],polygon=s['polygon']) for s in raw['slots']]
                validate_layout(geometry,native_size);native=union_mask(geometry)
                image,mask,valid,transform=letterbox_arrays(rgb,native,tuple(p['output_size']),tuple(p['rgb_fill']))
                fraction=float(mask.sum()/valid.sum());assert int(mask.sum())>=g['minimum_target_pixels']
                assert g['minimum_valid_foreground_fraction']<=fraction<=g['maximum_valid_foreground_fraction'],'Degenerate target union'
                target=cache/f'frame_{index:03}.npz'
                if target.exists():target=cache/f'frame_{index:03}_resume_{datetime.now(timezone.utc).strftime("%H%M%S%f")}.npz'
                with target.open('xb') as f:np.savez_compressed(f,rgb=image,mask=mask,valid=valid)
                with np.load(target,allow_pickle=False) as saved:
                    assert np.array_equal(saved['rgb'],image) and np.array_equal(saved['mask'],mask) and np.array_equal(saved['valid'],valid)
                rec=dict(index=index,source_id='SRC-DS-021',name=frame['name'],role='train' if frame['role']=='train' else 'development',
                    publisher_role='train' if frame['role']=='train' else 'valid',camera_id=geometry['camera_id'],group_id='ACPDS|'+frame['name'],
                    image=frame['image'],image_sha256=frame['image_sha256'],layout=frame['layout'],layout_sha256=frame['layout_sha256'],
                    original_size=list(native_size),exif_orientation=orientation,slots=len(geometry['slots']),transform=transform,
                    valid_pixels=int(valid.sum()),target_pixels=int(mask.sum()),valid_foreground_fraction=fraction,
                    cache=target.relative_to(ROOT).as_posix(),cache_sha256=digest(target))
                dump(journal,rec);records.append(rec)
                if frame['name'] in p['preview_names']:
                    pixels=image.astype('float32')*.7;pixels[mask]=.5*pixels[mask]+.5*np.array([35,205,145]);pixels[~valid]=[90,95,105]
                    preview=Image.fromarray(pixels.clip(0,255).astype('uint8')).resize((768,432),Image.Resampling.NEAREST)
                    canvas=Image.new('RGB',(768,490),'#f7f8fa');canvas.paste(preview,(0,40));draw=ImageDraw.Draw(canvas)
                    draw.text((12,12),'ACPDS TRAIN '+frame['name']+' | supplied bay union;gray=padding',fill='#14283f')
                    draw.text((12,478),'Martin Marek / ACPDS, MIT (2021). Data sanity check,not model accuracy.',fill='#14283f')
                    png=out/f'qualification_train_{len(previews)}.png';canvas.save(png)
                    dump(png.with_suffix('.json'),dict(source_record=rec,png_sha256=digest(png),selection='First two lexicographic admitted TRAIN names;not representative accuracy sample'))
                    previews.append(frame['name'])
            except (ValueError,OSError,AssertionError) as error:errors.append(dict(name=frame['name'],role=frame['role'],error_type=type(error).__name__,error=str(error)))
            dump(out/'progress.json',dict(phase='native_geometry_and_letterbox_cache',images_completed=len(records),errors=len(errors),total=266))
            if (index+1)%40==0:print('Qualified',len(records),'of266,errors',len(errors),flush=True)
        counts=Counter(r['role'] for r in records)
        checks=dict(all_images_cached=len(records)==266,train_count=counts['train']==g['train_images'],development_count=counts['development']==g['development_images'],
            no_aliases=not aliases,no_errors=not errors,preview_count=len(previews)==2)
        assert not forbidden;normal_forbidden=list(forbidden)
        try:(ROOT/'data/raw/acpds_official/UNADMITTED_TEST_PROBE.JPG').read_bytes()
        except PermissionError:probe=True
        else:raise AssertionError('Unadmitted source read not blocked')
        for f,h in bound.items():assert digest(ROOT/f)==h,f
        for frame in p['frames']:
            assert digest(ROOT/frame['image'])==frame['image_sha256'] and digest(ROOT/frame['layout'])==frame['layout_sha256']
        manifest=cache/'manifest.json';dump(manifest,dict(run_id=p['run_id'],source_id='SRC-DS-021',protocol_sha256=digest(path),records=records,
            output_size=p['output_size'],target=p['target'],validity=p['validity'],requires_validity_mask=True,incompatible_with_unmasked_legacy_trainers=True,
            data_gate_passed=all(checks.values()),checks=checks,final_pixels_or_semantics_opened=False,new_final_groups_admitted=False))
        report=dict(run_id=p['run_id'],started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds_this_invocation=time.perf_counter()-clock,
            seed=p['seed'],protocol_sha256=digest(path),cached_images=len(records),role_counts=dict(counts),source_ids=p['source_ids'],training_data_sources=['SRC-DS-021'],
            native_sizes=dict(Counter(str(r['original_size']) for r in records)),foreground_fraction_min=min((r['valid_foreground_fraction'] for r in records),default=None),
            foreground_fraction_max=max((r['valid_foreground_fraction'] for r in records),default=None),cache_bytes=sum((ROOT/r['cache']).stat().st_size for r in records),
            aliases=aliases,errors=errors,checks=checks,data_gate_passed=all(checks.values()),manifest=manifest.relative_to(ROOT).as_posix(),manifest_sha256=digest(manifest),
            all_cache_roundtrips_exact=True,normal_forbidden_accesses=normal_forbidden,unadmitted_source_probe_blocked=probe,
            TEST_pixels_or_semantics_opened=False,models_trained=0,model_calls=0,source_downloads=0,occupancy_labels_used_as_targets=False,
            production_promoted=False,limitations=p['limits'],target=p['target'],validity=p['validity'])
        dump(out/'run.json',report);dump(ROOT/'models/acpds_region_dataset.json',report);dump(ROOT/'reports/acpds_region_dataset_latest.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='ACPDS admitted TRAIN/VALID derived region-data qualification,no accuracy',started_at=started,finished_at=report['finished_at'],source_ids='SRC-DS-021;SRC-DS-001',split_ids='AuthorTRAIN231/VALID35 only;wholeTEST27closed',configuration=path.relative_to(ROOT).as_posix(),architecture='Native polygonunion/letterboxedRGB256x144/booltarget/nonpaddingvalidity',random_seed=174,hardware='CPU/bounded perframe',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds_this_invocation'],evaluation_metrics=json.dumps(dict(images=len(records),counts=dict(counts),checks=checks,errors=errors,aliases=aliases,model_calls=0)),logs=out.relative_to(ROOT).as_posix(),code_revision_basis='5ba48b8 plus sealed derived-data sources',implementation_sha256=digest(__file__),conclusions='Data gate='+str(all(checks.values()))+';not region/occupancy/model accuracy')
        with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);assert p['run_id'] not in state['completed_run_ids'];state['completed_run_ids'].append(p['run_id']);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=p['run_id'];state['acpds_region_dataset']=report;dump(state_path,state)
        print(json.dumps({k:report[k] for k in ['run_id','cached_images','role_counts','native_sizes','errors','data_gate_passed','duration_seconds_this_invocation','manifest']}),flush=True)
    except BaseException as error:
        dump(out/('interrupted_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),dict(error_type=type(error).__name__,error=str(error),completed_run_counted=False));raise
    finally:
        state=read(state_path);state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args();run(args.run) if args.run else prepare()
