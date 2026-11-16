"""Bounded development-only image acquisition and geometry qualification."""
import argparse,csv,io,json,os,random,sys,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
from smart_parking.zip_members import image_member_span,validate_member_range,decode_jpeg_member
from smart_parking.layout import validate_layout
from PIL import Image,ImageDraw,ImageFont
RAW=ROOT/'data/raw/acpds_official/17da2c8b33055be8019483260f0efbcbdfda0478';ROLES=ROOT/'data/manifests/acpds_source_roles_v1.json'
DEV=ROOT/'experiments/results/ACPDS-DEVELOPMENT-20261026T224240258641Z/development_annotations.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare():
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs']
    now=datetime.now(timezone.utc);rid='ACPDS-IMAGES-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False);dev=read(DEV)
    selected=[dict(role='train',name=n) for n in sorted(random.Random(152).sample(dev['train']['file_names'],3))]+[dict(role='valid',name=n) for n in dev['valid']['file_names']]
    inv=read(RAW/'directory_inventory.json');allowed={'images/'+n for d in dev.values() for n in d['file_names']};network_bytes=sum(image_member_span('images/'+r['name'],allowed,inv)[2]-image_member_span('images/'+r['name'],allowed,inv)[1]+1 for r in selected)
    assert len(selected)==38 and network_bytes<65_000_000
    code=['scripts/acquire_acpds_development_images.py','src/smart_parking/zip_members.py','tests/test_zip_members.py','src/smart_parking/layout.py']
    inputs=[DEV,ROLES,RAW/'directory_inventory.json',RAW/'head.json',RAW/'publisher_visualize.py',RAW/'publisher_transforms.py',RAW/'publisher_loader.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=152,source_ids=['SRC-DS-021'],hypothesis='Declared development images can be acquired as exact ZIP ranges and mapped to finite image-bounded quadrilaterals without accessing any whole TEST member.',
        selected=selected,selection='All35publisher VALID plus3seed152TRAIN examples;before any image pixels',network_budget_bytes=network_bytes,maximum_seconds=300,maximum_member_bytes=8_000_000,
        coordinate_mapping='Publisher visualize.py multiplies normalized x by W-1,y by H-1. Retain raw orientation;no EXIF transpose.',class_convention='Publisher occupancy boolean True/1 means occupied;False/0 vacant. Author loader casts occupancy to int64;visualization maps True to red. Check TRAIN overlays before any model evaluation.',
        gates=['Exact admitted TRAIN/VALID member only;unchanged ETag/range/CRC/descriptor','All38 JPEG files decode at4000x3000 without orientation transform','All mapped quadrilaterals validate within image bounds','Original final reservation/protected files unchanged'],
        input_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},implementation_hashes={p:digest(ROOT/p) for p in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],model_calls=0,final_members_acquired=0)
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));dump(out/'implementation_sources.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in code});print(str(out/'protocol.json'))

def overlay(image,layout,path):
    canvas=image.copy();draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',35)
    for slot in layout['slots']:
        color='#ee3344' if slot['ground_truth_occupied'] else '#11cf55';points=[tuple(p) for p in slot['polygon']];draw.line(points+[points[0]],fill=color,width=7);draw.text(points[0],slot['id'],fill=color,font=font,stroke_width=1,stroke_fill='black')
    canvas.thumbnail((1200,900));result=Image.new('RGB',(1200,950),'#152333');result.paste(canvas,(0,50));d=ImageDraw.Draw(result);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);d.text((12,8),'ACPDS TRAIN / publisher polygons / red=True occupied; green=False vacant',font=font,fill='white');d.text((12,29),'Martin Marek (2021), MIT / supplied geometry; not model predictions',font=font,fill='white');result.save(path)

def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path);assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not (out/'run.json').exists() and digest(path)==read(out/'protocol_binding.json')['sha256']
    for f,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    s=read(ROOT/'data/automation_state.json');assert not s['active_training_jobs'] and not s['active_validation_jobs'];s['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),cancel_file=(out/'CANCEL').relative_to(ROOT).as_posix(),maximum_seconds=300)];dump(ROOT/'data/automation_state.json',s)
    start=datetime.now(timezone.utc);clock=time.perf_counter();dev=read(DEV);inv=read(RAW/'directory_inventory.json');head=read(RAW/'head.json');allowed={'images/'+n for d in dev.values() for n in d['file_names']};frames=[];received=0
    try:
        for selected in p['selected']:
            if (out/'CANCEL').exists() or time.perf_counter()-clock>p['maximum_seconds']:raise InterruptedError('Image acquisition cancelled/deadline')
            role,name=selected['role'],selected['name'];assert role in ('train','valid') and name in dev[role]['file_names']
            entry,begin,end=image_member_span('images/'+name,allowed,inv,p['maximum_member_bytes']);member=RAW/'member_ranges'/f'{name}.bin';imagepath=RAW/'images'/name;member.parent.mkdir(exist_ok=True);imagepath.parent.mkdir(exist_ok=True)
            if member.exists():raise FileExistsError('Prior member requires explicit resumable receipt verification,not overwrite')
            requested=datetime.now(timezone.utc).isoformat()
            with urllib.request.urlopen(urllib.request.Request(inv['archive_url'],headers={'User-Agent':'SmartParkingPBL/0.2','Range':f'bytes={begin}-{end}','If-Match':head['etag']}),timeout=30) as response:
                body=response.read(end-begin+2);validate_member_range(response.status,response.headers.get('Content-Range'),begin,end,inv['total_bytes'],body,response.headers.get('ETag'),head['etag'])
            member.write_bytes(body);received+=len(body);receipt('SRC-DS-021',member,inv['archive_url'],'Exact admitted development JPEG member range',request_started_at=requested,status=206,start=begin,end=end,total=inv['total_bytes'],etag=head['etag'],role=role)
            decoded=decode_jpeg_member(body,entry,p['maximum_member_bytes']);assert not imagepath.exists();imagepath.write_bytes(decoded);receipt('SRC-DS-021',imagepath,inv['archive_url'],'CRC-verified admitted development JPEG,not whole archive',member='images/'+name,role=role,derived_from=member.relative_to(ROOT).as_posix(),derived_from_sha256=digest(member))
            with Image.open(io.BytesIO(decoded)) as source:
                assert source.format=='JPEG' and source.size==(4000,3000) and source.getexif().get(274,1)==1
                image=source.convert('RGB')
            index=dev[role]['file_names'].index(name);polygons=dev[role]['rois_list'][index];labels=dev[role]['occupancy_list'][index]
            layout=dict(schema_version=1,camera_id='ACPDS-unique-view-'+name,image_size=list(image.size),origin='Author supplied normalized parking-space polygons,not segmentation predictions',slots=[dict(id=str(i),polygon=[[float(x)*(image.width-1),float(y)*(image.height-1)] for x,y in polygon],ground_truth_occupied=int(y)) for i,(polygon,y) in enumerate(zip(polygons,labels))])
            validate_layout(layout,image.size);layoutpath=out/'layouts'/(name+'.json');dump(layoutpath,layout)
            if role=='train':overlay(image,layout,out/(name+'.png'))
            frames.append(dict(role=role,name=name,image=imagepath.relative_to(ROOT).as_posix(),image_sha256=digest(imagepath),layout=layoutpath.relative_to(ROOT).as_posix(),layout_sha256=digest(layoutpath),width=image.width,height=image.height,slots=len(labels),occupied=sum(labels),exif_orientation=1))
            dump(out/'progress.json',dict(images_completed=len(frames),network_bytes=received,final_members_accessed=0))
        for f,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
        assert received==p['network_budget_bytes'] and len(frames)==38
        manifest=dict(source_id='SRC-DS-021',role_manifest_sha256=digest(ROLES),frames=frames,final_members_accessed=0);dump(out/'development_images.json',manifest)
        r=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=p['seed'],protocol_sha256=digest(path),development_images=(out/'development_images.json').relative_to(ROOT).as_posix(),development_images_sha256=digest(out/'development_images.json'),images_decoded=len(frames),train_images=3,valid_images=35,valid_labelled_spaces=sum(f['slots'] for f in frames if f['role']=='valid'),network_bytes=received,geometry_gate_passed=True,all_dimensions=[4000,3000],all_normalized_xy_to_wminus1_hminus1=True,train_overlay_review='Pending separate human/agent visual review;no model score here',final_members_acquired=0,final_pixels_or_semantics_opened=False,model_calls=0,production_promoted=False,limitations='Supplied polygons;annotation correctness beyond structural checks not established;correlated lots/unknown dates/pretraining overlap;no CCTV sequence or automatic-region accuracy')
        dump(out/'run.json',r);dump(ROOT/'models/acpds_image_qualification.json',r);dump(ROOT/'reports/acpds_images_latest.json',r)
        reg=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with reg.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
        row=dict(experiment_id=p['run_id'],run_type='Real development JPEG and ROI geometry qualification',started_at=r['started_at'],finished_at=r['finished_at'],source_ids='SRC-DS-021',split_ids='All35VALID+3seededTRAIN;wholeTESTclosed',configuration=path.relative_to(ROOT).as_posix(),architecture='Bounded ZIP/CRC and image-coordinate adapter',random_seed=152,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=r['duration_seconds'],evaluation_metrics=json.dumps(r),logs=out.relative_to(ROOT).as_posix(),checkpoints='No model',code_revision_basis='7fe5e3a plus sealed selective member adapter',implementation_sha256=digest(__file__),conclusions='Geometry/integrity only;no model score;TESTclosed')
        with reg.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        s=read(ROOT/'data/automation_state.json');s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];s['acpds_image_qualification']=r
        print(json.dumps(r,indent=2))
    except BaseException as e:
        dump(out/'interrupted.json',dict(error=type(e).__name__,detail=str(e),frames_completed=len(frames),completed_run_counted=False));s=read(ROOT/'data/automation_state.json');raise
    finally:s['active_validation_jobs']=[];dump(ROOT/'data/automation_state.json',s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');a=parser.parse_args();run(a.run) if a.run else prepare()
