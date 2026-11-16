"""Record a fixed training-split demonstration without copying or editing data."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.demo_assets import select_training_demo,load_demo_assets

if __name__=='__main__':
    path=ROOT/'configs/demo_sample.json'
    if path.exists():record,_,_=load_demo_assets()
    else:
        record=select_training_demo();path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,indent=2))
