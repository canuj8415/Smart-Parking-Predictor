"""Acquire the public, hash-pinned real-data source. No training."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.data import acquire
if __name__ == '__main__':
    print(acquire(ROOT, allow_download=True))
