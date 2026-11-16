"""One public-feed collection and causal prospective baseline checkpoint."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.live import get_live
from smart_parking.prospective import record_snapshot
if __name__=='__main__':
    rows,metadata=get_live(refresh=True)
    print(json.dumps(record_snapshot(rows,metadata),indent=2))
