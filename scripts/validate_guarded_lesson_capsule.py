"""Sealed portable lesson13 payload,ZIP relocation and guarded-kernel acceptance."""
import argparse,csv,hashlib,importlib.metadata,io,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from capsule_payload import MANIFEST,digest,verify_payload,create_zip,extract_checked,safe_names
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.partial');tmp.write_bytes((json.dumps(v,indent=2)+'\n').encode());os.replace(tmp,p)


def prepare():
    state=read(ROOT/'data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    binding='data/manifests/guarded_region_lesson_v1.json';lesson=read(ROOT/binding)
    now=datetime.now(timezone.utc);rid='GUARDED-LESSON-CAPSULE-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    inputs=['notebooks/13_guarded_multisource_segmentation.ipynb',binding,*lesson['inputs'],'docs/source_evidence/acpds_20261026/LICENSE','data/source_manifest.csv']
    code=['scripts/validate_guarded_lesson_capsule.py','scripts/run_guarded_lesson_capsule.py','scripts/capsule_lesson_guard.py','scripts/capsule_payload.py','scripts/offline_jupyter_guard.py','tests/test_capsule_boundary.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=186,source_ids=lesson['source_ids'],
        hypothesis='The exact archived lesson executes from its own ZIP-relocated payload with original-project reads denied,unchanged hashes andno raw/model/final/private-runtime members.',
        input_hashes={name:digest(ROOT/name) for name in inputs},source_hashes={name:digest(ROOT/name) for name in code},
        source_notebook=inputs[0],source_binding=binding,maximum_seconds=600,maximum_payload_bytes=50000000,
        output_base='outputs/guarded_lesson_capsules/'+rid,
        runtime=dict(python=sys.version.split()[0],packages={p:importlib.metadata.version(p) for p in ['nbformat','nbclient','ipykernel','ipython','jupyter_client']},included_in_payload=False),
        gates=dict(exact_payload_and_zip=True,CRC_and_member_hashes=True,relocated_code_cells=5,relocated_inline_PNGs=2,archived_inputs=6,
            file_denial_probes=4,network_denial_probes=1,original_project_fallback_denied=True,local_copied_helpers=True,
            payload_unchanged_after_kernel=True,private_runtime_excluded=True,complete_source_attribution=True),
        no_model_training=True,no_new_accuracy=True,scope='Actual local relocated Jupyter/Python audits and ZIP integrity;not OS isolation,physical/new-machine/browser/student-mastery acceptance',
        retry_policy='Completed trial refuses rerun;incomplete attempt preserved and retry uses a new attempt directory under same run;no count until full acceptance',
        run_definition='One completed portable lesson validation trial,not a run per file,cell,probe or frame')
    dump(out/'protocol.json',p);dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')))
    dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});print(out/'protocol.json',flush=True)


def run(path):
    import psutil
    path=Path(path).resolve();out=path.parent;p=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and not(out/'run.json').exists()
    assert digest(path)==read(out/'protocol_binding.json')['sha256'] and p['source_hashes'][Path(__file__).resolve().relative_to(ROOT).as_posix()]==digest(__file__)
    bound={**p['input_hashes'],**p['source_hashes']}
    for name,expected in bound.items():assert digest(ROOT/name)==expected,name
    state_path=ROOT/'data/automation_state.json';state=read(state_path);assert not state['active_training_jobs'] and not state['active_validation_jobs']
    stamp=datetime.now(timezone.utc).strftime('%H%M%S%f');base=ROOT/p['output_base']/('attempt_'+stamp);base.mkdir(parents=True,exist_ok=False)
    state['active_validation_jobs']=[dict(run_id=p['run_id'],pid=os.getpid(),phase='Payload/ZIP relocation/guarded Jupyter',maximum_seconds=600,
        cancel_file=(base/'execution/CANCEL').relative_to(ROOT).as_posix(),resume_command='scripts/validate_guarded_lesson_capsule.py --run '+path.relative_to(ROOT).as_posix())];dump(state_path,state)
    started=datetime.now(timezone.utc).isoformat();clock=time.monotonic();private_runtime=base/'private_runtime';cleanup=[]
    def boundary():
        if time.monotonic()-clock>p['maximum_seconds'] or (out/'CANCEL').exists():raise InterruptedError('Capsule validation cancelled/deadline')
    def cleanup_owned_kernels():
        for process in psutil.process_iter(['pid','cmdline']):
            try:
                args=process.info['cmdline'] or []
                if 'ipykernel_launcher' not in args or '-f' not in args:continue
                connection=Path(args[args.index('-f')+1]).resolve()
                if connection.is_relative_to(private_runtime.resolve()) and connection.name.startswith('kernel-'):
                    process.terminate();process.wait(timeout=10);cleanup.append(process.pid)
            except (psutil.NoSuchProcess,psutil.AccessDenied,psutil.TimeoutExpired,ValueError,IndexError):continue
    try:
        boundary();payload=base/'payload';payload.mkdir();binding=read(ROOT/p['source_binding'])
        copies={p['source_notebook']:p['source_notebook'],p['source_binding']:p['source_binding'],**{name:name for name in binding['inputs']},
            **{name:name for name in ['scripts/run_guarded_lesson_capsule.py','scripts/capsule_lesson_guard.py','scripts/capsule_payload.py','scripts/offline_jupyter_guard.py']},
            'legal/ACPDS_MIT_LICENSE.txt':'docs/source_evidence/acpds_20261026/LICENSE'}
        safe_names(list(copies))
        for destination,source in copies.items():
            target=payload/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,target)
            assert digest(target)==bound.get(source,digest(ROOT/source))
        with (ROOT/'data/source_manifest.csv').open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;records=[row for row in reader if row['source_id'] in p['source_ids']]
        assert len(records)==3
        text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(records)
        (payload/'legal/source_records.csv').write_bytes(text.getvalue().encode())
        attribution='''# Source attribution for archived lesson13

PKLot / Almeida et al.; UFPR,2015. Publisher source:
https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/
Recorded licence CC BY4.0: https://creativecommons.org/licenses/by/4.0/ .
Included figures resize admitted DEVELOPMENT images andrender supplied bay polygons,
predicted masks andmetric labels. Original dataset files andweights are notincluded.

ACPDS / Martin Marek,Image-Based Parking Space Occupancy Classification:Dataset and
Baseline,2021,arXiv2107.12207: https://arxiv.org/abs/2107.12207 .
Official repository https://github.com/martin-marek/parking-space-occupancy ,pinned
17da2c8b33055be8019483260f0efbcbdfda0478. Authorpaper explicitly includes dataset/code/
models inMITgrant;Copyright(c)2021MartinMarek andfullMITnotice retained inlegal/.
Figures are annotated/resized archived DEVELOPMENT outputs,not independent final truth.

TorchVision/ImageNet ResNet18 features supported the source experiments under recorded
local academic weight terms;no pretrained or project-trained weights are distributed.
Project notebook,plots andaudit helpers are locally authored,AI-assisted research outputs.
All candidate admissions failed;software execution isnot new accuracy evidence.
Full three-source metadata is legal/source_records.csv .
'''
        (payload/'ATTRIBUTION.md').write_bytes(attribution.encode())
        readme='''# Archived guarded parking segmentation lesson13

This small capsule contains an executed notebook,six checksum-bound archived research
inputs andsource/licence notices. Candidate model-quality gates still failed.
It performs no training,new model inference,raw/final acquisition or app update.

Use an EXISTING Python environment withnbformat,nbclient,ipykernel,IPython andjupyter_client.
The validation runtime versions are inRUNTIME_REQUIREMENTS.json;dependencies are not
bundled andthis capsule does not install packages or acquire data.

From this extracted folder run:
    python scripts/run_guarded_lesson_capsule.py

Private runtime andexecuted-copy results are created innew sibling directories;
the payload stays unchanged. To validate separation froman original source project:
    python scripts/run_guarded_lesson_capsule.py --deny-project "path/to/original/project"

Keep PAYLOAD_MANIFEST.json andallrelative paths intact. The runner verifies exact
payload membership andhashes before starting. Raw/prospective/weight reads,payload
writes andexternal Python socket calls are denied inits project-file audit.
Original-project fallback denial is tested when --deny-project isprovided.
Python audits allow externalruntime libraries andarenot OS/network isolation.
This isnot a full app package or evidence ofphysical/new-machine/browser acceptance.
Student understanding isunassessed. Read ATTRIBUTION.md andthe failed-study limitations.
'''
        (payload/'README.md').write_bytes(readme.encode());dump(payload/'RUNTIME_REQUIREMENTS.json',p['runtime'])
        files={q.relative_to(payload).as_posix():dict(bytes=q.stat().st_size,sha256=digest(q)) for q in payload.rglob('*') if q.is_file()}
        total=sum(v['bytes'] for v in files.values());assert total<=p['maximum_payload_bytes']
        dump(payload/MANIFEST,dict(schema_version=1,run_id=p['run_id'],protocol_sha256=digest(path),source_lesson_binding_sha256=p['input_hashes'][p['source_binding']],files=files,
            private_runtime_included=False,models_or_raw_data_included=False,source_ids=p['source_ids']))
        receipt=verify_payload(payload);dump(out/'payload_receipt.json',dict(payload=payload.relative_to(ROOT).as_posix(),**receipt))
        boundary();archive=base/'lesson13.zip';create_zip(payload,archive);relocated=base/'relocated'
        roundtrip=extract_checked(archive,relocated,receipt['manifest_sha256']);assert roundtrip==receipt
        dump(out/'zip_receipt.json',dict(path=archive.relative_to(ROOT).as_posix(),bytes=archive.stat().st_size,sha256=digest(archive),CRC_checked=True,exact_roundtrip=True,**roundtrip))
        # Missing payload is rejected before any kernel/source fallback.
        incomplete=base/'incomplete_fixture';incomplete.mkdir();shutil.copyfile(payload/MANIFEST,incomplete/MANIFEST)
        try:verify_payload(incomplete,receipt['manifest_sha256'])
        except ValueError:missing_rejected=True
        else:raise AssertionError('Missing-input fixture was not rejected')
        boundary();execution=base/'execution';command=[sys.executable,str(relocated/'scripts/run_guarded_lesson_capsule.py'),'--scratch',str(private_runtime),'--output',str(execution),
            '--deny-project',str(ROOT),'--manifest-sha256',receipt['manifest_sha256']]
        with (out/'kernel_execution.txt').open('wb') as log:
            attempt=subprocess.run(command,cwd=relocated,stdout=log,stderr=subprocess.STDOUT,timeout=300,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        cleanup_owned_kernels();assert attempt.returncode==0,'Relocated kernel failed;see preserved log'
        kernel=read(execution/'checks.json');assert kernel['passed'] and kernel['original_project_fallback_denied'] and kernel['helpers_loaded_inside_capsule']
        assert kernel['code_cells']==5 and kernel['inline_PNGs']==2 and len(kernel['file_audit']['denied'])==4 and len(kernel['network_audit']['denied'])==1
        assert verify_payload(payload)==receipt and verify_payload(relocated)==receipt
        for name,expected in bound.items():assert digest(ROOT/name)==expected,name
        finished=datetime.now(timezone.utc).isoformat();report=dict(run_id=p['run_id'],started_at=started,finished_at=finished,duration_seconds=time.monotonic()-clock,
            seed=p['seed'],protocol_sha256=digest(path),source_ids=p['source_ids'],payload_path=payload.relative_to(ROOT).as_posix(),relocated_path=relocated.relative_to(ROOT).as_posix(),
            zip_path=archive.relative_to(ROOT).as_posix(),zip_sha256=digest(archive),zip_bytes=archive.stat().st_size,payload_receipt=receipt,
            runtime=p['runtime'],runtime_included=False,checks=dict(exact_payload_and_zip=True,CRC_and_hash_roundtrip=True,relocated_kernel=True,original_project_fallback_denied=True,
                helpers_inside_capsule=True,private_runtime_excluded=True,payload_unchanged=True,missing_input_rejected_before_kernel=missing_rejected,licence_and_attribution_retained=True),
            kernel=kernel,private_runtime_path=private_runtime.relative_to(ROOT).as_posix(),execution_checks=(execution/'checks.json').relative_to(ROOT).as_posix(),
            cleanup_owned_kernel_pids=cleanup,models_trained=0,new_model_calls=0,new_accuracy_evaluations=0,scope=p['scope'],passed=True)
        dump(out/'run.json',report);dump(ROOT/'models/guarded_lesson_capsule.json',report)
        dump(ROOT/'reports/guarded_lesson_capsule_latest.json',dict(run_id=p['run_id'],result_path=(out/'run.json').relative_to(ROOT).as_posix(),result_sha256=digest(out/'run.json'),passed=True))
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        assert not any(row['experiment_id']==p['run_id'] for row in rows)
        entry=dict(experiment_id=p['run_id'],run_type='Portable archived Jupyter lesson capsule validation',started_at=started,finished_at=finished,source_ids=';'.join(p['source_ids']),
            split_ids='Six immutable archived research inputs;no raw/model/final data',configuration=path.relative_to(ROOT).as_posix(),architecture='Manifest/ZIP relocated local Jupyter with project-file/socket audits',
            random_seed=186,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(dict(payload=receipt,checks=report['checks'],code_cells=5,PNGs=2,denial_probes=5)),
            logs=out.relative_to(ROOT).as_posix(),code_revision_basis='Sealed implementation/input hashes',implementation_sha256=digest(__file__),conclusions='Portable local lesson validation passed;not physicaloffline/newmachine/student mastery or new accuracy')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields,lineterminator='\n').writerow({k:entry.get(k,'') for k in fields})
        state=read(state_path);state['completed_run_ids'].append(p['run_id']);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']))
        state['last_completed_run']=p['run_id'];state['guarded_lesson_capsule']=report;dump(state_path,state)
        print(json.dumps(dict(run_id=p['run_id'],passed=True,payload=receipt,zip_bytes=report['zip_bytes'],duration_seconds=report['duration_seconds'])))
    except BaseException as error:
        cleanup_owned_kernels();dump(out/('interrupted_'+stamp+'.json'),dict(error=type(error).__name__,detail=str(error),attempt_path=base.relative_to(ROOT).as_posix(),completed_run_counted=False));raise
    finally:
        state=read(state_path);state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args();run(args.run) if args.run else prepare()
