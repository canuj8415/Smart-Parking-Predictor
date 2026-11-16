"""Preserve local server acceptance, documentation provenance and next actions."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T214738Z'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,value):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    path=ROOT/p;old=path.read_text(encoding='utf-8');assert title not in old
    path.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')
def main():
    if (E/'checks.json').exists():raise RuntimeError('Dated wake already recorded')
    now=datetime.now(timezone.utc).isoformat();s=read('data/automation_state.json');run=read('models/jupyter_server_acceptance.json')
    tests=read(E.relative_to(ROOT)/'regression_summary.json');assert tests['success'] and tests['tests']==184 and not tests['non_loopback_python_network_attempts']
    assert run['local_server_gate_passed'] and run['owned_server_stopped'] and all(digest(ROOT/p)==h for p,h in {**run['source_hashes'],**run['protected_hashes']}.items())
    assert s['completed_recorded_runs_since_schedule']==len(set(s['completed_run_ids']))==42 and s['scheduled_wakeups_completed']==28
    assert not s['active_training_jobs'] and not s['active_validation_jobs']
    sources=ROOT/'data/source_manifest.csv'
    with sources.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;rows=list(r)
    docs=[('SRC-DOC-019','Jupyter Server REST API','https://jupyter-server.readthedocs.io/en/stable/developers/rest-api.html',
        'Authenticated contents and kernelspec queries,kernel creation/deletion,and server shutdown endpoint semantics.'),
        ('SRC-DOC-020','Jupyter client messaging protocol','https://jupyter-client.readthedocs.io/en/latest/messaging.html',
        'execute_request framing,parent message IDs,execute_reply status and IOPub idle handling; do not assume fixed reply/output ordering.')]
    for sid,name,url,note in docs:
        assert not any(row['source_id']==sid for row in rows)
        local=Path('data/research')/(sid+'_jupyter_reference_20261025.json')
        write(local,dict(source_id=sid,title=name,url=url,original_creator='Project Jupyter documentation contributors',recorded_at=now,
            consulted_date='2026-10-25',access_method='Official documentation discovered/read through web search tool; exact per-page original fetch time not captured',
            notes=note,verbatim_source_text_copied=False,scope='Authored reference notes; not original downloaded webpage or training data'))
        receipt(sid,ROOT/local,url,'Authored consultation record for official Jupyter API/protocol documentation',
            acquisition_kind='authored_reference_notes',original_page_downloaded=False,original_fetch_time_precision='Date only; local note record time exact')
        row=dict(source_id=sid,resource_type='official software documentation reference',resource=name,original_creator='Project Jupyter documentation contributors',source_url=url,
            access_date='2026-10-25',access_time_precision='Web-tool consultation date; exact per-page original fetch time not captured; authored note/receipt time exact',
            version='Stable/current documentation observed25October2026; client messaging docs8.10.0',license='Documentation rights not independently audited; read/reference only,no verbatim text or assets copied',
            permission='Public documentation consultation; no source-content redistribution or training use',local_location=local.as_posix(),sha256=digest(ROOT/local),
            purpose='Implement authenticated localhost server/kernel compatibility checks',used_by=run['run_id'],modifications='Original page not downloaded; authored concise API notes retained',
            attribution='Project Jupyter; exact official documentation URL',status='Consulted; functional API use validated locally',open_issues='No claim of full documentation review or external source-content redistribution rights')
        rows.append({f:row.get(f,'') for f in fields})
    assert len(rows)==len({r['source_id'] for r in rows})==57
    for row in rows:
        if row['source_id']=='SRC-PKG-004':row.update(used_by=row['used_by']+'; '+run['run_id']+' authenticated localhost server/kernel and184tests',
            open_issues='Server/REST/websocket gate passes;visible frontend JavaScript/manual selection,all8fresh notebooks,physical/new-machine/student acceptance remain')
        if row['source_id']=='SRC-PKG-002':row.update(status='33official metadata acquisitions retained;24app wheels verified separately under SRC-PKG-003',
            permission='Public metadata consultation; prior resolver also cached wheel bodies,corrected append-only and tracked under SRC-PKG-003',
            open_issues='Original7-file core snapshot retained as history;complete app closure and installer receipts under SRC-PKG-003,83-wheel Jupyter extension under SRC-PKG-004')
    with sources.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(rows)
    pointer=dict(run_id=run['run_id'],python=run['python'],local_server_gate_passed=True,html_and_asset_http_verified=True,
        authenticated_websocket_kernel_verified=True,anonymous_kernel_api_rejected=True,owned_server_stopped=True,regression_tests=184,
        manual_visible_browser_or_frontend_javascript_verified=False,physical_offline_or_new_machine_verified=False,
        protocol='experiments/results/'+run['run_id']+'/protocol.json',results='experiments/results/'+run['run_id']+'/run.json',
        results_sha256=digest(ROOT/'experiments/results'/run['run_id']/'run.json'),guide='docs/OFFLINE_JUPYTER_SETUP.md')
    write('reports/jupyter_server_latest.json',pointer)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now;inventory['jupyter_server']=pointer
    live=read('data/processed/singapore_prospective/summary.json');receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    latest=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001')
    from smart_parking.live import parse_feed
    assert digest(ROOT/latest['local_path'])==latest['sha256'];payload=read(latest['local_path']);observed=parse_feed(payload)
    raw_count=sum(len(p['carpark_info']) for item in payload['items'] for p in item['carpark_data'])
    assert all(0<=r['available']<=r['capacity'] for r in observed)
    assert len(observed)==len({(r['car_park_id'],r['lot_type'],r['observed_at']) for r in observed})
    snapshots=len(list((ROOT/'data/raw/singapore_live').glob('*.json')))
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=latest,accepted_rows=len(observed),raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(observed),bounds_valid=True,duplicate_rows=0,not_a100_run_checkpoint=True,
        scope='Source-consistent prospective persistence only; not neural/camera accuracy'))
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in observed}),observations=len(observed),raw_lot_records=raw_count,
            raw_path=latest['local_path'],provider_timestamp=latest['provider_timestamp'],snapshot_count=snapshots,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    s.update(scheduled_wakeups_completed=29,last_updated_at=now,jupyter_server_acceptance=pointer,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage']))
    s['next_actions']=[
        'Local JupyterLab server acceptance passes:HTTP frontend shell/local JS asset/notebook contents,authenticated websocket kernel,new-venv interpreter/inline SVD+2D3D,anonymous403and clean shutdown.184tests plus3launcher negative checks pass. See reports/jupyter_server_latest.json. No visible frontend-JS/manual or physical/new-machine claim.',
        'Create a combined dated local demo+offline installer package at next integration milestone:latest source launchers/guides/training-only notebook,24app+83Jupyter wheels with notices/hash locks;validate in isolated relocated folder. Preserve all earlier packages. Current189-file demo is dated and lacks new installers/launcher work.',
        'Scientific priority remains genuinely fresh independent fixed-camera crossing/space/occupancy labels;source13inspection/source14rights-access gaps unchanged. No consumed final image/date/sequence reuse,source bypass/private access or author contact. No new weights/accuracy scoring this wake.',
        'Original8notebooks retained;only documented fresh-kernel/server checks accepted. Remaining visible browser/manual dialogs,all8fresh kernels,physical disconnection,new machine,student explanation/rehearsal and missing university documents. Use README data map and updated offline launch guide.',
        'Counter42;next100-run live checkpoint100. Source catalog57,including two authored official-Jupyter documentation consultation records. Token/private runtime files stay ignored;shared environment unchanged;no active jobs.',
        'Latest official source snapshot '+latest['accessed_at']+':'+str(snapshots)+'snapshots,'+str(live['scores_total'])+'matched baseline outcomes,MAE'+format(live['baseline_mae_spaces'],'.6f')+'. Continue sensible half-hour collection and causal frozen-target scoring;missing targets remain unscored.'
    ];write('data/automation_state.json',s)
    title='## 25 October 2026 / local JupyterLab server route verified'
    note=('New optional offline launcher disables update checks and makes extension management read-only,binds localhost and accepts notebook/port/no-browser/separate-state options. '
        'Actual isolated Jupyter server serves authenticated Lab HTML/local JS asset/notebook08source;anonymous kernelspec request403. '
        'Server-created project kernel uses the verified interpreter and returns a real inline training-image SVD plot;2D/3D arithmetic passes. '
        'Owned kernel deleted/server exits0;Python non-loopback audit attempts0.184regression tests and3invalid-launch controls pass. '
        'Usual project kernel state,original weights/notebooks and consumed final claims unchanged. No visible browser/frontend-JS execution,manual,physical/new-machine or scientific accuracy claim. '
        'One completed server trial advances41->42;software tests/requests/frames do not add runs. '
        'README now maps raw images/CSV/live JSON/normalized CSV/provenance/model results in plain language and corrects stale offline/sample-count wording. '
        'Source catalog57:official REST/messaging documentation consulted;authored notes/URLs/access precision retained,no source text/assets copied. '
        'Latest official snapshot'+str(snapshots)+',matched persistence outcomes'+str(live['scores_total'])+',MAE'+format(live['baseline_mae_spaces'],'.6f')+'spaces;not neural/camera accuracy. '
        'Guide:docs/OFFLINE_JUPYTER_SETUP.md;pointer:reports/jupyter_server_latest.json. Next:combined relocated demo+installer acceptance and fresh legitimate labelled evidence;remaining manual/student/academic gates separate.')
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(name,title,note)
    append('docs/UI_TEST_LOG.md',title,'Server/API/WebSocket route and inline PNG checked,including visual inspection of returned plot. No visible browser DOM/frontend-JavaScript/manual selection was tested. Server/kernel stopped cleanly;no UI process left open.')
    for name in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md']:append(name,title,
        'Catalog57. SRC-DOC-019official Jupyter Server REST API and SRC-DOC-020official Jupyter messaging documentation consulted. Authored reference notes under data/research and append-only receipts retain exact URLs,local hashes and honest date-only consultation precision. Documentation rights not independently audited;reference only,no copied source content/assets/training use. Existing107wheel/notices profile unchanged.')
    append('docs/AI_ASSISTANCE_LOG.md','### Official references for server implementation',
        'AI implemented and tested the launcher/server checks. References: https://jupyter-server.readthedocs.io/en/stable/developers/rest-api.html and https://jupyter-client.readthedocs.io/en/latest/messaging.html . Student contribution/mastery was not inferred.')
    path=ROOT/'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;requirements=list(r)
    for row in requirements:
        if row['requirement_id']=='OFF-01':row.update(test_result='107-package offline install,actual kernels,and authenticated local Lab/REST/WebSocket route pass;184tests plus3invalid-launch controls pass',
            actual_evidence='reports/offline_jupyter_latest.json; reports/jupyter_server_latest.json; docs/OFFLINE_JUPYTER_SETUP.md',
            open_problems='Existing base Python/OS/assets reused; visible frontend-JS/manual,all8fresh notebooks,physical/new-machine/student acceptance separate',next_action='Combined relocated demo+installer acceptance and remaining manual/physical/student gates')
        if row['requirement_id']=='PKG-01':row.update(test_result='Dated189-file copied demo preserved; separate107-package app+Jupyter installer set and local server/kernel checks pass',
            open_problems='Installers and dated demo remain separate; combined relocated package,physical/new-machine/manual and official acceptance unfinished',next_action='Build combined versioned local package with full original notices/provenance;validate in isolated copy')
        if row['requirement_id']=='SRC-01':row['test_result']='57unique source records;official Jupyter REST/protocol consultation notes added;all acquisition/provenance timing limitations retained'
        if row['requirement_id']=='PY-01':row.update(actual_evidence='notebooks/01..08; reports/offline_jupyter_latest.json; reports/jupyter_server_latest.json',
            test_result='8original notebooks executed;fresh lesson08and training-only smoke plus authenticated server-kernel route pass;not all8freshly rerun')
    with path.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(requirements)
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=42,scheduled_wakeups_completed=29,source_records=57,server_gate_passed=True,
        tests=184,launcher_negative_checks=3,original_assets_and_claims_unchanged=True,server_stopped=True,shared_environment_changed=False,
        visible_frontend_browser_tested=False,inline_png_visually_reviewed=True,next_live_milestone=100,no_active_jobs=True))
    print(json.dumps(dict(completed_trials=42,source_records=57,tests=184,live_snapshots=snapshots),indent=2))
if __name__=='__main__':main()
