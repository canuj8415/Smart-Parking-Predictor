import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.segmentation_experiment import train_known_camera
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resume-preparation',action='store_true');args=parser.parse_args()
    print(json.dumps(train_known_camera(resume_preparation=args.resume_preparation),indent=2),flush=True)
