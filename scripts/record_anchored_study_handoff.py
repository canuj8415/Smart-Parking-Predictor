"""Record paired diagnosis,one anchored study and exact comparison report."""
import csv,json,shutil,sys,zipfile,xml.etree.ElementTree as ET
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T070847Z'
TITLE='## 26 October 2026 / paired transfer diagnosis and rejected teacher-anchored study'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def dump(p,v):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,v):
    p=ROOT/p;s=p.read_text(encoding='utf-8');assert TITLE not in s;p.write_text(s.rstrip()+'\n\n'+TITLE+'\n\n'+v+'\n',encoding='utf-8')
def main():
    assert not (E/'handoff.json').exists()
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');run=read('models/anchored_source_development_head.json');diag=read('models/source_transfer_diagnostics.json');plain=read('models/source_balanced_development_head.json')
    assert state['last_completed_run']==run['run_id'] and state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==62
    assert state['scheduled_wakeups_completed']==41 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['epochs_completed']==2 and run['selected_epoch']==0 and not run['development_gate_passed']
    assert run['last_epoch']['overall']['hard_errors']==18 and run['candidate']['overall']['hard_errors']==12
    assert all(digest(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes'],**diag['source_hashes'],**diag['protected_hashes']}.items())
    tests=read(E/'software_tests.json');assert tests['returncode']==0 and 'Ran 245 tests' in tests['stderr']
    previous=read('reports/source_training_latest.json');assert digest(ROOT/previous['workbook'])==previous['workbook_sha256']
    dump(E/'previous_training_pointer.json',previous)
    output=ROOT/'outputs/transfer_report_20261026T070847Z';book=output/'Smart_Parking_Transfer_Comparison.xlsx'
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(book) as z:
        assert z.testzip() is None;cells={c.attrib['r']:c for c in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:c',ns)}
        for row,error in [(6,12),(7,20),(8,18),(9,12)]:assert abs(float(cells['E'+str(row)].find('s:v',ns).text)-(1-error/2028))<1e-12
        assert int(float(cells['B15'].find('s:v',ns).text))==8 and int(float(cells['B22'].find('s:v',ns).text))==1091
    archive=ROOT/'reports/transfer_study_20261026T070847Z';archive.mkdir(parents=True,exist_ok=False)
    for name in ['Smart_Parking_Transfer_Comparison.xlsx','preview.png','builder.mjs','inspection.json']:
        shutil.copyfile(output/name,archive/name);assert digest(output/name)==digest(archive/name)
    checks=read(E/'workbook_checks.json');checks.update(final_preview_visually_reviewed=True,date_and_time_fit_verified=True,
        artifact_engine='Bundled @oai/artifact-tool',workbook_sha256=digest(book),previous_workbook_sha256_unchanged=previous['workbook_sha256']);dump(E/'workbook_checks.json',checks)
    pointer=dict(run_id=run['run_id'],prior_training_run=plain['run_id'],diagnosis_run=diag['run_id'],training_crops=26552,validation_samples=2028,
        epochs_completed=2,selected_epoch=0,baseline_errors=12,plain_last_trained_errors=20,anchored_last_trained_errors=18,selected_errors=12,
        baseline_false_vacant=4,plain_last_false_vacant=6,anchored_last_false_vacant=6,selected_false_vacant=4,
        development_gate_passed=False,production_promoted=False,checkpoint=run['candidate_checkpoint'],checkpoint_sha256=run['candidate_checkpoint_sha256'],
        workbook=book.relative_to(ROOT).as_posix(),workbook_sha256=digest(book),archival_workbook=(archive/book.name).relative_to(ROOT).as_posix(),
        previous_workbook=previous['workbook'],previous_workbook_sha256=previous['workbook_sha256'],software_tests_passed=245,
        scope='Same reused PKLot DEVELOPMENT;source018TRAIN only;no final/new-park/night/live camera accuracy',guide='docs/TRANSFER_LEARNING_EXPLAINED.md')
    dump('reports/source_training_latest.json',pointer);dump('reports/anchored_source_training_latest.json',pointer)
    prior=read('data/manifests/open_space_usage_qualification_v4.json')
    usage=dict(prior,version=5,recorded_at=now,parent_usage='data/manifests/open_space_usage_qualification_v4.json',
        parent_usage_sha256=digest(ROOT/'data/manifests/open_space_usage_qualification_v4.json'),run_id=run['run_id'],
        usage_status='Same qualified TRAIN crops used in two rejected development head studies;whole source development-exposed',
        development_training_runs=[plain['run_id'],run['run_id']],diagnosis_run=diag['run_id'],production_admitted=False,independent_final_eligible=False,
        training_protocol='experiments/results/'+run['run_id']+'/protocol.json',training_protocol_sha256=digest(ROOT/'experiments/results'/run['run_id']/'protocol.json'),
        pending=['Do not repeat similar global head fitting without a distinct supported hypothesis',
            'Independent component work:qualify source-consistent Singapore history and freeze future global time holdout before any learned forecast validation',
            'Fresh independent camera final evidence required before any occupancy-model promotion'])
    dump('data/manifests/open_space_usage_qualification_v5.json',usage)
    latest=read('reports/open_space_data_latest.json');latest.update(current_training=pointer,usage_qualification='data/manifests/open_space_usage_qualification_v5.json');dump('reports/open_space_data_latest.json',latest)
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    last=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert digest(ROOT/last['local_path'])==last['sha256']
    payload=read(last['local_path']);rows=parse_feed(payload);raw_lots=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in rows) and len(rows)==len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')));next_poll=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    dump(E/'live_checks.json',dict(receipt=last,summary=live,snapshot_count=snapshots,accepted_rows=len(rows),raw_lot_records=raw_lots,invalid_capacity_excluded=raw_lots-len(rows),
        duplicate_rows=0,bounds_valid=True,next_sensible_collection_after=next_poll,separate100_run_checkpoint_due=False,scope='Previously frozen persistence targets only;no camera/neural live accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-018':item.update(status=usage['usage_status'],development_training_result=pointer,usage_qualification='data/manifests/open_space_usage_qualification_v5.json')
        if item['source_id']=='SRC-LIVE-001':item.update(raw_path=last['local_path'],provider_timestamp=last['provider_timestamp'],snapshot_count=snapshots,observations=len(rows),
            car_parks=len({r['car_park_id'] for r in rows}),raw_lot_records=raw_lots,prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    dump('data/dataset_inventory.json',inventory)
    catalog=ROOT/'data/source_manifest.csv'
    with catalog.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==58
    for item in sources:
        if item['source_id']=='SRC-DS-018':item.update(used_by='16448same qualified TRAIN crops in plain and teacher-anchored development head studies;explicit in-sample diagnostic only,no independent source evaluation',
            status='Both development head ideas rejected;starting research head retained,no app promotion',
            open_issues='Training fit improved1588->497errors on seen source examples,not generalization;plain20/anchored18development errors exceed warm12;source/night/unseen-lot accuracy unmeasured;source-wide development-exposed')
    with catalog.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    state.update(last_updated_at=now,scheduled_wakeups_completed=42,source_transfer_diagnosis=diag['run_id'],anchored_source_training=pointer,
        latest_training_workbook=pointer['workbook'],prospective_live_summary=live,last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Completed paired diagnosis61and one anchored head trial62. Plain transfer corrected3development mistakes but introduced11:net8extra(12->20),newfalse-vacant3removed1. UFPR05regressed9/corrected3;PUCPRregressed2. Added-source TRAIN errors1588->497andCE.294961->.076347are IN-SAMPLE FIT,not independent accuracy. Diagnosis CSV/cache snapshots preserve exact identities;no raw/final data read.',
        'Teacher-anchor trial fixed KLstrength1/temperature2 on ORIGINAL TRAIN only;sourceCEweights.75/.25,6epochmax/2patience. Two epochs,last18development errors/6false-vacant;still worse than warm12/4. Prespecified CE retains epoch0warm,gateFalse. Rawhead/optimizer/RNG/curves/selectedcheckpoint preserved. No app promotion,unseen/night/live accuracy,or causal proof from20vs18(different RNG consumption acknowledged). All model/claim originals and earlier reports unchanged.',
        'Do not continue a grid of similar global linear-head variations on the same2028development labels. Highest independent product task now:inspect captured Singapore source-consistent history for a genuine forecasting study. Before fitting/evaluating a changed learned predictor,freeze chronology,history-only training/development cutoff and a globally future time interval reserved across ALL carparks as final. Existing past snapshots have been seen in baseline/integration work and are DEVELOPMENT,not fresh final data. If history insufficient,record admission limits and continue collection rather than fabricate scores.',
        'For a Singapore forecast study,use only same-source/carpark/lot-type/capacity-consistent observations,real issue/source/target times,freshness and gap controls. All features available at issue time;no future realized horizon/capacity leakage. Compare with persistence on identical matched later targets;unknown/missing targets unscored. Preserve rawJSON/receipts. No transfer of Birmingham validation claim to Singapore and no camera scoring from aggregate counts. New once-only prospective final claim/protocol needed before scoring a selected changed model on reserved future targets.',
        'Source018whole collection remains development-exposed,valid/test semantics unopened,rights qualified only for this source. CNR image-content rights still unresolved/images unopened. Any occupancy candidate promotion needs genuinely fresh independent camera final evidence;all consumed PKLot/Birmingham/DAVIS groups stay closed and earlier failed rainy13/14retention stays failed. Region/background negatives remain unqualified.',
        'Counter62;wakeups42;source58;next separate100-run live checkpoint100;no active jobs/owned lock.245software tests PASS(4new paired-identity tests/3new synthetic teacher-loss tests). New one-sheet comparison workbook '+pointer['workbook']+'and its archive show12/20/18/12development mistakes;formulas/input perturb-restore/ZIPCRC/finalpreview verified,not nativeExcel. Previous workbook preserved. Guide docs/TRANSFER_LEARNING_EXPLAINED.md.',
        'Singapore'+live['checked_at']+':46snapshots,1171new matched frozen persistence targets,39643total,MAE4.856746spaces;1194new forecasts frozen;missing targets unscored. Next sensible collection AFTER'+next_poll+'. No camera/neural live accuracy. Existing424fileoffline demo remains dated. Python/Jupyter preserved;physical/manual/browser/student/official university acceptance remains open.'
    ];dump('data/automation_state.json',state)
    note=('Cached paired diagnosis on SAME2,028development slots:plain study corrected3forced mistakes but introduced11(12->20),added3false-vacant/removed1(4->6). UFPR05accounts9regressions/3corrections,PUCPR2regressions. Newsource TRAIN fit improves1,588->497errors and unweightedCE.294961->.076347on16,448SEEN examples;not generalization accuracy. '+
        'One distinct frozen teacher-anchored head study usesKLstrength1/temperature2against warm predictions on original TRAIN only,sourceCE.75/.25,max6/patience2,seed128. Two epochs completed;lasttrained18errors/6false-vacant,macrodevelopmentCE.025601stillabove warm.019421. Prespecified CE selection retains epoch0warm12errors/4false-vacant;strict improvementFalse,no app promotion.20vs18is not isolated causal evidence because RNG consumption can differ. All failed/trained/optimizer/RNG/cache/curves preserved;original checkpoints/claims unchanged,no final or source018valid/test read. '+
        '245software tests pass;4new synthetic paired-identity and3teacher-loss tests. Diagnosis60->61,anchoredtraining61->62;not perepoch/frame/test. Wakeups42/source58/next100-run milestone100/no active jobs. '+
        'New Excel comparison '+pointer['workbook']+'records12/20/18/12onreused development,seen-training fit,source/data/run IDs and no final performance claim. Artifact-tool formulas6/source counts/input-change restore/ZIPCRC/date fit/actual preview verified;nativeExcel not tested. Earlier workbook and exact newarchive preserved. '+
        'Singapore46snapshots adds1,171causal persistence matches,39,643total,MAE4.856746spaces;1,194newforecasts;missing targets unscored,not neural/camera accuracy. Next independent task:qualify captured Singapore history and reserve fresh FUTURE global time holdout before learned forecast work;stop similar linear-head grid attempts. Student guide:docs/TRANSFER_LEARNING_EXPLAINED.md.')
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','docs/DATASET_PROVENANCE.md','docs/THIRD_PARTY_SOURCES.md']:append(p,note)
    append('docs/UI_TEST_LOG.md','New one-sheet Excel comparison rendered and visually reviewed. Date/time display fitted and rerendered. No main-app/manual/nativeExcel/student acceptance claimed.')
    guide=ROOT/'docs/OPEN_SPACE_DATA_GUIDE.md';text=guide.read_text(encoding='utf-8');text=text.replace('A development-only training study used16,448\nselected crops and did not improve the comparison score. The app stayed unchanged.','Two development-only training studies used the same16,448selected crops.\nNeither beat the starting comparison. The app stayed unchanged.');guide.write_text(text,encoding='utf-8')
    append('docs/OPEN_SPACE_DATA_GUIDE.md','A teacher-retention penalty was tested after paired error diagnosis. The plain study made20development mistakes and this second study18,while the starting comparison made12. Both were rejected. '+
        'Better fit on already-seen training examples is not an independent score. See docs/TRANSFER_LEARNING_EXPLAINED.md and '+pointer['workbook']+'. Source usagev5retains the development-only restriction and all earlier records.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;items=list(reader)
    for row in items:
        if row['requirement_id'] in ['DATA-03','QA-02']:
            row['actual_evidence']+='; models/source_transfer_diagnostics.json; models/anchored_source_development_head.json; reports/anchored_source_training_latest.json'
            row['test_result']+=';paired11regressed/3corrected;teacher-anchored head18errors,warm12retained,gateFAIL;245software tests'
    with req.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(items)
    dump(E/'handoff.json',dict(recorded_at=now,completed_trials=62,wakeups=42,source_records=58,next_live_milestone=100,diagnosis=diag['run_id'],training_result=pointer,
        all245software_tests_passed=True,original_models_claims_reports_unchanged=True,no_active_jobs=True,next_sensible_live_collection_after=next_poll))
    print(json.dumps(dict(trials=62,wakeups=42,workbook=pointer['workbook'],snapshots=snapshots),indent=2))
if __name__=='__main__':main()
