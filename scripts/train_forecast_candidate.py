"""Run one separately saved forecasting improvement experiment."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.forecast_experiment import train_candidate
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int,default=80);parser.add_argument('--patience',type=int,default=12)
    parser.add_argument('--seed',type=int,default=44);parser.add_argument('--variant',choices=['residual','trend_guard'],default='residual')
    args=parser.parse_args();print(json.dumps(train_candidate(args.epochs,args.patience,args.seed,args.variant),indent=2))
