"""Record the dated offline Jupyter acceptance and resumable continuation."""
import csv,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T211737Z'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def append(path,title,text):
    p=ROOT/path;old=p.read_text(encoding='utf-8');assert title not in old
    p.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')

def main():
    if (E/'checks.json').exists():raise RuntimeError('Dated wake already recorded')
    state=read('data/automation_state.json');run=read('models/offline_jupyter_installation.json');run_id=run['run_id']
    assert run['offline_jupyter_gate_passed'] and run['original_assets_and_claims_unchanged']
    assert state['last_completed_run']==run_id and not state['active_validation_jobs'] and not state['active_training_jobs']
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==41
    assert state['scheduled_wakeups_completed']==27
    assert all(digest(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes']}.items())
    plan=read('dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json');assert plan['extension_wheels']==83
    assert plan['combined_wheels']==107 and plan['extension_bytes']==49287471 and plan['combined_bytes']==257829508
    assert all(digest(ROOT/e['path'])==e['sha256'] and e['crc_verified'] and e['embedded_notice_hashes'] for e in plan['entries'])
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    packages=[r for r in receipts if r['source_id']=='SRC-PKG-004'];assert len(packages)==166
    assert all(digest(ROOT/r['local_path'])==r['sha256'] for r in packages)
    archive=ROOT/'reports/offline_jupyter/v1';archive.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(ROOT/'dependencies/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json',archive/'WHEELHOUSE_MANIFEST.json')
    shutil.copyfile(ROOT/plan['lock_path'],archive/'requirements-app-jupyter-lock.txt')
    folder=ROOT/'experiments/results'/run_id
    parent=ROOT/'experiments/results'/run['continuation_of']
    write(E.relative_to(ROOT)/'probe_outputs.json',{mode:dict(folder=(parent if mode=='install' else folder).relative_to(ROOT).as_posix(),
        stdout=((parent if mode=='install' else folder)/(mode+'_stdout.txt')).read_text(encoding='utf-8'),
        stderr=((parent if mode=='install' else folder)/(mode+'_stderr.txt')).read_text(encoding='utf-8')) for mode in ['install','check','notebooks']})
    write(E.relative_to(ROOT)/'acquisition_receipts.json',dict(receipts=packages,per_file_original_network_times_captured=False,
        exact_local_cache_copy_times=True,metadata=83,wheels=83,source_id='SRC-PKG-004'))
    failures=[]
    for raw in sorted((ROOT/'data/raw/jupyter_metadata').iterdir()):
        if raw.is_dir():failures.append(dict(folder=raw.relative_to(ROOT).as_posix(),
            operation=read((raw/'operation.json').relative_to(ROOT)),completion=read((raw/'completion.json').relative_to(ROOT)),
            stdout=(raw/'stdout.txt').read_text(encoding='utf-8',errors='replace'),stderr=(raw/'stderr.txt').read_text(encoding='utf-8',errors='replace')))
    write(E.relative_to(ROOT)/'acquisition_operations.json',dict(operations=failures,
        interruptions=['Initial restricted DNS failed; not a package-unavailable claim',
            'Successful resolver report initially opened using Windows default encoding and raised UnicodeDecodeError; fixed to explicit UTF-8 and resumed the same report/cache without redownloading',
            'First restricted ensurepip bootstrap failed; interrupted run and partial environment retained,excluded from completed trial count',
            'First actual install succeeded but gate failed because strict guard rejected harmless ::1 bind; retained completed failed trial40. Continuation41reuses that newly installed venv,allows loopback and checks actual kernels; no repeat installation'],
        bootstrap_attempts=[p.parent.name for p in (ROOT/'experiments/results').glob('JUPYTER-OFFLINE-*/interrupted.json')]))
    pointer=dict(run_id=run_id,python=run['fresh_venv']+'/Scripts/python.exe',gate_passed=True,profile='Windows64/Python3.12 CPU app+JupyterLab',
        manifest='reports/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json',manifest_sha256=digest(archive/'WHEELHOUSE_MANIFEST.json'),
        lock='reports/offline_jupyter/v1/requirements-app-jupyter-lock.txt',lock_sha256=digest(archive/'requirements-app-jupyter-lock.txt'),
        extension_wheels=83,extension_bytes=49287471,combined_wheels=107,combined_bytes=257829508,
        executed_lesson08=(folder/'executed/08_image_patterns_and_svd.ipynb').relative_to(ROOT).as_posix(),
        executed_training_product=(folder/'executed/training_product_smoke.ipynb').relative_to(ROOT).as_posix(),
        fresh_kernel_notebooks=2,all_eight_notebooks_freshly_executed=False,lab_server_browser_ui_tested=False,
        physical_offline_or_new_machine_verified=False,shared_environment_changed=False,guide='docs/OFFLINE_JUPYTER_SETUP.md')
    write('reports/offline_jupyter_latest.json',pointer)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=datetime.now(timezone.utc).isoformat();inventory['offline_jupyter']=pointer
    from smart_parking.live import parse_feed
    live=read('data/processed/singapore_prospective/summary.json');latest=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001')
    assert digest(ROOT/latest['local_path'])==latest['sha256']
    payload=read(latest['local_path']);observed=parse_feed(payload)
    raw_lots=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in observed)
    identities=[(r['car_park_id'],r['lot_type'],r['observed_at']) for r in observed]
    assert len(identities)==len(set(identities))
    snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=latest,accepted_rows=len(observed),raw_lot_records=raw_lots,
        invalid_capacity_excluded=raw_lots-len(observed),bounds_valid=True,duplicate_rows=0,
        interpretation='Earlier frozen persistence forecasts matched later source observations; not neural/camera accuracy. Not a100-run milestone.'))
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in observed}),observations=len(observed),
            raw_lot_records=raw_lots,raw_path=latest['local_path'],provider_timestamp=latest['provider_timestamp'],snapshot_count=snapshot_count,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    path=ROOT/'data/source_manifest.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;rows=list(r)
    assert len(rows)==len({r['source_id'] for r in rows})==55
    for row in rows:
        if row['source_id']=='SRC-PKG-004':row.update(status='83original extension wheels verified; fresh offline install and two actual kernels pass',
            used_by=run_id+'; exact lesson08 plus training-only detector/convolution checks',
            open_issues='App24-wheel profile reused; base Python/OS/assets reused. Lab server/browser UI,all-eight fresh kernels,physical/new-machine/manual acceptance separate')
    with path.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(rows)
    state.update(scheduled_wakeups_completed=28,last_updated_at=datetime.now(timezone.utc).isoformat(),offline_jupyter_installation=pointer,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Fresh app+Jupyter installation now passes:107hash-locked packages total,83additional Jupyter wheels/49287471bytes. Actual two new kernels execute lesson08 inline graphics and training-only both-detector/2D/3D checks. See docs/OFFLINE_JUPYTER_SETUP.md/reports/offline_jupyter_latest.json. Original shared .venv,app-only venv,weights,notebooks and consumed claims unchanged.',
        'Next validate a local JupyterLab server/browser session and project kernel selection,then consider a combined installer/demo package at a meaningful milestone. Do not rerun notebook02on consumed final frame to claim new accuracy. All8original notebooks were not freshly rerun; lesson08and generated training-only smoke were.',
        'Fresh independent fixed-camera crossing/space/occupancy labels remain the scientific priority; source13inspection and source14access/rights gaps unchanged. No bypass/contact or consumed final reuse. Production model selection unchanged; no new training or live neural accuracy.',
        'Source catalog55. SRC-PKG-004has83release JSON+83original wheel receipts,creator/rights/notices/publisher hashes. Acquisition DNS/UTF8 and interrupted bootstrap failures preserved. Actual49MBextension size gate after resolver caching,not a pre-transfer cap.',
        'Remaining acceptance:physical disconnection,new machine,visible/manual dialogs,student explanation/rehearsal,missing university documents. Dated report/Excel/slides and189-file demo preserved. No universal100%accuracy claim.',
        'Counter41;next separate100-run live checkpoint100. Latest Singapore collection '+live['checked_at']+':'+str(snapshot_count)+'snapshots,'+str(live['scores_total'])+'matched baseline outcomes. Next sensible collection after21:57UTC. Continue causal source-consistent scoring;no active jobs.'
    ];write('data/automation_state.json',state)
    title='## 25 October 2026 / fresh offline Jupyter kernels verified'
    note=('New isolated app+Jupyter environment passes hash-locked --no-index installation and pip check. '
        '83additional publisher-hash/CRC/notice-verified wheels (49,287,471bytes);107packages with app profile (257,829,508bytes). '
        'Two genuine new kernels execute lesson08with inline graphics and a separate training-only both-detector/2D/3D check. '
        'Original notebook08source cells kept verbatim with a diagnostic setup cell; outputs saved separately,original notebooks unchanged. '
        'Same68occupied/32vacant/0uncertain fixed example agreement,not accuracy. No consumed final data reopened or model training. '
        'Python non-loopback socket access denied; native ZeroMQ/physical networking is outside Python audit coverage. '
        'Existing base Python/Windows/model/data assets reused. Not all8notebooks freshly rerun; JupyterLab server/browser UI,physical/new-machine/manual/student acceptance remain. '
        'Old app-only installation and failed readiness retained. Guide:docs/OFFLINE_JUPYTER_SETUP.md;pointer:reports/offline_jupyter_latest.json. '
        'Completed failed gate40retained:offline install succeeded but strict guard blocked harmless ::1 bind. Continuation41reuses that new venv without reinstalling,permits loopback and completes actual kernel checks. Interrupted bootstrap excluded. Source catalog55. Acquisition DNS and UTF8 failures preserved;resumed cached downloads without installing into shared runtime. '
        'Actual21:27UTC Singapore snapshot'+str(snapshot_count)+'matches'+str(live['scores_added'])+'earlier frozen persistence targets:'+str(live['scores_total'])+'total,MAE'+format(live['baseline_mae_spaces'],'.6f')+'spaces. '
        'Missing targets remain unscored;raw JSON/URL/time/SHA/normalized rows retained. No new neural/camera live score.')
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,title,note)
    append('docs/UI_TEST_LOG.md',title,'Actual fresh notebook kernels generate inline image outputs and both training-example overlays. JupyterLab browser/server,visible app layout/manual dialogs were not exercised. No physical-offline/new-machine claim.')
    for p in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md']:append(p,title,
        'SRC-PKG-004adds83official immutable release JSON and83original wheel archives,49,287,471bytesof archives. Publisher hashes,ZIP CRC and complete embedded notices retained. Source catalog55;exact cache-copy times and resolver network-operation bounds preserved. Local academic use;no external redistribution clearance claim. See reports/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json and append-only resource receipts.')
    append('docs/OFFLINE_APP_SETUP.md',title,'A separate app+Jupyter profile now passes actual fresh kernel checks. See docs/OFFLINE_JUPYTER_SETUP.md. The app-only installation described above remains unchanged; its184software tests retain their original scope/date.')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;rows=list(r)
    for row in rows:
        if row['requirement_id']=='OFF-01':row.update(status='In progress',actual_evidence='reports/offline_jupyter_latest.json; docs/OFFLINE_JUPYTER_SETUP.md; prior app-only checks preserved',
            test_result='107hash-locked packages install offline in new venv;pip check/import origins/two real kernels/inline plots/training detectors/convolutions pass',
            open_problems='Existing base Python/OS/assets reused; all8fresh kernels,Lab server/browser,physical/new-machine/manual/student acceptance separate',next_action='Validate Lab server and local kernel selection;then remaining acceptance and combined installer/demo')
        if row['requirement_id']=='SRC-01':row['test_result']='55unique source records;Jupyter83metadata+83original wheel receipts;creator/rights/notices/full hashes retained'
    with path.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(rows)
    write(E.relative_to(ROOT)/'checks.json',dict(run_id=run_id,completed_trials=41,source_records=55,offline_jupyter_gate_passed=True,
        original_weights_notebooks_and_consumed_claims_unchanged=True,two_actual_fresh_kernels=True,extension_wheels=83,extension_bytes=49287471,
        shared_environment_changed=False,no_active_jobs=True,next_live_checkpoint_at_run=100))
    print(json.dumps(pointer,indent=2))

if __name__=='__main__':main()
