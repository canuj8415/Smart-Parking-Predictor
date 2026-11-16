"""Read archived forecast reports for display; never re-score or read raw holdouts."""
import json
import math
from pathlib import Path
from .provenance import ROOT,digest
ORIGINAL='Original experiment'
LATER='Later-date check'
ORIGINAL_METHOD='Original LSTM'
LATER_METHOD='Group-relative residual LSTM'

def available_forecast_reports(root=ROOT):
    return [ORIGINAL]+([LATER] if (Path(root)/'models/forecast_final_evaluation.json').exists() else [])

def load_forecast_report(name,root=ROOT):
    root=Path(root)
    if name==ORIGINAL:
        card=json.loads((root/'models/lstm_30min_model_card.json').read_text())
        folder=(root/'experiments/results'/card['run_id']).resolve()
        if not folder.is_relative_to((root/'experiments/results').resolve()):raise ValueError('Invalid report location')
        predictions=folder/'test_predictions.json'
        rows=json.loads(predictions.read_text());m=card['metrics']
        return dict(name=name,run_id=card['run_id'],rows=rows,mae=m['mae_slots'],baseline_mae=m['persistence_mae_slots'],
            method_id='absolute_occupancy_lstm',method_label=ORIGINAL_METHOD,
            architecture='LSTM predicting absolute occupancy',source_id='SRC-DS-003',
            predictions_sha256=digest(predictions),checkpoint_sha256=card.get('checkpoint_sha256'),
            horizon_note='Half-hour grid targets; exact target-reading lead was not saved in this original report.')
    if name!=LATER:raise ValueError('Unknown forecast report')
    card=json.loads((root/'models/forecast_final_evaluation.json').read_text())
    folder=(root/'experiments/results'/card['run_id']).resolve()
    if not folder.is_relative_to((root/'experiments/results').resolve()):raise ValueError('Invalid report location')
    if digest(folder/'run.json')!=card['run_json_sha256'] or digest(folder/'test_predictions.json')!=card['predictions_sha256']:
        raise ValueError('Saved forecast report checksum changed')
    result=json.loads((folder/'run.json').read_text());final=result['final_evaluation']
    if not final['final_gate_passed']:raise ValueError('Later-date report did not pass its frozen gate')
    rows=json.loads((folder/'test_predictions.json').read_text())
    rows=[dict(r,predicted_occupied=r['candidate_occupied']) for r in rows]
    lead=final['actual_target_lead_minutes'];m=final['metrics']
    return dict(name=name,run_id=card['run_id'],rows=rows,mae=m['candidate_mae_spaces'],baseline_mae=m['persistence_mae_spaces'],
        method_id='trend_guarded_group_relative_residual_lstm',method_label=LATER_METHOD,
        architecture='Trend-guarded residual LSTM trained with a group-relative objective',source_id='SRC-DS-003',
        predictions_sha256=card['predictions_sha256'],checkpoint_sha256=card.get('checkpoint_sha256'),
        horizon_note=f"Half-hour grid targets; matched real readings arrive {lead['min']:.1f}–{lead['max']:.1f} minutes after the origin. Historical Birmingham, not live.")


def build_forecast_view(report,car_park_id):
    """One owned snapshot for plotting, explanatory text and later export.

    Reads only already loaded archived rows. It never fits a model, computes a
    fresh holdout score or substitutes sensor timestamps for missing values.
    """
    rows=sorted([dict(r) for r in report['rows'] if r['car_park_id']==car_park_id],key=lambda r:(r['origin'],r['target_time']))
    if not rows:raise ValueError('No archived forecast windows for this car park')
    for row in rows:
        capacity=row['capacity']
        if isinstance(capacity,bool) or not isinstance(capacity,(int,float)) or not math.isfinite(capacity) or capacity<=0:
            raise ValueError('Invalid saved parking capacity')
        for key in ['actual_occupied','predicted_occupied','persistence_occupied']:
            value=row[key]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=capacity:
                raise ValueError('Invalid saved occupancy count')
    actual=[r['capacity']-r['actual_occupied'] for r in rows]
    predicted=[r['capacity']-r['predicted_occupied'] for r in rows]
    baseline=[r['capacity']-r['persistence_occupied'] for r in rows]
    last=rows[-1]
    info=(f"{report['name']} · {report['method_label']} · Recorded grid target {last['target_time']}\n"
        f"Last historical forecast shown: {predicted[-1]:.1f} available / {last['capacity']} capacity. Actual: {actual[-1]:.0f}.\n"
        f"Overall report MAE: {report['method_label']} {report['mae']:.2f}; persistence {report['baseline_mae']:.2f} spaces. Lower is better.\n"
        f"{report['horizon_note']}")
    metadata={k:report.get(k) for k in ['name','run_id','method_id','method_label','architecture','source_id','predictions_sha256','checkpoint_sha256','mae','baseline_mae','horizon_note']}
    return dict(report=metadata,car_park_id=car_park_id,rows=rows,actual_available=actual,
        predicted_available=predicted,persistence_available=baseline,
        forecast_legend=report['method_label']+' forecast',info_text=info,
        plot_title=car_park_id+' · 30-minute grid targets',
        scope='Archived historical Birmingham predictions; no new evaluation, camera forecast or Singapore live forecast')
