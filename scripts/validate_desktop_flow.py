"""A bounded real-file integration trial of the video-bound desktop processing route."""
import csv,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.flow_setup import video_preview,make_setup,run_configured_flow
from smart_parking.provenance import digest

def main():
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('A job is already active')
    started=datetime.now(timezone.utc);run='DESKTOP-FLOW-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    prior=json.loads((ROOT/'experiments/results/GATE-VIDEO-20261024T231251838602Z/protocol.json').read_text())
    source=ROOT/prior['source_attribution']['local_path'];image,identity=video_preview(source)
    assert identity['source_sha256']==prior['source_sha256']
    setup=make_setup(identity,[[100,700],[1900,700]],'negative_to_positive')
    files=['scripts/validate_desktop_flow.py','src/smart_parking/flow_setup.py','src/smart_parking/app.py',
           'src/smart_parking/flow.py','src/smart_parking/video.py','src/smart_parking/vision.py']
    hashes={p:digest(ROOT/p) for p in files}
    protocol=dict(run_id=run,started_at=started.isoformat(),source_ids=['SRC-VID-001','SRC-MOD-001'],
        seed='Deterministic existing inference; no training',hypothesis='The new desktop route binds its gate to exact source bytes and first-frame pixels, runs three bounded real samples and exports consistent predictions without occupancy answers',
        source_sha256=identity['source_sha256'],setup=setup,max_processed_frames=3,interval_seconds=.5,
        detector_sha256='dd69338a24b8d7381807e247652bdc356325bcbaf1cd3e092e00e0a1a58706bf',
        source_hashes=hashes,code_revision_basis='b94172a plus exact source snapshots',
        gates=['3 processed frames','CSV and per-frame JSON counts agree','source unchanged before/after','no occupancy scores exported','recorded model hash matches frozen model'],
        scope='Already-seen licensed street clip; software integration only. Configured line is not a known parking entrance. No positive real crossing labels, flow accuracy, final model evaluation or new training.')
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf-8')
    snapshots={p:dict(sha256=hashes[p],source=(ROOT/p).read_text(encoding='utf-8')) for p in files}
    (folder/'implementation_sources.json').write_text(json.dumps(snapshots,indent=2)+'\n',encoding='utf-8')
    (folder/'source_attribution.json').write_text(json.dumps(prior['source_attribution'],indent=2)+'\n',encoding='utf-8')
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    start=time.perf_counter()
    try:
        from smart_parking.vision import VisionEngine
        engine=VisionEngine('fasterrcnn');assert engine.weight_sha256==protocol['detector_sha256']
        summary=run_configured_flow(setup,folder/'video',engine,max_frames=3,cancel=lambda:(folder/'CANCEL').exists())
        predictions=[json.loads(line) for line in (folder/'video/detections.jsonl').read_text().splitlines()]
        with (folder/'video/observations.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
        assert summary['processed_frames']==len(predictions)==len(rows)==3
        for p,row in zip(predictions,rows):
            assert not p['occupancy_evaluated'] and 'occupied' not in row and p['result']['counts'] is None
            assert p['result']['weight_sha256']==protocol['detector_sha256']
            assert p['result']['flow']['counts']=={k:int(row[k]) for k in ['entries','exits']}
        manifest=json.loads((folder/'video/source_and_gate.json').read_text());assert manifest['source_verified_after'] and manifest['status']=='completed'
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-start,
            summary=summary,validation_passed=True,accuracy_evaluated=False,source_after_sha256=digest(source))
        (folder/'predictions.json').write_text(json.dumps(predictions,indent=2)+'\n',encoding='utf-8')
        (folder/'run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,validation_passed=True,frames=3,flow=summary['flow_diagnostics'],duration=report['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        (folder/'interrupted.json').write_text(json.dumps(dict(error=str(error),completed_run_counted=False),indent=2)+'\n',encoding='utf-8')
        state=json.loads(state_path.read_text());raise
    finally:
        state['active_validation_jobs']=[];state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
