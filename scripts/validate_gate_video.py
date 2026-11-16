"""Fixed-cadence real-video flow integration; no accuracy ground truth supplied."""
import csv,json,os,statistics,sys,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.vision import VisionEngine
from smart_parking.video import process_video
from smart_parking.flow import GateCounter
from smart_parking.provenance import digest

def main():
    lock=ROOT/'.cache/gate_video.lock';lock.parent.mkdir(exist_ok=True)
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(descriptor,str(os.getpid()).encode());os.close(descriptor)
    try:validate()
    finally:lock.unlink(missing_ok=True)

def validate():
    started=datetime.now(timezone.utc);run='GATE-VIDEO-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    source=ROOT/'data/raw/wikimedia_street_traffic/Street_traffic.webm'
    attribution=json.loads(source.with_name('acquisition.json').read_text())
    assert digest(source)==attribution['sha256']
    config=GateCounter(image_size=[1920,1080],line=[[100,700],[1900,700]],entry_direction='negative_to_positive').config
    paths=['scripts/validate_gate_video.py','src/smart_parking/flow.py','src/smart_parking/video.py','src/smart_parking/vision.py']
    protocol=dict(run_id=run,started_at=started.isoformat(),source_id='SRC-VID-001',source_sha256=digest(source),
        seed='Not applicable: deterministic existing model inference and association; no randomized training',
        hypothesis='Explicit finite-line flow predictions integrate with video exports at0.5s cadence;2s archived samples force gap resets rather than unsupported cross-gap counts',
        gate_config=config,detector_threshold=.5,interval_seconds=.5,max_processed_frames=25,
        model='Existing Faster R-CNN ResNet50FPNv2; unchanged weights',model_sha256=digest(ROOT/'models/pretrained/fasterrcnn_resnet50_fpn_v2.pth'),
        original_photo_used_for_gate='REAL-VIDEO-20261024T175346074895Z/source_frame_00000.jpg; development visual setup only',
        split='Single already-seen street clip, integration only; no final data or model-selection accuracy',
        source_hashes={p:digest(ROOT/p) for p in paths},code_revision_basis='bd92e54 plus exact implementation snapshots',
        source_attribution=attribution,acceptance='Monotone timestamps, all CSV/JSON cumulative counts and event logs agree; no inferred occupancy; preserve original predictions and resets. This is a software gate, not a tracking-accuracy gate.',
        accuracy_evaluated=False,limitations=['Configured street line is not a real parking entrance','Box centres and association are predicted; no ground truth tracks/counts','Ambiguity, occlusion or missing observations may fragment tracks and undercount','No identity re-identification or deployment accuracy claim'])
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    (folder/'implementation_sources.json').write_text(json.dumps({p:dict(sha256=digest(ROOT/p),source=(ROOT/p).read_text(encoding='utf-8')) for p in paths},indent=2),encoding='utf-8')
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text())
    state['active_validation_jobs']=[dict(run_id=run,pid=os.getpid(),kind='bounded real-video inference; no trainer')];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    start=time.perf_counter()
    try:
        engine=VisionEngine('fasterrcnn');loaded=time.perf_counter()-start
        def progress(image,result,timestamp):print(f'{run} video{timestamp:.2f}s counts{result["flow"]["counts"]}',flush=True)
        summary=process_video(str(source),engine,None,folder/'video',every_seconds=.5,max_frames=25,confidence=.5,flow_config=config,
            callback=progress,cancel=lambda:(folder/'CANCEL').exists())
        logs=[json.loads(line) for line in (folder/'video/detections.jsonl').read_text().splitlines()]
        with (folder/'video/observations.csv').open(newline='') as stream:observations=list(csv.DictReader(stream))
        assert len(logs)==len(observations)==summary['processed_frames']
        times=[row['video_time_seconds'] for row in logs]
        assert all(b>a for a,b in zip(times,times[1:]))
        assert all(b-a<=config['max_gap_seconds'] for a,b in zip(times,times[1:]))
        events=[e for row in logs for e in row['result']['flow']['events']]
        assert events==summary['flow_events']
        entries=exits=0
        for log,row in zip(logs,observations):
            entries+=sum(e['event_type']=='entry' for e in log['result']['flow']['events'])
            exits+=sum(e['event_type']=='exit' for e in log['result']['flow']['events'])
            assert log['result']['flow']['counts']==dict(entries=entries,exits=exits)
            assert int(row['entries'])==entries and int(row['exits'])==exits
            assert not log['occupancy_evaluated'] and 'occupied' not in row
        sparse=GateCounter(**config)
        archived=ROOT/'experiments/results/REAL-VIDEO-20261024T175346074895Z/video/detections.jsonl'
        for line in archived.read_text().splitlines():
            record=json.loads(line);sparse_out=sparse.update(record['result']['detections'],record['video_time_seconds'])
        assert sparse.gap_resets==17 and sparse.entries==sparse.exits==0
        latency=[x['result']['latency_seconds'] for x in logs]
        report=dict(**protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-start,
            detector_load_seconds=loaded,summary=summary,median_inference_seconds=statistics.median(latency),
            sparse_replay=dict(input_path=str(archived.relative_to(ROOT)),sha256=digest(archived),result=sparse_out,
                interpretation='All17two-second gaps exceed0.75s; zero counts reflect abstention, not zero actual crossings'),
            export_consistency_passed=True,cancelled=(folder/'CANCEL').exists())
        (folder/'run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (folder/'source_attribution.json').write_text(json.dumps(attribution,indent=2),encoding='utf-8')
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(state['completed_run_ids']);state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,processed_frames=len(logs),counts=summary['flow_diagnostics'],duration=report['duration_seconds']),indent=2),flush=True)
    except BaseException as error:
        (folder/'interrupted.json').write_text(json.dumps(dict(error=str(error),completed_run_counted=False),indent=2),encoding='utf-8')
        state=json.loads(state_path.read_text());raise
    finally:
        state['active_validation_jobs']=[];state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')

if __name__=='__main__':main()
