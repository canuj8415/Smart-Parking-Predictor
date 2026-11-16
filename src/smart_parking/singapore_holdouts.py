"""Global future-time reservation and once-only selected forecast final claim."""
import json,os,hashlib,math
from datetime import timedelta
from pathlib import Path
from .singapore_history import aware_utc
from .prospective import SOURCE
from .provenance import digest,ROOT


def validate_reservation(value):
    if value['source_id']!=SOURCE or value['carparks_scope']!='ALL':raise ValueError('Canonical source/all-carpark scope required')
    created=aware_utc(value['created_at']);cutoff=aware_utc(value['historical_cutoff']);start=aware_utc(value['final_origin_start']);end=aware_utc(value['final_origin_end'])
    if not cutoff<=created<start<end:raise ValueError('Historical/future chronology invalid')
    if aware_utc(value['final_target_end'])!=end+timedelta(minutes=51):raise ValueError('Target/delivery closure must extend51minutes')
    return value


def assert_history_allowed(value,available_at,observed_at):
    validate_reservation(value);cutoff=aware_utc(value['historical_cutoff'])
    if aware_utc(available_at)>cutoff or aware_utc(observed_at)>cutoff:raise ValueError('Future or post-cutoff observation forbidden for fitting')


def final_once(reservation,selection,checkpoint,run_id,evaluate,*,as_of,receipts,expected_reservation_sha256,root=ROOT):
    """Only score a pre-frozen passing candidate after the whole final window.

    The callback may open target values only AFTER the global interval claim is
    flushed. Any failure consumes it. This does not issue forecasts retroactively.
    """
    reservation=Path(reservation);selection=Path(selection);checkpoint=Path(checkpoint)
    if digest(reservation)!=expected_reservation_sha256:raise ValueError('Reserved interval changed')
    value=validate_reservation(json.loads(reservation.read_text(encoding='utf-8')));chosen=json.loads(selection.read_text(encoding='utf-8'))
    if aware_utc(as_of)<aware_utc(value['final_target_end']):raise ValueError('Final window has not closed;no partial peeking')
    if chosen.get('development_gate_passed') is not True:raise ValueError('Passing frozen development selection required')
    if chosen['reservation_sha256']!=expected_reservation_sha256 or chosen['checkpoint_sha256']!=digest(checkpoint):raise ValueError('Selection/checkpoint binding invalid')
    if aware_utc(chosen['frozen_at'])>=aware_utc(value['final_origin_start']):raise ValueError('Candidate frozen too late')
    base=Path(root).resolve();ledger=(base/chosen['forecast_ledger']).resolve()
    if not ledger.is_relative_to(base) or digest(ledger)!=chosen['forecast_ledger_sha256']:raise ValueError('Frozen issuance ledger changed/outside project')
    forecasts=[json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not forecasts or len({r['forecast_id'] for r in forecasts})!=len(forecasts):raise ValueError('Missing/duplicate frozen forecasts')
    for forecast in forecasts:
        issued=aware_utc(forecast['issued_at']);committed=aware_utc(forecast['committed_at'])
        if not aware_utc(value['final_origin_start'])<=issued<aware_utc(value['final_origin_end']):raise ValueError('Forecast origin outside reserved interval')
        if not issued<=committed<issued+timedelta(minutes=20):raise ValueError('Forecast not committed before target window')
        if forecast['source_id']!=SOURCE or forecast['checkpoint_sha256']!=chosen['checkpoint_sha256'] or forecast['reservation_sha256']!=expected_reservation_sha256:raise ValueError('Forecast source/model/reservation binding invalid')
        if aware_utc(forecast['earliest_target'])!=issued+timedelta(minutes=20) or aware_utc(forecast['latest_target'])!=issued+timedelta(minutes=45):raise ValueError('Forecast target window changed')
        if any(k in forecast for k in ['actual_available','absolute_error_spaces','target_observed_at']):raise ValueError('Issuance ledger contains target outcomes')
        capacity=forecast['capacity'];predicted=forecast['predicted_available']
        if type(capacity) is not int or capacity<=0 or not math.isfinite(predicted) or not 0<=predicted<=capacity:raise ValueError('Invalid frozen forecast bounds')
        receipt=forecast['origin_receipt'];snapshot=(base/receipt['local_path']).resolve()
        if receipt['source_id']!=SOURCE or aware_utc(receipt['accessed_at'])>issued or not snapshot.is_relative_to(base) or digest(snapshot)!=receipt['sha256']:raise ValueError('Origin was not available/bound at issue time')
        if any(not isinstance(forecast.get(k),str) or not forecast[k].strip() for k in ['car_park_id','lot_type']):raise ValueError('Missing forecast series identity')
        observed=aware_utc(forecast['origin_observed_at']);feed=aware_utc(forecast['origin_provider_time'])
        if not observed<=feed<=issued+timedelta(seconds=30) or issued-observed>timedelta(minutes=3) or issued-aware_utc(receipt['accessed_at'])>timedelta(minutes=3):raise ValueError('Forecast origin was stale or temporally invalid')
    folder=Path(receipts);folder.mkdir(parents=True,exist_ok=True);lock=folder/'claim.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        start=aware_utc(value['final_origin_start']);end=aware_utc(value['final_target_end'])
        for path in folder.glob('*.claim.json'):
            old=json.loads(path.read_text(encoding='utf-8'))
            if old['canonical_source']==SOURCE and start<=aware_utc(old['interval_end']) and aware_utc(old['interval_start'])<=end:raise ValueError('Global source interval already consumed')
        identity=hashlib.sha256((SOURCE+'|'+start.isoformat()+'|'+end.isoformat()).encode()).hexdigest();marker=folder/(identity+'.claim.json')
        record=dict(run_id=run_id,canonical_source=SOURCE,carparks_scope='ALL',interval_start=start.isoformat(),interval_end=end.isoformat(),
            reservation_sha256=expected_reservation_sha256,checkpoint_sha256=digest(checkpoint),status='Consumed before callback;failure never releases interval')
        with marker.open('x',encoding='utf-8') as stream:json.dump(record,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    finally:lock.unlink(missing_ok=True)
    try:
        result=evaluate(value)
        if digest(reservation)!=expected_reservation_sha256 or digest(checkpoint)!=chosen['checkpoint_sha256'] or digest(ledger)!=chosen['forecast_ledger_sha256']:raise ValueError('Frozen final inputs changed during scoring')
    except BaseException as error:
        marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='failed;interval remains consumed',error=type(error).__name__,detail=str(error))),encoding='utf-8');raise
    marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='completed;interval consumed')),encoding='utf-8')
    return result
