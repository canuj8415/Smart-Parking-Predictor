import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecasting import train_forecast
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--epochs',type=int,default=18);p.add_argument('--horizon',type=int,choices=[30,60],default=30)
    args=p.parse_args();print(json.dumps(train_forecast(args.epochs,args.horizon//30),indent=2))
