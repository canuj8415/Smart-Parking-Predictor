"""Retrospective protection of demonstrably evaluated historical PKLot folds.

These records are dated NOW, not represented as claims made before the original
evaluations. No image/XML/metric score is opened or recomputed. This supplements
the completed full metadata audit without adding another experiment count.
"""
import csv,hashlib,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.pklot_group_ledger import ALIASES,build_ledger,identity
from smart_parking.holdouts import assert_holdout_closed

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    r=read(ROOT/'models/pklot_full_role_ledger.json');out=ROOT/'experiments/results'/r['run_id'];assert not(out/'historical_consumption_supplement.json').exists()
    s=read(ROOT/'data/automation_state.json');assert s['completed_recorded_runs_since_schedule']==102 and not s['active_training_jobs'] and not s['active_validation_jobs']
    with (ROOT/'data/splits/pklot-archive-inventory-v1/pairs.csv').open(encoding='utf-8-sig',newline='') as stream:pairs=list(csv.DictReader(stream))
    byday={}
    for pair in pairs:byday.setdefault(pair['capture_date'],set()).add(identity(pair['camera_id'],pair['capture_date']))
    exposures=[]
    for name in ['data/manifests/pklot_frames.csv','data/manifests/segmentation_known_camera_v1.json','data/manifests/region_broader_development_v1.json','data/manifests/pklot_fresh_development_v1.json','data/manifests/occupancy_expansion_v1.json','data/manifests/region_transfer_final_REGION-TRANSFER-20261024T204533261212Z.json']:
        if name.endswith('.csv'):
            with (ROOT/name).open(encoding='utf-8-sig',newline='') as stream:frames=list(csv.DictReader(stream))
        else:frames=read(ROOT/name)['frames']
        exposures.extend(dict(camera_id=f['camera_id'],date=f['date'],role=f.get('split',f.get('role')),source=name,image_sha256=f.get('image_sha256')) for f in frames)
    original=read(ROOT/'models/segmentation_model_card.json');vision=read(ROOT/'models/vision_model_card.json');known=read(ROOT/'models/segmentation_known_camera_candidate.json');manifest=ROOT/'data/manifests/segmentation_known_camera_v1.json'
    assert original['code_sha256']==digest(ROOT/'scripts/train_segmentation.py') and original['checkpoint_sha256']==digest(ROOT/'models/checkpoints/parking_unet.pt')
    assert original['metrics']['test_frames']>0 and {'pixel_iou','dice'}<=set(original['metrics'])
    assert vision['classifier_metrics']['samples']==360 and vision['checkpoint_sha256']==digest(ROOT/'models/checkpoints/occupancy_resnet18.pt')
    assert known['code_sha256']==digest(ROOT/'src/smart_parking/segmentation_experiment.py') and known['manifest_sha256']==digest(manifest)
    assert known['frames_by_split']['test']==6 and {'candidate','old_model','camera_geometry'}<=set(known['metrics'])
    closure=ROOT/'experiments/results'/known['run_id']/'selection_closed.json';assert read(closure)['checkpoint_sha256']==known['checkpoint_sha256']
    knownrows=[f for f in read(manifest)['frames'] if f['split']=='test'];dates=[(original,'models/segmentation_model_card.json',original['final_test_dates'],[]),
        (vision,'models/vision_model_card.json',[day for day,role in vision['dataset']['split_dates'].items() if role=='test'],[]),
        (known,'models/segmentation_known_camera_candidate.json',sorted({f['date'] for f in knownrows}),[f['image'] for f in knownrows])]
    now=datetime.now(timezone.utc).isoformat();records=[];before={p.name:digest(p) for p in (ROOT/'data/holdout_claims').glob('*.claim.json')};guardprobes=[]
    for card,cardpath,days,images in dates:
        groups=[]
        for day in days:
            assert len(byday.get(day,set()))==1,'Historical date must identify one known source camera'
            group=next(iter(byday[day]));groups.append(group)
            exposures.append(dict(camera_id=group[0],date=day,role='test',source=cardpath,image_sha256=None))
        groups=sorted(set(groups));names=sorted({(alias,day) for camera,day in groups for alias,canonical in ALIASES.items() if canonical==camera})
        key=hashlib.sha256(('retrospective-pklot-consumption-v1\n'+card['run_id']+'\n'+json.dumps(groups)).encode()).hexdigest();target=ROOT/'data/holdout_claims'/(key+'.claim.json');assert not target.exists()
        proof=dict(card=cardpath,card_sha256=digest(ROOT/cardpath),explicit_final_dates=days,metric_score_values_inspected=False,
            current_code_matches_recorded=(card.get('code_sha256')==digest(ROOT/('scripts/train_segmentation.py' if card is original else 'scripts/train_vision.py' if card is vision else 'src/smart_parking/segmentation_experiment.py'))))
        if card is vision:proof.update(current_manifest_matches_recorded=vision['manifest_sha256']==digest(ROOT/'data/manifests/pklot_frames.csv'),scope='Explicit historical card split_dates and completed360test-sample record establish whole-date use;current code/manifest hashes differ and are not silently treated as matching historical versions')
        if card is known:proof.update(selection_closed_sha256=digest(closure),matching_eval_code_loads_test=True)
        record=dict(record_type='retrospective_consumption_attestation',recorded_at=now,run_id=card['run_id'],status='Historical test evaluation completed;consumed. Recorded after evaluation,not a preregistration or prior claim.',claim_timing='retrospective;original evaluation predates this record',source_id='SRC-DS-001',canonical_source_groups=[list(g) for g in groups],source_groups=[list(g) for g in names],frame_ids=sorted({(ROOT/p).resolve().relative_to(ROOT).as_posix().casefold() for p in images}),protection_scope='Whole canonical camera/date and documented archive-folder aliases;unknown cross-date byte aliases still require separate qualification',evidence=proof,added_during_metadata_audit=r['run_id'],model_callbacks_executed=0)
        with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.flush();os.fsync(stream.fileno())
        records.append(dict(path=target.relative_to(ROOT).as_posix(),sha256=digest(target),canonical_groups=[list(g) for g in groups],recorded_now_not_backdated=True))
        for camera,day in names:
            probe=out/f'guard_probe_{camera}_{day}.json';dump(probe,dict(data_kind='synthetic_guard_fixture_with_real_protected_group',frames=[dict(camera_id=camera,date=day,image=f'data/fixtures/never_open_{camera}_{day}.jpg')]))
            try:assert_holdout_closed(probe,root=ROOT)
            except ValueError as error:guardprobes.append(dict(camera=camera,date=day,blocked=True,reason=str(error)))
            else:raise AssertionError('Historical consumption was not blocked')
    for name,sha in before.items():assert digest(ROOT/'data/holdout_claims'/name)==sha
    claims=[read(p) for p in (ROOT/'data/holdout_claims').glob('*.claim.json')];historical=read(ROOT/'models/pklot_unused_date_inventory.json')['exclusion_records'];current=build_ledger(pairs,exposures,claims,historical)
    assert current['durable_consumed_groups']==17 and current['status_counts']['historical_metadata_excluded']==16 and current['new_final_groups_admitted']==0
    train=next(g for g in current['groups'] if g['status']=='training_exposed');positive=out/'unrelated_train_guard_control.json';dump(positive,dict(data_kind='synthetic_guard_fixture_not_new_data_admission',frames=[dict(camera_id=train['camera_id'],date=train['capture_date'],image='data/fixtures/never_open_training_control.jpg')]))
    assert len(assert_holdout_closed(positive,root=ROOT))==1
    result=dict(run_id=r['run_id'],supplement_recorded_at=now,original_completed_run_json_unchanged_sha256=digest(out/'run.json'),record_type='Post-audit historical consumption integrity repair,no new experiment',records=records,guard_checks=guardprobes,unrelated_training_control_allowed=True,previous_claim_files_unchanged=before,guard_source_sha256=digest(ROOT/'src/smart_parking/holdouts.py'),supplement_source_sha256=digest(__file__),current_ledger=current,
        new_image_or_XML_reads=0,new_model_evaluations=0,completed_experiment_count_added=0,protection_records_not_backdated=True,limitations='Metadata-known historical exposure only;code/manifest mismatch for original vision record disclosed. Original metrics/weights untouched;no new final or training admission.')
    dump(out/'historical_consumption_supplement.json',result);dump(ROOT/'models/pklot_current_role_ledger.json',result);dump(ROOT/'reports/pklot_full_role_ledger_latest.json',result);s=read(ROOT/'data/automation_state.json');s['pklot_historical_consumption_repair']=result;dump(ROOT/'data/automation_state.json',s)
    print(json.dumps(dict(new_retrospective_records=len(records),current_consumed_groups=17,metadata_excluded_groups=16,guard_checks=len(guardprobes),count_added=0,images_or_XML_opened=0)))

if __name__=='__main__':main()
