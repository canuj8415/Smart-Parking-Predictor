"""Keep the saved analysis image paired with its actual prediction record."""
import csv
import io
import json
import math
import tempfile
from datetime import datetime,timezone
from pathlib import Path
from .provenance import digest


def _json(value):
    try:return json.dumps(value,indent=2,allow_nan=False)+'\n'
    except (TypeError,ValueError) as error:raise ValueError('Result contains unsupported or nonfinite JSON data.') from error


def _verify_png(path):
    from PIL import Image
    try:
        with Image.open(path) as image:
            if image.format!='PNG':raise ValueError('Saved visualization must be PNG')
            image.verify()
    except (OSError,SyntaxError) as error:raise ValueError('Saved visualization is incomplete or invalid.') from error


def _publish(parent,prefix,writer):
    """Publish a complete directory; clean only this invocation's owned files."""
    parent=Path(parent).resolve();parent.mkdir(parents=True,exist_ok=True)
    folder=Path(tempfile.mkdtemp(prefix='.'+prefix+'-staging-',dir=parent))
    final=parent/datetime.now(timezone.utc).strftime(prefix+'_%Y%m%dT%H%M%S%fZ')
    try:
        writer(folder)
        if final.exists():raise FileExistsError('An export already exists with this name;save again.')
        folder.rename(final)
        return final
    except BaseException as error:
        try:
            # No recursive removal: never remove an earlier export or follow an
            # unexpected subdirectory. Verify the absolute owned target first.
            if folder.exists():
                if folder.resolve().parent!=parent or not folder.name.startswith('.'+prefix+'-staging-'):
                    raise OSError('Export staging directory identity changed;left untouched')
                for file in folder.iterdir():
                    if file.is_dir() and not file.is_symlink():raise OSError('Unexpected export subdirectory;left untouched')
                    file.unlink()
                folder.rmdir()
        except OSError as cleanup_error:error.add_note('Staging cleanup incomplete: '+str(cleanup_error))
        raise

def export_analysis(parent,result,analysis_image,*,preview_image=None,preview_kind='analysis'):
    if result is None or analysis_image is None:
        raise ValueError('Run image analysis before saving results.')
    if not isinstance(result,dict):raise ValueError('Analysis record must be a JSON object.')
    record=_json(result);_json(preview_kind)
    def write(folder):
        analysis_image.save(folder/'overlay.png');_verify_png(folder/'overlay.png')
        (folder/'analysis.json').write_text(record,encoding='utf-8')
        names=['overlay.png','analysis.json']
        metadata=dict(schema_version=1,complete=True,analysis_overlay='overlay.png',
            analysis_overlay_sha256=digest(folder/'overlay.png'),analysis_record='analysis.json',
            analysis_record_sha256=digest(folder/'analysis.json'),displayed_view=preview_kind)
        if preview_image is not None and preview_kind!='analysis':
            preview_image.save(folder/'display_preview.png');_verify_png(folder/'display_preview.png');names.append('display_preview.png')
            metadata.update(display_preview='display_preview.png',display_preview_sha256=digest(folder/'display_preview.png'),
                preview_note='Separate displayed visualization; occupancy JSON describes overlay.png only')
        metadata['files']={name:digest(folder/name) for name in names}
        (folder/'export_metadata.json').write_text(_json(metadata),encoding='utf-8')
    return _publish(parent,'parking',write)


def export_forecast(parent,view,figure):
    """Export the displayed archived forecast, with its own method and provenance."""
    if view is None or figure is None:raise ValueError('Show an archived forecast before saving results.')
    report=view['report'];rows=view['rows']
    if not rows or any(r['car_park_id']!=view['car_park_id'] for r in rows):raise ValueError('Forecast selection does not match displayed results')
    for key in ['actual_available','predicted_available','persistence_available']:
        if len(view[key])!=len(rows):raise ValueError('Displayed forecast vector length differs from saved windows')
    def number(value):return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value)
    for i,row in enumerate(rows):
        capacity=row['capacity']
        if not number(capacity) or capacity<=0:raise ValueError('Invalid saved parking capacity')
        for occupied,available in [('actual_occupied','actual_available'),('predicted_occupied','predicted_available'),('persistence_occupied','persistence_available')]:
            a,b=row[occupied],view[available][i]
            if not number(a) or not 0<=a<=capacity or not number(b) or not 0<=b<=capacity or not math.isclose(b,capacity-a,rel_tol=1e-12,abs_tol=1e-9):
                raise ValueError('Displayed availability differs from saved occupied counts')
    csv_rows=[]
    for i,row in enumerate(rows):
        csv_rows.append(dict(source_id=report['source_id'],run_id=report['run_id'],report_name=report['name'],
            method_id=report['method_id'],method_label=report['method_label'],car_park_id=view['car_park_id'],
            origin=row['origin'],target_grid_time=row['target_time'],target_source_time=row.get('target_source_time'),
            actual_target_lead_minutes=row.get('actual_target_lead_minutes'),capacity=row['capacity'],
            actual_occupied=row['actual_occupied'],predicted_occupied=row['predicted_occupied'],persistence_occupied=row['persistence_occupied'],
            actual_available=view['actual_available'][i],predicted_available=view['predicted_available'][i],
            persistence_available=view['persistence_available'][i]))
    _json(csv_rows)  # Strict finite/serializable data before any directory creation.
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    csv_text=stream.getvalue()
    snapshot=dict(schema_version=1,report=report,car_park_id=view['car_park_id'],selected_windows=len(rows),
        scope=view['scope'],metrics_scope='Saved overall report metrics, not newly scored or limited to the selected car park',
        timestamps='Grid targets and real sensor timestamps are distinct;unrecorded source times/leads remain absent',
        original_occupied_prediction_column='candidate_occupied' if report['method_id']=='trend_guarded_group_relative_residual_lstm' else 'predicted_occupied')
    record=_json(snapshot)
    metadata=dict(schema_version=1,complete=True,displayed_report=report['name'],method_id=report['method_id'],
        method_label=report['method_label'],run_id=report['run_id'],car_park_id=view['car_park_id'],
        archived_predictions_sha256=report['predictions_sha256'])
    _json(metadata)
    def write(folder):
        figure.savefig(folder/'forecast.png',dpi=130);_verify_png(folder/'forecast.png')
        with (folder/'forecasts.csv').open('w',encoding='utf-8',newline='') as output:output.write(csv_text)
        (folder/'forecast_report.json').write_text(record,encoding='utf-8')
        metadata['files']={name:digest(folder/name) for name in ['forecast.png','forecasts.csv','forecast_report.json']}
        (folder/'export_metadata.json').write_text(_json(metadata),encoding='utf-8')
    return _publish(parent,'forecast',write)
