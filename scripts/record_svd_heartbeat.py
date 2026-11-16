"""Record the completed numerical lesson, actual notebook and collection gap."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed

E=ROOT/'experiments/evidence/HEARTBEAT-20261025T191535Z'
RUN='SVD-LESSON-20261025T191732227032Z'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('This dated heartbeat is already recorded')
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');run=read('models/svd_lesson_validation.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==36
    assert state['scheduled_wakeups_completed']==23 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['run_id']==RUN and run['validation_gate_passed']
    assert all(digest(ROOT/p)==h for p,h in run['source_hashes'].items())
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in production.items())
    notebook_path='notebooks/08_image_patterns_and_svd.ipynb';notebook=read(notebook_path)
    code=[c for c in notebook['cells'] if c['cell_type']=='code']
    assert len(code)==4 and all(c['execution_count'] is not None for c in code)
    assert not any(o.get('output_type')=='error' for c in code for o in c.get('outputs',[]))
    assert any('image/png' in o.get('data',{}) for c in code for o in c.get('outputs',[]))
    assert 'Notebook executed and saved successfully' in (E/'notebook_execution_2.txt').read_text(encoding='utf-8-sig')
    tests=(E/'unit_tests.txt').read_text(encoding='utf-8-sig');assert 'Ran 181 tests' in tests and tests.rstrip().endswith('OK')
    folder=ROOT/'experiments/results'/RUN
    figures={name:digest(folder/name) for name in ['rank_comparison.png','rank_comparison_reviewed.png','lesson_view.png']}
    write(E.relative_to(ROOT)/'artifact_checks.json',dict(notebook=notebook_path,notebook_sha256=digest(ROOT/notebook_path),
        executed_code_cells=4,saved_errors=0,inline_plot_embedded=True,figures=figures,
        first_grid_label_overlap_preserved=True,reviewed_grid_and_lesson_plot_visually_checked=True,
        repair='Layout only; no changed model/inference/accuracy evaluation; original plot retained',
        notebook_attempt1='Cancelled with no diagnostics after about3minutes; exact cause unknown',
        notebook_attempt2='Project-kernel run with explicit inline plot completed successfully'))
    write(E.relative_to(ROOT)/'limit_interruption.json',dict(recorded_at=now,
        interrupted_wakeup='2026-10-25T17:15:33.924Z',
        evidence='Automatic approval review reported account usage limit; a follow-up patch/read was not executed.',
        effect='Partial SVD module/app/tests persisted; no completed trial counted before resumption. No capacity workarounds or purchases.',
        resumed_wakeup='2026-10-25T19:15:35.978Z',
        collection_gap='Last successful feed16:52UTC; next19:16UTC. No fabricated missing observations or accuracy during the gap.'))
    sources_path=ROOT/'data/source_manifest.csv'
    with sources_path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==51 and not any(r['source_id']=='SRC-DOC-018' for r in sources)
    record=dict(source_id='SRC-DOC-018',resource_type='Official numerical API documentation',resource='NumPy2.5 numpy.linalg.svd',
        original_creator='NumPy developers',source_url='https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html',
        access_date='2026-10-25',access_time_precision='Date-only web documentation review; no local documentation download',
        version='NumPy2.5 manual; installed NumPy2.5.3',license='Documentation copyright NumPy developers; technical reference, no documentation assets/source excerpts copied',
        permission='Public API reference; existing installed NumPy licence notices retained',local_location='No documentation assets downloaded',
        purpose='Reduced SVD factor shapes/reconstruction convention for bounded real-image teaching lesson',
        used_by=RUN+';src/smart_parking/decomposition.py;notebooks/08_image_patterns_and_svd.ipynb',
        modifications='Independent lesson/application implementation; NumPy supplies the decomposition solver',
        attribution='NumPy developers; official SVD API documentation',status='used as technical reference',
        open_issues='Numerical teaching only; no from-scratch SVD solver, JPEG compressor or detector improvement claimed')
    sources.append({key:record.get(key,'') for key in fields})
    for row in sources:
        if row['source_id']=='SRC-DS-014':
            row.update(local_location='data/raw/traffic_candidate_metadata/mendeley_5d8k5bkb93_v1.html (publisher page only)',
                       status='publisher HTML acquired; dataset assets unacquired',
                       open_issues='125044-byte official HTML confirms dataset/CC BY4.0 with third-party rights caveat. Public file-browser bundle returned403; no bypass, login, images or annotations. File inventory/per-video credits still unresolved.')
    assert len(sources)==len({row['source_id'] for row in sources})==52
    with sources_path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    live=read('data/processed/singapore_prospective/summary.json');payload=read(receipt['local_path']);rows=parse_feed(payload)
    assert live['scores_added']==0 and live['scores_total']==22850 and live['forecasts_added']==1147
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        interpretation='Collection gap means no new admissible earlier target matches. Existing matched-only MAE unchanged; expired targets unscored, not zero error.'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=29,
            prospective_baseline_scored_outcomes=22850,prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    metadata_receipt=next(r for r in receipts if r['local_path']=='data/raw/traffic_candidate_metadata/mendeley_5d8k5bkb93_v1.html')
    assert digest(ROOT/metadata_receipt['local_path'])==metadata_receipt['sha256']
    inventory['datasets'].append(dict(source_id='SRC-DS-014',status='publisher_metadata_only',metadata_receipt=metadata_receipt,
        dataset_images_acquired=0,dataset_annotations_acquired=0,used_for_training=False,used_for_evaluation=False))
    write('data/dataset_inventory.json',inventory)
    state.update(last_updated_at=now,scheduled_wakeups_completed=24,
        svd_lesson=dict(run_id=RUN,guide='docs/IMAGE_COMPRESSION_LESSON.md',notebook=notebook_path,
            notebook_sha256=digest(ROOT/notebook_path),executed_code_cells=4,hidden_native_checks=True,visible_manual_acceptance=False),
        last_live_baseline_score=dict(outcomes=22850,mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['local_demo_bundle']['newer_source_changes_not_in_bundle']=['src/smart_parking/live.py','src/smart_parking/app.py','src/smart_parking/decomposition.py','notebooks/08_image_patterns_and_svd.ipynb']
    state['next_actions']=[
        'New SVD lesson completed:8 executed notebooks,36recorded trials/181software tests. Module/app/source checks and training-only image preserved; not detector preprocessing/accuracy. Read docs/IMAGE_COMPRESSION_LESSON.md. Student exercises/mastery pending.',
        'Refresh dated demo bundle at a meaningful acceptance milestone to include live.py guards and SVD lesson; prior184-file demo remains intact. Visible/manual-dialog,fresh installation,physical-offline and student rehearsal remain unverified; do not alter unrelated networking.',
        'Fresh labelled fixed-camera counting still blocked by data suitability. Source14 official HTML acquired, file-browser script403; no bypass/login or dataset assets. Source13 remains inspection-only, coordinate/label/rights gaps. Seek a legitimate independently labelled public source without reusing any consumed DAVIS/image/Birmingham finals.',
        'Technical report16:35 snapshot and older slides/Excel stay dated. New source catalog52; earlier report45andledger34/167 is an intentional historical snapshot. University documents/official template/student mastery still missing.',
        'Last official collection19:16UTC after usage-limit gap:29snapshots;22850matched baseline outcomes/MAE4.186346 unchanged;0new matches,7872expired/1147pending,74.38%resolved matching. Next sensible collection after19:46UTC; no per-simulation polling. Counter36; separate100-run milestone100. No active jobs.'
    ];write('data/automation_state.json',state)
    title='## 25 October 2026 / SVD lesson completed after usage-limit interruption'
    note='''SVD lesson now works in the Python app Convolution lab and executed notebook08.
Use1to160patterns on a resized256x160 grayscale view. One existing hash-bound
training-only PKLot image, no final labels/pixels or detector preprocessing.
Rank16:6,672factor numbers vs40,960grayscale numbers,53,376vs327,680float64bytes
(16.29%),MSE0.00465324,retained numerical energy98.6283%. This is not JPEG file
compression,model accuracy or an image-quality guarantee. Full rank maximum error
2.0539e-14 and factor storage162.89%; more patterns can require more memory.
No trained weights changed. NumPy supplies SVD; implementation provides bounded
input/rank checks, complete storage accounting, plots and app/notebook integration.

One recorded numerical/native trial advances35->36, not one run per rank/cell.
Five new numerical unit checks; all181software tests pass. Hidden native app tests
check ranks16/48,invalid/busy guards,2D/3D/SVD switching and no accumulating figures.
Eight notebooks now executed; notebook08has4code cells,zero saved errors and an
inline figure. First notebook attempt cancelled without diagnostics after about
3minutes; project-kernel retry with explicit inline display passed. Original grid
had overlapping row labels and is retained; separate reviewed layout fixes that
without a model rerun. Native visible/manual acceptance and student understanding
remain unverified. Guide:docs/IMAGE_COMPRESSION_LESSON.md.

Earlier17:15wake stopped when automatic approval review hit the account usage
limit; the attempted follow-up patch/read was not executed. WIP files persisted;
no completed run was counted then. Work resumed at19:15after access returned,
without bypasses,purchases or credits. Skipped wakeups are not completed trials.
Source14official125044-byte HTML acquired; public client-script403stopped file
inspection,no bypass/login/dataset images/annotations. New official NumPy2.5SVD
reference SRC-DOC-018 brings catalog52. Traffic evidence remains unqualified.

Actual19:16UTC Singapore snapshot29 follows a16:52->19:16collection gap. No new
admissible prior-target matches:22850matched/MAE4.186346unchanged;7872expired,
1147pending,74.38%resolved matching. Missing targets are unscored,not zero error.
New1147forecasts await later actual observations. Raw JSON,normalized CSV,URL,time,
SHA and bounds/duplicates retained. No neural/camera live accuracy.

No active jobs; counter36,next100-run checkpoint100. Original weights,failed
experiments and consumed final groups remain preserved. Old demo/report/Excel/
slides retain their dated scope; demo lacks latest live/SVD source. Next:meaningful
demo acceptance,legitimate fresh labelled counting evidence,and student practice.
Whole project,official university compliance and universal accuracy unclaimed.'''
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        p=ROOT/name;text=p.read_text(encoding='utf-8');assert title not in text
        p.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    p=ROOT/'docs/UI_TEST_LOG.md';p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nActual hidden-native app rank switching,invalid/busy guards and2D/3D/SVD chart replacement pass; figures do not accumulate. Original input image unchanged. No visible/manual acceptance or detector score. See models/svd_lesson_validation.json.\n',encoding='utf-8')
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=p.read_text(encoding='utf-8').replace('Seven executed teaching notebooks','Eight executed teaching notebooks')
    text=text.replace('07continuation/final limits |','07continuation/final limits,08image-pattern/SVD lesson |')
    text=text.replace('Twenty-eight authorized public snapshots acquired','Twenty-nine authorized public snapshots acquired')
    text=text.replace('| Tests/offline | 176 tests pass;','| Tests/offline | 181 tests pass;')
    text=text.replace('| From-scratch MLP |','| Image compression lesson | Numerical SVD/app/notebook checks pass | One training image; rank16factor memory16.29%of grayscale matrix; not JPEG size or detector accuracy; student mastery unassessed |\n| From-scratch MLP |')
    p.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    p=ROOT/'docs/REQUIREMENTS.csv'
    with p.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id']=='MATH-04':row.update(status='Tested',actual_evidence='src/smart_parking/decomposition.py; notebooks/08_image_patterns_and_svd.ipynb; models/svd_lesson_validation.json; docs/IMAGE_COMPRESSION_LESSON.md',
            test_result='Full reconstruction/error-energy/monotonicity/storage checks; real training-image/native integration gate passes;181software tests;4notebook code cells executed',
            open_problems='NumPy supplies solver; not from-scratch SVD/JPEG codec/model accuracy; independent student mastery and official unit compliance unverified',next_action='Student changes rank and explains reconstruction/storage tradeoff without assistance')
        if row['requirement_id']=='SRC-01':row['test_result']='52 unique source records; permanent IDs/licence/use/admission limits retained'
    with p.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    for name in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md']:
        p=ROOT/name;p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nSource catalog52. NumPy2.5SVD official technical reference SRC-DOC-018 supports the independent numerical lesson; no source text/code copied. PKLot training-image derivatives credited. Source14official HTML only, file-browser bundle403; no dataset labels/images acquired or use admitted. See docs/IMAGE_COMPRESSION_LESSON.md.\n',encoding='utf-8')
    write(E.relative_to(ROOT)/'checks.json',dict(run_id=RUN,completed_trials=36,software_tests=181,source_records=52,
        notebook_code_cells=4,notebook_errors=0,training_image_only=True,hidden_native_checks=True,
        reviewed_plot_layout=True,original_models_unchanged=True,no_raw_final_reread=True,active_jobs=[],
        live_snapshot_count=29,new_live_matches=0,live_matched_outcomes=22850))
    print(json.dumps(dict(completed_trials=36,software_tests=181,sources=52,notebook_code_cells=4),indent=2))


if __name__=='__main__':main()
