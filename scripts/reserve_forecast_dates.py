"""Reserve later dates using metadata only, without parsing numeric final outcomes."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
RUN='FORECAST-GROUP-ROBUST-20261025T094258007427Z'

if __name__=='__main__':
    target=ROOT/'data/manifests/forecast_fresh_dates_v1.json'
    if target.exists():raise FileExistsError('Preserve the original sealed date reservation')
    source=ROOT/'data/splits/birmingham-global-days-v1/manifest.csv'
    old=ROOT/'experiments/results/LSTM-20261024T091132028689Z/test_predictions.json'
    old_rows=json.loads(old.read_text());used={r[k][:10] for r in old_rows for k in ['origin','target_time']}
    # These selected fields are identifiers/timestamps only. Occupancy/availability
    # are never converted, inspected, used for selection, or saved here.
    with source.open(encoding='utf-8',newline='') as stream:
        metadata=[{k:r[k] for k in ['source_id','source_row','car_park_id','timestamp','capture_date','split']}
                  for r in csv.DictReader(stream)]
    reserved=[r for r in metadata if r['split']=='test' and r['capture_date'] not in used]
    assert reserved and all(r['capture_date']>max(used) for r in reserved)
    result=json.loads((ROOT/'experiments/results'/RUN/'run.json').read_text())
    checkpoint=ROOT/'experiments/results'/RUN/'candidate.pt'
    assert result['metrics']['validation_gate_passed'] and digest(checkpoint)==result['checkpoint_sha256']
    report=dict(schema_version=1,reserved_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-003',
        source_manifest=source.relative_to(ROOT).as_posix(),source_manifest_sha256=digest(source),
        original_consumed_predictions=old.relative_to(ROOT).as_posix(),original_consumed_predictions_sha256=digest(old),
        original_scored_dates=sorted(used),reserved_dates=sorted({r['capture_date'] for r in reserved}),
        reserved_rows=len(reserved),reserved_parks=sorted({r['car_park_id'] for r in reserved}),metadata=reserved,
        selected_candidate_run=RUN,selected_checkpoint_sha256=result['checkpoint_sha256'],
        selected_result_sha256=digest(ROOT/'experiments/results'/RUN/'run.json'),
        status='reserved; not evaluated; no numeric final outcome parsing in this reservation script',
        evidence_scope='Dates absent from the only archived historical forecast test-prediction artifact. Original source ingestion/auditing was not a physically blinded data collection. Not a new external source.',
        requirements_before_use=['Never use these dates for training, calibration, development tuning or repeated final evaluation',
            'Implement and test an exclusive durable overlap-aware date claim BEFORE any evaluation callback accesses numeric outcomes; failures consume the dates',
            'Fix a causal window-construction/target-time protocol using training/development only. Original half-hour grid produced no archived scored final windows on these dates; do not promise adequate future sample count',
            'Freeze the exact candidate, preprocessing, eligibility rules, comparators and acceptance gates before one-time final evaluation; report unavailable metrics if no admissible windows',
            'An eventual result is Birmingham source-specific; no live Singapore/camera transfer claim'],
        reservation_code_sha256=digest(Path(__file__)))
    with target.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:report[k] for k in ['reserved_dates','reserved_rows','reserved_parks','status']},indent=2))
