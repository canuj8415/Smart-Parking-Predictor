"""Bounded official CNR-EXT archive/metadata acquisition; no image decode/use."""
import json,sys,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest,receipt
def main():
    record=ROOT/'data/manifests/cnrpark_author_release_20261025.json';release=json.loads(record.read_text(encoding='utf-8'))['release']
    folder=ROOT/'data/raw/cnrpark_official';folder.mkdir(parents=True,exist_ok=True)
    expected=['CNRPark+EXT.csv','CNR-EXT-Patches-150x150.zip'];selected=[next(a for a in release['assets'] if a['name']==name) for name in expected]
    assert sum(a['size'] for a in selected)<=512*1024**2
    E=ROOT/'experiments/evidence/HEARTBEAT-20261025T224739Z';E.mkdir(parents=True,exist_ok=True)
    operation=dict(started_at=datetime.now(timezone.utc).isoformat(),source_id='SRC-DS-002',assets=[{k:a[k] for k in ['id','name','size','browser_download_url','updated_at','digest']} for a in selected],
        licence_basis='Publisher homepage explicitly declares CNRPark-EXT ODbL1.0; local acquisition/inspection only. Individual image-content terms and operational scope still to inspect.',
        purpose='Metadata/schema/rights/archive inspection and sealed grouping before any image model use',byte_budget=512*1024**2,images_decoded=False,training_or_scoring_performed=False)
    (E/'acquisition_operation.json').write_text(json.dumps(operation,indent=2)+'\n',encoding='utf-8')
    results=[]
    receipt('SRC-DS-002',record,'https://github.com/fabiocarrara/deep-parking/releases/tag/archive',
        'Official author release metadata returned by GitHub connector and serialized locally',metadata_only=True,original_http_bytes=False,exact_per_page_fetch_time_captured=False)
    for a in selected:
        path=folder/a['name'];partial=path.with_suffix(path.suffix+'.partial')
        if path.exists():raise FileExistsError('Preserve original completed assets:'+str(path))
        started=datetime.now(timezone.utc).isoformat();clock=time.monotonic()
        try:
            with urllib.request.urlopen(urllib.request.Request(a['browser_download_url'],headers={'User-Agent':'SmartParkingAcademic/0.3'}),timeout=45) as response,partial.open('xb') as stream:
                if response.headers.get('Content-Length') and int(response.headers['Content-Length'])!=a['size']:raise ValueError('Release/header size mismatch')
                transferred=0
                while chunk:=response.read(1024**2):
                    if (E/'CANCEL').exists() or time.monotonic()-clock>300:raise InterruptedError('Bounded acquisition cancelled/timed out')
                    transferred+=len(chunk)
                    if transferred>a['size'] or transferred>512*1024**2:raise ValueError('Source exceeds declared size/budget')
                    stream.write(chunk)
                if transferred!=a['size']:raise ValueError('Incomplete author artifact')
                final=response.url
            partial.replace(path)
            r=receipt('SRC-DS-002',path,a['browser_download_url'],'Original author artifact;inspection only,not yet training/scoring',
                retrieval_url=final,licence='Publisher-declared ODbL1.0 database;individual-content scope under inspection',
                publisher_asset_id=a['id'],publisher_asset_updated_at=a['updated_at'],publisher_checksum=a.get('digest'),
                checksum_basis='Local SHA256;publisher release does not provide a checksum',started_at=started,inspection_only=True)
            results.append(dict(name=a['name'],status='downloaded',receipt=r))
        except Exception as error:
            results.append(dict(name=a['name'],status='failed',error=type(error).__name__,detail=str(error),partial_retained=str(partial),started_at=started,finished_at=datetime.now(timezone.utc).isoformat()))
    (E/'acquisition_results.json').write_text(json.dumps(dict(results=results,images_decoded=False),indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k!='receipt'} for r in results],indent=2))
if __name__=='__main__':main()
