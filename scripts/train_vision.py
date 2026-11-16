import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.training import train_vision
if __name__=='__main__':print(json.dumps(train_vision(),indent=2))
