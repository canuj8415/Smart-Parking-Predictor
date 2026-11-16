"""Record frozen occupancy diagnostics, source-label gaps and continuation."""
import csv,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
C='OCCUPANCY-BROADER-20261025T084307397022Z';F='OCCUPANCY-FUSION-20261025T084837737165Z'
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T083725Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def rows(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f);return r.fieldnames,list(r)
def table(p,fields,values):
    with (ROOT/p).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL if p=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);w.writeheader();w.writerows(values)
def append(p,text):
    title='25October2026 / frozen occupancy and detector-fusion reliability'
    path=ROOT/p;old=path.read_text(encoding='utf-8')
    if title not in old:path.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat();c=read('experiments/results/'+C+'/run.json');f=read('experiments/results/'+F+'/run.json')
    tests=(E/'unit_tests_final.txt').read_text(encoding='utf-8-sig');assert re.search('Ran 95 tests',tests) and tests.rstrip().endswith('OK')
    write(E.relative_to(ROOT)/'software_checks.json',dict(checked_at=now,tests_passed=95,failures=0,scope='Probability/categorical confusion, uncertainty denominators, invalid inputs, prior product regressions; not camera accuracy'))
    previous=read('experiments/evidence/HEARTBEAT-20261025T003925Z/production_unchanged.json')
    for p,h in previous.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    write(E.relative_to(ROOT)/'production_unchanged.json',previous)
    write('models/occupancy_broader_evaluation.json',c);write('models/occupancy_fusion_evaluation.json',f)
    # Recompute the documented comparison from immutable saved row decisions.
    predictions=read('experiments/results/'+F+'/predictions.json');changes=[r for r in predictions if r['classifier_state']!=r['fused_state']]
    assert len(changes)==7 and all(r['classifier_state']=='vacant' and r['fused_state']=='uncertain' for r in changes)
    assert sum(r['label']==1 for r in changes)==2
    write(E.relative_to(ROOT)/'comparison_checks.json',dict(source_labelled_slots=948,source_missing_labels=396,changed_decisions=7,
        occupied_caught_as_uncertain=2,vacant_withheld_as_uncertain=5,remaining_false_vacant=1,thresholds_unchanged=True,weights_unchanged=True,
        final_images_decoded=0,final_annotations_decoded=0,figures_visually_reviewed=['occupancy_confusion_comparison.png','false_vacancy_examples.png']))
    write(E.relative_to(ROOT)/'source_document_review.json',dict(date='2026-10-25',source_id='SRC-DS-001',publisher_page='https://web.inf.ufpr.br/vri/databases/parking-lot-database/',
        review='Publisher describes XML slot locations and occupancy labels. No absent-attribute default was established from this page. Local original XML has396missing attributes in4selected frames.',
        official_readme='https://www.inf.ufpr.br/lesoliveira/download/pklot-readme.pdf',readme_result='Web fetch timed out; not downloaded or read',policy='Retain unknown labels; no imputation or claim of complete-camera ground truth'))
    fields,registry=rows('experiments/EXPERIMENT_REGISTRY.csv');known={r['experiment_id'] for r in registry}
    for ident,r in [(C,c),(F,f)]:
        if ident in known:continue
        directory='experiments/results/'+ident
        value=dict(experiment_id=ident,run_type='Frozen classifier-only broader occupancy evaluation' if ident==C else 'Existing detector/classifier fusion comparison; no fitting',started_at=r['started_at'],finished_at=r['finished_at'],
            source_ids=';'.join(r['source_ids']),split_ids='Broader24development frames/6dates;948explicit labels;396unknown excluded; final closed',configuration=directory+'/protocol.json',
            architecture='Frozen project ResNet18 classifier' if ident==C else 'Unmodified Faster R-CNN ResNet50 + frozen ResNet18 + existing slot fusion',model_version=r.get('classifier_run_id','existing unmodified pipeline'),
            epochs=0,batch_size=r.get('batch_size','image plus existing classifier batch'),random_seed=r['seed'],hardware='CPU4threads; BLAS1/OMP2/MKL2',execution_environment='Python3.12.10; Torch2.14.0+cpu',training_duration=r['duration_seconds'],
            evaluation_metrics=json.dumps(dict(metrics=r['metrics'] if ident==C else r['fused'],diagnostic_gate_passed=r['diagnostic_gate_passed'])),logs=directory,checkpoints='Existing unchanged classifier/detector files',
            code_revision_basis='132621d plus sealed exact source snapshots',implementation_sha256=r['code_sha256']['scripts/evaluate_broader_occupancy.py' if ident==C else 'scripts/evaluate_broader_fusion.py'],
            conclusions='Hard accuracy98.42% on948labelled crops; band3false vacancies/395vacant calls; camera gate fails;396unknown labels excluded' if ident==C else 'Same948labels:3->1false vacancies,6->13uncertain; diagnostic gate passes; no model/threshold change or complete-camera accuracy')
        registry.append({k:value.get(k,'') for k in fields})
    table('experiments/EXPERIMENT_REGISTRY.csv',fields,registry)
    live=read('data/processed/singapore_prospective/summary.json')
    receipts=[json.loads(r) for r in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()];latest=[r for r in receipts if r['source_id']=='SRC-LIVE-001'][-1]
    from sys import path as module_path
    module_path.insert(0,str(ROOT/'src'))
    from smart_parking.live import parse_feed
    raw=read(latest['local_path']);valid=parse_feed(raw);assert len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in valid})==len(valid)
    assert hashlib.sha256((ROOT/latest['local_path']).read_bytes()).hexdigest()==latest['sha256']
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=latest,accepted_lot_observations=len(valid),car_parks=len({r['car_park_id'] for r in valid}),raw_lot_records=sum(len(r['carpark_info']) for r in raw['items'][0]['carpark_data']),duplicates=0,bounds_valid=True,
        interpretation='No new scores at08:40because08:25forecasts were before their20min target window; keep pending outcomes unscored. No camera/neural live accuracy.'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-001':item['broader_occupancy_evaluation']=dict(classifier_run=C,fusion_run=F,frames=24,date_groups=6,explicit_labels=948,unknown_labels=396,label_coverage=948/1344,
            classifier_hard_accuracy=c['metrics']['hard']['accuracy_on_covered'],fused_false_vacant=1,fused_predicted_vacant=388,fused_uncertain=13,diagnostic_gate_passed=True,full_camera_accuracy_evaluated=False)
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in valid}),observations=len(valid),raw_lot_records=sum(len(r['carpark_info']) for r in raw['items'][0]['carpark_data']),provider_timestamp=latest['provider_timestamp'],raw_path=latest['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==20
    state.update(scheduled_wakeups_completed=12,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['occupancy_reliability']=dict(classifier_run=C,fusion_run=F,labelled_slots=948,unknown_slots=396,classifier_hard_accuracy=c['metrics']['hard']['accuracy_on_covered'],
        classifier_band_false_vacant=3,fused_false_vacant=1,fused_vacant_predictions=388,fused_uncertain=13,diagnostic_gate_passed=True,weights_or_thresholds_changed=False)
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;8scored issue cohorts; source matching is not camera accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Next scheduled collection should score08:25/08:40forecasts only against actual later fresh same-capacity targets. Current2323pending at08:40;9074scored;4466expired. Counter20,next separate100-run checkpoint100.',
        'Frozen occupancy and existing fusion now have development evidence on948labelled slots;396missing attributes stay unknown. Fusion changes2risky vacant calls to uncertain but1remains. Diagnostic pass is limited: do not tune thresholds on observed errors or claim complete-camera accuracy.',
        'Investigate the remaining ufpr05slot40case using training-data diagnosis/predeclared robustness, not post-hoc score thresholds. Any calibration/refit needs a training-only design and fresh final evaluation. Preserve current weights and every error case.',
        'Broader region trial0.797653still fails gates, shared final6closed. Forecast candidates still fail per-park gates; actual target times must accompany a bounded robustness study. MetaPKLot remains inspection-only.',
        'Application gate editor, labelled flow footage, native export-save, report compilation, physical/fresh offline, university documents and student rehearsal remain unfinished. Dated slides/guide retain their earlier metrics; latest explanation is docs/OCCUPANCY_RELIABILITY.md.'
    ]
    write('data/automation_state.json',state)
    overview='''Completed two frozen, preregistered development trials on the same24frames/
6dates/3known cameras.948slots have explicit original0/1labels;396slots in
4PUCPR2012-10-30frames lack the occupied attribute (99each) and stay unscored.
Label coverage948/1344=70.54%; crops/date groups are correlated. No full-camera
accuracy or independent final-test claim; no labels imputed or passed to engine.

OCCUPANCY-BROADER-20261025T084307397022Z: frozen existing ResNet18 classifier
hard0.5accuracy933/948=98.42%, confusion[[395,11],[4,538]]. Existing0.25/0.75
band:942decisions/6uncertain,3false-vacant among395vacant predictions(0.759%).
UFPR05has3/77wrong vacancy calls(3.90%), so the preregistered per-camera
diagnostic gate fails despite the aggregate. Brier0.01362 and probability
ECE0.01175 are descriptive, not individual confidence guarantees. Old360crop
test95.28%remains a separate cohort; this evaluation did not improve weights.

OCCUPANCY-FUSION-20261025T084837737165Z: unchanged Faster R-CNN/ResNet50+
classifier+existing geometry rules, confidence0.5and same uncertainty bands.
Geometry-only inputs exclude answer labels. Full24frame engine inference makes
7classifier-vacant decisions uncertain:2source-labelled occupied and5vacant.
False-vacant3->1,uncertain6->13. Fusion answers935/948(98.63%coverage), with
accuracy924/935=98.82%on answered cases. Vacancy precision387/388=99.74%,
wrong-free fraction1/388=0.258%; UFPR05remaining1/72=1.389%. The limited
diagnostic gate passes; deployment/whole-camera/perfect accuracy does not follow.
Remaining case:ufpr05slot40,2013-03-21,score0.0828. Original source labels remain
the reference, without independent human relabelling. No weights, thresholds or
production rules changed. Classifier score difference across batches<2e-10.

Protocols/code/checkpoint/input hashes, all crop scores, per-frame/date/camera
counts, label-availability audit, remaining error and credited real-input figures
retained.95software tests pass. Initial metrics import found a dictionary syntax
error before evaluation; it was corrected and all subsequent suites passed.
Three production checkpoint hashes unchanged; shared final6images/XML unopened.
Two real validation trials bring counter20; next100-run checkpoint100. No jobs
active. Mask/forecast acceptance failures remain separate from this diagnostic.

Official snapshot08:40UTC retained rawJSON/history/receipt/checksum and froze1139
new forecasts;0new scores because08:25targets had not reached20minutes yet.
15863issued/9074scored,4466expired and2323pending at collection. Matched-only
persistenceMAE3.7976637unchanged;67.02%resolved matching is not accuracy. No
neural Singapore or camera/flow live score invented. All16snapshots remain.

Publisher PKLot page rechecked25October: it describes XML occupancy annotations,
but no missing-attribute default was established from that page. Official readme
fetch timed out. Missing attributes remain unknown under the frozen protocol.
New easy explanation:docs/OCCUPANCY_RELIABILITY.md. Earlier reports/slide deck
remain dated snapshots. Remaining product/final-report/offline/student tasks and
exact next actions stay in data/automation_state.json.'''
    for p in ['docs/AUTONOMOUS_PROGRESS.md','docs/PROJECT_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/TEST_RESULTS.md','95software checks pass. Two frozen occupancy diagnostics:948labelled/396unknown slots; class band3false-vacancy calls vs existing fusion1, with6->13uncertain. Fusion passes the limited predeclared diagnostic; no whole-camera/new-camera/final-test claim. Exact source, output arithmetic and input-crop hash checks retained.3production hashes unchanged; no threshold fitting. Evidence HEARTBEAT-20261025T083725Z and OCCUPANCY-BROADER/FUSION result folders.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant implemented separate probability/categorical evaluation metrics with denominator tests, preregistered and executed frozen classifier and existing full-pipeline checks, audited396missing source labels, reviewed publisher documentation, plotted actual errors, and recorded evidence.95software checks pass after a corrected initial import syntax error. No student independent contribution, retraining, threshold tuning or final-test result is implied.')
    for p in ['docs/RESEARCH_LOG.md','docs/THIRD_PARTY_SOURCES.md']:append(p,'PKLot original source SRC-DS-001 reused under existing attribution/CC BY4.0. Primary publisher page https://web.inf.ufpr.br/vri/databases/parking-lot-database/ reviewed25October2026: general XML label description does not establish a default for absent attributes. Official https://www.inf.ufpr.br/lesoliveira/download/pklot-readme.pdf fetch timed out; no download/read claim. Local4selected original XMLs have396missing occupied attributes. No labels repaired/imputed; exact original files, crop transforms and attribution retained.')
    fields,sources=rows('data/source_manifest.csv')
    for item in sources:
        if item['source_id']=='SRC-DS-001' and '948labelled' not in item['used_by']:
            item['used_by']+='; frozen classifier/fusion evaluation on948labelled development slots,396unknown excluded'
            item['open_issues']+='; explicit occupancy attributes absent for396slots in4selected PUCPR2012-10-30frames; default meaning not established, no imputation'
    table('data/source_manifest.csv',fields,sources)
    fields,requirements=rows('docs/REQUIREMENTS.csv')
    for q in requirements:
        if q['requirement_id']=='OCC-01':q.update(actual_evidence=q['actual_evidence']+'; models/occupancy_fusion_evaluation.json',test_result='Same948labelled slots: existing fusion reduces false-vacant3->1, uncertain6->13; proposed diagnostic passes;95software checks',open_problems='396unknown labels;3known cameras/6dates; remaining false vacancy; no complete-camera or unseen-camera guarantee')
        if q['requirement_id']=='CLS-01':q['actual_evidence']+='; models/occupancy_broader_evaluation.json'
        if q['requirement_id']=='DATA-02':q['actual_evidence']+='; data/manifests/broader_occupancy_label_coverage_v1.json';q['open_problems']='396missing occupancy attributes in broader24frames remain unknown; full-archive/perceptual audit incomplete'
    table('docs/REQUIREMENTS.csv',fields,requirements)
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Fifteen authorized public snapshots acquired','Sixteen authorized public snapshots acquired').replace('88 tests pass; network-disabled-process image check passes','95 tests pass; network-disabled-process image check passes')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','Frozen broader occupancy:948explicit labels/396unknown. Class hard accuracy98.42%on this development cohort; existing fusion reduces confident false-vacancy3->1 and leaves13uncertain. Limited diagnostic gate passes; no full-camera/final accuracy or production change.95software checks pass; counter20. Source label gaps and remaining error retained. Live16snapshots/9074matched persistence outcomes; later08:25/08:40targets still pending at last collection.')
    print(json.dumps(dict(counter=20,tests=95,classifier_hard_accuracy=c['metrics']['hard']['accuracy_on_covered'],fused_false_vacant=1,fused_uncertain=13,diagnostic_passed=True),indent=2))
