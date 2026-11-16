"""Reproduce quality checks and a chronological split, entirely in Python."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.data import prepare
if __name__ == '__main__':
    report = prepare(ROOT)
    print(json.dumps({k:v for k,v in report.items() if k not in {'car_park_coverage','limitations'}},indent=2))
