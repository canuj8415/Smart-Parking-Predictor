"""Supplementary launcher rejection and existing-suite checks; not model runs."""
import contextlib,io,json,os,runpy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T214738Z';E.mkdir(parents=True,exist_ok=True)
from offline_jupyter_guard import install
save=install(E/'regression_network.json',loopback=True)
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/server_regressions')
if __name__=='__main__':
    module=runpy.run_path(str(ROOT/'scripts/start_jupyter.py'));main=module['main'];negative=[]
    for args in [['--notebook','../README.md'],['--port','0'],['--port','65536']]:
        text=io.StringIO()
        with contextlib.redirect_stderr(text):
            try:main(args)
            except SystemExit as error:assert error.code==2
            else:raise AssertionError('Invalid launcher arguments unexpectedly started a server')
        negative.append(dict(args=args,exit_code=2,message=text.getvalue()))
    with (E/'regression_tests.txt').open('w',encoding='utf-8') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    save();network=json.loads((E/'regression_network.json').read_text(encoding='utf-8'))
    summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),success=result.wasSuccessful(),
        launcher_negative_checks=negative,python=sys.executable,non_loopback_python_network_attempts=network['denied'],
        scope='Existing suite in107-package app+Jupyter venv plus launcher rejection controls;not scientific accuracy,not all-eight notebook execution')
    (E/'regression_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2));raise SystemExit(0 if result.wasSuccessful() and not network['denied'] else 1)
