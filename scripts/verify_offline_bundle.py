"""Additional genuine notebook checks in the copied fresh environment."""
import hashlib,json,os,runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
def main():
    mode=sys.argv[1]
    if mode=='app':runpy.run_path(str(ROOT/'scripts/verify_relocated_demo.py'),run_name='__main__');return
    if mode=='transactions':
        import io,socket,unittest
        from package_offline_guard import install
        output=ROOT/'outputs/transaction_check';output.mkdir(parents=True,exist_ok=False)
        save=install(ROOT,output/'audit.json');sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT))
        suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_export_transactions');stream=io.StringIO()
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        (output/'test_log.txt').write_text(stream.getvalue(),encoding='utf-8');assert result.wasSuccessful() and result.testsRun==13
        save();normal=json.loads((output/'audit.json').read_text());assert not normal['denied']
        try:socket.getaddrinfo('offline-negative-control.invalid',80)
        except PermissionError:pass
        else:raise AssertionError('Nonloopback negative control was not blocked')
        save();audit=json.loads((output/'audit.json').read_text());assert len(audit['denied'])==1
        report=dict(status='passed',synthetic_transaction_tests=13,normal_forbidden_attempts=0,negative_network_probe_blocked=True,
            python=sys.executable,prefix=sys.prefix,export_module_sha256=hashlib.sha256((ROOT/'src/smart_parking/exports.py').read_bytes()).hexdigest(),
            scope='Actual fresh copied environment;synthetic failures/fixtures,not model accuracy or physical disconnection',audit=audit)
        (ROOT/'EXPORT_TRANSACTION_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return
    from package_offline_guard import install
    output=ROOT/'outputs/notebook_check';output.mkdir(parents=True,exist_ok=False)
    save=install(ROOT,output/'controller_audit.json')
    import nbformat,nbclient,cv2,numpy,torch
    origins={m.__name__:str(m.__file__) for m in [nbformat,nbclient,cv2,numpy,torch]}
    assert all(Path(p).is_relative_to(Path(sys.prefix)) for p in origins.values())
    from execute_notebook import setup_kernel
    state=ROOT/'.notebook_state';setup_kernel(state)
    startup=state/'ipython/profile_default/startup';startup.mkdir(parents=True,exist_ok=True)
    (startup/'00-bundle-audit.py').write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(ROOT/'scripts'))+')\nfrom package_offline_guard import install\n_save_bundle=install('+repr(str(ROOT))+','+repr(str(output/'kernel_audit.json'))+')\nimport cv2\nassert Path(cv2.__file__).is_relative_to(Path(sys.prefix))\n',encoding='utf-8')
    source=ROOT/'notebooks/08_image_patterns_and_svd.ipynb';book=nbformat.read(source,as_version=4)
    for cell in book.cells:
        if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
    book.cells.insert(0,nbformat.v4.new_code_cell('import sys\nfrom pathlib import Path\nassert Path(sys.prefix)==Path('+repr(str(Path(sys.prefix)))+')\nprint("Package-local kernel:",sys.executable)'))
    nbclient.NotebookClient(book,timeout=180,startup_timeout=60,kernel_name='smart-parking-python',resources={'metadata':{'path':str(ROOT)}}).execute()
    nbformat.write(book,output/'08_executed.ipynb')
    pngs=sum('image/png' in o.get('data',{}) for c in book.cells if c.cell_type=='code' for o in c.outputs)
    assert pngs>=1 and all(o.output_type!='error' for c in book.cells if c.cell_type=='code' for o in c.outputs)
    save();kernel=json.loads((output/'kernel_audit.json').read_text(encoding='utf-8'));assert not kernel['denied']
    result=dict(status='passed',python=sys.executable,prefix=sys.prefix,origins=origins,all_modules_from_package_venv=True,
        actual_kernel_executed=True,inline_png_outputs=pngs,original_notebook_unchanged=True,kernel_audit=kernel,
        scope='Fresh copied-folder notebook08with extra diagnostic cell;no final data/no accuracy;Python fallback/network guard,not physical isolation')
    (ROOT/'NOTEBOOK_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
