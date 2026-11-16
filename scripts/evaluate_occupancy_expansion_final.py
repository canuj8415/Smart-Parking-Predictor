"""Prepare, commit, then run one frozen paired final comparison; never replay."""
import argparse
import csv
import gc
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.paired_occupancy_final import evaluate_paired_once,score,acceptance


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def prepare():
    state=read('data/automation_state.json');assert not state['active_training_jobs'] and not state['active_validation_jobs']
    classifier=read('models/occupancy_expansion_candidate.json');fusion=read('models/occupancy_expansion_fusion_candidate.json')
    assert classifier['validation_gate_passed'] and fusion['validation_gate_passed']
    original=ROOT/'models/checkpoints/occupancy_resnet18.pt';candidate=ROOT/classifier['candidate_checkpoint']
    assert digest(original)==classifier['original_checkpoint_sha256']
    assert digest(candidate)==classifier['candidate_checkpoint_sha256']==fusion['candidate_checkpoint_sha256']
    manifest=ROOT/'data/manifests/pklot_fresh_final_v2.json';frames=assert_holdout_closed(manifest,root=ROOT)
    assert len(frames)==6 and len({(r['camera_id'],r['date']) for r in frames})==3
    started=datetime.now(timezone.utc);rid='OCCUPANCY-PAIRED-FINAL-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/rid;folder.mkdir(parents=True,exist_ok=False)
    paths=['scripts/evaluate_occupancy_expansion_final.py','src/smart_parking/paired_occupancy_final.py',
        'src/smart_parking/holdouts.py','src/smart_parking/vision.py','src/smart_parking/layout.py',
        'src/smart_parking/analysis_identity.py','src/smart_parking/provenance.py']
    hashes={p:digest(ROOT/p) for p in paths}
    protocol=dict(version='occupancy-paired-final-v1',run_id=rid,prepared_at=started.isoformat(),
        preparation_base_revision=subprocess.run(['git','rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip(),
        seed=132,source_ids=['SRC-DS-001','SRC-MOD-001','SRC-MOD-002','SRC-MOD-003'],source_hashes=hashes,
        manifest=manifest.relative_to(ROOT).as_posix(),manifest_sha256=digest(manifest),
        models={name:dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p)) for name,p in [('original',original),('candidate',candidate)]},
        development_cards={name:dict(path=p,sha256=digest(ROOT/p)) for name,p in [
            ('classifier','models/occupancy_expansion_candidate.json'),('fusion','models/occupancy_expansion_fusion_candidate.json')]},
        detector_weight_hashes=fusion['detector_weight_hashes'],detectors=['fasterrcnn','maskrcnn'],
        resolution=640,detection_confidence=.5,uncertain_low=.25,uncertain_high=.75,
        hypothesis='Expanded occupancy head retains useful reliability on the three untouched known-camera/date groups,paired against the unchanged original under both detector configurations.',
        gates=dict(minimum_labels=120,minimum_groups=3,minimum_group_labels=20,minimum_each_class=10,
            accuracy_min=.95,accuracy_drop_max=.005,group_accuracy_min=.90,group_accuracy_drop_max=.025,
            wrong_occupied_extra_fraction=.01,vacancy_retention=.95,uncertain_max=.10,uncertain_extra_max=.02,
            group_uncertain_max=.15,group_correct_drop_fraction=.025),
        acceptance='Every acceptance()check must pass for BOTH detectors; includes no overall/group false-vacant regression and some strict observed benefit. No automatic product promotion.',
        limits=dict(torch_threads=4,wall_seconds=900,final_frames=6),
        missing_label_policy='Keep every configured slot in app output;score only explicit0/1labels;unknown counts remain in support report;insufficient support fails qualification without fabricated accuracy.',
        geometry='Original final XML geometry is supplied after the claim;occupancy answers stripped before each model input. Not automatic parking-space segmentation.',
        limitations=['Only6correlated photos/3dates/3known camera views,not unseen-carpark/physical/live accuracy',
            'Entire3camera-date groups consumed once even after a failure or interruption',
            'Original and candidate each use the same RGB pixels/geometry/COCOdetector and fixed thresholds',
            'No exhaustive vehicle-box/mask annotations;no detector mAP/instance-mask accuracy',
            'Repeated final inference occurs solely within this frozen paired callback,not subsequent tuning'])
    dump(folder/'protocol.json',protocol)
    dump(folder/'selection.json',dict(validation_gate_passed=True,checkpoint_sha256=digest(candidate),
        protocol_sha256=digest(folder/'protocol.json'),basis='Both frozen classifier/fusion development gates passed; bindings verified before final claim'))
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    print(json.dumps(dict(run_id=rid,protocol=str(folder/'protocol.json'),next='Commit the frozen controller/protocol before --run; final pixels/labels remain unopened'),indent=2))


def run(rid):
    if Path(rid).name!=rid or not rid.startswith('OCCUPANCY-PAIRED-FINAL-'):raise ValueError('Existing final run ID required')
    folder=ROOT/'experiments/results'/rid;protocol=read(folder/'protocol.json')
    assert not (folder/'run.json').exists(),'A completed final cannot be replayed'
    # A real Git checkpoint witnesses the exact protocol and implementation before
    # the claim. This check reads text/model metadata, never final image labels.
    frozen_revision=subprocess.run(['git','rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    for path in [*(ROOT/p for p in protocol['source_hashes']),folder/'protocol.json',folder/'selection.json']:
        saved=subprocess.run(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],check=True,capture_output=True).stdout
        assert saved==path.read_bytes(),'Final protocol/controller must be committed byte-for-byte before decoding'
    state_path=ROOT/'data/automation_state.json';state=read(state_path)
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    started=datetime.now(timezone.utc);timer=time.perf_counter()
    state['active_validation_jobs']=[dict(run_id=rid,cancel_file=str(folder/'CANCEL'),deadline_seconds=900,
        warning='Final groups will be consumed even if this job fails;do not resume/replay')]
    dump(state_path,state)
    def boundary():
        if (folder/'CANCEL').exists() or time.perf_counter()-timer>900:
            raise InterruptedError('Frozen final cancelled/deadline; groups remain consumed')
    def evaluate(frames):
        import torch
        from PIL import Image
        from smart_parking.layout import read_pklot_xml
        from smart_parking.vision import VisionEngine
        torch.manual_seed(protocol['seed']);torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
        bundles={name:torch.load(ROOT/binding['path'],map_location='cpu',weights_only=True) for name,binding in protocol['models'].items()}
        prepared=[];support=[]
        # First final pixel/XML access is INSIDE this callback, after the paired
        # binding receipt and original durable whole-date claim have been fsynced.
        for f in frames:
            boundary()
            assert digest(ROOT/f['image'])==f['image_sha256'] and digest(ROOT/f['annotation'])==f['annotation_sha256']
            with Image.open(ROOT/f['image']) as source:image=source.convert('RGB')
            labelled=read_pklot_xml(ROOT/f['annotation'],image.size);assert labelled['camera_id']==f['camera_id']
            geometry={k:v for k,v in labelled.items() if k!='slots'}
            geometry['slots']=[dict(id=s['id'],polygon=s['polygon']) for s in labelled['slots']]
            answers={s['id']:s['ground_truth_occupied'] for s in labelled['slots']}
            prepared.append((f,image,geometry,answers))
            support.append(dict(camera_id=f['camera_id'],date=f['date'],frame=f['image'],configured_slots=len(answers),
                explicit_labels=sum(v is not None for v in answers.values()),unknown_labels=sum(v is None for v in answers.values()),
                occupied_labels=sum(v==1 for v in answers.values()),vacant_labels=sum(v==0 for v in answers.values())))
        dump(folder/'final_support.json',support)
        all_results={};all_groups=sorted({(f['camera_id'],f['date']) for f in frames})
        for detector in protocol['detectors']:
            engine=VisionEngine(detector=detector,resolution=protocol['resolution']);rows={name:[] for name in bundles}
            for frame_no,(f,image,geometry,answers) in enumerate(prepared,1):
                original_detections=None
                for name,bundle in bundles.items():
                    boundary();engine.classifier.load_state_dict(bundle['state_dict']);engine.classifier.eval()
                    engine.classifier_sha256=protocol['models'][name]['sha256'];engine.classifier_run_id=bundle.get('run_id')
                    result,overlay=engine.analyze(image,geometry,confidence=protocol['detection_confidence'],
                        uncertain_low=protocol['uncertain_low'],uncertain_high=protocol['uncertain_high'])
                    if name=='original':original_detections=result['detections']
                    else:assert result['detections']==original_detections,'Paired detector outputs unexpectedly differ'
                    for observation in result['slots']:
                        label=answers[observation['slot_id']]
                        if label is None:continue
                        rows[name].append(dict(frame=f['image'],image_sha256=f['image_sha256'],camera_id=f['camera_id'],date=f['date'],label=label,**observation))
                    dump(folder/detector/name/f'frame_{frame_no:02d}.json',dict(source_frame=f,result=result))
                dump(folder/'progress.json',dict(detector=detector,paired_frames_completed=frame_no,scored_slots=len(rows['candidate'])))
                print(json.dumps(dict(detector=detector,paired_frame=frame_no,scored_slots=len(rows['candidate']))),flush=True)
            values={name:score(group) for name,group in rows.items()}
            groups={name:{key:score([r for r in values if (r['camera_id'],r['date'])==key]) for key in all_groups} for name,values in rows.items()}
            checks,passed=acceptance(values['original'],values['candidate'],groups['original'],groups['candidate'],protocol['gates'])
            all_results[detector]=dict(overall=values,per_group={name:[dict(camera_id=c,date=d,**v) for (c,d),v in group.items()] for name,group in groups.items()},checks=checks,final_gate_passed=passed)
            for name,values in rows.items():dump(folder/detector/name/'final_predictions.json',values)
            del engine;gc.collect()
        return dict(support=support,detectors=all_results,paired_final_gate_passed=all(v['final_gate_passed'] for v in all_results.values()))
    try:
        result=evaluate_paired_once(ROOT/protocol['manifest'],folder/'selection.json',folder/'protocol.json',rid,evaluate,root=ROOT)
        assert all(digest(ROOT/p)==h for p,h in protocol['source_hashes'].items())
        assert all(digest(ROOT/b['path'])==b['sha256'] for b in protocol['models'].values())
        outcome=dict(protocol,started_at=started.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),
            execution_frozen_revision=frozen_revision,duration_seconds=time.perf_counter()-timer,**result,
            all_final_groups_now_consumed=True,production_promoted=False)
        dump(folder/'run.json',outcome);dump(ROOT/'models/occupancy_expansion_final.json',outcome)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='Once-only paired occupancy final comparison',started_at=started.isoformat(),finished_at=outcome['finished_at'],
            source_ids=';'.join(protocol['source_ids']),split_ids='pklot_fresh_final_v2;6photos/3wholegroups nowconsumed',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Frozen original/expanded ResNet18 head with both actual COCOdetectors',
            epochs=0,random_seed=132,hardware='CPU/Torch4threads',execution_environment=sys.version.split()[0],training_duration=outcome['duration_seconds'],
            evaluation_metrics=json.dumps(result),logs=folder.relative_to(ROOT).as_posix(),checkpoints=protocol['models']['candidate']['path'],
            code_revision_basis=frozen_revision,implementation_sha256=protocol['source_hashes']['scripts/evaluate_occupancy_expansion_final.py'],
            conclusions='Frozen paired final gate='+str(result['paired_final_gate_passed'])+'; all groups consumed; no promotion or live/unseen-camera claim')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=read(state_path);assert rid not in state['completed_run_ids'];state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,gate=result['paired_final_gate_passed'],support=result['support'],detectors=result['detectors']),indent=2),flush=True)
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),completed_run_counted=False,
            final_groups_may_be_consumed=True,do_not_resume_or_replay=True))
        state=read(state_path);raise
    finally:
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true');group.add_argument('--run')
    args=parser.parse_args()
    if args.prepare:prepare()
    else:run(args.run)
