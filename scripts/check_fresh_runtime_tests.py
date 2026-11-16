"""Run the existing regression suite in the fresh app environment without network."""
import json,os,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/fresh_runtime_unit_tests')
attempts=[]


def audit(event,args):
    if event in {'socket.connect','socket.getaddrinfo'}:
        attempts.append(event);raise PermissionError('Network blocked during fresh-runtime regressions')


if __name__=='__main__':
    assert Path(sys.prefix).resolve()!=Path(sys.base_prefix).resolve()
    sys.addaudithook(audit)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    evidence=ROOT/'experiments/evidence/HEARTBEAT-20261025T204537Z/fresh_unit_test_summary.json'
    evidence.write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        success=result.wasSuccessful(),network_attempts=attempts,python_executable=sys.executable,
        prefix=sys.prefix,base_prefix=sys.base_prefix,scope='Existing regression suite in new app-only venv;not scientific accuracy or Jupyter execution'),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() and not attempts else 1)
