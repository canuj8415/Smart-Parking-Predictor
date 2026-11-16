"""Install only the pinned video wheel into this project; shared environments stay unchanged."""
import json,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import download

if __name__=='__main__':
    url='https://pypi.org/pypi/opencv-python-headless/4.13.0.92/json'
    with urllib.request.urlopen(url,timeout=30) as response:metadata=json.load(response)
    wheel=next(item for item in metadata['urls'] if item['filename'].endswith('win_amd64.whl'))
    path=download('SRC-PKG-001',wheel['url'],'dependencies/wheels/'+wheel['filename'],
                  'Pinned local video decoder; Apache 2.0 package and bundled notices',wheel['digests']['sha256'])
    subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(ROOT/'dependencies/python'),str(path)],check=True)
    print('Installed project-local video dependency:',path.name)
