"""Record verified app-only offline installation, cache correction and continuation."""
import csv,json,re,shutil,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed

E=ROOT/'experiments/evidence/HEARTBEAT-20261025T204537Z'
RUN='OFFLINE-INSTALL-20261025T210141239920Z'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('This dated heartbeat is already recorded')
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');run=read('models/offline_app_installation.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==39
    assert state['scheduled_wakeups_completed']==26 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['offline_app_installation_gate_passed'] and run['app_validation']['all_six_dependencies_from_fresh_venv']
    assert all(not check['network_attempts'] and check['returncode']==0 for check in run['checks'].values())
    assert all(digest(ROOT/p)==h for p,h in run['source_hashes'].items())
    tests=read(E.relative_to(ROOT)/'fresh_unit_test_summary.json');assert tests['tests']==184 and tests['success'] and not tests['network_attempts']
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in production.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    manifest_path=ROOT/'dependencies/offline_app/v1/WHEELHOUSE_MANIFEST.json';manifest=read(manifest_path.relative_to(ROOT))
    assert len(manifest['entries'])==24 and manifest['total_bytes']==208542037
    assert all(digest(ROOT/e['path'])==e['sha256'] and e['crc_verified'] and e['embedded_notice_hashes'] for e in manifest['entries'])
    assert digest(ROOT/manifest['lock_path'])==manifest['lock_sha256']
    archive=ROOT/'reports/offline_runtime/v1';archive.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(manifest_path,archive/'WHEELHOUSE_MANIFEST.json')
    shutil.copyfile(ROOT/manifest['lock_path'],archive/'requirements-app-cpu-lock.txt')
    pointer=dict(run_id=RUN,profile='App-only Windows64/Python3.12 CPU; existing base Python/Tk reused',
        python=run['fresh_venv']+'/Scripts/python.exe',wheelhouse='dependencies/offline_app/v1',
        manifest_sha256=digest(manifest_path),lock_sha256=manifest['lock_sha256'],
        archived_manifest='reports/offline_runtime/v1/WHEELHOUSE_MANIFEST.json',
        archives=24,archive_bytes=208542037,offline_app_installation_gate_passed=True,fresh_runtime_software_tests=184,
        jupyter_profile_installed=False,physical_offline_or_new_machine_verified=False,shared_environment_changed=False,
        guide='docs/OFFLINE_APP_SETUP.md')
    write('reports/offline_runtime_latest.json',pointer)
    result=ROOT/'experiments/results'/RUN
    logs={}
    for mode in ['install','dependency_check','preflight','app']:
        logs[mode]=dict(stdout=(result/(mode+'_stdout.txt')).read_text(encoding='utf-8'),stderr=(result/(mode+'_stderr.txt')).read_text(encoding='utf-8'))
    write(E.relative_to(ROOT)/'offline_probe_outputs.json',logs)
    write(E.relative_to(ROOT)/'wheelhouse_integrity.json',dict(manifest_sha256=digest(manifest_path),lock_sha256=manifest['lock_sha256'],
        files=24,bytes=208542037,all_publisher_hashes_and_crc_verified=True,all_embedded_notices_retained=True,
        archived_manifest_sha256=digest(archive/'WHEELHOUSE_MANIFEST.json'),archived_lock_sha256=digest(archive/'requirements-app-cpu-lock.txt')))
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    wheel_receipts=[r for r in receipts if r['source_id']=='SRC-PKG-003'];assert len(wheel_receipts)==24
    assert all(r['acquisition_kind']=='verified_pip_cache_copy' and digest(ROOT/r['local_path'])==r['publisher_sha256'] for r in wheel_receipts)
    metadata_receipts=[r for r in receipts if r['source_id']=='SRC-PKG-002'];assert len(metadata_receipts)==33
    assert all(digest(ROOT/r['local_path'])==r['sha256'] for r in metadata_receipts)
    write(E.relative_to(ROOT)/'runtime_acquisition_receipts.json',dict(wheels=wheel_receipts,metadata=metadata_receipts,
        exact_per_file_network_timestamps_captured=False,cache_recovery_times_exact=True,
        scope='Resolver downloads happened before post-resolution budget check;208542037byteswithin512MiB. Cache recovery made no additional network transfer.'))
    sources_path=ROOT/'data/source_manifest.csv'
    with sources_path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==len({r['source_id'] for r in sources})==54
    for row in sources:
        if row['source_id']=='SRC-PKG-003':row.update(status='24original archives verified; app-only offline install/integration passed',
            used_by=RUN+'; fresh app-only venv,184regression tests and frozen training-example app checks',
            open_issues='App-only profile; existing Python/Tk/OS reused. Jupyter/new-machine/physical-offline/manual/student acceptance and external distribution rights separate')
        if row['source_id']=='SRC-PKG-002':row.update(used_by='Official core/CPU/transitive release metadata for24-package app closure;33raw metadata acquisitions',
            open_issues='Corev1snapshot retained; full app closure/wheels now separately verified under SRC-PKG-003. Resolver initial cache flag corrected append-only; no Jupyter closure yet')
    with sources_path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001');assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    live=read('data/processed/singapore_prospective/summary.json');payload=read(receipt['local_path']);rows=parse_feed(payload)
    assert live['scores_total']==26047 and live['scores_added']==1105
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        interpretation='1105earlier frozen persistence forecasts matched later actual targets; not camera/neural accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['offline_runtime']=pointer
    inventory['runtime_metadata'].update(files=33,core_distributions=5,resolved_app_distributions=24,metadata_only=True,
        installer_assets_downloaded=24,offline_app_installation_accepted=True,installer_source_id='SRC-PKG-003',
        correction='Earlier no-download flag was inaccurate for resolver dry-run;see RUNTIME_DRYRUN_CACHE_20261025.json')
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=32,
            prospective_baseline_scored_outcomes=26047,prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    previous_readiness=state['installation_readiness'];state.update(last_updated_at=now,scheduled_wakeups_completed=27,offline_runtime=pointer,
        installation_readiness=dict(run_id=RUN,offline_app_installation_gate_passed=True,prior_failed_readiness=previous_readiness['run_id'],
            dependency_closure_resolved=True,profile='App-only CPU; Jupyter separate',shared_environment_changed=False,guide='docs/OFFLINE_APP_SETUP.md'),
        last_live_baseline_score=dict(outcomes=26047,mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Fresh APP-ONLY offline install now passes:24publisher-hash/CRC-verified wheels,208542037bytes,all184tests in new venv,zero network attempts during install/check/app/tests. Both detectors agree with frozen training sample; exports,semantic,cached live,archived forecasts,SVD,2video samples pass. See reports/offline_runtime_latest.json/docs/OFFLINE_APP_SETUP.md. Existing base Python/Tk/OS reused; shared .venv untouched.',
        'Next prepare a separate compatible Jupyter extension closure with immutable official artifacts,then verify actual notebook-kernel execution offline. App-only profile deliberately lacks Jupyter/IPython. Keep previous failed readiness38 and positive install39; avoid replaying identical tests/copying full demo merely to increase counts.',
        'Resolver pip --dry-run DIDdownload/cache wheel archives despite no installation. Initialplanv1flag inaccurate,preserved and corrected byruntime_wheelhouse_plan_v2.json and provenance correction.24original archives recovered from cache with no further transfer; complete notices preserved. Metadata33files; catalog54. No publish/redistribution/paid services.',
        'Main-project8notebooks remain executed in original notebook environment. Old189-file demo remains dated; create combined app-installer/demo bundle only at meaningful acceptance milestone. Visible/manual/new-machine/physical-offline and student rehearsal remain unverified; official university documents/mastery absent. Prior report/Excel/slides remain dated.',
        'Fresh independent fixed-camera crossing labels still needed; source13inspection/source14publicclient403gaps unchanged,no bypass or author contact. Never reuse consumed DAVIS/image/Birmingham finals for changed methods. Original weights unchanged.',
        'Last official collection20:56UTC:32snapshots,26047matched baseline outcomes,MAE3.820977,8117expired/1280pending,76.24%resolved matching. Next sensiblecollection after21:26UTC. Counter39; separate100-run checkpoint100; no active jobs.'
    ];write('data/automation_state.json',state)
    title='## 25 October 2026 / verified fresh app-only offline dependency installation'
    note='''Fresh app-only offline installation PASS:24original Windows64/Python3.12 CPU
wheels,208,542,037bytes,complete hash-locked requirements. Publisher SHA256,ZIP
CRC and embedded licence/notice hashes verified. New venv installs with --no-index
--require-hashes;pip check and preflight pass. All184existing software tests pass
in that fresh venv. Installation,checks,app and tests make zero network attempts.
Sixcore modules import from the new venv; decoder preloaded explicitly to prove
the freshly installed artifact. Ordinary source can prefer its identical bundled
decoder. Shared .venv and original checkpoints/data remain unchanged.

Actual hidden-native app checks pass:both frozen detectors on existing training
sample agree with68occupied/32vacant/0uncertain;paired exports,semantic-preview
separation,two archived forecasts,cached live,SVD and2already-seen licensed video
samples. This is software/prediction agreement,not ground-truth accuracy. No
final images/dates/sequences reread or rescored. Existing base Python/Tk/Windows
reused; no fresh-machine,physical-disconnection,manual-dialog or student mastery
claim. Jupyter/IPython are not installed in this app-only profile. Prior failed
readiness trial38 retained; one completed fresh-install trial advances38->39,
not one run per wheel/subprocess/test/frame. Guide:docs/OFFLINE_APP_SETUP.md;
pointer:reports/offline_runtime_latest.json.

Important provenance correction:the resolver --dry-run downloaded complete wheel
archives into its project-local pip cache without installing packages. Initial
planv1incorrectly marked installer_files_acquired=False. Original plan/logs are
preserved;v2and RUNTIME_DRYRUN_CACHE_20261025.json explicitly correct it. Whole
archives were then recovered from that cache,verified and staged with no extra
network transfer. Actual total208542037bytesis within512MiB; size gate checked
after resolver caching,not claimed as a pre-transfer hard limit. Exact per-file
network times were not captured; resolver operation bounds and exact local cache
copy/verification receipts retained. Source catalog54:PKG-002metadata now33files,
PKG-003original24installer archives with full per-package licence/creator records.

Actual20:56UTC official snapshot32 matches1105later frozen persistence targets:
26,047total,MAE3.820977spaces,8117expired/1280pending,76.24%resolved matching.
Immutable raw JSON,normalized CSV,URL,time,SHA,bounds/duplicates retained; no
camera/neural live accuracy. Earlier source gaps remain unscored,not zero error.

No active jobs; next100-run milestone100. Next:Jupyter offline extension or
legitimate fresh labelled counting evidence,then remaining native/physical/
student acceptance. Old demo/report/Excel/slides keep dated scope; full project,
official academic compliance and universal accuracy are not claimed complete.'''
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        path=ROOT/name;text=path.read_text(encoding='utf-8');assert title not in text
        path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    path=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=path.read_text(encoding='utf-8').replace('31 authorized public snapshots acquired','32 authorized public snapshots acquired')
    cohorts=sum(c['scored']>0 for c in live['forecast_coverage']['cohorts'])
    text=re.sub(r'\| Live-source forecasting \| [^|]+\| [^\n]+',f'| Live-source forecasting | {cohorts} prospective persistence cohorts scored | 26,047 matched later outcomes,MAE3.821; variable target windows,no neural/camera live accuracy |',text,count=1)
    text=re.sub(r'\| Tests/offline \|[^\n]+','| Tests/offline | 184 tests pass in fresh app-only offline venv; representative native app checks pass | Base Python/Tk/OS reused; Jupyter/new-machine/physical/manual acceptance still pending |',text,count=1)
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    path=ROOT/'docs/INSTALLATION_READINESS.md';old=path.read_text(encoding='utf-8');path.write_text('# Current offline app installation update\n\nThe fresh app-only offline installation now passes;see docs/OFFLINE_APP_SETUP.md and reports/offline_runtime_latest.json. Jupyter,new-machine,physical-offline and manual acceptance remain separate. The prior failure/readiness snapshot below is preserved as history.\n\n## Historical readiness snapshot before the complete wheelhouse\n\n'+old,encoding='utf-8')
    path=ROOT/'docs/UI_TEST_LOG.md';path.write_text(path.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nActual new-venv hidden-native detectors/paired exports/semantic/archived forecasts/cached live/SVD/video pass with networking blocked. Same frozen training prediction counts,not accuracy. No visible/manual/physical/new-machine/Jupyter acceptance. See models/offline_app_installation.json.\n',encoding='utf-8')
    for name in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md']:
        path=ROOT/name;path.write_text(path.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nSource catalog54. SRC-PKG-003retains24official original wheel archives,publisher hashes/CRC and complete notices;33primary metadata acquisitions under SRC-PKG-002. Resolver no-download flag corrected append-only; network timestamps exactness limits explicit. Local academic installation only,no external redistribution clearance claim. See reports/offline_runtime/v1/WHEELHOUSE_MANIFEST.json and per-file receipts.\n',encoding='utf-8')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id']=='OFF-01':row.update(status='In progress',actual_evidence='docs/OFFLINE_APP_SETUP.md; reports/offline_runtime_latest.json; models/offline_app_installation.json; prior failed readiness retained',
            test_result='24hash-locked wheels install in fresh app-only venv offline; pip check/preflight/native model/export checks and184regression tests pass;zero network attempts',
            open_problems='Existing base Python/Tk/Windows and original model/data assets reused; Jupyter extension,new-machine,visible/manual and physical-disconnection acceptance pending',next_action='Prepare separate verified Jupyter closure,then remaining explicit acceptance; keep old failed readiness and full provenance')
        if row['requirement_id']=='SRC-01':row['test_result']='54unique source records;per-artifact URLs/hashes/licences retained; resolver cache misstatement corrected without erasing original'
    with path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=39,source_records=54,fresh_app_runtime_tests=184,
        offline_app_installation_gate_passed=True,jupyter_profile_installed=False,shared_environment_unchanged=True,
        original_weights_and_consumed_claims_unchanged=True,wheels=24,wheel_bytes=208542037,source_metadata_files=33,
        resolver_cache_misstatement_corrected=True,network_attempts_during_install_validation_tests=0,
        no_active_jobs=True,live_snapshots=32,live_matched_outcomes=26047))
    print(json.dumps(dict(completed_trials=39,offline_app_installation_gate_passed=True,fresh_runtime_tests=184,wheels=24,sources=54),indent=2))


if __name__=='__main__':main()
