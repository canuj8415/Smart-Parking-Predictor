"""Save combined-package acceptance and a concise truthful continuation ledger."""
import csv,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T221738Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,value):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    path=ROOT/p;old=path.read_text(encoding='utf-8');assert title not in old
    path.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')
def main():
    if (E/'checks.json').exists():raise RuntimeError('Dated wake already saved')
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');rid=state['last_completed_run']
    run=read('experiments/results/'+rid+'/run.json');checks=read(E.relative_to(ROOT)/'package_checks.json');package=ROOT/run['package']
    assert run['combined_demo_gate_passed'] and checks['fresh_environment_inside_copy'] and checks['existing_environment_overwrite_refused']
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==43 and state['scheduled_wakeups_completed']==29
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert all(digest(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes']}.items())
    assert run['payload_files']==419 and run['payload_bytes']==806444601
    assert all(digest(package/e['path'])==e['sha256'] for e in run['payload'])
    previous=read('reports/demo_package_latest.json');history=ROOT/'reports/demo_package_history'/previous['run_id'];history.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(ROOT/'reports/demo_package_latest.json',history/'latest_pointer.json')
    pointer=dict(run_id=rid,kind='Combined selected demo and107-wheel offline installer',path=run['package'],
        files=run['payload_files'],bytes=run['payload_bytes'],manifest_sha256=digest(package/'BUNDLE_MANIFEST.json'),
        validation_sha256=digest(package/'COMBINED_VALIDATION.json'),guide='docs/COMBINED_OFFLINE_DEMO_GUIDE.md',
        fresh_package_environment=run['package']+'/.venv',runtime_reused=False,existing_base_python_reused=True,
        fresh_package_install_verified=True,physical_network_disconnection_verified=False,new_machine_verified=False,visible_manual_acceptance=False,
        python=run['package']+'/.venv/Scripts/python.exe',installer_wheels=107,installer_bytes=257829508,
        included_notebooks=['08_image_patterns_and_svd.ipynb'],actual_copied_folder_kernel_verified=True,previous_run=previous['run_id'],
        previous_pointer_archive=(history/'latest_pointer.json').relative_to(ROOT).as_posix(),scientific_accuracy_evaluated=False)
    cached=next(e['path'] for e in run['payload'] if e['path'].startswith('data/raw/singapore_live/') and e['path'].endswith('.json'))
    pointer.update(cached_live_snapshot=cached,cached_live_provider_timestamp=read(package/cached)['items'][0]['timestamp'])
    write('reports/offline_demo_latest.json',pointer);write('reports/demo_package_latest.json',pointer);write('models/combined_offline_demo_package.json',run)
    folder=ROOT/'experiments/results'/rid
    write(E.relative_to(ROOT)/'probe_outputs.json',{name:dict(stdout=(folder/(name+'_stdout.txt')).read_text(encoding='utf-8'),
        stderr=(folder/(name+'_stderr.txt')).read_text(encoding='utf-8')) for name in ['install','app','notebook']})
    write(E.relative_to(ROOT)/'artifact_identity.json',dict(pointer=pointer,ready=read(package/'READY.json'),
        payload_manifest_sha256=pointer['manifest_sha256'],start_here_sha256=digest(package/'START_HERE.md'),
        old_demo_manifest_unchanged=digest(ROOT/previous['path']/'BUNDLE_MANIFEST.json')==previous['manifest_sha256'],
        scope='419copied payload files; generated .venv/metadata/outputs not counted as payload. No base Python/full data/all8notebooks distribution.'))
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    latest=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert digest(ROOT/latest['local_path'])==latest['sha256']
    from smart_parking.live import parse_feed
    payload=read(latest['local_path']);rows=parse_feed(payload);raw_lots=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in rows) and len(rows)==len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in rows})
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=latest,accepted_rows=len(rows),raw_lot_records=raw_lots,
        invalid_capacity_excluded=raw_lots-len(rows),bounds_valid=True,duplicate_rows=0,not_a100_run_checkpoint=True,
        scope='Later source observations score previously frozen persistence forecasts;not neural/camera accuracy. Bundle snapshot remains separately dated.'))
    inventory=read('data/dataset_inventory.json');inventory.update(inventoried_at=now,combined_offline_demo=pointer)
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_lots,
            raw_path=latest['local_path'],provider_timestamp=latest['provider_timestamp'],snapshot_count=snapshots,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state.update(last_updated_at=now,scheduled_wakeups_completed=30,combined_offline_demo=pointer,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Combined copied-folder gate passes:419payload files/806444601bytes,107original wheels/full notices,NEW package-local .venv installed no-index/hash-locked;both actual hidden detector/export/semantic/cached-live/archived-forecast/SVD/2video routes and genuine notebook08kernel pass. See reports/offline_demo_latest.json/docs/COMBINED_OFFLINE_DEMO_GUIDE.md. Original datasets/checkpoints and older packages preserved.',
        'Prioritize genuinely fresh independent labelled parking-camera data and an evidence-driven model improvement. Current image/Birmingham/DAVIS final groups are consumed;never tune/re-evaluate changed methods on them. Existing source13inspection/source14rights-access gaps remain. Public read-only research/small licensed acquisitions allowed;no bypass/private access/contact.',
        'Remaining demonstration acceptance:visible browser/frontend JavaScript,manual dialogs/physical disconnection/new machine,student explanation/rehearsal and missing official university documents. Only notebook08and selected demo assets are in combined bundle;full training data/other7notebooks stay in main project. Rebuild venv if moving paths;do not overwrite verified environments.',
        'Do not rebuild identical packages/repeat model inference merely to inflate counts. Latest dated report/Excel/slides remain historical snapshots. Normal package audits have zero denials;separate deliberate fallback/DNS probes are expected blocked controls,not live observations. No model training or new scientific accuracy this wake.',
        'Counter43;next separate100-run live checkpoint100. Source catalog57unchanged;metadata/107wheels copied with hashes,not newly downloaded. No active jobs. Current server and full184software regression evidence remain separately dated.',
        'Latest Singapore observation '+latest['accessed_at']+':'+str(snapshots)+'snapshots,'+str(live['scores_total'])+'matched earlier persistence targets,MAE'+format(live['baseline_mae_spaces'],'.6f')+'. Bundle retains its frozen earlier snapshot. Continue sensible half-hour cadence and causal scoring;missing targets remain unscored.'
    ];write('data/automation_state.json',state)
    title='## 25 October 2026 / combined offline demonstration verified in a fresh copy'
    note=('Combined selected local demo passes:419copied payload files,806,444,601bytes,including107original offline wheel archives (257,829,508bytes),their publisher metadata/full notices and frozen app/model/data assets. '
        'NEW .venv inside the copy installs no-index/hash-locked;all107expected versions verified,dependency check passes. Both actual hidden detector/export/semantic/archived forecast/cached live/SVD/progress/video routes pass. '
        'Actual copied-folder Jupyter kernel executes notebook08with inline plot;no stripped-magic-only claim. Both detector training-example counts agree68/32/0out of100,not accuracy. '
        'Normal Python fallback/non-loopback audits have zero denials;separate original-README/DNS probes correctly blocked. Existing-environment overwrite rejected without changing config. '
        'All payload hashes,original model/notebook/final claims and earlier demo bytes unchanged. Existing Windows/base Python/Tk reused;native extensionIO/physical offline,new-machine,visible/manual and student/official acceptance unverified. '
        'Selected package excludes full datasets/other7notebooks;rebuild environment after moving paths. Source catalog57;copying existing archives is not a new download. '
        'One completed combined trial advances42->43. Latest Singapore snapshot'+str(snapshots)+':'+str(live['scores_total'])+'matched later baseline outcomes,MAE'+format(live['baseline_mae_spaces'],'.6f')+'spaces;no neural/camera live accuracy. '
        'Main live history is newer than frozen bundle snapshot. Guide:docs/COMBINED_OFFLINE_DEMO_GUIDE.md;pointer:reports/offline_demo_latest.json. Next scientific priority:fresh legitimate independent labels;remaining manual/student/academic gates separate.')
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,title,note)
    append('docs/UI_TEST_LOG.md',title,'Actual hidden copied-folder app with freshly installed runtime exercises both models,exports,semantic separation,archived forecasts,cached live,SVD/progress and bounded video. Genuine copied-folder notebook kernel returns inline plot. Mocked dialogs;no visible browser/manual/physical/new-machine acceptance.')
    for p in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md']:append(p,title,'Catalog57unchanged.419copied payload records preserve original hashes/source IDs,107original installer archives with full notices and107official per-release metadata files. No new package download or external publication. Wider source register is not an assertion that full datasets are included. Local academic use;external redistribution clearance remains unclaimed.')
    old=(ROOT/'docs/DEMO_PACKAGE_GUIDE.md').read_text(encoding='utf-8')
    (ROOT/'docs/DEMO_PACKAGE_GUIDE.md').write_text('# Current combined offline package\n\nThe latest selected demo now includes its107-wheel installer set and a freshly verified package-local environment. See docs/COMBINED_OFFLINE_DEMO_GUIDE.md and reports/offline_demo_latest.json. The older runtime-only package below is retained as history.\n\n## Historical runtime-only demo\n\n'+old,encoding='utf-8')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;requirements=list(r)
    for row in requirements:
        if row['requirement_id']=='PKG-01':row.update(status='In progress',actual_evidence='reports/offline_demo_latest.json; models/combined_offline_demo_package.json; docs/COMBINED_OFFLINE_DEMO_GUIDE.md',
            test_result='419payload files/806444601bytes;107-wheel installer plus NEW copied-folder venv,actual app/export/video and genuine notebook08kernel checks pass',
            open_problems='Selected demo only;full training data/other7notebooks/basePython excluded;visible/manual/physical/new-machine/student and official acceptance remain',next_action='Retain verified package;prioritize fresh scientific labels and remaining manual/student acceptance rather than repeated rebuilds')
        if row['requirement_id']=='OFF-01':row.update(test_result='Combined copy installs NEW107-package local venv offline;actual detector/export/video/cached app and real Jupyter kernel pass;original fallback controls block',
            actual_evidence='reports/offline_demo_latest.json; docs/COMBINED_OFFLINE_DEMO_GUIDE.md; prior offline/server/regression checks preserved',
            open_problems='Base Python/Windows/Tk reused;native IO/physical disconnection,new machine,visible/manual/student acceptance separate',next_action='Manual/physical/student acceptance when appropriate;preserve all independent model-data limits')
    with path.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(requirements)
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=43,wakeups=30,source_records=57,payload_files=419,payload_bytes=806444601,
        fresh_copied_environment=True,all107versions_verified=True,actual_notebook_kernel=True,overwrite_refusal=True,original_assets_and_claims_unchanged=True,
        old_packages_preserved=True,no_new_accuracy_or_training=True,no_active_jobs=True,next_live_milestone=100))
    print(json.dumps(dict(completed_trials=43,package=run['package'],live_snapshots=snapshots,sources=57),indent=2))
if __name__=='__main__':main()
