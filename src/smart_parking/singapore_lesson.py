"""Read only completed DEVELOPMENT evidence for the Singapore teaching lesson.

This module has no training, acquisition, issuance or final-scoring entry point.
It never opens raw observations, growing histories, future batches or claims.
"""
import csv
import json
import math
from html import escape
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from .provenance import ROOT, digest

ADMISSION = 'SG-HISTORY-20261026T074623970649Z'
RIDGE = 'SG-RIDGE-20261026T075317623534Z'
TREND = 'SG-LAD-20261026T081112980974Z'
RESERVATION = 'data/manifests/singapore_forecast_reservation_v1.json'
ISSUANCE = 'data/manifests/singapore_trend_issuance_v1.json'
SCORING = 'data/manifests/singapore_trend_scoring_v1.json'
FROZEN_HASHES = {
    RESERVATION: 'bd47defbec2e4e73388b4eb4ad8dd8d04528a04df15ae78242427ca93f5afaca',
    ISSUANCE: 'b68cf781fea32a16ee3d05914ff17c325bdd5594bec92f538811a1e711ac9625',
    SCORING: '1dc86326f3152ca090572041434e057980e151ee75ea4a2b8292f4385cb3aa1b'}


def _time(value):
    at = datetime.fromisoformat(value)
    if at.tzinfo is None:
        raise ValueError('Evidence timestamps require explicit timezones')
    return at


def pair_development(ridge, trend, historical_cutoff, training_cutoff):
    """Reject different cohorts, duplicate IDs, future rows and changed errors."""
    cutoff, split = _time(historical_cutoff), _time(training_cutoff)
    if not ridge or not trend or not split < cutoff:
        raise ValueError('Nonempty paired past-development evidence required')
    def indexed(rows):
        result = {}
        for row in rows:
            key = (row['car_park_id'], row['lot_type'], row['issued_at'])
            if key in result:
                raise ValueError('Duplicate development identity')
            result[key] = row
        return result
    a, b = indexed(ridge), indexed(trend)
    if a.keys() != b.keys():
        raise ValueError('Methods must share identical development windows')
    paired = []
    for key in sorted(a):
        first, second = a[key], b[key]
        base_a = {k: v for k, v in first.items() if k not in ['learned_available', 'learned_absolute_error']}
        base_b = {k: v for k, v in second.items() if k not in ['learned_available', 'learned_absolute_error']}
        if base_a != base_b:
            raise ValueError('Paired input/target evidence differs')
        issue = _time(second['issued_at']); target = _time(second['target_observed_at'])
        if (second['source_id'] != 'SRC-LIVE-001' or second['role'] != 'development'
                or not split <= issue < target <= _time(second['target_available_at']) <= cutoff
                or not _time(second['previous_available_at']) < _time(second['origin_available_at']) <= issue):
            raise ValueError('Noncausal, nondevelopment or post-cutoff row rejected')
        capacity = int(second['capacity']); actual = int(second['target_available'])
        origin = int(second['origin_available'])
        if capacity <= 0 or not 0 <= actual <= capacity or not 0 <= origin <= capacity:
            raise ValueError('Development counts outside physical capacity')
        for row in [first, second]:
            prediction = float(row['learned_available']); error = float(row['learned_absolute_error'])
            if (not math.isfinite(prediction) or not 0 <= prediction <= capacity
                    or not math.isclose(error, abs(prediction-actual), abs_tol=1e-9)
                    or not math.isclose(float(row['persistence_absolute_error']), abs(origin-actual), abs_tol=1e-9)):
                raise ValueError('Stored error does not match the paired observation')
        paired.append(dict(issued_at=second['issued_at'], persistence_error=abs(origin-actual),
                           ridge_error=float(first['learned_absolute_error']), trend_error=float(second['learned_absolute_error'])))
    return paired


def load_lesson(root=ROOT):
    root = Path(root)
    hashes = {}
    def load_json(name, expected=None):
        path = root/name; actual = digest(path)
        if expected is not None and actual != expected:
            raise ValueError('Frozen lesson input changed: '+name)
        hashes[name] = actual
        return json.loads(path.read_text(encoding='utf-8'))
    admission = load_json(f'experiments/results/{ADMISSION}/run.json')
    config = load_json(ISSUANCE, FROZEN_HASHES[ISSUANCE])
    scoring = load_json(SCORING, FROZEN_HASHES[SCORING])
    reservation = load_json(RESERVATION, FROZEN_HASHES[RESERVATION])
    ridge = load_json(f'experiments/results/{RIDGE}/run.json')
    trend = load_json(f'experiments/results/{TREND}/run.json', config['development_run_sha256'])
    selection = load_json('data/manifests/singapore_trend_frozen_selection_v1.json', config['selection_sha256'])
    model = load_json(f'experiments/results/{TREND}/model.json', selection['checkpoint_sha256'])
    csvs = []
    for run in [ridge, trend]:
        name = f"experiments/results/{run['run_id']}/observations.csv"
        if digest(root/name) != run['observations_sha256']:
            raise ValueError('Development CSV checksum changed')
        hashes[name] = run['observations_sha256']
        with (root/name).open(encoding='utf-8', newline='') as stream:
            csvs.append(list(csv.DictReader(stream)))
    paired = pair_development(*csvs, reservation['historical_cutoff'], reservation['training_cutoff'])
    n = len(paired)
    if n != 9202 or ridge['development_gate_passed'] or not trend['development_gate_passed']:
        raise ValueError('Lesson experiment identities/gate decisions differ')
    origins = defaultdict(list)
    for row in paired:
        origins[row['issued_at']].append(row)
    by_origin = [dict(issued_at=key, samples=len(rows), **{name: math.fsum(r[name] for r in rows)/len(rows)
                 for name in ['persistence_error', 'ridge_error', 'trend_error']}) for key, rows in sorted(origins.items())]
    maes = {name: math.fsum(r[name] for r in paired)/n for name in ['persistence_error', 'ridge_error', 'trend_error']}
    if (len(by_origin) != 9 or not math.isclose(maes['ridge_error'], ridge['candidate']['mae_spaces'], abs_tol=1e-9)
            or not math.isclose(maes['trend_error'], trend['candidate']['mae_spaces'], abs_tol=1e-9)
            or not math.isclose(maes['persistence_error'], trend['persistence']['mae_spaces'], abs_tol=1e-9)):
        raise ValueError('Recorded aggregate scores do not match stored paired errors')
    return dict(scope='Completed DEVELOPMENT evidence only; no new real evaluation', paired_windows=n,
        global_development_times=len(origins), historical_cutoff=reservation['historical_cutoff'],
        training_cutoff=reservation['training_cutoff'], coefficient=model['coefficient'],
        maes=maes, by_origin=by_origin, relative_development_gain=1-maes['trend_error']/maes['persistence_error'],
        training=admission['summary']['roles']['train'], development=admission['summary']['roles']['development'],
        final_origins=[reservation['final_origin_start'], reservation['final_origin_end']],
        final_closure=reservation['final_target_end'], final_gate=config['final_gate'],
        actual_final_result='Not loaded by this lesson', source_id='SRC-LIVE-001',
        licence='Singapore Open Data Licence 1.0; official data.gov.sg feed under accepted terms',
        rejected_ridge_run=RIDGE, selected_trend_run=TREND, scoring_frozen_at=scoring['frozen_at'], input_hashes=hashes)


def teaching_prediction(previous, current, gap_minutes, capacity, coefficient):
    """Pure synthetic arithmetic; never fits or saves the frozen candidate."""
    if (any(type(x) is not int for x in [previous, current, capacity]) or capacity <= 0
            or not 0 <= previous <= capacity or not 0 <= current <= capacity
            or type(gap_minutes) not in (int, float) or not math.isfinite(gap_minutes) or not 10 <= gap_minutes <= 45
            or type(coefficient) not in (int, float) or not math.isfinite(coefficient) or not 0 <= coefficient <= 1):
        raise ValueError('Teaching inputs must satisfy the frozen trend input bounds')
    change = (current-previous)*30/gap_minutes
    return dict(data_kind='synthetic_teaching_example', previous=previous, current=current,
        past_gap_minutes=gap_minutes, projected_30min_change=change, coefficient=coefficient,
        prediction=float(max(0, min(capacity, current+coefficient*change))), persistence_prediction=current,
        actual_future_value='Unknown; no synthetic result is treated as real accuracy')


def table_html(rows):
    """Escaped notebook tables using only standard Python; no pandas dependency."""
    if not rows:
        raise ValueError('At least one table row is required')
    columns = list(rows[0])
    if any(set(row) != set(columns) for row in rows):
        raise ValueError('All table rows must share the same columns')
    def text(value):
        if type(value) is float:
            value = f'{value:,.6f}'.rstrip('0').rstrip('.')
        return escape(str(value))
    return ('<table style="border-collapse:collapse;text-align:left">'
            '<thead><tr>'+''.join('<th style="padding:6px 12px;border-bottom:2px solid #64748b">'+text(c)+'</th>' for c in columns)
            +'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td style="padding:6px 12px;border-bottom:1px solid #cbd5e1">'+text(row[c])+'</td>' for c in columns)+'</tr>' for row in rows)
            +'</tbody></table>')


def plot_development(lesson):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={'width_ratios': [1, 1.7]})
    fig.patch.set_facecolor('#f8fafc')
    names = ['Last count', 'Ridge\n(rejected)', 'Trend\n(research)']
    values = [lesson['maes'][k] for k in ['persistence_error', 'ridge_error', 'trend_error']]
    axes[0].bar(names, values, color=['#64748b', '#d97706', '#0f766e'], width=.62)
    for index, value in enumerate(values):
        axes[0].text(index, value+.13, f'{value:.2f}', ha='center', fontsize=11, fontweight='bold')
    axes[0].set_ylim(0, max(values)*1.2)
    axes[0].set_ylabel('Mean absolute error (spaces)')
    axes[0].set_title('Same 9,202 development windows', loc='left', fontsize=12, pad=14)
    times = lesson['by_origin']; changes = [r['trend_error']-r['persistence_error'] for r in times]
    axes[1].bar(range(len(times)), changes, color=['#0f766e' if value <= 0 else '#b91c1c' for value in changes])
    axes[1].axhline(0, color='#475569', linewidth=.9)
    axes[1].axhline(.5, color='#b91c1c', linestyle='--', linewidth=.8)
    axes[1].text(8.4, .52, 'Frozen +0.5 limit', ha='right', fontsize=8, color='#991b1b')
    axes[1].set_xticks(range(len(times)), [_time(r['issued_at']).strftime('%d Oct\n%H:%M') for r in times], fontsize=8)
    axes[1].set_ylabel('Trend MAE minus last-count MAE (spaces)')
    axes[1].set_xlabel('Collection time (UTC)')
    axes[1].set_title('Nine collection times: negative means lower error', loc='left', fontsize=12, pad=14)
    for axis in axes:
        axis.spines[['top', 'right']].set_visible(False)
        axis.yaxis.set_major_locator(MaxNLocator(5))
        axis.grid(axis='y', alpha=.16); axis.set_axisbelow(True)
    fig.suptitle('Singapore forecasting: development evidence', x=.065, ha='left', fontsize=17, fontweight='bold')
    fig.text(.065, .02, 'Historical development only. Nine shared times are not thousands of independent days. No learned live/final score.', fontsize=9, color='#475569')
    fig.tight_layout(rect=[.02, .06, 1, .9])
    return fig
