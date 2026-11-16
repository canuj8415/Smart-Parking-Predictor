"""Inspect saved real-kernel outputs and retain lossless PNG display evidence."""
import base64,hashlib,json,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    info=json.loads((ROOT/'reports/offline_jupyter_latest.json').read_text(encoding='utf-8'))
    output=ROOT/'outputs/notebook_validation'/info['run_id'];output.mkdir(parents=True,exist_ok=False)
    records=[]
    for key in ['executed_lesson08','executed_training_product']:
        path=ROOT/info[key];book=json.loads(path.read_text(encoding='utf-8'));images=[];code=[]
        for index,cell in enumerate(book['cells']):
            if cell['cell_type']!='code':continue
            assert cell['execution_count'] is not None;code.append(index)
            for item in cell.get('outputs',[]):
                assert item['output_type']!='error'
                data=item.get('data',{})
                if 'image/png' in data:
                    value=data['image/png'];value=''.join(value) if isinstance(value,list) else value
                    png=output/(key+'_'+str(len(images))+'.png');png.write_bytes(base64.b64decode(value,validate=True))
                    with Image.open(png) as image:size=image.size;image.verify()
                    images.append(dict(path=png.relative_to(ROOT).as_posix(),sha256=sha(png),dimensions=size,cell_index=index))
        assert images
        if key=='executed_lesson08':
            original=json.loads((ROOT/'notebooks/08_image_patterns_and_svd.ipynb').read_text(encoding='utf-8'))
            assert len(book['cells'])==len(original['cells'])+1
            assert all(c['source']==d['source'] and c['cell_type']==d['cell_type']
                for c,d in zip(original['cells'],book['cells'][1:]))
        records.append(dict(notebook=info[key],sha256=sha(path),code_cells=len(code),all_code_executed_without_errors=True,images=images))
    evidence=ROOT/'experiments/evidence/HEARTBEAT-20261025T211737Z/notebook_output_checks.json'
    evidence.write_text(json.dumps(dict(run_id=info['run_id'],notebooks=records,source_notebook_unchanged=True),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(notebooks=len(records),png_outputs=sum(len(r['images']) for r in records),output=str(output)),indent=2))
if __name__=='__main__':main()
