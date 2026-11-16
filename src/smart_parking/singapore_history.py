"""Receipt-timed,source-consistent historical admission for availability forecasts."""
from collections import defaultdict,Counter
from datetime import datetime,timedelta,timezone
from .prospective import instant,SOURCE


def aware_utc(value):
    at=datetime.fromisoformat(value)
    if at.tzinfo is None:raise ValueError('Collection/issue/cutoff times need an explicit offset')
    return at.astimezone(timezone.utc)


def canonical_observation(row,available_at,snapshot,sha256):
    """The acquisition receipt supplies availability time,never source time/mtime."""
    if row.get('source_id')!=SOURCE:raise ValueError('Wrong canonical source')
    if any(not isinstance(row.get(k),str) or not row[k].strip() for k in ['car_park_id','lot_type']):raise ValueError('Missing series identity')
    cap,available=row['capacity'],row['available']
    if type(cap) is not int or type(available) is not int or cap<=0 or not 0<=available<=cap:raise ValueError('Invalid count/capacity')
    collected=aware_utc(available_at);observed=instant(row['observed_at']);feed=instant(row['feed_timestamp'])
    if observed>feed or feed-observed>timedelta(minutes=3):raise ValueError('Observation/source lag invalid')
    if not timedelta(seconds=-30)<=collected-feed<=timedelta(minutes=3):raise ValueError('Feed not fresh at receipt')
    if not timedelta(seconds=-30)<=collected-observed<=timedelta(minutes=3):raise ValueError('Observation not fresh at receipt')
    return dict(source_id=SOURCE,car_park_id=row['car_park_id'],lot_type=row['lot_type'],capacity=cap,available=available,
        available_at=collected.isoformat(),observed_at=observed.isoformat(),feed_timestamp=feed.isoformat(),
        source_observed_text=row['observed_at'],source_feed_text=row['feed_timestamp'],snapshot=snapshot,snapshot_sha256=sha256)


def deduplicate_observations(records):
    """Keep first receipt for exact duplicates;quarantine all conflicting revisions."""
    groups=defaultdict(list)
    for row in records:groups[(row['car_park_id'],row['lot_type'],row['observed_at'])].append(row)
    accepted=[];conflicts=[];duplicates=0
    for key,rows in sorted(groups.items()):
        values={(r['capacity'],r['available']) for r in rows}
        if len(values)>1:
            conflicts.append(dict(series=list(key[:2]),observed_at=key[2],versions=rows));continue
        ordered=sorted(rows,key=lambda r:(aware_utc(r['available_at']),r['snapshot']))
        accepted.append(ordered[0]);duplicates+=len(ordered)-1
    return sorted(accepted,key=lambda r:(aware_utc(r['available_at']),r['car_park_id'],r['lot_type'])),conflicts,duplicates


def causal_examples(records,history_cutoff,train_cutoff):
    """Two known same-capacity observations predict a later fresh20-45min target.

    Select the first RECEIVED qualifying target. The train label must itself
    arrive before the global training cutoff. No interpolation or gap filling.
    """
    cutoff=aware_utc(history_cutoff);split=aware_utc(train_cutoff)
    if not split<cutoff:raise ValueError('Training cutoff must precede historical cutoff')
    series=defaultdict(list)
    for row in records:
        if row['source_id']!=SOURCE:raise ValueError('Wrong source')
        if any(aware_utc(row[k])>cutoff for k in ['available_at','observed_at','feed_timestamp']):raise ValueError('Observation exceeds frozen history cutoff')
        series[(row['car_park_id'],row['lot_type'])].append(row)
    examples=[];excluded=Counter()
    for identity,rows in sorted(series.items()):
        rows=sorted(rows,key=lambda r:(aware_utc(r['available_at']),aware_utc(r['observed_at'])))
        previous=None
        for index,origin in enumerate(rows):
            issue=aware_utc(origin['available_at']);observed=aware_utc(origin['observed_at'])
            if previous is None:previous=origin;excluded['no_previous_observation']+=1;continue
            if observed<=aware_utc(previous['observed_at']):excluded['out_of_order_source_time']+=1;continue
            old=previous;previous=origin
            gap=(observed-aware_utc(old['observed_at'])).total_seconds()/60
            if old['capacity']!=origin['capacity']:excluded['previous_capacity_changed']+=1;continue
            if not 10<=gap<=45:excluded['previous_gap_outside10to45min']+=1;continue
            target=None
            for candidate in rows[index+1:]:
                arrival=aware_utc(candidate['available_at']);target_at=aware_utc(candidate['observed_at']);feed=aware_utc(candidate['feed_timestamp'])
                if arrival>issue+timedelta(minutes=51):break
                if candidate['capacity']!=origin['capacity']:break
                if not issue<target_at<=feed<=arrival+timedelta(seconds=30):continue
                if issue+timedelta(minutes=20)<=target_at<=issue+timedelta(minutes=45):target=candidate;break
            if target is None:excluded['no_admissible_later_target']+=1;continue
            target_available=aware_utc(target['available_at'])
            if issue<split and target_available<=split:role='train'
            elif issue>=split:role='development'
            else:excluded['training_label_arrived_after_train_cutoff']+=1;continue
            cap=origin['capacity'];latest=origin['available'];prior=old['available']
            examples.append(dict(source_id=SOURCE,car_park_id=identity[0],lot_type=identity[1],capacity=cap,role=role,
                issued_at=issue.isoformat(),origin_observed_at=origin['observed_at'],origin_available_at=origin['available_at'],
                previous_observed_at=old['observed_at'],previous_available_at=old['available_at'],previous_gap_minutes=gap,
                origin_available=latest,previous_available=prior,origin_fraction=latest/cap,previous_fraction=prior/cap,
                past_fraction_change_per_minute=(latest-prior)/(cap*gap),nominal_forecast_minutes=30,
                target_observed_at=target['observed_at'],target_available_at=target['available_at'],target_available=target['available'],
                actual_target_lead_minutes=(aware_utc(target['observed_at'])-issue).total_seconds()/60,
                persistence_absolute_error=abs(latest-target['available']),origin_snapshot=origin['snapshot'],previous_snapshot=old['snapshot'],target_snapshot=target['snapshot']))
    return examples,dict(excluded)
