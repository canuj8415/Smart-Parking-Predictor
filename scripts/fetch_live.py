import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.live import get_live
if __name__=='__main__':
    rows,metadata=get_live(refresh=True)
    print(json.dumps(dict(metadata=metadata,observations=len(rows),car_parks=len({r['car_park_id'] for r in rows}),sample=rows[:2]),indent=2))
