"""Bounded primary-source metadata checks; no image or label acquisition/use."""
import concurrent.futures,json,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import receipt,digest
def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'data/raw/cnrpark_research'/stamp;folder.mkdir(parents=True,exist_ok=False)
    urls=[('homepage_https','https://cnrpark.it/','GET'),('homepage_http','http://cnrpark.it/','GET'),
        ('patches_https','https://cnrpark.it/dataset/CNRPark-Patches-150x150.zip','HEAD'),('patches_http','http://cnrpark.it/dataset/CNRPark-Patches-150x150.zip','HEAD'),
        ('cnr_catalog','https://openportal.isti.cnr.it/doc?id=people______%3A%3A82a7de1e67ac2d1a64791ab662b78bfb','GET'),
        ('author_readme','https://raw.githubusercontent.com/fabiocarrara/deep-parking/master/README.md','GET')]
    def fetch(item):
        name,url,method=item;started=datetime.now(timezone.utc).isoformat()
        try:
            request=urllib.request.Request(url,method=method,headers={'User-Agent':'SmartParkingAcademic/0.3'})
            with urllib.request.urlopen(request,timeout=18) as response:
                body=response.read(1024**2+1) if method=='GET' else b''
                if len(body)>1024**2:raise ValueError('Metadata exceeds1MiBbound')
                result=dict(name=name,url=url,method=method,started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),
                    status=response.status,final_url=response.url,headers=dict(response.headers))
                if method=='GET':
                    path=folder/(name+('.md' if name=='author_readme' else '.html'))
                    with path.open('xb') as stream:stream.write(body)
                    result.update(path=path.relative_to(ROOT).as_posix(),sha256=digest(path),bytes=len(body))
                return result
        except Exception as error:return dict(name=name,url=url,method=method,started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),error=type(error).__name__,detail=str(error))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(fetch,urls))
    for row in results:
        if 'path' in row:receipt('SRC-DOC-012' if row['name']=='author_readme' else 'SRC-DS-002',ROOT/row['path'],row['url'],
            'Primary CNRPark source/access/licence metadata inspection; no image/label acquisition or operational use',metadata_only=True,retrieval_url=row['final_url'])
    result=dict(recorded_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-002',results=results,dataset_assets_acquired=False,licence_verified_for_operational_use=False)
    (folder/'access_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    E=ROOT/'experiments/evidence/HEARTBEAT-20261025T224739Z';E.mkdir(parents=True,exist_ok=True);(E/'primary_access.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([dict(name=r['name'],status=r.get('status'),error=r.get('error'),bytes=r.get('bytes')) for r in results],indent=2))
if __name__=='__main__':main()
