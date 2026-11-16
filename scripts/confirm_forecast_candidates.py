"""Bounded, predeclared multi-seed development comparison, excluding final test."""
import csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.forecast_experiment import train_candidate
from smart_parking.forecasting import build_windows
from smart_parking.provenance import digest

if __name__=='__main__':
    folder=ROOT/'experiments/results'/('FORECAST-CONFIRMATION-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True)
    schedule=[('residual',45),('residual',46),('trend_guard',44),('trend_guard',45),('trend_guard',46)]
    protocol=dict(created_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-003',
        schedule=[dict(variant=v,seed=s) for v,s in schedule],max_epochs=80,patience=12,
        hypothesis='A past-hour trend constraint will reduce two per-park regressions; confirm raw and guarded residual models over seeds 44,45,46.',
        gate='Same existing overall >=5% MAE improvement and <=10% per-park regression where n>=10; no promotion without fresh final evaluation',
        final_test_evaluated=False,model_code_sha256=digest(ROOT/'src/smart_parking/forecast_experiment.py'))
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    w=build_windows(splits=('train','validation'));diagnosis=[]
    for park in ['NIA Car Parks','Others-CCCPS119a']:
        for split,rows in w.items():
            subset=[r for r in rows if r['car_park_id']==park]
            changes=[(r['y']-r['baseline'])*r['capacity'] for r in subset]
            diagnosis.append(dict(car_park_id=park,split=split,windows=len(subset),mean_signed_change_spaces=sum(changes)/len(changes),mean_abs_change_spaces=sum(abs(c) for c in changes)/len(changes)))
    (folder/'distribution_diagnosis.json').write_text(json.dumps(diagnosis,indent=2),encoding='utf-8')
    results=[]
    for variant,seed in schedule:
        r=train_candidate(seed=seed,variant=variant);results.append(r)
        (folder/'completed_runs.json').write_text(json.dumps([a['run_id'] for a in results],indent=2),encoding='utf-8')
        print(json.dumps(dict(run=r['run_id'],seed=seed,variant=variant,metrics=r['metrics'])),flush=True)
    previous=json.loads((ROOT/'experiments/results/FORECAST-RESIDUAL-20261024T161926856855Z/run.json').read_text())
    all_results=[previous]+results;summary=[]
    for r in all_results:
        failed=[p['car_park_id'] for p in r['per_park'] if p['windows']>=10 and p['candidate_mae']>p['persistence_mae']*1.1]
        summary.append(dict(run_id=r['run_id'],variant=r.get('variant','residual'),seed=r['seed'],epochs=r['epochs_completed'],best_epoch=r['best_epoch'],validation_mae=r['metrics']['candidate_validation_mae_slots'],improvement=r['metrics']['improvement_vs_persistence'],gate_passed=r['metrics']['validation_gate_passed'],failed_parks=failed))
    (folder/'summary.json').write_text(json.dumps(dict(protocol=protocol,runs=summary,diagnosis=diagnosis,production_changed=False,limitations=['All results are development validation; validation is reused across hypotheses','No independent final result or live forecasting accuracy']),indent=2),encoding='utf-8')
    with (folder/'comparison.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
    with registry.open(encoding='utf-8',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;records=list(reader)
    ids={r['experiment_id'] for r in records}
    for r in results:
        if r['run_id'] in ids:continue
        p='experiments/results/'+r['run_id'];item={k:'see run.json' for k in fields}
        item.update(experiment_id=r['run_id'],run_type='real-data training and development validation only',started_at=r['started_at'],finished_at=r['finished_at'],source_ids=r['source_id'],split_ids=r['split_id'],configuration=p+'/protocol.json',architecture=r['architecture'],model_version=r['run_id'],optimizer=r['optimizer'],learning_rate=r['learning_rate'],epochs=r['epochs_completed'],batch_size=r['batch_size'],random_seed=r['seed'],hardware='i9-14900HX; CPU',execution_environment='Python 3.12.10; Torch '+r['torch_version'],training_duration=r['training_seconds'],loss_curves=p+'/curves.json',evaluation_metrics=json.dumps(r['metrics']),logs=p,checkpoints=p+'/candidate.pt',implementation_sha256=r['code_sha256'],conclusions='Development validation only; no production promotion; see per-park gate results')
        records.append(item)
    with registry.open('w',encoding='utf-8',newline='') as f:writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    print(json.dumps(dict(confirmation_folder=str(folder),runs=summary),indent=2),flush=True)
