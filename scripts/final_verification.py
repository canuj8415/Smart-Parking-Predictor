"""Record final product artifact checks and actual test output without retraining."""
import csv,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import nbformat
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest

if __name__=='__main__':
    folder=ROOT/'experiments/evidence'/('FINAL-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True)
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,capture_output=True,text=True)
    (folder/'unit_tests.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
    if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
    notebooks={}
    for name in ['01_real_data_audit.ipynb','02_parking_product.ipynb']:
        path=ROOT/'notebooks'/name;nb=nbformat.read(path,as_version=4);nbformat.validate(nb)
        cells=[c for c in nb.cells if c.cell_type=='code']
        if any(c.execution_count is None for c in cells) or any(o.output_type=='error' for c in cells for o in c.outputs):raise ValueError('Notebook execution evidence incomplete')
        notebooks[name]=dict(executed_code_cells=len(cells),sha256=digest(path))
    with (ROOT/'data/source_manifest.csv').open(encoding='utf-8',newline='') as stream:sources=list(csv.DictReader(stream))
    if len(sources)!=len({r['source_id'] for r in sources}):raise ValueError('Duplicate source IDs')
    with (ROOT/'docs/REQUIREMENTS.csv').open(encoding='utf-8',newline='') as stream:tasks=list(csv.DictReader(stream))
    if len(tasks)!=len({r['requirement_id'] for r in tasks}):raise ValueError('Duplicate requirement IDs')
    broken=[]
    for path in [ROOT/'README.md',*(ROOT/'docs').glob('*.md')]:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if not target.startswith(('https:','http:','#')) and not (path.parent/target).exists():broken.append([path.name,target])
    if broken:raise ValueError('Broken links: '+str(broken))
    smoke=json.loads((ROOT/'models/product_smoke_summary.json').read_text());video=smoke.get('video_smoke')
    if not isinstance(video,dict) or video['processed_frames']<1:raise ValueError('Video integration not yet verified')
    result=dict(checked_at=datetime.now(timezone.utc).isoformat(),python=sys.version,interpreter=sys.executable,
        tests_passed=int(re.search(r'Ran (\d+) tests?',tests.stderr).group(1)),source_records=len(sources),requirement_rows=len(tasks),
        notebooks=notebooks,broken_links=broken,real_image_run=smoke['run_id'],counts=smoke['fasterrcnn']['counts'],
        video_fixture_frames_processed=video['processed_frames'],
        assets={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in (ROOT/'models/checkpoints').glob('*') if p.is_file()},
        caveats=['Small-subset classifier score, weak semantic mask, LSTM worse than persistence',
                 'No detector mAP or vehicle mask ground-truth metric','No physical offline rehearsal or full official audit',
                 'Desktop checks resumed after explicit user authorization; see docs/UI_TEST_LOG.md',
                 'Native export dialog typing could not be verified; export writer covered by regression tests'])
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
