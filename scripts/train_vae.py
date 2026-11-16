import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.generative import train_vae
if __name__=='__main__':print(json.dumps(train_vae(),indent=2))
