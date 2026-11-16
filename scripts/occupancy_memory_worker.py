"""Isolated,hidden,hard-capped software-resource fixture worker;no model calls."""
import argparse,hashlib,json,os,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
# Both workers import the same reference stack before measuring incremental RSS.
from smart_parking.vision import assign_occupancy
from smart_parking.occupancy_patches import assign_occupancy_patches,prepare_slot_patches
from smart_parking.occupancy_fixtures import large_case
import psutil

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--algorithm',choices=['reference','patches'],required=True);a=parser.parse_args();case=large_case();process=psutil.Process();baseline=process.memory_info().rss;peak=[baseline];stop=threading.Event()
    def monitor():
        while not stop.wait(.002):
            current=process.memory_info().rss;peak[0]=max(peak[0],current)
            if current>900*1024**2:os._exit(86)
    thread=threading.Thread(target=monitor,daemon=True);thread.start();clock=time.perf_counter()
    observations=(assign_occupancy if a.algorithm=='reference' else assign_occupancy_patches)(*case);duration=time.perf_counter()-clock;peak[0]=max(peak[0],process.memory_info().rss);stop.set();thread.join(.1)
    canonical=json.dumps(observations,sort_keys=True,separators=(',',':')).encode();slot_bytes=96*1920*1080 if a.algorithm=='reference' else sum(m.nbytes for _,m,_ in prepare_slot_patches(case[0],case[1]));print(json.dumps(dict(algorithm=a.algorithm,fixture='synthetic1920x1080/96slots/24boxes',duration_seconds=duration,baseline_rss_bytes=baseline,peak_rss_bytes=peak[0],incremental_peak_rss_bytes=peak[0]-baseline,rss_sampling_seconds=.002,slot_boolean_bytes=slot_bytes,observations_sha256=hashlib.sha256(canonical).hexdigest(),slots=len(observations),model_calls=0,camera_accuracy_evaluated=False)))

if __name__=='__main__':main()
