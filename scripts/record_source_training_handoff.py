"""Save genuine crop/training results,failed improvement and the Excel report."""
import csv,json,sys,shutil,zipfile,xml.etree.ElementTree as ET
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T063846Z'
TITLE='## 26 October 2026 / genuine source-balanced head training retained the warm comparison'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,v):
    p=ROOT/p;s=p.read_text(encoding='utf-8');assert TITLE not in s;p.write_text(s.rstrip()+'\n\n'+TITLE+'\n\n'+v+'\n',encoding='utf-8')
def main():
    assert not (E/'handoff.json').exists()
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');run=read('models/source_balanced_development_head.json');prep=read('models/source_occupancy_crop_preparation.json');diag=read(E/'training_diagnostics.json')
    assert state['last_completed_run']==run['run_id'] and state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==60
    assert state['scheduled_wakeups_completed']==40 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['epochs_completed']==2 and run['selected_epoch']==0 and not run['development_gate_passed'] and not run['production_promoted']
    assert all(digest(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes'],**prep['source_hashes'],**prep['protected_hashes']}.items())
    assert digest(ROOT/prep['manifest'])==prep['manifest_sha256']
    assert read(E/'software_tests.json')['returncode']==0 and 'Ran 238 tests' in read(E/'software_tests.json')['stderr']
    output=ROOT/'outputs/training_report_20261026T063846Z';book=output/'Smart_Parking_Training_Study.xlsx'
    with zipfile.ZipFile(book) as archive:
        assert archive.testzip() is None;ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        cells={c.attrib['r']:c for c in ET.fromstring(archive.read('xl/worksheets/sheet1.xml')).findall('.//s:c',ns)}
        for col,key in [('B','warm_comparison'),('C','last_trained_epoch'),('D','selected_head')]:assert abs(float(cells[col+'8'].find('s:v',ns).text)-diag[key]['metrics']['overall']['hard_accuracy'])<1e-12
        assert int(float(cells['B21'].find('s:v',ns).text))==26552
    archive_dir=ROOT/'reports/source_training_20261026';archive_dir.mkdir(parents=True,exist_ok=False)
    for name in ['Smart_Parking_Training_Study.xlsx','preview.png','builder.mjs','inspection.json']:
        shutil.copyfile(output/name,archive_dir/name);assert digest(output/name)==digest(archive_dir/name)
    checks=read(E/'workbook_checks.json');checks.update(final_preview_visually_inspected=True,finish_timestamp_number_format_verified=True,
        artifact_engine='Bundled @oai/artifact-tool',source_counts_match=True,formulas_recalculated_after_input_change_and_restored=True,
        workbook_sha256=digest(book),native_excel_session_tested=False);dump(E/'workbook_checks.json',checks)
    diag.update(warm_checkpoint_sha256=run['warm_checkpoint_sha256'],last_head_sha256=digest(ROOT/'experiments/results'/run['run_id']/'last_head.pt'),
        metric_implementation_sha256=digest(ROOT/'scripts/train_occupancy_expansion.py'),selection_unchanged=True);dump(E/'training_diagnostics.json',diag)
    pointer=dict(run_id=run['run_id'],crop_preparation_run=prep['run_id'],training_crops=26552,new_source_crops=16448,excluded_source_crops=96,
        epochs_completed=2,selected_epoch=0,development_gate_passed=False,production_promoted=False,
        baseline_errors=12,last_trained_errors=20,selected_errors=12,baseline_false_vacant=4,last_trained_false_vacant=6,
        selected_false_vacant=4,validation_samples=2028,scope='Reused PKLot development only;new source training only,no final/new-park/night/live camera accuracy',
        checkpoint=run['candidate_checkpoint'],checkpoint_sha256=run['candidate_checkpoint_sha256'],
        workbook=book.relative_to(ROOT).as_posix(),workbook_sha256=digest(book),archival_workbook=(archive_dir/'Smart_Parking_Training_Study.xlsx').relative_to(ROOT).as_posix(),
        software_tests_passed=238,guide='docs/OPEN_SPACE_DATA_GUIDE.md')
    dump('reports/source_training_latest.json',pointer)
    prior=read('data/manifests/open_space_usage_qualification_v3.json')
    usage=dict(prior,version=4,recorded_at=now,run_id=run['run_id'],parent_usage='data/manifests/open_space_usage_qualification_v3.json',
        parent_usage_sha256=digest(ROOT/'data/manifests/open_space_usage_qualification_v3.json'),
        usage_status='Qualified masked TRAIN crops used in one rejected DEVELOPMENT-ONLY head study;source remains development-exposed',
        model_training_admitted=True,experimental_development_training_admitted=True,production_admitted=False,
        admission_basis='Completed source crop gate plus timestamped frozen development-only training protocol;earlier usagev3 described the pre-crop phase,not a changed image-rights decision',
        crop_preparation_run=prep['run_id'],training_protocol='experiments/results/'+run['run_id']+'/protocol.json',
        training_protocol_sha256=digest(ROOT/'experiments/results'/run['run_id']/'protocol.json'),new_source_training_crops=16448,
        excluded_selected_crops=96,source_target_mapping={'0space_occupied':1,'1space_vacant':0},model_training_performed=True,
        source_model_evaluation_performed=False,independent_final_eligible=False,
        pending=['Diagnose retained cached development regressions before proposing another distinct bounded hypothesis',
            'Fresh independent final evidence required before any app promotion;all consumed finals stay closed'])
    dump('data/manifests/open_space_usage_qualification_v4.json',usage)
    latest=read('reports/open_space_data_latest.json');latest.update(current_training=pointer,usage_qualification='data/manifests/open_space_usage_qualification_v4.json');dump('reports/open_space_data_latest.json',latest)
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
    last=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert digest(ROOT/last['local_path'])==last['sha256']
    payload=read(last['local_path']);rows=parse_feed(payload);raw_lots=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in rows) and len(rows)==len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')));next_poll=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json',dict(receipt=last,summary=live,snapshot_count=snapshots,accepted_rows=len(rows),raw_lot_records=raw_lots,
        invalid_capacity_excluded=raw_lots-len(rows),bounds_valid=True,duplicate_rows=0,separate100_run_checkpoint_due=False,next_sensible_collection_after=next_poll,
        scope='Causal persistence scoring only;not new-source/PKLot camera or neural live accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-018':item.update(status=usage['usage_status'],used_for_model_training=True,used_for_model_evaluation=False,
            occupancy_crop_preparation=prep,development_training_result=pointer,usage_qualification='data/manifests/open_space_usage_qualification_v4.json')
        if item['source_id']=='SRC-LIVE-001':item.update(raw_path=last['local_path'],provider_timestamp=last['provider_timestamp'],snapshot_count=snapshots,
            observations=len(rows),car_parks=len({r['car_park_id'] for r in rows}),raw_lot_records=raw_lots,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    dump('data/dataset_inventory.json',inventory)
    catalog=ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==58
    for item in sources:
        if item['source_id']=='SRC-DS-018':item.update(used_by='16448qualified masked TRAIN crops in one genuine source-balanced frozenResNet18 head study;no independent source evaluation',
            modifications='Originals preserved;32label-blind polygons/frame cap,96tiny/ambiguous crops excluded,source class0occupied->model1/class1vacant->model0;208600155byte crop cache',
            status='Development head trial did not improve PKLot development;warm epoch0retained,no app promotion',
            open_issues='New source/night/unseen-lot accuracy unmeasured;allsource development-exposed;trained epoch2regressed12->20errors/4->6false-vacant on reusedPKLot development;fresh final needed before promotion')
    with catalog.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    state.update(last_updated_at=now,scheduled_wakeups_completed=41,source_balanced_training=pointer,latest_training_workbook=pointer['workbook'],
        prospective_live_summary=live,last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Completed actual development training:SOURCE-CROPS preparation59then SOURCE-BALANCED-HEAD60.26552train crops=10104PKLot+16448newsource;96excluded(55small/41ambiguous). Two AdamW head epochs from preserved warm comparison;frozen backbone unchanged. Epoch2reused2028PKLot development errors12->20,false-vacant4->6,macro loss.01942075->.02863934. Prespecified CE selection retains epoch0warm,gateFalse. Original app model never changed. Excel '+pointer['workbook']+';reportspointer reports/source_training_latest.json.',
        'Highest next analysis:use saved last_head.pt,warm checkpoint,old feature-cache checksums and E/training_diagnostics.json to identify per-camera/date paired development regressions and crop-quality links BEFORE another training idea. Cached features and all failed epochs retained;do not repeat the same source25percent study or count frames/epochs as runs. Qualitative crop gallery shows some distant crops remain blurry despite12pixel minimum;quantify source TRAIN quality only if needed,do not use finals.',
        'A distinct bounded next candidate may anchor old-head predictions while learning new source,or tighten predeclared crop quality after source-only analysis. Freeze a hypothesis/config/source/data hashes and validation gates first. All newsource validation/test semantics remain unopened and not independent final;source018is one development-exposed group. PKLot2028is reused DEVELOPMENT,not final. No app promotion without genuinely fresh independent final evidence. Never replay consumed PKLot/Birmingham/DAVIS finals or waive earlier failed rainy retention13/14<95percent.',
        'Crop cache517NPZfiles/208600155bytes and newsource517feature chunks retained. Original215PKLot feature chunks reused with exact SHA;original/warm backbone tensors verified equal;newsource classindices explicitly inverted for model labels. New source current usagev4records qualified experimental training admission;v1-v3preserved as historical stages. Region/background negatives still unqualified;unknown/conflicting support never treated as vacant/background. CNR image rights unresolved,images unopened.',
        'Counter60;wakeups41;source58;next separate100-run live checkpoint100;no active jobs/owned training lock removed.238software tests pass,including5new synthetic source-crop/mass tests. One-sheet Excel source values/formula caches/recalculation perturb-and-restore/ZIPCRC/actualpreview checked using bundled artifact-tool;nativeExcel not tested. Original424fileoffline package remains dated.',
        'Latest Singapore'+live['checked_at']+':45snapshots,1103new matching frozen persistence targets,38472total,MAE4.859742spaces,1300new forecasts. Missing targets unscored. Next sensible collection AFTER'+next_poll+'. No live neural/camera accuracy. Python/Jupyter retained;manual/physical/browser/student/official university acceptance remains open.'
    ];dump('data/automation_state.json',state)
    note=('Prepared16,448source TRAIN occupancy crops from517accepted photos with a label-blind32polygon/frame cap;96excluded(55native-side<12pixels,41unambiguous support<95percent),all retained with reasons. Gray127input outside unambiguous polygon support;source0occupied maps model1 and source1vacant maps model0.517NPZcachefiles/208,600,155bytes,source/row/crop hashes preserved. '+
        'Genuine frozen-ResNet18 linear-head training used26,552crops(10,104original PKLot+16,448newsource),source-weighted.75/.25,camera/class-balanced,seed128,max6epochs/patience2. Original215feature chunks hash-verified;newsource517feature chunks retained;warm/original backbones verified identical. '+
        'Two epochs completed in168.86seconds with early stopping. On SAME reused2,028PKLot DEVELOPMENT labels,last trained epoch errors12->20,confident false-vacant4->6,correct confident empty665->661,review19->20;macro loss.01942075->.02863934. Prespecified loss selection keeps epoch0warm comparison;selected12errors/4false-vacant,strict improvement gateFalse. All trained/best/last/checkpoint/cache states retained. This is a rejected transfer hypothesis,not improved final performance. Warm comparison was already a separate unpromoted research checkpoint;running app stilluses original model. '+
        'No newsource validation/test semantics or consumed final data used. No night/new-park/live camera accuracy claim. Existing final failure/claims and original3production checkpoints unchanged.238software tests pass;crop59andtraining60are two completed trials,not perframe/epoch. Source58,wakeups41,next100-run checkpoint100,no active jobs. '+
        'One-sheet Excel '+pointer['workbook']+' compares warm/trained/retained results and data/source counts. Artifact-tool authoring with bundled runtime;4relevant formula caches,source counts,input perturb/restore,ZIPCRC and actual final preview verified;nativeExcel not tested. Archival exactcopy:'+pointer['archival_workbook']+'. '+
        'OfficialSingapore45snapshots adds1,103causal persistence matches,38,472total,MAE4.859742spaces;1,300newforecasts;missing targets unscored,not neural/camera accuracy. Next:paired cached development regression analysis before any distinct bounded training hypothesis.')
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','docs/DATASET_PROVENANCE.md','docs/THIRD_PARTY_SOURCES.md']:append(p,note)
    append('docs/UI_TEST_LOG.md','Actual16-crop source-label gallery and final one-sheet Excel preview visually inspected. Timestamp formatting corrected and final report rerendered. No app UI/nativeExcel/manual/student acceptance claimed.')
    guide=ROOT/'docs/OPEN_SPACE_DATA_GUIDE.md';s=guide.read_text(encoding='utf-8');s=s.replace('39,068supplied space outlines. No model has been trained on them yet.','39,068supplied space outlines. A development-only training study used16,448\nselected crops and did not improve the comparison score. The app stayed unchanged.')
    s=s.replace('We have not checked every annotation or trained a model with this source.','At that four-photo inspection stage,we had not checked every annotation or trained a model with this source.');guide.write_text(s,encoding='utf-8')
    append('docs/OPEN_SPACE_DATA_GUIDE.md','We have now trained a separate experimental model using26,552small parking-space pictures:10,104from PKLot and16,448from the new source. '+
        'Think of adding a second workbook of practice questions. After two learning passes,the experiment made20mistakes on the same2,028development examples,compared with12for its starting comparison model. '+
        'It incorrectly called6occupied spaces empty,compared with4before. The automatic selection rule kept the starting checkpoint. The running app was not replaced. '+
        'This records a real unsuccessful training idea;it does not claim perfect accuracy. New-park/night accuracy was not tested. '+
        'The Excel report is `'+pointer['workbook']+'`. Actual training-crop records are `'+prep['manifest']+'`;crop files are under outputs/source_occupancy_crops/. '+
        'The original publisher archive,all excluded crops,training checkpoints and failed results remain saved. Current source decision:usagev4. Next:inspect which development mistakes changed before trying a different training idea.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;items=list(reader)
    for row in items:
        if row['requirement_id'] in ['DATA-02','DATA-03','QA-02']:
            row['actual_evidence']+='; reports/source_training_latest.json; models/source_balanced_development_head.json'
            row['test_result']+=';16448source crops/26552combined train,2epochs,development gateFAIL and epoch0warm retained;238software tests'
            row['open_problems']+=';Transfer candidate did not improve reused development;new independent final required before promotion'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(items)
    dump(E/'handoff.json',dict(recorded_at=now,completed_trials=60,wakeups=41,source_records=58,next_live_milestone=100,training_result=pointer,
        all238software_tests_passed=True,training_failed_to_improve=True,original_models_claims_warm_checkpoint_unchanged=True,
        workbook_visual_review_complete=True,source_crop_gallery_reviewed=True,native_excel_tested=False,no_active_jobs=True,next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(trials=60,wakeups=41,workbook=pointer['workbook'],development_gate=False,snapshots=snapshots),indent=2))
if __name__=='__main__':main()
