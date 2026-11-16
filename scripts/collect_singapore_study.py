"""Source-compliant collection and qualified study issuance, without scoring it."""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.live import get_live
from smart_parking.prospective import record_snapshot
from smart_parking.singapore_issuance import issue_forecasts, load_candidate
from smart_parking.singapore_history import aware_utc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--issue-only', action='store_true', help='No network acquisition; use only a genuinely fresh receipted origin')
    args = parser.parse_args()
    config_path = ROOT/'data/manifests/singapore_trend_issuance_v1.json'
    load_candidate(config_path, ROOT)
    now = datetime.now(timezone.utc)
    report = dict(checked_at=now.isoformat(), source_id='SRC-LIVE-001', collection='not_requested',
                  learned_final_scoring='Disabled here; once-only final callback remains separate')
    if not args.issue_only:
        summary_path = ROOT/'data/processed/singapore_prospective/summary.json'
        previous = json.loads(summary_path.read_text(encoding='utf-8')) if summary_path.exists() else None
        if previous and now < aware_utc(previous['checked_at'])+timedelta(minutes=30):
            report['collection'] = 'not_due_under_30minute_history_plan'
            report['next_collection_after'] = (aware_utc(previous['checked_at'])+timedelta(minutes=30)).isoformat()
        else:
            rows, metadata = get_live(refresh=True)
            report['collection'] = 'cached' if metadata['cached'] else 'acquired'
            report['baseline'] = record_snapshot(rows, metadata)
    report['study_issuance'] = issue_forecasts(config_path)
    output = ROOT/'reports/singapore_issuance_latest.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
