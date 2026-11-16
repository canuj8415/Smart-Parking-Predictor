"""Run project tests with import and temporary paths explicitly inside this workspace."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    temporary=(ROOT/'outputs/test_temp_project').resolve()
    if not temporary.is_relative_to(ROOT/'outputs'):raise ValueError('Unexpected test temporary directory')
    temporary.mkdir(parents=True,exist_ok=True)
    if not temporary.resolve().is_relative_to(ROOT/'outputs'):raise ValueError('Temporary root escaped workspace')
    env=os.environ.copy();env.update(TEMP=str(temporary),TMP=str(temporary),PYTHONPATH=str(ROOT/'src'))
    return subprocess.call([sys.executable,'-m','unittest','discover','-s','tests',*sys.argv[1:]],cwd=ROOT,env=env)

if __name__=='__main__':raise SystemExit(main())
