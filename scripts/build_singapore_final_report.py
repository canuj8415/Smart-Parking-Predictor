"""Render the completed Singapore archive without opening raw targets or rescoring."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    saved = json.loads((ROOT/'reports/singapore_final_latest.json').read_text())
    path = ROOT/saved['result_path']
    assert digest(path) == saved['result_sha256']
    assert digest(path.parent/'completed.json') == saved['completion_sha256']
    report = json.loads(path.read_text()); metrics = report['metrics']
    outcome = ROOT/Path(report['claim_path']).with_suffix('.outcome.json')
    assert json.loads(outcome.read_text())['status'] == 'completed;interval consumed'
    folder = path.parent/'archived_report_v1'
    folder.mkdir(exist_ok=False)
    rows = [dict(issued_at=at, **value) for at, value in metrics['by_origin'].items()]
    with (folder/'by_origin.csv').open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    plt.rcParams.update({'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout='constrained')
    values = [metrics['persistence_same_cohort_mae_spaces'], metrics['learned_mae_spaces']]
    bars = axes[0].bar(['Persistence', 'Frozen trend'], values, color=['#718096', '#167d8d'])
    axes[0].bar_label(bars, fmt='%.3f', padding=4)
    axes[0].set(ylim=(0, max(values)*1.2), ylabel='Mean absolute error (parking spaces)',
                title=f"Same {metrics['matched']:,} matched forecasts\n{metrics['relative_improvement']:.1%} lower overall MAE")
    delta = [r['learned_mae']-r['persistence_mae'] for r in rows]
    axes[1].bar(range(1, len(rows)+1), delta, color=['#b53737' if d > .5 else '#167d8d' for d in delta])
    axes[1].axhline(.5, color='#b53737', linestyle='--', label='Frozen maximum regression: +0.5')
    axes[1].axhline(0, color='black', linewidth=.8)
    axes[1].set(xlabel='Matched global origin in chronological order',
                ylabel='Trend MAE minus persistence MAE (spaces)',
                title=f"Worst origin: +{max(delta):.3f} spaces\nOverall acceptance gate: FAILED")
    axes[1].set_xticks(range(1, len(rows)+1, 2)); axes[1].legend(fontsize=8)
    fig.suptitle('Singapore prospective availability study — archived final result', fontsize=14)
    fig.supxlabel(f"Coverage {metrics['matched_fraction']:.2%}; {metrics['expired_unmatched']:,} forecasts unmatched. "
                  'Actual target horizon 20–45 minutes. Aggregate availability, not camera accuracy.\n'
                  'Source: official data.gov.sg / Singapore Open Data Licence 1.0. No app-model promotion.', fontsize=9)
    fig.savefig(folder/'final_comparison.png', dpi=160); plt.close(fig)
    explanation = f'''# Singapore frozen prospective study

The frozen trend model reduced paired mean absolute error by {metrics['relative_improvement']:.2%},
from {values[0]:.6f} to {values[1]:.6f} parking spaces. The final acceptance gate FAILED:
the worst origin regressed by {metrics['worst_origin_mae_regression_spaces']:.6f} spaces,
exceeding the prespecified 0.5-space limit. No threshold was relaxed and no app model was promoted.

There were {metrics['forecasts']:,} genuine pre-target forecasts, {metrics['matched']:,} matched
later observations ({metrics['matched_fraction']:.2%}), {metrics['global_matched_origins']} matched
global origins and {metrics['matched_series']:,} carpark/lot-type series. Missing forecasts have
no invented target or zero error. Targets fall within the frozen 20–45-minute observation window;
this is not an exact 30-minute benchmark. Forecasts within an origin are correlated.

All seven frozen checks: {json.dumps(metrics['checks'], sort_keys=True)}.

The global final interval is consumed, including all carparks, aliases and failed evaluations.
Do not tune or retest a changed method on it. An overall average gain does not erase a failed
origin-retention gate. Any future method needs a new protocol and fresh future interval.
The Birmingham LSTM is a separate model; this result establishes no camera/segmentation/
occupancy accuracy or universal guarantee. Local acquisition/commit clocks are audit evidence,
not independent external timestamp attestations. Missed account-limit periods were not backfilled.

Source SRC-LIVE-001: official data.gov.sg parking availability; Singapore Open Data Licence 1.0.
This report renders saved metrics only. It does not open raw target JSON or run the scorer again.
Result: {report['run_id']}; SHA256 {digest(path)}.
'''
    (folder/'EXPLANATION.md').write_text(explanation, encoding='utf-8')
    artifacts = {p.relative_to(ROOT).as_posix(): digest(p) for p in folder.iterdir() if p.is_file()}
    (folder/'artifact_hashes.json').write_text(json.dumps(dict(input_result=saved, artifacts=artifacts,
        renderer_sha256=digest(Path(__file__)), raw_targets_opened=False, scientific_runs_added=0), indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())


if __name__ == '__main__':
    main()
