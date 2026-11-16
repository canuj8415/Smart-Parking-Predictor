"""Persist startup/readiness limits and official metadata without claiming install success."""
import csv,json,re,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed

E=ROOT/'experiments/evidence/HEARTBEAT-20261025T201536Z'
RUN='INSTALL-READINESS-20261025T202311919686Z'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('This dated heartbeat is already recorded')
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json');run=read('models/installation_readiness.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==38
    assert state['scheduled_wakeups_completed']==25 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert run['launcher_diagnostic_gate_passed'] and not run['offline_installation_gate_passed']
    assert all(digest(ROOT/path)==h for path,h in run['source_hashes'].items())
    tests=(E/'unit_tests.txt').read_text(encoding='utf-8-sig');assert 'Ran 184 tests' in tests and tests.rstrip().endswith('OK')
    existing=read(E.relative_to(ROOT)/'existing_environment.json');assert existing['prerequisites_found'] and existing['discovery_only']
    assert all(not row['audit']['network_attempts'] for row in run['checks'].values())
    assert run['checks']['launch']['returncode']==run['checks']['check']['returncode']==2
    assert not run['checks']['launch']['audit']['heavy_import_attempts']
    assert run['checks']['baseline']['audit']['heavy_import_attempts']==['smart_parking.app','numpy']
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/path)==h for path,h in production.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    # Preserve the exact human-facing failures and audit records in tracked evidence.
    result=ROOT/'experiments/results'/RUN
    probes={}
    for mode in ['baseline','check','launch','pip']:
        probes[mode]=dict(stdout=(result/(mode+'_stdout.txt')).read_text(encoding='utf-8'),
            stderr=(result/(mode+'_stderr.txt')).read_text(encoding='utf-8'),audit=read((result/(mode+'_audit.json')).relative_to(ROOT)))
    write(E.relative_to(ROOT)/'isolated_probe_outputs.json',probes)
    plan=read('data/manifests/runtime_core_candidates_v1.json')
    assert not plan['failures'] and len(plan['core_candidates'])==5
    assert all(len(row['compatible_core_candidates'])==1 for row in plan['core_candidates'])
    assert all(row['compatible_core_candidates'][0]['sha256'] for row in plan['core_candidates'])
    assert not plan['transitive_dependency_closure_resolved'] and plan['wheel_files_downloaded']==0
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    metadata_receipts=[row for row in receipts if row['source_id']=='SRC-PKG-002']
    assert len(metadata_receipts)==7 and all(digest(ROOT/row['local_path'])==row['sha256'] for row in metadata_receipts)
    write(E.relative_to(ROOT)/'runtime_metadata_receipts.json',dict(receipts=metadata_receipts,core_selection_sha256=digest(ROOT/'data/manifests/runtime_core_candidates_v1.json'),
        wheels_downloaded=0,closure_resolved=False,scope='Primary metadata and CPU/Windows/Python3.12 core candidates only; not a complete install lock'))
    source_path=ROOT/'data/source_manifest.csv'
    with source_path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==52
    record=dict(source_id='SRC-PKG-002',resource_type='official runtime release metadata and core candidate selection',
        resource='Existing app pins:PyTorch/TorchVision CPU,NumPy,Pillow,Matplotlib',
        original_creator='PyTorch/TorchVision,NumPy,Pillow,Matplotlib developers; PyPI publisher index',
        source_url='https://pypi.org/; https://download.pytorch.org/whl/cpu/',
        download_url='Exact7primary metadata/index URLs in data/resource_receipts.jsonl',
        access_date=metadata_receipts[0]['accessed_at'],access_time_precision='Exact UTC per-resource receipts',
        version='torch2.14.0/torchvision0.29.0 CPU cp312win_amd64 candidates;numpy2.5.3/Pillow12.3.0/matplotlib3.11.2',
        license='Metadata includes publisher licence fields; wheel notices/dependency closure still require verification before operational installation',
        permission='Public metadata inspection only; no wheel assets acquired or installed',
        original_size=str(sum(row['bytes'] for row in metadata_receipts))+'bytes/7metadata files',
        local_location=plan['metadata_folder'],sha256='Per-metadata SHA256 in receipts; core candidate publisher hashes in runtime_core_candidates_v1.json',
        purpose='Prepare reproducible bounded offline wheel acquisition without modifying working environment',
        used_by='Installation readiness research; next-step core candidate plan only',modifications='Original metadata/index bytes retained; compatible core filenames/hashes selected by current interpreter tags',
        attribution='Named package creators; exact official PyPI/PyTorch URLs in receipts',status='metadata acquired; no installer assets downloaded',
        open_issues='Core candidates are not a resolved dependency closure; CPU wheel sizes/transitive licences/full size budget and actual fresh offline install not verified')
    sources.append({key:record.get(key,'') for key in fields});assert len({row['source_id'] for row in sources})==53
    with source_path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    receipt=next(row for row in reversed(receipts) if row['source_id']=='SRC-LIVE-001');assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    live=read('data/processed/singapore_prospective/summary.json');payload=read(receipt['local_path']);rows=parse_feed(payload)
    assert live['scores_total']==24942 and live['scores_added']==1051
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows),duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        interpretation='1051previously frozen persistence forecasts matched later actual observations; no neural/camera accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),raw_lot_records=raw_count,
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=31,
            prospective_baseline_scored_outcomes=24942,prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    inventory['runtime_metadata']=dict(source_id='SRC-PKG-002',selection='data/manifests/runtime_core_candidates_v1.json',core_distributions=5,
        files=7,metadata_only=True,installer_assets_downloaded=0,offline_installation_accepted=False)
    write('data/dataset_inventory.json',inventory)
    state.update(last_updated_at=now,scheduled_wakeups_completed=26,
        installation_readiness=dict(run_id=RUN,launcher_diagnostic_gate_passed=True,offline_installation_gate_passed=False,
            clean_venv=run['fresh_environment'],shared_environment_changed=False,core_candidate_plan='data/manifests/runtime_core_candidates_v1.json',
            dependency_closure_resolved=False,guide='docs/INSTALLATION_READINESS.md'),
        last_live_baseline_score=dict(outcomes=24942,mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['local_demo_bundle']['newer_source_changes_not_in_bundle']=['run_app.py','src/smart_parking/environment.py','docs/INSTALLATION_READINESS.md','scripts/build_demo_package.py']
    state['next_actions']=[
        'Prepare complete offline runtime closure from the pinned official core candidate metadata in data/manifests/runtime_core_candidates_v1.json. Verify CPU wheel sizes/publisher hashes/licences and transitive dependencies,total bounded disk/network budget before acquisition; use immutable receipts. No installers downloaded yet; never modify shared .venv. Build/validate a new clean-venv offline installation once complete, retaining failed readiness trial.',
        'New startup preflight/main-project diagnostic works; source change newer than last189-file demo. Includes no-model/no-network prerequisite discovery,plain missing-component guidance and logged import failure.184software tests;38completed trials. Clean venv diagnostic passes but offline installation gate FAILS: only decoder wheel in selected wheelhouse. Existing base Python is still reused,not a new-machine or physical-offline claim.',
        'Prior189-file demo remains dated and preserved; future package builder now includes installation guide. Rebuild at a meaningful acceptance milestone,not for every counter change. Main-project8notebooks and original weights/final claims unchanged. Visible/manual dialogs,copied-folder kernel,physical offline and student rehearsal remain unverified.',
        'Fresh independent fixed-camera crossing labels remain needed. Source13inspection-only and source14file-browser403limits stand; no bypass or author messages. No reuse of consumed DAVIS/image/Birmingham finals for changed methods. Source catalog53; old report/Excel/slides stay dated; official university documents/student mastery missing.',
        'Last official collection20:19UTC:31snapshots,24942matched persistence outcomes,MAE3.928634,7978expired/1303pending,75.77%resolved matching. Next sensible30mincollection after20:49UTC; counter38,separate100-run checkpoint100. No active jobs.'
    ];write('data/automation_state.json',state)
    title='## 25 October 2026 / clear startup preflight and failed clean offline readiness gate'
    note='''Main launcher now discovers required modules before importing the heavy app.
Missing components produce clear setup guidance and exit2; --check-environment
returns discovery-only JSON without opening GUI,loading models or network use.
Import/ABI failures get a plain message plus local diagnostic log. Discovery is
not proof of binary/model compatibility. Existing runtime prerequisite check passes.

One bounded recorded trial creates a fresh local venv with no system site-packages,
reusing the existing base Python interpreter. Old launcher attempts app/numpy imports
and emits ModuleNotFoundError traceback. New normal/check modes exit2 with the
five missing app components before heavy imports. All four isolated child probes
make zero network attempts. Shared environment/data/weights unchanged. Local
ensurepip bootstraps pip only; no app package installation. Offline pip --dry-run
--no-index FAILS due missing torch2.14.0 wheel; selected wheelhouse contains only
verified OpenCV wheel. This preserves an explicit failed installation-acceptance
gate,not a successful fresh install/new-computer/physical-disconnection result.
184software tests pass; counter37->38for one completed trial,not per subprocess.

Official PyPI version metadata and PyTorch CPU indexes were then captured as
SRC-PKG-002:7immutable metadata files with SHA receipts,5compatible core wheel
candidates with publisher hashes for Windows64/Python3.12. Zero wheels downloaded
or installed. The core plan is not a complete dependency lock; transitive closure,
CPU artifact sizes/notices and total bounded acquisition budget remain to verify.
This is not a claim that missing wheels are unavailable online. Guide:
docs/INSTALLATION_READINESS.md; plan:data/manifests/runtime_core_candidates_v1.json.
Source catalog53. Later work must use a separate fresh environment,not shared .venv.

Actual20:19UTC authorized Singapore snapshot31 adds1051later matched persistence
targets:24,942total,MAE3.928634spaces;7978expired/1303pending,75.77%resolved matching.
Raw JSON,normalized CSV,URL,provider/retrieval time,SHA and bounds/duplicate checks
retained. These are source-consistent baseline outcomes,not neural/camera accuracy.
No final image/date/sequence reread,model retraining or production weight changes.

No active jobs; counter38,next100-run checkpoint100. Existing189-file demo remains
a dated copy without this new launcher module/guide; builder includes the guide
for a future meaningful rebuild. Prior demo versions and all failed/selected
studies retained. Next:complete verified offline dependency preparation or legitimate
fresh labelled counting evidence,and remaining native/manual/student acceptance.
Whole project completion,official compliance and universal accuracy unclaimed.'''
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        path=ROOT/name;text=path.read_text(encoding='utf-8');assert title not in text
        path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    path=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=path.read_text(encoding='utf-8').replace('Thirty authorized public snapshots acquired','31 authorized public snapshots acquired')
    cohorts=sum(c['scored']>0 for c in live['forecast_coverage']['cohorts'])
    text=re.sub(r'\| Live-source forecasting \| [^|]+\| [^\n]+',f'| Live-source forecasting | {cohorts} prospective persistence cohorts scored | 24,942 matched later outcomes, MAE3.929; actual variable target windows; no neural/camera live accuracy |',text,count=1)
    text=text.replace('| Tests/offline | 181 tests pass; prior relocated local-demo check retained | Physical disconnected rehearsal/fresh offline setup still pending |',
        '| Tests/offline | 184 tests pass; clean-venv startup diagnosis passes, offline install gate fails | Core installer wheels missing locally; official metadata candidates saved, dependency closure unresolved; physical/new-machine acceptance pending |')
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    for name in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md']:
        path=ROOT/name;path.write_text(path.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nSource catalog53. SRC-PKG-002 captures exact PyPI release JSON and official PyTorch CPU indexes for existing pins;7metadata files,5core candidates,publisher hashes. No wheel assets downloaded or licence/closure/install acceptance claimed. See data/manifests/runtime_core_candidates_v1.json and per-URL resource receipts.\n',encoding='utf-8')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;requirements=list(reader)
    for row in requirements:
        if row['requirement_id']=='OFF-01':row.update(status='In progress',actual_evidence='docs/INSTALLATION_READINESS.md; models/installation_readiness.json; '+RUN+'; prior relocated demo evidence',
            test_result='184software tests; old/new clean-venv startup negative control passes; all4probe networks blocked; offline --no-index dry-run installation gate FAILS due missing core wheels',
            open_problems='Only decoder wheel locally; official5core metadata candidates are not full transitive closure. Fresh install/new-machine/visible-manual/physical-offline acceptance still missing',
            next_action='Verify/acquire bounded complete offline wheels with hashes/licences,then install into separate clean environment and validate original checkpoints without shared-env mutation')
        if row['requirement_id']=='QA-01':row['actual_evidence']+='; src/smart_parking/environment.py; run_app.py; models/installation_readiness.json';row['test_result']='184software tests; clean missing-package startup is readable before heavy imports; binary compatibility discovery limits explicit'
        if row['requirement_id']=='SRC-01':row['test_result']='53 unique source records; permanent IDs,metadata receipts,licences/use/admission limits retained'
    with path.open('w',encoding='utf-8',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(requirements)
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=38,software_tests=184,sources=53,run_id=RUN,
        launcher_diagnostic_gate_passed=True,offline_installation_gate_passed=False,core_metadata_candidates=5,
        transitive_closure_resolved=False,wheel_assets_downloaded=0,shared_environment_unchanged=True,
        original_weights_and_final_claims_unchanged=True,no_active_jobs=True,live_snapshot_count=31,live_matched_outcomes=24942))
    print(json.dumps(dict(completed_trials=38,tests=184,sources=53,offline_installation_gate_passed=False),indent=2))


if __name__=='__main__':main()
