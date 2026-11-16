"""Freeze and score a source-specific live baseline against later observations.

This is a next-snapshot persistence baseline with an explicit 20-45 minute
observation window, not a trained neural forecast or exact 30-minute benchmark.
"""
import hashlib,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from .provenance import ROOT

SOURCE='SRC-LIVE-001'
SINGAPORE=timezone(timedelta(hours=8))
MAX_FEED_AGE=timedelta(minutes=3)
MAX_OBSERVATION_LAG=timedelta(minutes=3)

def instant(value):
    at=datetime.fromisoformat(value)
    # HDB carpark update_datetime has no offset; provider-local Singapore time.
    if at.tzinfo is None:at=at.replace(tzinfo=SINGAPORE)
    return at.astimezone(timezone.utc)

def _valid(row):
    return row.get('source_id')==SOURCE and int(row['capacity'])>0 and 0<=int(row['available'])<=int(row['capacity'])

def freeze_baseline(rows,issued_at):
    issued=instant(issued_at);result=[];seen=set()
    for row in rows:
        if not _valid(row):continue
        feed=instant(row['feed_timestamp']);observed=instant(row['observed_at'])
        if not timedelta(seconds=-30)<=issued-feed<=timedelta(minutes=3):continue
        if not timedelta(seconds=-30)<=issued-observed<=timedelta(minutes=3):continue
        key=(row['car_park_id'],row['lot_type'],row['feed_timestamp'])
        if key in seen:continue
        seen.add(key)
        identity='|'.join((SOURCE,*key,'next_snapshot_persistence_v1'))
        result.append(dict(forecast_id=hashlib.sha256(identity.encode()).hexdigest(),source_id=SOURCE,
            car_park_id=row['car_park_id'],lot_type=row['lot_type'],capacity=int(row['capacity']),
            issued_at=issued.isoformat(),origin_provider_time=feed.isoformat(),origin_observed_at=observed.isoformat(),
            earliest_target=(issued+timedelta(minutes=20)).isoformat(),latest_target=(issued+timedelta(minutes=45)).isoformat(),
            method='next_snapshot_persistence_v1',predicted_available=int(row['available']),
            scope='Prospective next-snapshot baseline, variable 20-45 minute horizon; not neural or camera accuracy'))
    return result

def score_baseline(forecasts,rows,collected_at,already_scored=()):
    collected=instant(collected_at);done=set(already_scored);scores=[]
    indexed={}
    for row in rows:
        if _valid(row):indexed.setdefault((row['car_park_id'],row['lot_type']),[]).append(row)
    for forecast in forecasts:
        if forecast['forecast_id'] in done:continue
        issued=instant(forecast['issued_at']);minimum=instant(forecast['earliest_target']);maximum=instant(forecast['latest_target'])
        candidates=[]
        for row in indexed.get((forecast['car_park_id'],forecast['lot_type']),[]):
            observed=instant(row['observed_at']);feed=instant(row['feed_timestamp'])
            if int(row['capacity'])!=forecast['capacity']:continue
            if not issued<observed<=feed<=collected+timedelta(seconds=30):continue
            if not minimum<=observed<=maximum:continue
            if collected-feed>MAX_FEED_AGE or feed-observed>MAX_OBSERVATION_LAG:continue
            candidates.append((observed,row))
        if not candidates:continue
        observed,row=min(candidates,key=lambda p:p[0]);actual=int(row['available'])
        scores.append(dict(forecast_id=forecast['forecast_id'],source_id=SOURCE,car_park_id=forecast['car_park_id'],
            lot_type=forecast['lot_type'],issued_at=issued.isoformat(),observed_at=observed.isoformat(),
            scored_at=collected.isoformat(),actual_horizon_minutes=(observed-issued).total_seconds()/60,
            predicted_available=forecast['predicted_available'],actual_available=actual,
            absolute_error_spaces=abs(forecast['predicted_available']-actual),method=forecast['method']))
        done.add(forecast['forecast_id'])
    return scores

def load_records(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()] if Path(path).exists() else []

def ledger_status(forecasts,scores,as_of):
    """Expose missing-target coverage without converting missing targets to errors.

    Scoring can accept a late-delivered target for at most feed age plus source
    observation lag after the target window. Until then it remains pending.
    This is forecast/observation matching coverage, never prediction accuracy.
    """
    now=instant(as_of);seen=set();cohorts={}
    done={r['forecast_id'] for r in scores if instant(r['scored_at'])<=now}
    names=['scored','pending_before_window','pending_in_window','awaiting_late_delivery','expired_missing_target']
    counts={name:0 for name in names};excluded_future=0
    for forecast in forecasts:
        identity=forecast['forecast_id']
        if identity in seen:raise ValueError('Duplicate forecast IDs in prospective ledger')
        seen.add(identity);issued=instant(forecast['issued_at'])
        if issued>now:excluded_future+=1;continue
        first=instant(forecast['earliest_target']);last=instant(forecast['latest_target'])
        if identity in done:status='scored'
        elif now<first:status='pending_before_window'
        elif now<=last:status='pending_in_window'
        elif now<=last+MAX_FEED_AGE+MAX_OBSERVATION_LAG:status='awaiting_late_delivery'
        else:status='expired_missing_target'
        counts[status]+=1;cohort=cohorts.setdefault(issued.isoformat(),dict(issued_at=issued.isoformat(),**{n:0 for n in names}))
        cohort[status]+=1
    resolved=counts['scored']+counts['expired_missing_target']
    return dict(as_of=now.isoformat(),**counts,forecasts_issued_by_as_of=sum(counts.values()),
        resolved_forecasts=resolved,matched_fraction_of_resolved_forecasts=counts['scored']/resolved if resolved else None,
        late_delivery_grace_minutes=(MAX_FEED_AGE+MAX_OBSERVATION_LAG).total_seconds()/60,
        excluded_future_forecasts=excluded_future,cohorts=[cohorts[k] for k in sorted(cohorts)],
        interpretation='Target-matching coverage, not accuracy. Expired missing targets have no score, not zero error. Pending forecasts excluded from resolved denominator.')

def record_snapshot(rows,metadata,now=None,folder=None):
    now=now or datetime.now(timezone.utc).isoformat();folder=Path(folder or ROOT/'data/processed/singapore_prospective');folder.mkdir(parents=True,exist_ok=True)
    forecast_path=folder/'forecasts.jsonl';score_path=folder/'scores.jsonl'
    existing=load_records(forecast_path);scores=load_records(score_path)
    additions=score_baseline(existing,rows,now,{r['forecast_id'] for r in scores})
    identifiers={r['forecast_id'] for r in existing}
    frozen=[dict(**r,snapshot_path=metadata['path']) for r in freeze_baseline(rows,now) if r['forecast_id'] not in identifiers]
    for path,records in [(score_path,additions),(forecast_path,frozen)]:
        if records:
            with path.open('a',encoding='utf-8',newline='\n') as stream:
                for record in records:stream.write(json.dumps(record)+'\n')
    total=scores+additions
    summary=dict(checked_at=now,source_id=SOURCE,snapshot_path=metadata['path'],forecasts_added=len(frozen),scores_added=len(additions),
        forecasts_total=len(existing)+len(frozen),scores_total=len(total),
        baseline_mae_spaces=sum(r['absolute_error_spaces'] for r in total)/len(total) if total else None,
        neural_accuracy_evaluated=False,camera_accuracy_evaluated=False,
        protocol='Freeze persistence at issue time, then score only later fresh same-source/same-capacity observations 20-45 minutes later. No exact 30-minute accuracy claim.',
        missing_target_policy='No score or invented zero where matching later observation is unavailable')
    summary['forecast_coverage']=ledger_status(existing+frozen,total,now)
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary
