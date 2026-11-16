"""One train-only absolute-error trend learner for aggregate availability.

Fit an unclipped space-count increment objective. Clip predictions to physical
bounds afterwards; this does not claim to optimize the clipped loss globally.
"""
import math
import re
from .singapore_history import aware_utc

METHOD = 'same_source_lad_trend_v1'


def _count(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r'0|[1-9][0-9]*', value):
        return int(value)
    raise ValueError('Counts must be nonnegative integers')


def causal_trend(row):
    """Use only two counts already available at issue; never a future lead."""
    capacity = _count(row['capacity'])
    current = _count(row['origin_available'])
    previous = _count(row['previous_available'])
    issue = aware_utc(row['issued_at'])
    origin_at = aware_utc(row['origin_available_at'])
    previous_at = aware_utc(row['previous_available_at'])
    observed = aware_utc(row['origin_observed_at'])
    prior_observed = aware_utc(row['previous_observed_at'])
    gap = (observed-prior_observed).total_seconds()/60
    supplied_gap = float(row['previous_gap_minutes'])
    if (capacity <= 0 or current > capacity or previous > capacity
            or not previous_at < origin_at <= issue
            or observed > origin_at or prior_observed > previous_at
            or not 10 <= gap <= 45 or not math.isfinite(supplied_gap)
            or not math.isclose(gap, supplied_gap, abs_tol=1e-8)):
        raise ValueError('Invalid or unavailable causal trend context')
    return current, capacity, (current-previous)*30/gap


def fit_trend(rows):
    """Minimize sum|target-current-alpha*past_30min_change|, alpha in [0,1].

    Each nonzero change contributes ratio (target-current)/change with weight
    abs(change). The lower weighted median is a minimizer before restricting
    alpha; clipping it gives a constrained minimizer. Zero-change rows add only
    a constant. Tie selection is deterministic and never consults development.
    """
    if not rows:
        raise ValueError('Training examples are required')
    ratios = []
    for row in rows:
        current, capacity, change = causal_trend(row)
        target = _count(row['target_available'])
        if target > capacity:
            raise ValueError('Training target outside capacity')
        if change:
            ratios.append(((target-current)/change, abs(change)))
    coefficient = 0.0
    if ratios:
        ratios.sort(key=lambda pair: pair[0])
        half = math.fsum(weight for _, weight in ratios)/2
        cumulative = 0.0
        for ratio, weight in ratios:
            cumulative += weight
            if cumulative >= half:
                coefficient = max(0.0, min(1.0, ratio))
                break
    return dict(method=METHOD, coefficient=coefficient, nominal_horizon_minutes=30,
                coefficient_bounds=[0, 1], training_examples=len(rows),
                informative_training_examples=len(ratios),
                objective='Unclipped space-increment absolute error; no intercept',
                prediction='Last count plus coefficient times past 30min change, clipped to capacity',
                preprocessing='None; coefficient fit on training rows only')


def predict_available(model, rows):
    coefficient = model['coefficient']
    if (model['method'] != METHOD or model['nominal_horizon_minutes'] != 30
            or type(coefficient) not in (int, float)
            or not math.isfinite(coefficient) or not 0 <= coefficient <= 1):
        raise ValueError('Invalid frozen trend model')
    result = []
    for row in rows:
        current, capacity, change = causal_trend(row)
        result.append(float(max(0, min(capacity, current+coefficient*change))))
    return result
